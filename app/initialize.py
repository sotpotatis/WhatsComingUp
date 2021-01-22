"""Initialize.py
Innehåller kod för att initiera och skapa en Flask-app med blueprints
från auth_routes och main_routes-filerna och dessutom initiera en databas."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy() #Initiera en databas först

#Fortsätt med definitioner och importering
import os
from models import User
from flask_login import LoginManager
from flask import Flask

def create_app():
    app = Flask(__name__) #Skapa en app

    #Initiera databasen
    app.config["SECRET_KEY"] = os.environ["SQLALCHEMY-KEY"] #Hemlig nyckel
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data/db.sqlite" #Konfigurera databas-URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False #Satt till False för att missa deprecationvarning.
    db.init_app(app=app) #Initiera databasen mot den aktuella appen

    #Läs in Flask-Login för att hantera inloggning
    login_manager = LoginManager() #Inloggningshanterare
    login_manager.login_view = "auth.login" #Standard-loginvy
    login_manager.init_app(app) #Initiera LoginManager

    #Skapa en user-loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    #Registrera blueprints, dvs. "mallar" för auth och main routes
    from auth_routes import auth as auth_blueprint
    from main_routes import main as main_blueprint
    app.register_blueprint(auth_blueprint) #Auth-blueprint och auth routes
    app.register_blueprint(main_blueprint) #Main-blueprint och main routes

    return app #Returnera appen
