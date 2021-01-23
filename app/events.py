"""Events.py
Funktioner för att hämta event för alla plattformar:
- Google Calendar
- SSIS API
- Canvas API
- Eatery API"""

import datetime,json,os,pytz,requests,dateutil.parser,logging

google_calendar_names = {
"te20a": "stockholmscience.se_1883fj0aciqjki8mmminh2fs2f7f0@resource.calendar.google.com",
"te20b": "stockholmscience.se_188170h985g6ajr5ghhcekjl4ic9o@resource.calendar.google.com",
"te20c": "stockholmscience.se_188dosol7timcjeblcaln5nrkaqc8@resource.calendar.google.com",
"te20d": "stockholmscience.se_1888peihgoe28jqigmjgf5v5tis1o@resource.calendar.google.com",
"te19a": "stockholmscience.se_3130353533383833363536@resource.calendar.google.com",
"te19b": "stockholmscience.se_3130343634393431323331@resource.calendar.google.com",
"te19c": "stockholmscience.se_3130333934323134323038@resource.calendar.google.com",
"te19d": "stockholmscience.se_3130323735383031343138@resource.calendar.google.com",
"te18a": "stockholmscience.se_3133363436323537343935@resource.calendar.google.com",
"te18b": "stockholmscience.se_3133353535373534343234@resource.calendar.google.com",
"te18c": "stockholmscience.se_3133343634303632313431@resource.calendar.google.com",
"te18d": "tockholmscience.se_3133333735393137323932@resource.calendar.google.com"
}
def school_time():
    return datetime.datetime.now(tz=pytz.timezone("Europe/Stockholm"))

def get_canvas_data(canvas_token):
    canvas_url = f"https://canvas.ssis.nu/api/v1/users/self/calendar_events?access_token={canvas_token}"
    canvas_request = requests.get(canvas_url, headers={"User-Agent": "Python/WhatsComingUp"})
    return canvas_request.json()

def check_bbb(string):
    return True if "bbb.ssis.nu" in string else False

def get_schedule(class_name):
    """Funktion för att hämta ett schema
    för en klass, både från SSIS API och Google Calendar.. Kollar om det finns ett globalt
    sparat schema på servern för klassen, annars så
    skickas en förfrågning till SSIS server för att fråga efter ny data."""
    logging.info("Hämtar schema...")
    #from ssis_schedule.Schedule import Schedule
    import app.ssis_schedule.Schedule as sc
    schedule = sc.Schedule(class_name)
    cached_schedule_filepath = os.path.join(os.getcwd(), f"data/cached/ssis_schedule/{class_name}.json")
    class_name = class_name.lower()
    if not os.path.exists(cached_schedule_filepath):
        logging.info("Schemat är inte cachat...")
        schedule_cached = False
        cached_schedule_data = {"cached_ssis_data": None, "cached_google_data": None, "cached_at": str(school_time().date())}
    else:
        logging.info("Laddar in cachad data...")
        cached_schedule_data = json.loads(open(cached_schedule_filepath, "r").read())
        cached_schedule_date = cached_schedule_data["cached_at"]
        cached_ssis_data = cached_schedule_data["cached_ssis_data"]
        cached_google_data = cached_schedule_data["cached_google_data"]
        schedule_cached = False if cached_schedule_date != cached_schedule_data["cached_at"] else True
    if schedule_cached == False: #Om schemat ska cachas
        logging.info("Schemat ska cachas!")
        schedule.get_schedule()
        cached_ssis_data = schedule.schedule_json #Hämta schema-JSON
        GOOGLE_API_TOKEN = os.environ["GOOGLE-CALENDAR-TOKEN"]
        google_calendar_name = google_calendar_names[class_name]
        google_schedule_url = f"https://www.googleapis.com/calendar/v3/calendars/{google_calendar_name}/events?key={GOOGLE_API_TOKEN}"
        google_schedule_request = requests.get(google_schedule_url)
        google_schedule_json = google_schedule_request.json()["items"]
        cached_google_data = []
        for item in google_schedule_json: #Lägg bara till event som pågår idag
            if "start" not in item.keys() or "dateTime" not in item["start"].keys():
                logging.warning("Inget startdatum definierat.")
                continue
            if dateutil.parser.parse(item["start"]["dateTime"]).date() == school_time().date():
                #Kolla efter BBB-länk
                bbb_link = None
                if "location" in item.keys():
                    for location in item["location"].split(","):
                        if check_bbb(location):
                            print("BBB-länk hittad i plats!")
                            bbb_link = location
                            break
                if "description" in item.keys():
                    if check_bbb(item["description"]):
                        print("BBB-länk hittad i beskrivning!")
                        bbb_link = item["description"]
                        break
                item["bbb"] = bbb_link
                cached_google_data.append(item)

        with open(cached_schedule_filepath, "w") as cached_schedule_file:
            cached_schedule_file.write(json.dumps(
                {"cached_ssis_data": cached_ssis_data, "cached_google_data": cached_google_data, "cached_at": str(school_time())}
            ))
    else:
        print("Schemat ska inte cachas.")
    schedule.parse_schedule_json(cached_ssis_data)
    return schedule.schedule, cached_google_data #Returnera schemadata.

