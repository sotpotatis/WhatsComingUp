"""Main_routes.py
Innehåller alla routes som inte
är relaterat till inloggning (allt som inte loggar in, loggar ut, eller registrerar en användare.)"""
import logging
from flask import Blueprint, render_template
from flask_login import login_required
main = Blueprint("main", __name__)

@main.route("/")
def index():
    logging.info("Returnerar statisk startsida!")
    return render_template("index.html")

@main.route("/login", methods=["GET"])
def login():
    logging.info("Returnerar statisk inloggningssida!")
    return render_template("login.html")

@main.route("/signup", methods=["GET"])
def signup():
    logging.info("Returnerar statisk registreringssida!")
    return render_template("signup.html")

#Användarens sida.
@main.route("/userpage")
@login_required
def userpage():
    logging.info("Returnerar användarsida...")
    return "Du är inloggad!"
