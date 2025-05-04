import os
import os.path
from dotenv import load_dotenv
from pydantic import BaseModel
import pickle
import datetime
import pytz

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request



# Load env variables
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

CREDENTIALS = os.environ["CALENDER_CREDENTIALS"] #path to file with credentials

API_KEY = os.environ["GEMINI_API_KEY"]

llm = ChatGoogleGenerativeAI(
  model = "gemini-2.0-flash",
  temperature=0,
  api_key = API_KEY
)

def prepareAgentPrompt():
  template = """
  Today is {today}.
  You are a helpful assistant that helps users check their calendar.

  Conversation history: {history}

  The input is: {input}

  If the user asks about appointments, availability, or events on a specific day:
  - Check if the events for that date are already stored in memory.
  - If they are stored, use the stored data.
  - If not, extract the date from the input and convert it to YYYY-MM-DD format, then call the `getEvents` tool with the extracted date.


  Example:
  User: "What appointments do I have on the 6th of June?"
  → Extracted date: "2025-06-06"
  → Call tool: getEvents(date="2025-06-06")

  In your answer, make sure to include all events of that day and if there is not start or end time, use 00:00 and 23:59.
  For events spanning multiple days, consider all days between the start and end date as separate all-day events from 00:00 to 23:59.
  Return the result as a JSON object in this format, make sure to include all events of that day:
  {{
    "action": "return_scheduled_events",
    "data": {{
      "date": "<actual date in YYYY-MM-DD>",
      "events": [{{"start": "<HH:MM>", "end": "<HH:MM>", "summary": "<summary>"}}]
    }}
  }}


  {agent_scratchpad}
  """
  # and ask, if the user would like to consider the events in the planning, or if the events can be ignored.
  return ChatPromptTemplate.from_template(template)

memory = ConversationBufferMemory(memory_key="history", input_key="input")
config = RunnableConfig(configurable={"memory": memory})
prompt = prepareAgentPrompt()

# Input schema for the weather tool
class EventsInput(BaseModel):
  date: str  # Format: YYYY-MM-DD


# LangChain-compatible tool
@tool(args_schema=EventsInput)
def getEvents(date):
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
  # Call the Calendar API
  targetDate = datetime.datetime.strptime(date, "%Y-%m-%d")
  startDt = localTz.localize(datetime.datetime.combine(targetDate, datetime.time.min))
  endDt = localTz.localize(datetime.datetime.combine(targetDate, datetime.time.max))

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


# Agent setup
tools = [getEvents]
agent = create_tool_calling_agent(llm, tools, prompt)
agentExecutor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)

# Run query
today_str = datetime.date.today().isoformat()
response = agentExecutor.invoke({"input": "What appointments do I have tomorrow?",
                                "today": today_str
                                }, 
                                config=config)
print(response)
