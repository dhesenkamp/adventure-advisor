import asyncio
import python_weather
"""python-weather relies on wttr.in, which uses worldweatheronline.com/weather-api/"""
from datetime import datetime

from langchain_core.tools import tool
from langchain_community.utilities import OpenWeatherMapAPIWrapper

from base_agent import BaseAgent


WEATHER_PROMPT_TEMPLATE = (
    "Extract the date and location from the input and convert the date to string YYYY-MM-DD format, then call the `getWeather` tool with the extracted date and location."
    "If no specific date is provided, assume the request is for today."
    "Today is {today}."
    "Example:"
    "User: 'What will the weather be like on 6th of June in Berlin?'"
    "→ Extracted date: '2025-06-06'"
    "→ Extracted location: 'Berlin'"
    "→ Call tool: getWeather(location='Berlin', date='2025-06-06')"
    "User input: {input}\n\n"
    "Chat history: {history}\n\n"
    "Your scratchpad: {agent_scratchpad}\n\n"
    """Return the result as a valid JSON object in this format:
    {{
      "action": "return_weather",
      "data": {{
        "date": "<actual date in YYYY-MM-DD>",
        "location": "<location>",
        "forecast": [<returned weather information>]
      }}
    }}"""
)


@tool
def getWeather(location: str, date: str) -> dict:
  """
  Get the weather forecast for a specific location and date using the python-weather library.
  Return weather parameters such as high, low, average temperature, sunrise, sunset, wind, precipitation, etc.

  Args:
    location (str): The location for which to fetch the weather.
    date (str): The date for which to fetch the weather, in YYYY-MM-DD format.
  Returns:
    result (dict): A dictionary containing the weather forecast for the specified date and location. If no forecast is found, an error message is returned.
  """
  async def fetchWeather(location: str, date: str):
    print(f"Fetching weather for {location} on {date}...")
    async with python_weather.Client(unit=python_weather.METRIC) as client:
      forecasts = await client.get(location)
      targetDay = datetime.strptime(date, "%Y-%m-%d").date()

      for daily in forecasts:
        if daily.date == targetDay:

          rainChance = dict()
          for hourly in daily.hourly_forecasts:
            rainChance.update(
                {hourly.time.isoformat(): hourly.chances_of_rain}
            )

          return {
              "date": str(daily.date),
              "location": location,
              "sunrise": daily.sunrise,
              "sunset": daily.sunset,
              "sunlight": daily.sunlight,
              "avg_temperature": daily.temperature,
              "highest_temperature": daily.highest_temperature,
              "lowest_temperature": daily.lowest_temperature,
              "snowfall": daily.snowfall,
              "rain_chance": rainChance,
          }

      return {"error": "No forecast found for this date."}

  result = asyncio.run(fetchWeather(location, date))

  return result


TOOLS = [getWeather]


class WeatherAgent(BaseAgent):
  """
  Specialized agent for fetching weather forecasts, uses LangChain framework and the python-weather library to get weather data.
  """

  def __init__(self, apiKey, tools=TOOLS, promptTemplate=WEATHER_PROMPT_TEMPLATE):
    super().__init__(
        apiKey=apiKey,
        tools=tools,
        promptTemplate=promptTemplate
    )
