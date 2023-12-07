from flask import Flask, render_template, session, request, flash
import mysql.connector
from db_config import DATABASE_CONFIG

# Function to show user that something gone wrong
def apology(msg, code):
    return render_template("apology.html", code=code, msg=msg)

def is_logged_in():
    if session.get("user_id") is None:
        return False
    return True

# Initialize database connection
def connect_to_database():
    try:
        db = mysql.connector.connect(**DATABASE_CONFIG)
        return db, None
    except mysql.connector.Error as err:
        return None, err
    
# Close database connection
def close_database(db, cursor):
    cursor.close()
    db.close()

# Check if user correctly answered and if so add 1 score to
def user_answer():
    # Select user id
    user_id = session["user_id"]

    # Check if user answered correctly
    user_choice = request.form.get("option")
    correct_ans = session["correct_ans"]

    # Show a result to user and add score point to user account
    if user_choice == correct_ans:

        flash("You answered correctly!")

        db, db_error = connect_to_database()

        if db is None:
            return apology(f"Database error: {db_error}", 500)
        
        cursor = db.cursor()

        try:
            cursor.execute("UPDATE users SET score = score + 1 WHERE id = %s", (user_id, ))
            db.commit()
        except mysql.connector.Error as err:
            close_database(db, cursor)
            return apology(f"Database error: {err}", 500)
        
        close_database(db, cursor)
    else:
        flash("You are incorrect...")
