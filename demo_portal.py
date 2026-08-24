import os

from dotenv import load_dotenv
from flask import Flask, redirect, request, send_from_directory, session, url_for

load_dotenv()

app = Flask(__name__)

secret_key = os.environ.get("FLASK_SECRET_KEY")
if not secret_key:
    raise EnvironmentError("FLASK_SECRET_KEY is missing from .env")
app.secret_key = secret_key

DOWNLOAD_DIR = "demo_portal_data"
DOWNLOAD_FILENAME = "report.txt"


@app.route("/")
def home():
    return "Hello Flask"


@app.route("/login", methods=["GET", "POST"])
def login():
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
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return """
    <h1>Dashboard</h1>
    <a href="/download">Download report</a>
    """


@app.route("/download")
def download():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return send_from_directory(DOWNLOAD_DIR, DOWNLOAD_FILENAME, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
