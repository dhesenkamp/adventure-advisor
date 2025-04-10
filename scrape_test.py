import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from supabase import create_client, Client


# CONFIG
SUPABASE_URL = "https://ovpkmntjpebbfbsnedlq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im92cGttbnRqcGViYmZic25lZGxxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQyMDM3MDgsImV4cCI6MjA1OTc3OTcwOH0.rZ-zn9v96ddsJMmqmvJoKi8qQuq0RfiPDZIidb3woTo"
SITEMAP_URL = "https://www.visittrentino.info/static/sitemaps/alpsteintours_en.xml"

# Init Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def getDriver():
  options = Options()
  options.add_argument("--headless=new")
  options.add_argument("--disable-gpu")
  options.add_argument("--no-sandbox")
  driver = webdriver.Chrome(options=options)
  return driver


def getSitemapUrls(sitemapUrl):
  print('getSitemapUrls')
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
  }
  try:
    response = requests.get(sitemapUrl, headers=headers)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    return [loc.text for loc in root.findall(".//{*}loc")]
  except Exception as e:
    print(f"Error fetching sitemap: {str(e)}")
    return []


def extractFloat(text):
  try:
    return float(re.search(r'[\d.]+', text.replace(',', '')).group())
  except:
    return 0.0


def extractTime(text):
  try:
    if 'h' in text:
      hours = int(re.search(r'(\d+)\s*h', text).group(1))
      mins = int(re.search(r'(\d+)\s*m', text).group(1)) if 'm' in text else 0
      return hours * 60 + mins
    return int(re.search(r'\d+', text).group())
  except:
    return 0


def scrapeRouteData(driver, routeUrl):
  print(f"Scraping: {routeUrl}")
  try:
    driver.get(routeUrl)

    # Wait for any one stat block to load
    WebDriverWait(driver, 10).until(
      EC.presence_of_element_located((By.CLASS_NAME, 'oax_clearfix'))
    )

    # Title
    title = driver.find_element(By.TAG_NAME, 'h1').text.strip()

    # Description
    descriptionBlocks = driver.find_elements(By.CSS_SELECTOR, '.description p')
    description = ' '.join([p.text.strip() for p in descriptionBlocks]) or "No description"

    # Stats
    stats = {}
    statBlocks = driver.find_elements(By.CLASS_NAME, 'oax_clearfix')
    for block in statBlocks:
      try:
        label = block.find_element(By.CLASS_NAME, 'oax_left').text.strip().lower()
        value = block.find_element(By.CLASS_NAME, 'oax_right').text.strip()
        stats[label] = value
      except Exception as e:
        print(f"Error parsing stat block: {e}")

    # Debug: print stats dictionary
    print("Extracted stats:", stats)

    # Parse stats
    distance = extractFloat(stats.get('distance', '0 km'))
    elevation = extractFloat(stats.get('elevation gain', '0 m'))
    duration = extractTime(stats.get('duration', '0 min'))
    difficulty = stats.get('difficulty', 'unknown').title()

    # GPX link
    gpxLink = None
    links = driver.find_elements(By.TAG_NAME, 'a')
    for link in links:
      href = link.get_attribute('href')
      if href and href.endswith('.gpx'):
        gpxLink = urljoin(routeUrl, href)
        break

    return {
      'title': title,
      'description': description,
      'distanceKm': distance,
      'elevationGainM': elevation,
      'difficulty': difficulty,
      'durationMin': duration,
      'url': routeUrl,
      'gpxDownloadUrl': gpxLink
    }

  except Exception as e:
    print(f"Error scraping {routeUrl}: {str(e)}")
    return None


def downloadGpx(gpxUrl):
  print('downloadGpx')
  if not gpxUrl:
    return None
  try:
    response = requests.get(gpxUrl)
    response.raise_for_status()
    return response.text
  except Exception as e:
    print(f"Error downloading GPX: {str(e)}")
    return None


def main():
  print('main')
  routeUrls = getSitemapUrls(SITEMAP_URL)
  driver = getDriver()

  for url in routeUrls:
    try:
      routeData = scrapeRouteData(driver, url)
      if routeData and routeData['gpxDownloadUrl']:
        routeData['gpxData'] = downloadGpx(routeData['gpxDownloadUrl'])

      # Store in Supabase
      if routeData:
        data, count = supabase.table('hiking_routes').insert(routeData).execute()
        print(f"Inserted: {routeData['title']}")
    except Exception as e:
      print(f"Error processing {url}: {str(e)}")

  driver.quit()


if __name__ == "__main__":
  main()