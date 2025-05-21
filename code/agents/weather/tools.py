import asyncio
from datetime import datetime

import python_weather
from langchain_core.tools import tool
from langchain_community.utilities import OpenWeatherMapAPIWrapper

"""TODO
- use langchain community OWM wrapper (pip install pyowm)
- get OWM API key
"""


@tool
def getWeather(location: str, date: str) -> dict:
  """
  Get the weather forecast for a specific location and date using the python-weather library.
  Return weather parameters such as high, low, average temperature, sunrise, sunset, snowfall.

  Args:
      location (str): The location for which to fetch the weather.
      date (str): The date for which to fetch the weather, in YYYY-MM-DD format.
  Returns:
      dict: A dictionary containing the weather forecast for the specified date and location. If no forecast is found, an error message is returned.
  """
  async def fetchWeather(location: str, date: str):
    async with python_weather.Client() as client:
      forecasts = await client.get(location)
      targetDay = datetime.strptime(date, "%Y-%m-%d").date()

      for f in forecasts:
        if f.date == targetDay:
          return {
              "date": str(f.date),
              "location": location,
              "avg_temperature": f.temperature,
              "highest_temperature": f.highest_temperature,
              "lowest_temperature": f.lowest_temperature,
              "snowfall": f.snowfall,
              "sunrise": f.sunrise,
              "sunset": f.sunset
          }

      return {"error": "No forecast found for this date."}

  result = asyncio.run(fetchWeather(location, date))

  return result
