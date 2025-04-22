import os
from google import genai
from google.genai import types
from orchestrator import OrchestratorAgent
from weather import WeatherAgent
from activity import ActivityAgent

weather = WeatherAgent()
activity = ActivityAgent()
orchestrator = OrchestratorAgent({"weather": weather, "activity": activity})

request = "What's the weather like in Trento, Italy tomorrow at 12:00? and give me 315 minute long mountainbiking tour in trento for tomorrow also at 12:00"
response = orchestrator.run(request)
print(response)
