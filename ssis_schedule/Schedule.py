"""Schedule.py
The main code for the library.
This library allows access to the SSIS Calendar API
for getting events (lessons and meetings primarily)
in a room in the school."""
import requests, datetime, urllib.parse, pytz, re, warnings
from .exceptions import NoDataException
ROOMS_LOWERCASE = ["tetris",
"zelda",
"space invaders",
"donkey kong",
"pac-man",
"snake",
"monopol",
"domino",
"schack",
"go",
"plockepinn",
"backgammon",
"mastermind",
"yatzy",
"arkaden",
"pentry 1",
"pentry 2"] #A list of all the rooms in the school in lowercase.
class Schedule(object):
    """The Schedule class is the main class for a schedule mapped to either
    a teacher, a student, or a room"""
    def __init__(self, schedule_string, headers={"User-Agent": "Python/SSISScheduleAPI (made by 20alse)"}):
        """Initialization function.
        Schedule_string can either be a room (Pac Man),
        a teacher's initials (JAG), or a class (Te20A).
        The headers matches the headers sent with each request.
        It is included so that the school administrator knows who sent the request in case something is wrong."""
        self.schedule_string = schedule_string
        self.headers  = headers
        self.schedule_string_urlsafe = urllib.parse.quote(schedule_string) #Create a URLsafe string of the entered schedule name
        self.schedule_url = f"https://api.ssis.nu/cal?room={self.schedule_string_urlsafe}" #Generate the URL to send requests to.
        #PLEASE NOTE: Door URLs only works with classroom names. NOT with teachers or other schedules such as "Hela skolan"
        self.door_url = f"api.ssis.nu/.cal/sc-{self.schedule_string_urlsafe}/" #Generate the URL that is used for the door displays in the school
        self.schedule_type = self.parse_type(self.schedule_string) #Parse the type of the schedule name string into its corresponding type.
        self.schedule_last_retrieved = None
        self.schedule = None
        self.schedule_json = None

    def get_today(self):
        """Quick function for getting the date and time in the time zone of the school, Stockholm."""
        return datetime.datetime.now(tz=pytz.timezone("Europe/Stockholm")) #Return the current date in time in the school's timezone

    def get_schedule(self, force_request=False):
        if self.schedule_last_retrieved != None and self.schedule_last_retrieved.date == self.get_today().date and not force_request: #If the schedule has already been retrieved today and a request has not been forced
            return self.schedule #Return the cached version of the schedule
        else: #If not, get the schedule again
            self.schedule_request = requests.get(self.schedule_url, headers=self.headers)
            if self.schedule_request.text == "": #If an empty response is returned, raise a NoData exception
                raise NoDataException("No data was recieved in the response from the SSIS server. Make sure that the entered schedule name is correct.")
            self.schedule_json = self.schedule_request.json()
            return self.parse_schedule_json(self.schedule_json) #Returned the parsed and converted version of the JSON. This will be stored into a self variable.

    def parse_schedule_json(self, schedule_json):
        """Function for converting provided schedule JSON into
        Entry objects with metadata."""
        events = [] #List of parsed entry objects
        for event in schedule_json: #Loop through all events
            #Create a dictionary with all kwargs to pass to the Event class upon creation
            event_kwargs = {"subject": event["subject"],
                            "participating_classes": None,
                            "participating_teachers": None,
                            "room": None,
                            "starts_at": self.parse_schedule_time(event["start_time"]),
                            "ends_at": self.parse_schedule_time(event["end_time"]),
                            "starts_at_raw": event["start_time"],
                            "ends_at_raw": event["end_time"]} #Pass some things which we already know or can convert, such as the schedule time, to this variable.
            #Now, loop through the participants to find metadata for those.
            #Create a list to store found classes in
            if self.schedule_type != "class": #If the schedule isn't for a class, start with a blank list
                participating_classes = []
            else: #If the schedule is, start by adding that class to the participant list.
                participating_classes = [self.schedule_string]
            #Create a list to store found participating teachers in
            if self.schedule_type != "teacher": #If the schedule isn't for a teacher, start with a blank list
                participating_teachers = []
            else: #If the schedule is, start by adding that teacher to the participant list.
                participating_teachers = [self.schedule_string]
            #Create a list to store found rooms in
            if self.schedule_type != "room": #If the schedule isn't for a room, start with a blank list
                found_rooms = []
            else: #If the schedule is, start by adding that room to the list of rooms.
                found_rooms = [self.schedule_string]
            participants_list = event["participants"].split(",") #Create a list of participants
            for participant in participants_list:
                if participant.lower() != self.schedule_string.lower(): #If the participant is different from the schedule string, do the below checks (otherwise we might end up adding duplicates)
                    participant_type = self.parse_type(participant) #Parse what type of participant we are talking about
                    #Append the participant to whereever it should be appended
                    if participant_type == "class":
                            participating_classes.append(participant)
                    elif participant_type == "room":
                            found_rooms.append(participant)
                    elif participant_type == "teacher":
                            participating_teachers.append(participant)
            event_kwargs["participating_classes"] = participating_classes
            event_kwargs["participating_teachers"] = participating_teachers
            event_kwargs["room"] = found_rooms
            events.append(Event(**event_kwargs)) #Create an event object and append it to the list of events
        self.schedule = events #Update the self variable with schedule data
        return self.schedule #Returned the parsed data

    def parse_schedule_time(self, string):
        """Function for converting a supplied time string (for example 10:00) to a
        datetime object. Events are always for the same day."""
        hour_info = datetime.datetime.strptime(string, "%H:%M")
        day_info = self.get_today()
        parsed_dt = datetime.datetime.combine(day_info.date(), hour_info.time()) #Combine the two datetime objects. Use today's date, but include the time
        return parsed_dt #Return the result

    def parse_type(self, string):
        """Function for parsing a passed string into one of three types:
        - a class
        - a teacher
        - a room
        ...or a blank string, None."""
        original_string = string #Store the original string that was passed the the function initially.
        string = string.lower().strip(" ")  #Covert the string to lowercase and remove any spaces in the beginning and end so it works with our regexps.
        if len(string) == 0: #string.count("") == len(string): #If the string is blank
            return None
        #If the string is not blank, let's check what it is
        if re.fullmatch("te[0-9]{2}[a-z]|hela skolan|individuella val", string): #If the string is a class (or a group of classes)
            return "class"
        elif re.fullmatch("[a-z]{3}", string): #If the string is a teacher
            return "teacher"
        elif string in ROOMS_LOWERCASE: #If the string is one of the rooms
            return "room"
        elif "pentry" in string: #If the string is related to pentrys
            return "pentry"
        else:
            warnings.warn(f"Parsing error: could not parse {string}")
            return None

class Event:
    """The event class is the main class for events, and it provides
    all kinds of metadata."""
    def __init__(self, subject, participating_classes, participating_teachers, room, starts_at, ends_at, starts_at_raw, ends_at_raw):
        self.subject = subject #The subject
        self.participating_classes = participating_classes #The participating class
        self.participating_teachers = participating_teachers #The participating teachers
        self.room = room #The room the event takes place in
        self.starts_at = starts_at #When the event starts
        self.ends_at = ends_at #When the event ends
        self.starts_at_raw = starts_at_raw #When the event starts, but as a raw, unparsed string
        self.ends_at_raw = ends_at_raw #When the event ends, but as a raw, unparsed string
        self.all_day = True if starts_at.hour < 6 else False #Specify if the event is an all-day one or not.
        #Duration is a timedelta object referencing the event duration
        if self.all_day: #If the current event is an all-day event
            self.ends_at = self.ends_at.replace(hour=23, minute=59, second=59) #Add almost one day to it so that the end time will be correct
        self.duration = (self.starts_at-self.ends_at)
