import os
import getpass
import datetime

from agents.orchestrator import OrchestratorAgent
from agents.weather import WeatherAgent
from agents.calendar import CalendarAgent


if "GEMINI_API_KEY" not in os.environ:
  os.environ["GEMINI_API_KEY"] = getpass.getpass("Enter Gemini API key: ")

API_KEY = os.environ["GEMINI_API_KEY"]

weatherAgent = WeatherAgent(apiKey=API_KEY)
calendarAgent = CalendarAgent(apiKey=API_KEY)

orchestrator = OrchestratorAgent(
    apiKey=API_KEY,
    agents={
        "weather": weatherAgent,
        "calendar": calendarAgent
    }
)

tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
query = f"Do I have any meetings on {tomorrow} and what should I wear in Berlin?"
result = orchestrator.run(query)
print(result)
