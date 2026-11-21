import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database.db import initialize_database, dashboard_counts, initialize_users, verify_user, create_user
import os
import threading
import webbrowser
app = Flask(__name__)
app.secret_key = "change-this-later"
initialize_database()
initialize_users()

LOW_STOCK_THRESHOLD = 10   # temporary default, becomes an admin setting later


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        role = request.form.get("role", "admin")
        user = verify_user(username, password)
        if user and user[4] == role:
           session["user_id"] = user[0]
           session["username"] = user[1]
           session["full_name"] = user[3]
           session["role"] = user[4]
           return redirect(url_for("home"))
        flash("Invalid ID, password or login type.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        error = None
        if not full_name:
            error = "Full name is required."
        elif len(username) < 3:
            error = "User ID must be at least 3 characters."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        if not error:
            try:
                create_user(username, password, full_name, "member")
                flash("Account created. You can now sign in as a Member.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "That User ID is already taken."
        flash(error, "error")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    total, stock, low, expired = dashboard_counts(LOW_STOCK_THRESHOLD)
    return render_template(
        "dashboard.html", total=total, stock=stock, low=low, expired=expired
    )

if __name__ == "__main__":
    # open the browser once (not again on every auto-reload)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=True)