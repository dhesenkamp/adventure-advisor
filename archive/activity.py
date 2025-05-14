import os
import json
import re
import supabase
from google import genai
from google.genai import types

API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = "https://ovpkmntjpebbfbsnedlq.supabase.co"
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


ALLOWED_COLUMNS = [
    'title', 'category', 'short_description', 'long_description', 'directions',
    'teaser_text', 'public_transit', 'parking', 'starting_point', 'destination', 'safety_guidelines',
    'equipment', 'additional_info', 'tip', 'duration_min', 'length_m', 'ascent_m', 'descent_m',
    'min_altitude', 'max_altitude', 'difficulty', 'stamina', 'experience', 'landscape', 'coordinates',
    'way_types', 'season_available', 'region', 'primary_region', 'regions', 'image_url', 'elevation_profile_url'
]


class ActivityAgent:
  def __init__(self):
    self.client = genai.Client(api_key=API_KEY)
    self.model = "gemini-2.0-flash"
    column_hint = "\n".join([f"- {col}" for col in ALLOWED_COLUMNS])
    self.instructions = f"You are an outdoor activity agent. Given a user request, extract key criteria for searching a database of outdoor activities."
    f"Return the results as a valid JSON object using only the following fields: {column_hint} Only include fields mentioned or implied in the user's request."
    f"You may assume the search will handle ranges for numeric values like length and duration."
    f"Return only a JSON object."
    self.supabase = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

  def getActivity(self, prompt):
    extractPrompt = (
        f"Extract search criteria from this user request for outdoor activities:\n\n"
        f"{prompt}\n\n"
        f"Return only a JSON object with keys such as category, difficulty, region, season, length_m, etc."
    )

    response = self.client.models.generate_content(
        model=self.model,
        config=types.GenerateContentConfig(
            system_instruction=self.instructions),
        contents=extractPrompt
    )

    criteria = self.extractJsonFromText(response.text)
    if not criteria:
      return "I couldn't extract valid search criteria."

    query = self.buildQuery(criteria)
    print("Criteria:", criteria)
    print("Query (before .execute()):", query)
    result = query.execute()
    # result = self.supabase.table("hiking_routes").select("*").match(query).execute()

    if result.data:
      return json.dumps(result.data[:3], indent=2)  # Return first 3 results
    return "No matching outdoor activities found."

  def extractJsonFromText(self, text):
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if not match:
      return None
    try:
      cleaned = match.group(0).replace("'", '"')
      return json.loads(cleaned)
    except json.JSONDecodeError:
      return None

  def buildQuery(self, criteria):
    query = self.supabase.table("hiking_routes").select("*")

    for key, value in criteria.items():
      if key == "length_m":
        try:
          target = int(value)
          lower = max(0, target - 1000)  # 1 km tolerance
          upper = target + 1000
          query = query.gte("length_m", lower).lte("length_m", upper)
        except ValueError:
          continue
      elif key == "duration_min":
        try:
          duration = int(value)
          lower = max(0, duration - 30)
          upper = duration + 30
          query = query.gte("duration_min", lower).lte("duration_min", upper)
        except ValueError:
          continue
      elif key in ["regions", "season_available"]:  # JSONB array columns
        if isinstance(value, list):
          query = query.contains(key, value)
        else:
          query = query.contains(key, [value])
      elif key in ALLOWED_COLUMNS:
        query = query.eq(key, value)
    return query
