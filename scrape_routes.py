import os
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client


# Configure these variables
SUPABASE_URL = "https://ovpkmntjpebbfbsnedlq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im92cGttbnRqcGViYmZic25lZGxxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQyMDM3MDgsImV4cCI6MjA1OTc3OTcwOH0.rZ-zn9v96ddsJMmqmvJoKi8qQuq0RfiPDZIidb3woTo"
SITEMAP_URL = "https://www.visittrentino.info/static/sitemaps/alpsteintours_en.xml"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def getSitemapUrls(sitemapUrl):
  print('getSitemapUrls')
  """Extract all URLs from the sitemap with proper headers"""
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.visittrentino.info/'
  }
  
  try:
    response = requests.get(sitemapUrl, headers=headers)
    response.raise_for_status()
    
    # Check if response is XML
    if 'xml' not in response.headers.get('Content-Type', ''):
      print("Warning: Response doesn't appear to be XML")
    
    soup = BeautifulSoup(response.content, 'lxml-xml')
    return [loc.text for loc in soup.find_all('loc')]
  
  except Exception as e:
    print(f"Error fetching sitemap: {str(e)}")
    return []


def scrapeRouteData(routeUrl):
  """Scrape individual route page with proper selectors"""
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  }
  try:
    response = requests.get(routeUrl, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract title
    title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "No title"

    # Extract description (combine all paragraph elements)
    description = ' '.join([p.get_text(strip=True) for p in soup.select('.description p')]) or "No description"

    def extractRouteStats(soup):
      stats = {}
      
      # Find all stat containers
      statContainers = soup.find_all('div', class_='oax_clearfix')
      
      for container in statContainers:
        labelDiv = container.find('div', class_='oax_left')
        valueDiv = container.find('div', class_='oax_right')
        
        if labelDiv and valueDiv:
          label = labelDiv.get_text(strip=True).lower()
          value = valueDiv.get_text(strip=True)
          stats[label] = value
      
      return stats

    # Usage in your scrapeRouteData function:
    stats = extractRouteStats(soup)
    distance = stats.get('distance', '0 km')
    elevation = stats.get('elevation gain', '0 m')

    def extractFloat(text):
      try:
        return float(re.search(r'[\d.]+', text.replace(',','')).group())
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
    
    distanceKm = extractFloat(stats.get('distance', '0 km'))
    duration = extractTime(stats.get('duration', '0 min'))

    # Find GPX download link
    gpxLink = None
    for link in soup.find_all('a', href=True):
      if link['href'].lower().endswith('.gpx'):
        gpxLink = urljoin(routeUrl, link['href'])
        break

    return {
      'title': title,
      'description': description,
      'distanceKm': distance,
      'elevationGainM': elevation,
      'difficulty': stats.get('difficulty', 'unknown').title(),
      'durationMin': duration,
      'url': routeUrl,
      'gpxDownloadUrl': gpxLink
    }

  except Exception as e:
    print(f"Error scraping {routeUrl}: {str(e)}")
    return None


def downloadGpx(gpxUrl):
  """Download GPX file content"""
  print('downloadGpx')
  if not gpxUrl:
    return None
  response = requests.get(gpxUrl)
  return response.text


def main():
  print('main')
  routeUrls = getSitemapUrls(SITEMAP_URL)
  
  for url in routeUrls:
    print(f"Processing: {url}")
    try:
      # Scrape route data
      routeData = scrapeRouteData(url)
      
      # Download GPX
      if routeData['gpxDownloadUrl']:
        routeData['gpxData'] = downloadGpx(routeData['gpxDownloadUrl'])
      
      # Insert into Supabase
      data, count = supabase.table('hiking_routes').insert(routeData).execute()
      print(f"Inserted: {routeData['title']}")
      
    except Exception as e:
      print(f"Error processing {url}: {str(e)}")


if __name__ == "__main__":
  main()