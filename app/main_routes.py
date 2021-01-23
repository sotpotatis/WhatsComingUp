"""Main_routes.py
Innehåller alla routes som inte
är relaterat till inloggning (allt som inte loggar in, loggar ut, eller registrerar en användare.)"""
import logging, events
from flask import Blueprint, render_template, Markup, request, Response, redirect
from flask_login import login_required, current_user
from initialize import db
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
    #Hämta skoldata
    logging.info("Hämtar användarens event...")
    user_events = events.get_events(current_user)
    event_html_template = """<h1>{title}</h1><p>{description}</p><p>Börjar: {starts}, slutar: {ends}</p><a href={link}>Länk</a>"""
    event_html_template = """<div class="p-3 rounded bg-red-500 ml-44 mr-44 mb-4">
    <h1 class="text-xl font-bold">{title}</h1>
    <p>{description}</p>
    <p class="text-sm">{starts}</p>
        <p class="text-sm">{ends}</p>
    <p><!--<span class="iconify" data-icon="bx:bxs-door-open" data-inline="false"></span>-->{room}</p>
    <button class="bg-indigo-500 p-2 m-2 rounded"><!--<span class="iconify" data-icon="bx:bx-link" data-inline="false"></span>--> Länk</button>
    </div>"""
    event_htmls = []
    """Eventformat: {"type": "homework", "title": title, "description": description,
    "times": {"start": starts_at, "end": ends_at}, "room": None,
    "link": url, "icon": None}"""
    logging.info("Genererar HTML...")
    for event in user_events:
        event_html = event_html_template.format(
            title=event["title"],
            description=event["description"],
            starts=str(event["times"]["start"]),
            ends=str(event["times"]["end"]),
            room=event["room"],
            link=event["link"]
        )
        event_htmls.append(event_html)
    if len(event_htmls) == 0: #Om inga event finns
        event_htmls = ["<p>Lyxigt! Det finns inga event för idag.</p>"]
    logging.info("Returnerar användarsida!")
    return render_template("userpage.html", username=current_user.username, events_html=Markup("".join(event_htmls))) #Rendera användarsida

@main.route("/settings")
@login_required
def settings():
    """Statisk sida för att returnera inställningssidan."""
    logging.info("Tog emot en förfrågan för att visa användarsidan!")
    #Kolla om man kan fylla i någon data från start
    canvas_token_prefill = current_user.user_canvas_api_token
    if canvas_token_prefill == None:
        canvas_token_prefill = ""
    class_prefill = current_user.user_class
    if class_prefill == None:
        class_prefill = "te18a"
    return render_template("settings.html", canvas_token_prefill=canvas_token_prefill, class_prefill=class_prefill)
@main.route("/user/update", methods=["POST"])
@login_required
def update_user():
    """Endpoint för att uppdatera en användare.
    Accepterar ett formulär med följande värden:
    - class: användarens klass
    - canvas-token: användarens canvas-token"""
    user = current_user
    for key, value in request.form.items():
        if key == "canvas-token":
            logging.info("Uppdaterar Canvas-token...")
            user.canvas_api_token = value
        elif key == "class":
            logging.info("Uppdaterar klass...")
            user.user_class = value
        else:
            logging.warning(f"Ogiltig nyckel {key} skickad!")
            return Response("Ogiltig nyckel skickad! Stopp.", status=403)
    db.session.commit()
    return redirect("/userpage")
