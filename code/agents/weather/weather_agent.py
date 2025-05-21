import os
import sys
import getpass
import python_weather
import datetime

from agents.base_agent import BaseAgent
from agents.weather.tools import getWeather
from agents.weather.prompt_template import PROMPT_TEMPLATE


TOOLS = [getWeather]


class WeatherAgent(BaseAgent):
  """
  Specialized agent for fetching weather forecasts, uses LangChain framework and the python-weather library to get weather data.
  """

  def __init__(self, apiKey, tools=TOOLS, promptTemplate=PROMPT_TEMPLATE):
    super().__init__(
        apiKey=apiKey,
        tools=tools,
        promptTemplate=promptTemplate
    )

if __name__ == "__main__":
  if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = getpass.getpass("Enter Gemini API key: ")

  executor = WeatherAgent(
      apiKey=os.environ["GEMINI_API_KEY"]
  )

  tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
  query = f"How's the weather in Berlin {tomorrow}?"
  result = executor.run(query)
  print(result.get("output"))
