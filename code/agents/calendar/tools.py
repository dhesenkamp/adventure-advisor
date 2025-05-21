import os
import json
import pickle
import pytz
import datetime

from dotenv import load_dotenv

from langchain_core.tools import tool
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

CREDENTIALS = json.loads(os.environ.get("GOOGLE_OAUTH_CREDENTIALS"))
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


@tool
def getEvents(date: str):
  """
  Get the events that are stored in the user's calendar.
  """

  creds = None
  tzName = "Europe/Berlin"

  if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
      creds = pickle.load(token)

  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())

    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          CREDENTIALS, SCOPES)
      creds = flow.run_local_server(port=0)

  # Save the credentials for the next run
  with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

  service = build('calendar', 'v3', credentials=creds)
  localTz = pytz.timezone(tzName)

  targetDate = datetime.datetime.strptime(date, "%Y-%m-%d")
  startDt = localTz.localize(
      datetime.datetime.combine(targetDate, datetime.time.min))
  endDt = localTz.localize(
      datetime.datetime.combine(targetDate, datetime.time.max))

  timeMin = startDt.isoformat()
  timeMax = endDt.isoformat()

  eventsResult = service.events().list(
      calendarId='primary',
      timeMin=timeMin,
      timeMax=timeMax,
      singleEvents=True,
      orderBy='startTime'
  ).execute()

  events = []
  for event in eventsResult.get('items', []):

    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))
    summary = event.get('summary', 'No title')
    events.append({
        "summary": summary,
        "start": start,
        "end": end
    })

  return {"date": date, "events": events}
