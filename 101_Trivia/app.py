from flask import Flask, render_template, redirect, request, session, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
import openai
import os
from dotenv import load_dotenv
from random import randint
from helpers import apology, is_logged_in, user_answer, connect_to_database, close_database

# Load variables from .env file
load_dotenv()  

# Configure application
app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():  
    if is_logged_in() == False:
        return redirect("/login") 
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget user_id
    session.clear()

    # If user submitted via POST
    if request.method == "POST":
        # Check if username was submitted
        if not request.form.get("username"):
            return apology("Please provide username", 403)
        
        # Check if password was submitted
        elif not request.form.get("password"):
            return apology("Please provide password", 403)
        
        # Get user input
        username = request.form.get("username")
        password = request.form.get("password")

        # Search if submitted data is in database
        db, db_error = connect_to_database()

        if db is None:
            return apology(f"Database error: {db_error}", 500)
        
        cursor = db.cursor(dictionary=True)

        # Query database for user data
        cursor.execute("SELECT * FROM users WHERE username = %s", (username, ))
        rows = cursor.fetchall()

        # Check if user exist in database
        if not rows:
            close_database(db, cursor)
            return apology("User doesn't exist", 403)
        
        # Check if username and password are correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], password):
            close_database(db, cursor)
            return apology("Invalid username and~sor password", 403)
        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        
        # Redirect to homepage and close connection with database
        close_database(db, cursor)
        return redirect("/")
    
    # Else user sumbitted via GET
    else:
        # Render login template
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # If user submitted via POST
    if request.method == "POST":
        # Check if username was submitted
        if not request.form.get("username"):
            return apology("Please provide username", 403)
        
        # Check if password was submitted
        elif not request.form.get("password"):
            return apology("Please provide password", 403)
        
        # Check if repetition of the password was submitted
        elif not request.form.get("repeat"):
            apology("Please provide password repetition", 403)
        
        # Get user input
        username = request.form.get("username")
        password = request.form.get("password")

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2', salt_length=16)

        #Insert user data into database
        db, db_error = connect_to_database()

        if db is None:
            return apology(f"Database error: {db_error}", 500)
        
        cursor = db.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            db.commit()
        except:
            close_database(db, cursor)
            return apology("User already exists", 403) 
               
        # Return to login template and close database connection
        close_database(db, cursor)
        return redirect("/login")
    
    # Else if user submitted via GET
    else:
        # Render register template
        return render_template("register.html")
    
@app.route("/logout")
def logout():
    # Forget user_id
    session.clear()
    # Redirect user to login form
    return redirect("/login")

@app.route("/game-topic", methods=["GET", "POST"])
def game_topic():
    # If user submitted via POST
    if request.method == "POST":

        # Get user input
        topic = request.form.get("topic")
        
        # Check if user submitted one word in english topic
        for letter in topic:
            if letter == " ":
                return apology("Your topic word wasn't described in one word", 403)
        
        # Take user chosen topic
        session["topic"] = topic

        # Redirect to the creative game
        return redirect("/creative-game")
    # Else user submitted via GET
    else:
        return render_template("game-topic.html")

@app.route("/creative-game", methods=["GET", "POST"])
def creative_game():
    if request.method == "POST":
        user_answer()
        return redirect("/game-topic")
    else:
        # Render chosen ABCD question
        topic = session["topic"]

        # OPENAI API key import
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # Variable to counter gpt model trials
        n = 0

        # List to store question info
        question_info = []

        # Variable to store answers
        answers = ""

        # Loop until list has 5 elements or answers are "A,B,C,D"
        while (len(question_info) != 5 or answers.find("A,B,C,D") != -1) :
            if n == 3:
                break
            try:
                completion = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo-0613",
                temperature = 1,
                    messages=[
                        {"role": "system", "content": "You are a master of creating trivia questions and answers to them"},
                        {"role": "user", "content": f"Make one trivia question about {topic} in csv format with columns: question, ans_a, ans_b, ans_c, ans_d, correct_ans. Only last answer should be: A, B, C or D."}
                        ]
                        )
            except:
                flash("Sorry, it's hard to build a question out of your word...")
                return redirect("/game-topic")            
            
            # Separate question info from ai model output
            output = completion.choices[0].message["content"]

            # Split output to values only 
            output = output.split("\n")[1]

            # Variables to store separated question
            question = output.split("?")[0] + '?'
            answers = output.split("?")[1]

            # Slice comma after question column and strip from blank signs and quotes both answers and question
            answers = answers.strip(' "')
            answers = answers[1:]
            question =question.strip(' "')

            # Make a list of information for creative game
            question_info = answers.split(",")

            # Initizalize  rest of required variables to play creative game, strip answers from blank signs and quotes
            try:
                ans_a = question_info[0].strip(' "')
                ans_b = question_info[1].strip(' "')
                ans_c = question_info[2].strip(' "')
                ans_d = question_info[3].strip(' "')
                correct_ans = question_info[4].upper().strip(' "')
            except:
                flash("Sorry, it's hard to build a question out of your word...")
                return redirect("/game-topic")

            # Set correct answer to check if user will be right
            session["correct_ans"] = correct_ans

            # Number of trials
            n += 1
        # If too many wrong outputs
        if n == 3:
            flash("Sorry, it's hard to build a question out of your word...")
            return redirect("/game-topic")

        # Render game template
        return render_template("creative-game.html", question=question, ans_a=ans_a, ans_b=ans_b, ans_c=ans_c, ans_d=ans_d)
    
@app.route("/ranking")
def ranking():

    # Select user information required to display in ranking.html
    db, db_error = connect_to_database()

    if db is None:
        return apology(f"Database error: {db_error}", 500)
    
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT username, score FROM users ORDER BY score DESC")
    users_info = cursor.fetchall()

    # Close connection with database
    close_database(db, cursor)

    # Render ranking.html
    return render_template("ranking.html", users_info=users_info)

@app.route("/challenge-game", methods=["GET", "POST"])
def challenge_game():
    # If user sebmitted via POST
    if request.method == "POST":
        user_answer()
        return redirect("/challenge-game")
    else:
        # Select questions to display them in challenge-game.html
        db, db_error = connect_to_database()

        if db is None:
            return apology(f"Database error: {db_error}", 500)

        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT MAX(id) FROM questions")
        questions_number = cursor.fetchone()
        
        # Set random question for the user
        new_question_id = randint(1, int(questions_number["MAX(id)"]))
        
        # Select question information 
        cursor.execute("SELECT * FROM questions WHERE id = %s", (new_question_id, ))
        question = cursor.fetchone()
        session["correct_ans"] = question["correct_ans"]
        
        return render_template("challenge-game.html", question=question)

if __name__  == "__main__":
    app.run()