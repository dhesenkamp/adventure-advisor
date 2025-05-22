import os
import json
import re
from datetime import datetime
from supabase import create_client, Client

# CONFIG
SUPABASE_URL = "https://ovpkmntjpebbfbsnedlq.supabase.co"
SUPABASE_KEY = "**************************"
JSON_DIR = r"C:\Users\luzie\OneDrive\Desktop\Studium\Master\2. Semester\Designing Large Scale AI Systems\tour_json"  # Replace with your folder path

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def parseJsonFromFile(filePath):
  with open(filePath, 'r', encoding='utf-8') as f:
    raw = f.read()
    jsonText = re.sub(r'^alp\.jsonp\[-?\d+\]key=.+?\(', '', raw).rstrip(')')
    return json.loads(jsonText)

def extractRouteFields(data):
  content = data["answer"]["contents"][0]
  meta = content.get("meta", {})
  texts = content.get("texts", {})
  timestamps = meta.get("timestamp", {})
  coordinates = content.get("geoJson", {}).get("coordinates", [])
  stats = content.get("metrics", {})
  rating = content.get("ratingInfo", {})

  return {
    "id": int(content.get("id")),
    "title": content.get("title"),
    "type": content.get("type"),
    "category": content.get("category", {}).get("title"),
    "short_description": texts.get("short"),
    "long_description": texts.get("long"),
    "directions": texts.get("directions"),
    "teaser_text": content.get("teaserText"),
    "public_transit": texts.get("publicTransit"),
    "parking": texts.get("parking"),
    "starting_point": texts.get("startingPoint"),
    "destination": texts.get("destination"),
    "safety_guidelines": texts.get("safetyGuidelines"),
    "equipment": texts.get("equipment"),
    "additional_info": texts.get("additionalInformation"),
    "tip": texts.get("tip"),
    "duration_min": stats.get("duration", {}).get("minimal"),
    "length_m": stats.get("length"),
    "ascent_m": stats.get("elevation",{}).get("ascent"),
    "descent_m": stats.get("elevation",{}).get("descent"),
    "min_altitude": stats.get("elevation",{}).get("minAltitude"),
    "max_altitude": stats.get("elevation",{}).get("maxAltitude"),
    "difficulty": rating.get("difficulty"),
    "stamina": rating.get("stamina"),
    "experience": rating.get("experience"),
    "landscape": rating.get("landscape"),
    "coordinates": coordinates,
    "way_types": content.get("wayTypeInfo"),
    "season_available": [month for month, available in content.get("season", {}).items() if available.lower() == "yes"],
    "region": meta.get("source", {}).get("name"),
    "primary_region": content.get("primaryRegion", {}).get("title"),
    "regions": content.get("regions"),
    "image_url": content.get("primaryImage", {}).get("meta", {}).get("source", {}).get("name"),
    "elevation_profile_url": stats.get("elevation",{}).get("elevationProfile",{}).get("url"),
    "source_organization": meta.get("source", {}).get("name"),
    "source_url": meta.get("source", {}).get("url"),
    "created_at": timestamps.get("createdAt"),
    "updated_at": timestamps.get("lastModifiedAt"),
    "raw_json": content
  }

def uploadToSupabase(payload):
  try:
    data, count = supabase.table('hiking_routes').upsert(payload, on_conflict=['id']).execute()
    print(f"Inserted: {payload['title']}")
  except Exception as e:
    print(f"Failed to insert {payload.get('id')}: {e}")

def main():
  for fileName in os.listdir(JSON_DIR):
    if not fileName.endswith(".json"):
      continue
    filePath = os.path.join(JSON_DIR, fileName)
    try:
      parsed = parseJsonFromFile(filePath)
      payload = extractRouteFields(parsed)
      uploadToSupabase(payload)
    except Exception as e:
      print(f"Error processing {fileName}: {e}")

if __name__ == "__main__":
  main()
