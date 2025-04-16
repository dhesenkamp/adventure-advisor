import os
from google import genai
from google.genai import types
from orchestrator import OrchestratorAgent
from weather import WeatherAgent
from app import StreamlitApp

weather = WeatherAgent()
orchestrator = OrchestratorAgent({"weather": weather})

# request = "What's the weather like in Trento, Italy tomorrow?"
# response = orchestrator.run(request)
# print(response)

app = StreamlitApp(orchestrator=orchestrator)
app.run()
