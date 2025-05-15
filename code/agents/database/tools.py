import os
from supabase import create_client
from langchain_core.tools import tool

URL = "https://ovpkmntjpebbfbsnedlq.supabase.co"
KEY = os.environ.get("SUPABASE_API_KEY")


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
  string_fields = {"category", "region", "primary_region"}
  lte_fields = {"max_altitude", "descent_m"}
  eq_fields = {"experience", "difficulty"}
  gte_fields = {
      "duration_min", "length_m", "ascent_m", "min_altitude"
  }

  for field, value in features.items():
    if value is None:
      continue

    if field in string_fields and isinstance(value, str):
      query = query.ilike(field, f"%{value}%")
    elif field in lte_fields and isinstance(value, int):
      query = query.lte(field, value)
    elif field in gte_fields and isinstance(value, int):
      query = query.gte(field, value)
    elif field in eq_fields:
      query = query.eq(field, value)

  response = query.limit(limit).execute()
  return response.data


if __name__ == "__main__":
  if "SUPABASE_API_KEY" not in os.environ:
    os.environ["SUPABASE_API_KEY"] = input("Enter Supabase API key: ")

  result = queryDatabase.invoke({
      "category": "Hiking",
      "difficulty": 1,
      "duration_min": 60,
      "limit": 1
  })
  print(result)
