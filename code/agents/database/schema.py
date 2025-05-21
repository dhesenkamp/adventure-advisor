import os
import supabase

url = "https://ovpkmntjpebbfbsnedlq.supabase.co"
key = os.environ.get("SUPABASE_API_KEY")
client = supabase.create_client(url, str(key))


def get_unique(field: str):
  """helper function to get unique values from a field in the database"""
  response = (
      client.from_("hiking_routes")
      .select(field)
      .range(0, 3000)
      .execute()
  )
  return list(set(item[field] for item in response.data))


"""
DB properties:
id, title, type, category, short_description, long_description, directions, teaser_text, public_transit, parking, starting_point, destination, safety_guidelines, equipment, additional_info, tip, duration_min, length_m, ascent_m, descent_m, min_altitude, max_altitude, difficulty, stamina, experience, landscape, coordinates, way_types, season_available, region, primary_region, regions, image_url, elevation_profile_url, source_organization, source_url, created_at, updated_at, raw_json
"""

CATEGORY = [
    "Long distance cycling", "Winter hiking", "Alpine tour", "MTB Transalp", "Trail running", "Cycle routes", "Horseback riding", "Cross-country skiing", "Theme trail", "Mountainbiking", "Gravel Bike", "Freeride skiing", "Hiking with kids",
    "Fishing", "Long distance hiking trail", "Snowshoeing", "Race cycling", "Fixed rope route", "Ice climbing", "Mountain tour", "Alpine climbing", "E-Bike", "Hiking trail", "Back-country skiing", "Pilgrim trail", "Nordic walking"
]
TYPE = ["tour"]

print(get_unique("primary_region"))
