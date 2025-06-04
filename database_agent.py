import os
from dotenv import load_dotenv
from supabase import create_client
from langchain_core.tools import tool
from base_agent import BaseAgent

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_API_KEY")

QUERY_PROMPT_TEMPLATE = (
    "You are a database query generator. Given a natural language query, you will utilize the tool `queryDatabase` to retrieve data from a Supabase database of hiking, biking, and other outdoor sports activities.\n\n"
    "Your job has two steps:\n"
    "1. Extract any relevant filters from the user query (e.g. category, difficulty, duration, region, etc.) and use them **as arguments to the tool**.\n"
    "2. Take the response from the tool and generate a final JSON output like this:\n"
    """{{
    "action": "return_activities",
    "data": [
      {{
        "title": "<title of the activity>",
        "location": "<region or primary_region>",
        "length": "<length_m>",
        "difficulty": "<difficulty>"
      }},
      ...
    ]
    }}\n\n"""
    "You can query for activities based on the following features:\n"
    "- category: str\n"
    "- difficulty: int [0, 1, 2, 3]\n"
    "- duration_min: int\n"
    "- length_m: int\n"
    "- ascent_m: int\n"
    "- descent_m: int\n"
    "- min_altitude: int\n"
    "- max_altitude: int\n"
    "- experience: int [0-6]\n"
    "- region: str\n"
    "- primary_region: str\n\n"
    "Extract only those features mentioned in the user query. Stick to the correct types, translating natural language where needed (e.g., 'easy' can be 0, 'hard' can be 3).\n\n"
    "Example user query: 'I want to go for a long hike in the Brenta Dolomites with medium difficulty and around 3 hours long.'\n"
    "Extracted features:\n"
    "- category: 'Hiking'\n"
    "- difficulty: 1 or 2\n"
    "- duration_min: 180\n"
    "- region: 'Brenta' or 'Dolomites'\n"
    "- primary_region: 'Brenta' or 'Dolomites'\n\n"
    "User query: {input}\n\n"
    "Chat history: {history}\n\n"
    "Your scratchpad: {agent_scratchpad}\n\n"
    "Return a JSON object in the following format:\n"
    """{{
    "action": "return_activities",
    "data": {{
        "title": "<title of the activity>",
        "location": "<region or primary_region>",
        "length": "<length_m>",
        "difficulty": "<difficulty>"
      }}
  }}"""
)


@tool
def queryDatabase(
    category: str = None, difficulty: int = None,
    duration_min: int = None, length_m: int = None, ascent_m: int = None,
    descent_m: int = None, min_altitude: int = None, max_altitude: int = None,
    experience: int = None, region: str = None, primary_region: str = None,
    limit: int = 5
):
  """
  Query a Supabase database for outdoor activities based on various (optional) parameters

  Args:
    category: str, 
      ["Long distance cycling", "Winter hiking", "Alpine tour", "MTB Transalp", "Trail running", "Cycle routes", "Mountainbiking", "Gravel Bike", "Hiking with kids", "Long distance hiking trail", "Mountain tour", "Alpine climbing", "Hiking trail"]
    difficulty: int, [0, 1, 2, 3]
    duration_min: int,
    length_m: int,
    ascent_m: int,
    descent_m: int,
    min_altitude: int,
    max_altitude: int,
    experience: int, [0, 1, 2, 3, 4, 5, 6]
    region: str
    primary_region: str
  Returns:
    list: list of dicts containing the query results, e.g. [{"title": "Hiking in the Alps", "region": "Alps", "length_m": 12000, "difficulty": 2}, {}, ...]
  """

  client = create_client(URL, KEY)

  """NB: query from 'random_hiking_routes' for server-side shuffling. 'hiking_routes' is the original table"""
  query = client.from_("random_hiking_routes").select(
      "title, region, length_m, difficulty")

  features = {
      "category": category,
      "difficulty": difficulty,
      "duration_min": duration_min,
      "length_m": length_m,
      "ascent_m": ascent_m,
      "descent_m": descent_m,
      "min_altitude": min_altitude,
      "max_altitude": max_altitude,
      "experience": experience,
      "region": region,
      "primary_region": primary_region
  }

  # Define how to handle each field
  stringFields = {"category", "region", "primary_region"}
  lteFields = {"max_altitude", "descent_m"}
  eqFields = {"experience", "difficulty"}
  gteFields = {
      "duration_min", "length_m", "ascent_m", "min_altitude"
  }

  for field, value in features.items():
    if value is None:
      continue

    if field in stringFields and isinstance(value, str):
      query = query.ilike(field, f"%{value}%")
    elif field in lteFields and isinstance(value, int):
      query = query.lte(field, value)
    elif field in gteFields and isinstance(value, int):
      query = query.gte(field, value)
    elif field in eqFields:
      query = query.eq(field, value)

  response = query.limit(limit).execute()
  return response.data


TOOLS = [queryDatabase]


class DatabaseAgent(BaseAgent):
  def __init__(self, apiKey: str, tools: list = TOOLS, promptTemplate: str | None = QUERY_PROMPT_TEMPLATE):

    super().__init__(apiKey=apiKey, tools=tools, promptTemplate=promptTemplate)
