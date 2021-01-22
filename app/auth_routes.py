"""Auth_routes.py
Innehåller routes relaterade till inloggning, dvs. routes för att
logga in, logga ut, och registrera sig."""

import logging
from flask import Blueprint, request, redirect
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from initialize import db
auth = Blueprint("auth", __name__)

@auth.route("/signup", methods=["POST"])
def signup():
    """Funktion för att registrera en användare
    på tjänsten."""
    logging.info("Tog emot en förfrågan att registrera en användare!")
    logging.info("Hämtar detaljer från förfrågning...")
    username = request.form["username"]
    password = request.form["password"]
    #Kolla att kraven följs
    if not (len(username) < 25 and len(username) > 2):
        logging.warning("För kort eller för långt användarnamn skickat!")
        return "För kort eller för långt användarnamn."

    if not (len(password) >= 8):
        logging.warning("För kort lösenord skickat!")
        return "För kort lösenord."

    print("Kraven för att skapa en ny användare har uppföljts! Skapar...")
    hashed_password = generate_password_hash(password, "sha256")
    user = User(username=username, password=hashed_password) #Skapa en ny användare
    print("Lägger till användare i databas...")
    db.session.add(user)
    print("Verkställer ändringar...")
    db.session.commit()
    return redirect("/userpage")

@auth.route("/login", methods=["POST"])
def login():
    """Funktion för att logga in på tjänsten."""
    logging.info("Tog emot en förfrågan att logga in en användare!")
    logging.info("Hämtar detaljer från förfrågning...")
    username = request.form["username"]
    password = request.form["password"]
    remember = False #TODO: Lägg till val för att komma ihåg användaren om jag har tid
    found_user = User.query.filter_by(username=username).first()
    user_exists = True if (found_user) != None else False
    if not user_exists:
        logging.warning("Användaren existerar inte!")
        return "Användarnamnet existerar inte. Vänligen försök igen."
    password_valid = check_password_hash(found_user.password, password)
    if not password_valid:
        logging.warning("Ogiltigt lösenord!")
        return "Lösenordet är ogiltigt."
    logging.info("Allt verkar giltigt! Loggar in användare...")
    try:
        login_user(found_user, remember=remember) #Logga in användaren
    except Exception as e:
        logging.critical("Misslyckades med att logga in användare.", exc_info=True)
        return "Oops - misslyckades med att logga in dig. Vänligen försök igen."
    logging.info("Användare inloggad.")
    return redirect("/userpage")

@auth.route("/logout")
@login_required
def logout():
    """Funktion för att logga ut en användare från tjänsten."""
    logging.info("Tog emot en förfrågan att logga ut en användare!")
    try:
        logout_user()
    except Exception as e:
        logging.critical("Fel! Misslyckades med att logga ut användare!", exc_info=True)
        return "Kunde tyvärr inte logga ut dig från tjänsten."
    #(om ett fel inte inträffar kommer nedanstående returneras)
    return "Du har blivit utloggad."
