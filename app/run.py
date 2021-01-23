"""Run.py
Fil för att köra appen."""
import os, logging
from initialize import create_app, db

#Logging-konfiguration
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)


#App-konfiguration
run_debugged = True #Om appen ska köras i debugg-läge (Flask) eller inte.
app = create_app() #Skapa en app

#Kolla om databasen existerar. Om inte - skapa en ny
database_path = os.path.join(os.getcwd(), "data/db.sqlite")
database_exists = os.path.exists(database_path)
if not database_exists:
    print("Programmet hittade ingen databas. En ny databas kommer att skapas om du inte stänger programmet NU!")
    input("Tryck enter för att skapa en NY, TOM databas! Detta kan INTE ångras!")
    db.create_all(app=create_app()) #Skapa en databas

logging.info("Startar Flask...")
if __name__ == '__main__':
    app.run(debug=run_debugged)
