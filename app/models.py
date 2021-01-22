from flask_login import UserMixin
from initialize import db

class User(UserMixin, db.Model):
    """Klassen som definierar en användare."""

    #Basgrejer - ID, användarnamn, lösenord (lösenord lagras självklart hashat)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)

    #Grejer mer specifikt till applikationen. Alla utom klass lagras säkert hashat 😌
    user_class = db.Column(db.String(5), default=None) #Vilken klass användaren går i (5 i definitionen betyder att längden på definierade klasser ska vara fem bokstäver)
    user_google_calendar_ids = db.Column(db.String, default=None) #Länkar till ID:n av kalendar som användaren vill integrera i applikationen.
    user_canvas_api_token = db.Column(db.String, default=None) #Användarens token i Canvas
