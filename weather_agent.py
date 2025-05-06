import python_weather
import asyncio
from datetime import datetime
from pydantic import BaseModel
from langchain_core.tools import tool

import os
import os
from dotenv import load_dotenv
from pydantic import BaseModel

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI


# Load env variables
load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    api_key=API_KEY
)


def prepareAgentPrompt():
  template = """
      Look up the weather and give a forcast for the given day. Use the users {input} to get the location and day.
      {agent_scratchpad}
      Return the result as a valid JSON object in this format:
      {{
        "action": "return_sql_query_results",
        "data": {{
          "query": "<PostgreSQL query here>",
          "query_response": [<array of rows as JSON objects>]
        }}
      }}
    """
  return ChatPromptTemplate.from_template(template)


memory = ConversationBufferMemory()
config = RunnableConfig(configurable={"memory": memory})
prompt = prepareAgentPrompt()

# Input schema for the weather tool


class WeatherInput(BaseModel):
  location: str
  date: str  # Format: YYYY-MM-DD

# Async function to fetch the weather forecast


async def fetchWeather(location: str, date: str):
  async with python_weather.Client() as client:
    forecasts = await client.get(location)
    targetDay = datetime.strptime(date, "%Y-%m-%d").date()

    for forecast in forecasts:
      if forecast.date == targetDay:
        return {
            "date": str(forecast.date),
            "location": location,
            "avg_temperature": forecast.temperature,
            "highest_temperature": forecast.highest_temperature,
            "lowest_temperature": forecast.lowest_temperature,
            "snowfall": forecast.snowfall,
            "sunrise": forecast.sunrise,
            "sunset": forecast.sunset
        }

    return {"error": "No forecast found for this date."}


# LangChain-compatible tool
@tool(args_schema=WeatherInput)
def getWeather(location: str, date: str):
  """
  Get the weather forecast for a specific location and date (YYYY-MM-DD).
  Returns sky conditions, temperature, high, and low forecast.
  """
  result = asyncio.run(fetchWeather(location, date)
                       )  # date format (YYYY-MM-DD)
  return result


# Agent setup
tools = [getWeather]
agent = create_tool_calling_agent(llm, tools, prompt)
weatherExecutor = AgentExecutor(
    agent=agent, tools=tools, memory=memory, verbose=True)

# Run query
response = weatherExecutor.invoke(
    {"input": "What will the weather be like in Hamburg on 2025-05-02?"}, config=config)
print(response)
