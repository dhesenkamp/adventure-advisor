import os
from dotenv import load_dotenv
import requests
import argparse
from base_agent import BaseAgent
from calendar_agent import CalendarAgent
from weather_agent import WeatherAgent
from database_agent import DatabaseAgent
from orchestrator import Orchestrator
from app import StreamlitApp

if __name__ == "__main__":
  # get args from cl
  parser = argparse.ArgumentParser(description="Adventure Advisor")
  parser.add_argument(
      "-u", "--user", type=str, default="User",
      help="Username for the session"
  )
  args = parser.parse_args()

  load_dotenv()
  GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

  calendarAgent = CalendarAgent(apiKey=GEMINI_API_KEY)
  weatherAgent = WeatherAgent(apiKey=GEMINI_API_KEY)
  databaseAgent = DatabaseAgent(apiKey=GEMINI_API_KEY)
  agents = {
      "calendar": calendarAgent,
      "weather": weatherAgent,
      "database": databaseAgent
  }
  orchestrator = Orchestrator(apiKey=GEMINI_API_KEY, agents=agents)

  app = StreamlitApp(orchestrator, user=args.user)
  app.run()
