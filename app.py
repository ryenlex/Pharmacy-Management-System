from flask import Flask, render_template
from database.db import initialize_database, dashboard_counts
import os
import threading
import webbrowser

app = Flask(__name__)
app.secret_key = "change-this-later"
initialize_database()


@app.route("/")
def home():
    total, stock, low, expired = dashboard_counts(10)
    return render_template(
        "dashboard.html", total=total, stock=stock, low=low, expired=expired
    )


if __name__ == "__main__":
    # open the browser once (not again on every auto-reload)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=True)