def get_school_food():
    food_request_url = "https://eatery.nero2k.com/api/json"
    food_request = requests.get(food_request_url)
    return food_request.json()

def get_events(current_user):
    """Sammanhängande funktion för att hämta alla event för en användare
    från alla plattformar och returnera det i ett sammanhängande format.
    Format: {"title": "Dator- och nätverksteknik", "description": None, "times": {"start": [DT], "end": [DT]}, "room": None eller str, "link": None eller str, "icon": "", "type": ""}"""
    user_class = current_user.user_class
    user_canvas_token = current_user.user_canvas_api_token
    today_schedule_for_user, google_calendar_for_user_class = get_schedule(user_class) if user_class != None else ([], [])
    user_homework = get_canvas_data(user_canvas_token) if user_canvas_token != None else []
    school_food = get_school_food()
    events = []
    #Översätt allt till det universella JSON-formatet
    for event in today_schedule_for_user:
        event_schedule_json = {"type": "schedule","title": event.subject,"description": "Lektion", "times": {"start": event.starts_at, "end": event.ends_at},"room": event.room,"link": None,"icon": None}
        #Försök hitta en BBB-länk för lektionen i kalender-datan
        for google_event in google_calendar_for_user_class:
            if google_event["bbb"] != None and google_event["subject"] == event.subject: #Vi utgår från att man inte har samma ämne två gånger per dag... *isande ansikte emoji*
                event_schedule_json["link"] = google_event["bbb"]
        events.append(
            event_schedule_json
        )
        #Försök detektera lunch...
        event_index = today_schedule_for_user.index(event)
        if event_index < len(today_schedule_for_user)-1:
            next_event = today_schedule_for_user[event_index+1]
            difference_between_lessons = event.ends_at - next_event.starts_at
            current_hour = school_time().hour
            if round(difference_between_lessons.seconds/60) >= 20 and (current_hour >= 10  and current_hour <= 13):
                logging.info("Lunch hittad! Lägger till lunch...")
                day_names = ["monday", "tuesday", "wednesday", "thurday", "friday"]
                today_food = school_food["menu"][day_names[school_time().weekday()]]
                lunch_description = "\n-".join(today_food)
                lunch_event = {"type": "lunch","title": "Lunch","description": lunch_description, "times": {"start": event.ends_at, "end": next_event.starts_at},"room": "Eatery","link": "https://eatery.nero2k.com/","icon": None}
                events.append(lunch_event)
    #Hämta läxor
    for homework in user_homework:
        title = homework["title"]
        starts_at = dateutil.parser.parse(homework["start_at"])
        ends_at = dateutil.parser.parse(homework["end_at"])
        url = homework["html_url"]
        description = homework["description"]
        homework_event = {"type": "homework", "title": title, "description": description,
                       "times": {"start": starts_at, "end": ends_at}, "room": None,
                       "link": url, "icon": None}
        events.append(homework_event)
    def sort_event(event):
        return event["times"]["start"]
    events.sort(key=sort_event)
    return events