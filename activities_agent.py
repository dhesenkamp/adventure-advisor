
import os
import json
import re
import supabase
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain import hub
from langchain.memory import ConversationBufferMemory

from supabase.client import Client, create_client

API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = "https://ovpkmntjpebbfbsnedlq.supabase.co"
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


# function not yet in use, but maybe good for later use to initialize agent
def prepareAgentPrompt(input_text):
  agentPrompt = f"""
  Query the database using PostgreSQL syntax.

  The database contains information about outdoor activities. 
  Relevant searchable text columns include: 'title', 'category', 'short_description', 'long_description', 'directions', 
  'teaser_text', 'public_transit', 'parking', 'starting_point', 'destination', 'safety_guidelines',
  'equipment', 'additional_info', 'tip', 'region', 'primary_region', 'image_url', 'elevation_profile_url'.
  
  Numerical columns include: 'difficulty', 'stamina', 'experience', 'landscape'.

  Numerical columns that need to be searched in ranges include: 'duration_min', 'length_m', 'ascent_m', 'descent_m', 'min_altitude', 'max_altitude'.

  Array-type columns include: regions, way_types, season_available — use `unnest()` when querying these if searching inside arrays , 'coordinates'.

  Regarding the category, the user might use different words for describing the type of sport, here is a summary, which word mean what: {
      "hiking": ["Hiking trail", "Mountain tour", "Alpine tour", "Winter hiking", "Hiking with kids", "Theme trail", "Pilgrim trail", "Long distance hiking trail"],
      "biking": ["Mountainbiking", "Race cycling", "Cycle routes", "MTB Transalp", "E-Bike", "Gravel Bike"],
      "walking": ["Nordic walking", "City walking tour", "Hiking with kids", "Theme trail"],
      "cycling": ["Long distance cycling", "Race cycling", "Cycle routes", "E-Bike", "Gravel Bike"],
      "mountainbiking": ["Mountainbiking", "MTB Transalp", "E-Bike"],
      "running": ["Trail running", "Jogging"],
      "winter": ["Winter hiking", "Snowshoeing", "Cross-country skiing", "Back-country skiing", "Tobogganing", "Freeride skiing"],
      "climbing": ["Alpine climbing", "Fixed rope route", "Ice climbing"],
      "water": ["Canoeing & SUP", "Kayaking", "Rafting", "Canyoning", "Fishing"],
      "family": ["Hiking with kids", "Theme trail", "Tobogganing"],
      "horse": ["Horseback riding"]
    }

  Example queries:
  - Search by keyword in the title or category:
    SELECT * FROM hiking_routes WHERE title ILIKE '%input_text%';
    SELECT * FROM hiking_routes WHERE category ILIKE '%hiking%';

  - Search by range in a numerical column like duration_min:
    SELECT * FROM hiking_routes WHERE duration_min BETWEEN 102 AND 138;
    For getting the range you can call the function get_range_query(column, target) with target being the time in minutes, that the user prompted.

  - Search by a numerical value in difficulty:
    SELECT * FROM hiking_routes WHERE difficulty = 2;

  - Search using an array column:
    SELECT * FROM hiking_routes, unnest(season_available) AS season WHERE season ILIKE '%summer%';

  It is not necessary to search all columns — only those needed based on the input.

  Generate a PostgreSQL query using the input: {input_text}.

  Return the result as a valid JSON object in this format (following A2A spec for agent interoperability):

  {{
    "action": "return_sql_query_results",
    "data": {{
      "query": "<PostgreSQL query here>",
      "query_response": [<array of rows as JSON objects>]
    }}
  }}
  """

  return agentPrompt



# Load env variables
load_dotenv()

# initiate supabase db
SUPABASE_URL = "https://ovpkmntjpebbfbsnedlq.supabase.co"
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
HOST = SUPABASE_URL.replace("https://", "").replace("http://", "")
USER = "postgres"
PASSWORD = SUPABASE_KEY
PORT = 5432
DB_NAME = "postgres" 

connectionUri = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}?sslmode=require"

# Create the SQLDatabase
DB = SQLDatabase.from_uri(connectionUri)

supabase = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

llm = ChatOpenAI(temperature=0)

memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
prompt = hub.pull("hwchase17/openai-functions-agent")



# Connect to Supabase SQL
#connection_uri = "postgresql://postgres:<your-password>@DB.<your-project>.supabase.co:5432/postgres?sslmode=require"
#DB = SQLDatabase.from_uri(connection_uri)

# Define SQL query tool
@tool
def searchActivities(query: str) -> str:
    """Search the hiking_routes table using natural language input."""
    dbChain = SQLDatabaseChain.from_llm(llm, db=supabase, verbose=True)
    return dbChain.run(query)

# Agent setup
tools = [searchActivities]
prompt = hub.pull("hwchase17/openai-functions-agent")
agent = create_tool_calling_agent(llm, tools, prompt)
agentExecutor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)

# Run query
response = agentExecutor.invoke({"input": "Find a hiking route under 10km with low difficulty."})
print(response["output"])
