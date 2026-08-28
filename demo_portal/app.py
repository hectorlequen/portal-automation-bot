import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, request, send_from_directory, session, url_for

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

app = Flask(__name__)

secret_key = os.environ.get("FLASK_SECRET_KEY")
if not secret_key:
    raise EnvironmentError("FLASK_SECRET_KEY is missing from .env")
app.secret_key = secret_key

DOWNLOAD_DIR = BASE_DIR / "demo_portal_data"
DOWNLOAD_FILENAME = "report.txt"


@app.route("/")
def home():
    """Returns a static greeting confirming the server is running."""
    return "Hello Flask"


@app.route("/login", methods=["GET", "POST"])
def login():
    """Serves the login form and handles login submissions.

    GET returns the login form (200). POST checks the submitted
    username/password against the hardcoded demo credentials: on success it
    sets session["logged_in"] and redirects (302) to /dashboard; on failure it
    returns 401 with an "Invalid credentials" body.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "demo" and password == "demo123":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return "Invalid credentials", 401

    return """
    <form method="post" action="/login">
        <label for="username">Username</label>
        <input type="text" id="username" name="username">

        <label for="password">Password</label>
        <input type="password" id="password" name="password">

        <button type="submit">Log in</button>
    </form>
    """


@app.route("/dashboard")
def dashboard():
    """Returns the dashboard page, or redirects to /login if not authenticated.

    Returns 200 with a link to /download if session["logged_in"] is set,
    otherwise redirects (302) to /login.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return """
    <h1>Dashboard</h1>
    <a href="/download">Download report</a>
    """


@app.route("/download")
def download():
    """Serves the demo report file, or redirects to /login if not authenticated.

    Returns DOWNLOAD_DIR/DOWNLOAD_FILENAME as an attachment (200) if
    session["logged_in"] is set, otherwise redirects (302) to /login.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return send_from_directory(DOWNLOAD_DIR, DOWNLOAD_FILENAME, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
