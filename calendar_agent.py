import json
import os
import datetime
import pytz
from dotenv import load_dotenv

from langchain_core.tools import tool

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from base_agent import BaseAgent

load_dotenv()

CREDENTIALS = json.loads(os.environ["GOOGLE_OAUTH_CREDENTIALS"])
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CALENDAR_PROMPT_TEMPLATE = (
    "You are a helpful assistant that helps users check their calendar for events and time conflicts."
    "Today is {today}\n\n"
    "Chat history: {history}\n\n"
    "The input is: {input}\n\n"
    "Your scratchpad: {agent_scratchpad}\n\n"
    "If the user asks about appointments, availability, or events on a specific day:"
    "- Check if the events for that date are already stored in memory."
    "- If they are stored, use the stored data."
    "- If not, extract the date from the input and convert it to YYYY-MM-DD format, then call the `getEvents` tool with the extracted date."
    "Example:"
    "User: 'What appointments do I have on the 6th of June?'"
    "→ Extracted date: '2025-06-06'"
    "→ Call tool: getEvents(date='2025-06-06')"
    "In your answer, make sure to include all events of that day and if there is not start or end time, use 00:00 and 23:59."
    "For events spanning multiple days, consider all days between the start and end date as separate all-day events from 00:00 to 23:59."
    """Return the result as a JSON object in this format, make sure to include all events of that day:
    {{
      "action": "return_scheduled_events",
      "data": {{
        "date": "<actual date in YYYY-MM-DD>",
        "events": [{{"start": "<HH:MM>", "end": "<HH:MM>", "summary": "<summary>"}}]
      }}
    }}"""
)


@tool
def getEvents(date: str, timezone: str = "Europe/Berlin"):
  """Get the events that are stored in the user's calendar.
  Args:
      date (str): The date for which to retrieve events in YYYY-MM-DD format.
      timezone (str): The timezone to use for the date. Defaults to "Europe/Berlin".
  """

  creds = None

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_config(
          CREDENTIALS, SCOPES)
      creds = flow.run_local_server(port=0)

  with open("token.json", "w") as token:
    token.write(creds.to_json())

  localTz = pytz.timezone(timezone)

  targetDate = datetime.datetime.strptime(date, "%Y-%m-%d")
  startDt = localTz.localize(
      datetime.datetime.combine(targetDate, datetime.time.min))
  endDt = localTz.localize(
      datetime.datetime.combine(targetDate, datetime.time.max))

  timeMin = startDt.isoformat()
  timeMax = endDt.isoformat()

  try:
    events = list()

    service = build("calendar", "v3", credentials=creds)
    calList = service.calendarList().list().execute()

    for cal in calList.get("items", []):

      eventsResult = (service.events().list(
          calendarId=cal["id"],
          timeMin=timeMin,
          timeMax=timeMax,
          singleEvents=True,
          orderBy="startTime",
      ).execute())

      for event in eventsResult.get("items", []):
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        summary = event.get("summary", "No title")
        events.append({
            "summary": summary,
            "start": start,
            "end": end
        })

    if not events:
      return
    return {"date": date, "events": events}

  except HttpError as error:
    print(f"An error occurred: {error}")


TOOLS = [getEvents]


class CalendarAgent(BaseAgent):
  """
  Specialized agent for fetching calendar events, uses LangChain framework and the Google Calendar API to get calendar data.
  """

  def __init__(self, apiKey, tools=TOOLS, promptTemplate=CALENDAR_PROMPT_TEMPLATE):
    super().__init__(
        apiKey=apiKey,
        tools=tools,
        promptTemplate=promptTemplate
    )
