import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///revelation.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        userrow = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
        return render_template("index.html", users=userrow)


@app.route("/profile_articles")
@login_required
def index():
    if session.get("user_id") is None:
        return render_template("profile_articles.html")
    else:
        userrow = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
        return render_template("index.html", users=userrow)

@app.route("/profile_favorites")
@login_required
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        userrow = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
        return render_template("index.html", users=userrow)

@app.route("/profile_settings")
@login_required
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        userrow = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
        return render_template("index.html", users=userrow)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user for an account."""

    # POST
    if request.method == "POST":

        # Validate form submission
        if not request.form.get("fname"):
            error = 'Missing first name'
            return render_template('register.html', error=error)
        elif not request.form.get("lname"):
            error = 'Missing last name'
            return render_template('register.html', error=error)
        elif not request.form.get("uname"):
            error = 'Missing username'
            return render_template('register.html', error=error)
        elif not request.form.get("pword"):
            error = 'Missing password'
            return render_template('register.html', error=error)
        elif not request.form.get("email"):
            error = 'Missing email'
            return render_template('register.html', error=error)
        elif not request.form.get("school"):
            error = 'Missing school'
            return render_template('register.html', error=error)
        elif not request.form.get("hsc"):
            error = 'Missing high school/undegraduate'
            return render_template('register.html', error=error)
        elif not request.form.get("re"):
            error = 'Missing researcher/editor'
            return render_template('register.html', error=error)

        usernamerows = db.execute("SELECT * FROM users WHERE user_id = ?", request.form.get("uname"))
        if len(usernamerows) > 0:
            error = 'Username already taken'
            return render_template('register.html', error=error)

        emailrows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))
        if len(emailrows) > 0:
            error = 'Email already exists'
            return render_template('register.html', error=error)

        if request.form.get("hsc") == "hs":
            hscvalue = 0
        elif request.form.get("hsc") == "c":
            hscvalue = 1

        if request.form.get("re") == "r":
            revalue = 0
        elif request.form.get("re") == "e":
            revalue = 1

        # Add user to database
        db.execute("INSERT INTO users (firstname, lastname, username, password, email, school, hsc, re, bio) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            request.form.get("fname"),
                            request.form.get("lname"),
                            request.form.get("uname"),
                            generate_password_hash(request.form.get("pword")),
                            request.form.get("email"),
                            request.form.get("school"),
                            hscvalue,
                            revalue,
                            "Hello!")

        currentuser = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("uname"))

        # Log user in
        session["user_id"] = currentuser[0]["user_id"]

        # Let user know they're registered
        flash("Registered!")
        return redirect("/")

    # GET
    else:
        if session.get("user_id") is None:
            return render_template("register.html")
        else:
            return redirect("/")


@app.route("/article")
def article():
    if session.get("user_id") is None:
        if request.args.get("id") and request.args.get("id").isnumeric():
            articlerow = db.execute("SELECT * FROM articles WHERE article_id = ? AND status = 1", request.args.get("id"))
            if len(articlerow) > 0:
                authorrow = db.execute("SELECT * FROM users WHERE user_id = ?", articlerow[0]["primary_author_id"])
                editorrow = db.execute("SELECT * FROM users WHERE user_id = ?", articlerow[0]["editor"])
                return render_template("article.html", articles=articlerow, authors=authorrow, editors=editorrow)
            else:
                return redirect("/")
        else:
            return redirect("/")
    else:
        if request.args.get("id") and request.args.get("id").isnumeric():
            userrow = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
            articlerow = db.execute("SELECT * FROM articles WHERE article_id = ? AND status = 1", request.args.get("id"))
            if len(articlerow) > 0:
                authorrow = db.execute("SELECT * FROM users WHERE user_id = ?", articlerow[0]["primary_author_id"])
                editorrow = db.execute("SELECT * FROM users WHERE user_id = ?", articlerow[0]["editor"])
                return render_template("article.html", users=userrow, articles=articlerow, authors=authorrow, editors=editorrow)
            else:
                return redirect("/")
        else:
            return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("username"):
            error = 'Missing username'
            return render_template('login.html', error=error)
        elif not request.form.get("password"):
            error = 'Missing password'
            return render_template('login.html', error=error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            error = 'Invalid username or password'
            return render_template('login.html', error=error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

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


@app.route("/publish", methods=["GET", "POST"])
@login_required
def publish():
    # POST
    if request.method == "POST":
        # Validate form submission
        if not request.form.get("article_title"):
            error = 'Missing title'
            return render_template('publish.html', error=error)
        elif not request.form.get("article_topic"):
            error = 'Missing topic'
            return render_template('publish.html', error=error)
        elif not request.form.get("article_abstract"):
            error = 'Missing abstract'
            return render_template('publish.html', error=error)
        elif not request.form.get("article_introduction"):
            error = 'Missing introduction'
            return render_template('publish.html', error=error)
        elif not request.form.get("article_materials_methods"):
            error = 'Missing materials and methods'
            return render_template('publish.html', error=error)
        elif not request.form.get("article_results"):
            error = 'Missing results'
            return render_template('publish.html', error=error)
        elif not request.form.get("article_discussion"):
            error = 'Missing discussion'
            return render_template('publish.html', error=error)
        elif not request.form.get("article_conclusion"):
            error = 'Missing conclusion'
            return render_template('publish.html', error=error)
        elif not request.form.get("article_references"):
            error = 'Missing references'
            return render_template('publish.html', error=error)

        from datetime import datetime
        now = datetime.now()

        import random
        color = "#%06x" % random.randint(0, 0xFFFFFF)

        doc = request.form.get("article_abstract") + "  " + request.form.get("article_materials_methods") + " " + request.form.get("article_results") + " " + request.form.get("article_discussion") + " " + request.form.get("article_conclusion")
        
        from nltk import tokenize
        from operator import itemgetter
        import math

        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize 
        stop_words = set(stopwords.words('english'))

        total_words = doc.split()
        total_word_length = len(total_words)
        print(total_word_length)

        total_sentences = tokenize.sent_tokenize(doc)
        total_sent_len = len(total_sentences)
        print(total_sent_len)

        tf_score = {}
        for each_word in total_words:
            each_word = each_word.replace('.','')
            if each_word not in stop_words:
                if each_word in tf_score:
                    tf_score[each_word] += 1
                else:
                    tf_score[each_word] = 1

        # Dividing by total_word_length for each dictionary element
        tf_score.update((x, y/int(total_word_length)) for x, y in tf_score.items())
        print(tf_score)

        def check_sent(word, sentences): 
            final = [all([w in x for w in word]) for x in sentences] 
            sent_len = [sentences[i] for i in range(0, len(final)) if final[i]]
            return int(len(sent_len))

        idf_score = {}
        for each_word in total_words:
            each_word = each_word.replace('.','')
            if each_word not in stop_words:
                if each_word in idf_score:
                    idf_score[each_word] = check_sent(each_word, total_sentences)
                else:
                    idf_score[each_word] = 1

        # Performing a log and divide
        idf_score.update((x, math.log(int(total_sent_len)/y)) for x, y in idf_score.items())

        print(idf_score)

        tf_idf_score = {key: tf_score[key] * idf_score.get(key, 0) for key in tf_score.keys()}
        print(tf_idf_score)

        def get_top_n(dict_elem, n):
            result = dict(sorted(dict_elem.items(), key = itemgetter(1), reverse = True)[:n]) 
            return result

        editorrow = db.execute("SELECT * FROM users WHERE re = 1 ORDER BY RANDOM() LIMIT 1")
        labels = str(list(get_top_n(tf_idf_score, 8).keys()))

        # Add user to database
        db.execute("INSERT INTO articles (primary_author_id, secondary_authors, topic, labels, date, color, title, abstract, introduction, materials_methods, results, discussion, conclusion, articlereferences, editor) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            session["user_id"],
                            request.form.get("article_secondary_authors"),
                            request.form.get("article_topic"),
                            labels[1:-1],
                            now,
                            color,
                            request.form.get("article_title"),
                            request.form.get("article_abstract"),
                            request.form.get("article_introduction"),
                            request.form.get("article_materials_methods"),
                            request.form.get("article_results"),
                            request.form.get("article_discussion"),
                            request.form.get("article_conclusion"),
                            request.form.get("article_references"),
                            editorrow[0]["user_id"]
                            )
        
        # Let user know they're registered
        flash("Sent for publishing!")
        return redirect("/profile_articles")
    else:
        userrow = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
        return render_template("publish.html", users=userrow)


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)