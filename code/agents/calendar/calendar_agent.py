import os
import sys
import getpass
import pickle
import datetime
import pytz

from langchain_core.runnables import RunnableConfig
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor


from agents.base_agent import BaseAgent
from agents.calendar.tools import getEvents
from agents.calendar.prompt_template import PROMPT_TEMPLATE

TOOLS = [getEvents]
CREDENTIALS = "..../credentials.json"


class CalendarAgent(BaseAgent):
  """
  Specialized agent for fetching calendar events, uses LangChain framework and the Google Calendar API to get calendar data.
  """

  def __init__(self, apiKey, tools=TOOLS, promptTemplate=PROMPT_TEMPLATE):
    super().__init__(
        apiKey=apiKey,
        tools=tools,
        promptTemplate=promptTemplate
    )
    self.memory = ConversationBufferMemory(
        memory_key="history", input_key="input")
    self.config = RunnableConfig(configurable={"memory": self.memory})
    self.executor = AgentExecutor(
        agent=self.agent,
        tools=self.tools,
        memory=self.memory,
        verbose=True,
    )

  def run(self, query, today=None):
    return self.executor.invoke({"input": query, "today": today}, config=self.config)


if __name__ == "__main__":

  if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = getpass.getpass("Enter Gemini API key: ")

  executor = CalendarAgent(
      apiKey=os.environ["GEMINI_API_KEY"],
  )

  today = datetime.datetime.now().date()
  query = "Do I have any appointments in the next two days?"

  result = executor.run(query, today)
  print(result.get("output"))
