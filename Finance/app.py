from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Collect all important information about user's stocks to show it in HTML
    user_id = session.get("user_id")

    # List of dictionaries for all user stocks
    user_stocks = db.execute(
        "SELECT stock_symbol, shares_number FROM user_stocks WHERE user_id = ?", user_id
    )

    # Variable to see how much different stocks user has
    count = 0

    # Creating dictionary for all info to display in index.html
    all_user_stocks = []
    for row in user_stocks:
        symbol = row["stock_symbol"]
        stock_info = lookup(symbol)
        dict = {
            "symbol": symbol,
            "name": stock_info["name"],
            "shares": row["shares_number"],
            "price": stock_info["price"],
            "total": row["shares_number"] * stock_info["price"],
        }
        all_user_stocks.append(dict)
        count += 1

    # Select how much money is in user's wallet
    wallet_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    wallet_cash = wallet_cash[0]["cash"]

    # Select how much money user has in wallet + in stocks
    total_cash = 0
    for row in all_user_stocks:
        total_cash += row["total"]
    total_cash += wallet_cash

    return render_template(
        "index.html",
        all_user_stocks=all_user_stocks,
        wallet_cash=wallet_cash,
        total_cash=total_cash,
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Check if user wrote stock symbol and if it's in database
        symbol = request.form.get("symbol").upper()
        company_stock_info = lookup(symbol)
        if company_stock_info == None:
            return apology("write a proper company stock symbol", 400)

        # Check if user wrote a number of shares
        shares_number = request.form.get("shares")
        if shares_number == "" or not shares_number.isnumeric():
            return apology("write the number of stocks to buy", 400)

        # Check if user wrote a proper number of shares grater than 0
        if int(shares_number) <= 0:
            return apology("write a proper number of stocks to buy", 400)

        # Check if user has enough money to buy these stocks
        user_id = session.get("user_id")
        user_money = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        user_money = user_money[0]["cash"]
        if int(user_money) < (int(shares_number) * company_stock_info["price"]):
            return apology("you do not have enough money to buy these stocks", 400)

        # If evething is ok then add stocks history database
        username = db.execute("SELECT username FROM users WHERE id = ?", user_id)
        username = username[0]["username"]
        stock_price = company_stock_info["price"]
        total_price = stock_price * int(shares_number)
        db.execute(
            "INSERT INTO stocks_history VALUES (?, ?, ?, ?, ?, ?, datetime(), 'buy')",
            user_id,
            username,
            symbol,
            shares_number,
            stock_price,
            total_price,
        )

        # Update user's virtual wallet
        new_cash_amount = user_money - total_price
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash_amount, user_id)

        # Update user's stock amount in user_stocks database
        # If it is first purchase of company stock
        list = db.execute(
            "SELECT * FROM user_stocks WHERE stock_symbol = ? and user_id = ?",
            symbol,
            user_id,
        )
        if not list:
            db.execute(
                "INSERT INTO user_stocks VALUES (?, ?, ?)",
                user_id,
                symbol,
                shares_number,
            )
        else:
            # Check amount of chosen stocks already on user's account
            total_stock_amount = db.execute(
                "SELECT shares_number FROM user_stocks WHERE stock_symbol = ? and user_id = ?",
                symbol,
                user_id,
            )
            total_stock_amount = int(total_stock_amount[0]["shares_number"]) + int(shares_number)
            db.execute(
                "UPDATE user_stocks SET shares_number = ? WHERE stock_symbol = ? and user_id = ?",
                total_stock_amount,
                symbol,
                user_id,
            )

        # Redirect user to the homepage
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Store all info about user's trnsactions
    user_id = session.get("user_id")
    shares_history = db.execute("SELECT * FROM stocks_history WHERE user_id = ?", user_id)
    return render_template("history.html", shares_history=shares_history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        symbol = request.form.get("symbol")
        company_stock_info = lookup(symbol)
        try:
            price = usd(company_stock_info["price"])
        except:
            return apology("quoted company does not exist", 400)

        # Redirect user to quoted.html template
        return render_template("quoted.html", company_stock_info=company_stock_info, price=price)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # If user submitted a form via POST
    if request.method == "POST":
        # Check if username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Check if password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Check if confirmation of the password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation of the password", 400)

        # Check if password and confirmation of the password are the same
        if not request.form.get("password") == request.form.get("confirmation"):
            return apology("entered different passwords", 400)

        # Check if username is already taken
        rows = db.execute("SELECT username FROM users")
        for row in rows:
            if request.form.get("username") == row["username"]:
                return apology("this username is already taken", 400)

        # Create hashed password of the user
        hash = generate_password_hash(
            request.form.get("password"), method="pbkdf2", salt_length=16
        )

        # Query database to INSERT new user
        db.execute("INSERT INTO users (username, hash) VALUES (?,?)", request.form.get("username"), hash)

        # Redirect user to home page
        return redirect("/")

    # Else user reached route via GET
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Check user's id and username
    user_id = session.get("user_id")
    username = db.execute("SELECT username FROM users WHERE id = ?", user_id)
    username = username[0]["username"]

    # If user reached it via POST
    if request.method == "POST":
        # Check if it's possible to sell amount of chosen stocks user demand to sell
        # Chosen stocks to sell
        chosen_stocks = request.form.get("symbol")
        if chosen_stocks is None:
            return apology("must chose stocks to sell", 403)
        # Chosen amount of stocks to sell
        chosen_stocks_amount = int(request.form.get("shares"))
        # Real amount of stocks in user wallet
        real_stocks_amount = db.execute("SELECT shares_number FROM user_stocks WHERE stock_symbol = ? and user_id = ?", chosen_stocks, user_id)
        try:
            real_stocks_amount = real_stocks_amount[0]["shares_number"]
            if chosen_stocks_amount > real_stocks_amount:
                return apology("not enough stocks to sell", 403)
        except:
            return apology("not enough stocks to sell", 403)
        # If it's OK then sell chosen stocks: reduce amount of stocks in user_stocks database and make a record in stocks_history database
        stock_value = lookup(chosen_stocks)
        stock_value = stock_value["price"]
        sold_stocks_value = stock_value * chosen_stocks_amount
        new_stock_amount = real_stocks_amount - chosen_stocks_amount
        db.execute("UPDATE user_stocks SET shares_number = ? WHERE stock_symbol = ? and user_id = ?", new_stock_amount, chosen_stocks, user_id)
        db.execute("INSERT INTO stocks_history VALUES (?, ?, ?, ?, ?, ?, datetime(), 'sell')", user_id, username, chosen_stocks, chosen_stocks_amount, stock_value, sold_stocks_value)

        # Add cash from sold stocks to user wallet
        user_money = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        user_money = user_money[0]["cash"]
        new_cash_amount = user_money + sold_stocks_value
        print(new_cash_amount)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash_amount, user_id)

        # If user sold all stocks of chosen company delete record from user_stocks database
        num = db.execute("SELECT shares_number FROM user_stocks WHERE stock_symbol = ? and user_id = ?;", chosen_stocks, user_id)
        num = num[0]["shares_number"]
        if num == 0:
            db.execute("DELETE FROM user_stocks WHERE stock_symbol = ? and user_id = ?;", chosen_stocks, user_id)
        return redirect("/")

    else:
        # Dict of user's symbols
        symbols = db.execute("SELECT stock_symbol FROM user_stocks WHERE user_id = ?", user_id)
        return render_template("sell.html", symbols=symbols)
