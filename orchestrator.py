import os
import json
import re
from google import genai
from google.genai import types

API_KEY = os.environ["GEMINI_API_KEY"]


class OrchestratorAgent:
  def __init__(self, agents):
    self.client = genai.Client(api_key=API_KEY)
    self.model = "gemini-2.0-flash"
    self.agents = agents
    self.instructions = f"You are an orchestrator, responsible for coordinating the activities of other agents. You will receive a user message and must decide which agent(s), if any, to call. Available agents: {', '.join(self.agents.keys())}. If no agents are needed, you will respond directly to the user."

  def getWeather(self, prompt):
    print("-- invoking weather agent --")
    extractPrompt = (
        f"Extract the location and time/date from this user message:\n\n"
        f"{prompt}\n\n"
        f"Return the location and time/date ONLY in valid JSON format. Do not include any other text.\n\n"
        f'Example: {{"location": "Trento, Italy", "time": "this weekend"}}'
    )
    response = self.client.models.generate_content(
        model=self.model,
        config=types.GenerateContentConfig(
            system_instruction=self.instructions
        ),
        contents=extractPrompt
    )

    # Extract JSON from the response
    structuredData = self.extractJsonFromText(response.text)
    if not structuredData:
      print("Failed to extract JSON from response.")
      return "I couldn't understand the location and time you provided."
    location = structuredData["location"]
    try:
      time = structuredData["time"]
    except KeyError:
      time = "now"

    weatherQuery = f"What is the weather in {location} at {time}?"
    weatherResult = self.agents["weather"].getWeather(weatherQuery)

    return weatherResult

  def run(self, prompt, weather=str()):
    requiredAgents = self.decideAgents(prompt)
    for agent in requiredAgents:
      if agent == "weather":
        weather = self.getWeather(prompt)

    finalAnswer = self.client.models.generate_content(
        model=self.model,
        config=types.GenerateContentConfig(
            system_instruction="Based on the context you have, provide a concise and relevant answer to the user's question. If you have called any agents, include their responses in your answer.",
        ),
        contents=prompt + weather
    )
    return finalAnswer.text

  def extractJsonFromText(self, text):
    # Find the first JSON-like object using a basic regex
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if not match:
      return None

    try:
      cleaned = match.group(0).replace("'", '"')
      return json.loads(cleaned)
    except json.JSONDecodeError as e:
      print("JSON parsing failed:", e)
      return None

  def decideAgents(self, prompt):
    # Placeholder for agent decision logic
    # This could be more complex based on the prompt
    if "weather" in prompt.lower():
      return ["weather"]
    else:
      return []
