import os
from google import genai
from google.genai import types

API_KEY = os.environ["GEMINI_API_KEY"]


class WeatherAgent:
  def __init__(self):
    self.client = genai.Client(api_key=API_KEY)
    self.model = "gemini-2.0-flash"
    self.instructions = "You are a weather agent. You will be given a location and time by an orchestrator LLM. You will return the weather for that location at the specified time. If no time is specified, you will return the current weather. Be precise, as your answer will only be part of a larger conversation."
    self.context = str()

  def getWeather(self, prompt):
    response = self.client.models.generate_content(
        model=self.model,
        config=types.GenerateContentConfig(
            system_instruction=self.instructions
        ),
        contents=self.getContext() + prompt
    )
    self.setContext(prompt + response.text)
    return response.text

  def setContext(self, context):
    """Given a message or prompt and the past context, create a very concise updated context to use for future calls."""
    if self.context:
      newContext = self.context + "\n\n" + context
      instructions = f"Summarize this history for use as LLM context:\n\n{newContext}"
      response = self.client.models.generate_content(
          model=self.model,
          config=types.GenerateContentConfig(
              system_instruction=instructions
          ),
      )
      self.context = response.text

  def getContext(self):
    return self.context
