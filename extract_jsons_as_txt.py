import os
import re
import requests
import xml.etree.ElementTree as ET

SITEMAP_URL = "https://www.visittrentino.info/static/sitemaps/alpsteintours_en.xml"
API_TEMPLATE = "https://api-oa.com/api/v2/project/api-trentino/contents/{}?display=verbose&edit=&fallback=true&jsapi=1&key=IKFFP3AG-EMWGMGUJ-4OSSMTMS&lang=en&legacyJson=&share=&token=&callback=alp.jsonp[-9255270690]key=IKFFP3AG-EMWGMGUJ-4OSSMTMS"
OUTPUT_DIR = "tour_jsons"

HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def ensureOutputDirectory():
  if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def extractTourIds(sitemapUrl):
  try:
    response = requests.get(sitemapUrl, headers=HEADERS)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    loc_tags = root.findall(".//{*}loc")
    ids = []
    for tag in loc_tags:
      match = re.search(r"_tour_(\d+)", tag.text)
      if match:
        ids.append(match.group(1))
    return ids
  except Exception as e:
    print(f"Error fetching sitemap: {e}")
    return []

def downloadJson(tourId):
  url = API_TEMPLATE.format(tourId)
  try:
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text
  except Exception as e:
    print(f"Error downloading JSON for {tourId}: {e}")
    return None

def saveJsonToFile(tourId, jsonData):
  filePath = os.path.join(OUTPUT_DIR, f"{tourId}.txt")
  with open(filePath, "w", encoding="utf-8") as f:
    f.write(jsonData)

def main():
  ensureOutputDirectory()
  tourIds = extractTourIds(SITEMAP_URL)
  print(f"Found {len(tourIds)} tour IDs")

  for tourId in tourIds:
    print(f"Processing ID: {tourId}")
    jsonData = downloadJson(tourId)
    if jsonData:
      saveJsonToFile(tourId, jsonData)

if __name__ == "__main__":
  main()
