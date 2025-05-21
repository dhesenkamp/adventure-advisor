import os
import supabase
import getpass

from dotenv import load_dotenv

from agents.base_agent import BaseAgent
from agents.database.prompt_template import QUERY_PROMPT
from agents.database.tools import queryDatabase

load_dotenv()

TOOLS = [queryDatabase]


class DatabaseAgent(BaseAgent):
  def __init__(self, apiKey: str, tools: list = TOOLS, promptTemplate: str | None = QUERY_PROMPT):

    super().__init__(apiKey=apiKey, tools=tools, promptTemplate=promptTemplate)


if __name__ == "__main__":
  if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = getpass.getpass("Enter Gemini API key: ")

  executor = DatabaseAgent(
      apiKey=os.environ.get("GEMINI_API_KEY")
  )

  query = "I want to go hiking in the Garda region with medium difficulty and for up to 4 hours."
  response = executor.run(query)
  print(response)
