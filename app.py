import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from database.db import initialize_database, dashboard_counts, initialize_users, verify_user, create_user,fetch_medicine, fetch_medicines, fetch_categories, add_category, add_medicine, update_medicine
import os 
from datetime import datetime
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

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return render_template("forbidden.html"), 403
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

@app.route("/medicines")
@admin_required
def medicines():
    return render_template("medicines.html", medicines=fetch_medicines())

def normalize_date(text):
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return text or ""

def validate_medicine(form):
    errors = {}
    name = form["name"]
    if not name:
        errors["name"] = "Name is required."
    category = form["category"] or "Other"

    quantity = None
    try:
        quantity = int(form["quantity"])
        if quantity < 0:
            raise ValueError
    except ValueError:
        errors["quantity"] = "Enter a valid non-negative whole number."

    price = None
    try:
        price = float(form["price"])
        if price < 0:
            raise ValueError
    except ValueError:
        errors["price"] = "Enter a valid non-negative price."

    if not form["expiry"]:
        errors["expiry"] = "Expiry date is required."
    else:
        try:
            datetime.strptime(form["expiry"], "%Y-%m-%d")
        except ValueError:
            errors["expiry"] = "Use the format YYYY-MM-DD."

    cleaned = {"name": name, "category": category, "quantity": quantity,
               "price": price, "expiry": normalize_date(form["expiry"])}
    return errors, cleaned


@app.route("/medicines/add", methods=["GET", "POST"])
@admin_required
def add_medicine_page():
    form = {"name": "", "category": "", "quantity": "", "price": "", "expiry": ""}
    errors = {}
    if request.method == "POST":
        form = {key: request.form.get(key, "").strip() for key in form}
        errors, cleaned = validate_medicine(form)
        if not errors:
            add_category(cleaned["category"])
            add_medicine(cleaned["name"], cleaned["category"], cleaned["quantity"],
                         cleaned["price"], cleaned["expiry"])
            flash("Medicine saved successfully.", "success")
            return redirect(url_for("medicines"))
    return render_template("add_medicine.html", form=form, errors=errors,
                           categories=fetch_categories(), heading="Add Medicine")

@app.route("/medicines/<int:medicine_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_medicine_page(medicine_id):
    medicine = fetch_medicine(medicine_id)
    if medicine is None:
        abort(404)
    form = {
        "name": medicine[1],
        "category": medicine[2],
        "quantity": str(medicine[3]),
        "price": str(medicine[4]),
        "expiry": normalize_date(medicine[5]),
    }
    errors = {}
    if request.method == "POST":
        form = {key: request.form.get(key, "").strip() for key in form}
        errors, cleaned = validate_medicine(form)
        if not errors:
            add_category(cleaned["category"])
            update_medicine(medicine_id, cleaned["name"], cleaned["category"],
                            cleaned["quantity"], cleaned["price"], cleaned["expiry"])
            flash("Medicine updated successfully.", "success")
            return redirect(url_for("medicines"))
    return render_template("add_medicine.html", form=form, errors=errors,
                           categories=fetch_categories(), heading="Edit Medicine")

if __name__ == "__main__":
    # open the browser once (not again on every auto-reload)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=True)