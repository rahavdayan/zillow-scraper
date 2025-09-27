#!/usr/bin/env python3
"""
Enhanced Trulia Scraper - Property Detail Extraction
Visits individual property pages to get complete data:
prices, beds, baths, sqft, and other details
"""

import requests
import csv
import time
import random
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re
import json
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TruliaEnhancedScraper:
    def __init__(self):
        """Initialize enhanced Trulia scraper"""
        self.session = requests.Session()
        self.properties = []
        self.visited_urls = set()  # Track visited URLs to avoid duplicates
        
        # Professional headers with more variation to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.trulia.com/'
        }
        self.session.headers.update(self.headers)
        
        # Focus on Hoboken, NJ and surrounding Tri-State areas with 50-50 NJ/NY split
        self.nj_locations = [
            {
                'name': 'Hoboken, NJ Rentals',
                'state': 'NJ',
                'urls': [
                    'https://www.trulia.com/for_rent/Hoboken,NJ/',
                    'https://www.trulia.com/for_rent/Hoboken,NJ/2_p/',
                    'https://www.trulia.com/for_rent/Hoboken,NJ/3_p/'
                ]
            },
            {
                'name': 'Jersey City, NJ Rentals',
                'state': 'NJ',
                'urls': [
                    'https://www.trulia.com/for_rent/Jersey-City,NJ/',
                    'https://www.trulia.com/for_rent/Jersey-City,NJ/2_p/',
                    'https://www.trulia.com/for_rent/Jersey-City,NJ/3_p/'
                ]
            },
            {
                'name': 'Weehawken, NJ Rentals',
                'state': 'NJ',
                'urls': [
                    'https://www.trulia.com/for_rent/Weehawken,NJ/',
                    'https://www.trulia.com/for_rent/Weehawken,NJ/2_p/'
                ]
            },
            {
                'name': 'Union City, NJ Rentals',
                'state': 'NJ',
                'urls': [
                    'https://www.trulia.com/for_rent/Union-City,NJ/',
                    'https://www.trulia.com/for_rent/Union-City,NJ/2_p/'
                ]
            },
            {
                'name': 'North Bergen, NJ Rentals',
                'state': 'NJ',
                'urls': [
                    'https://www.trulia.com/for_rent/North-Bergen,NJ/',
                    'https://www.trulia.com/for_rent/North-Bergen,NJ/2_p/'
                ]
            },
            {
                'name': 'Fort Lee, NJ Rentals',
                'state': 'NJ',
                'urls': [
                    'https://www.trulia.com/for_rent/Fort-Lee,NJ/',
                    'https://www.trulia.com/for_rent/Fort-Lee,NJ/2_p/'
                ]
            },
            {
                'name': 'Edgewater, NJ Rentals',
                'state': 'NJ',
                'urls': [
                    'https://www.trulia.com/for_rent/Edgewater,NJ/',
                    'https://www.trulia.com/for_rent/Edgewater,NJ/2_p/'
                ]
            }
        ]
        
        self.ny_locations = [
            {
                'name': 'Manhattan, NY Rentals',
                'state': 'NY',
                'urls': [
                    'https://www.trulia.com/for_rent/Manhattan,NY/',
                    'https://www.trulia.com/for_rent/Manhattan,NY/2_p/',
                    'https://www.trulia.com/for_rent/Manhattan,NY/3_p/',
                    'https://www.trulia.com/for_rent/Manhattan,NY/4_p/'
                ]
            },
            {
                'name': 'Brooklyn, NY Rentals',
                'state': 'NY',
                'urls': [
                    'https://www.trulia.com/for_rent/Brooklyn,NY/',
                    'https://www.trulia.com/for_rent/Brooklyn,NY/2_p/',
                    'https://www.trulia.com/for_rent/Brooklyn,NY/3_p/',
                    'https://www.trulia.com/for_rent/Brooklyn,NY/4_p/'
                ]
            },
            {
                'name': 'Queens, NY Rentals',
                'state': 'NY',
                'urls': [
                    'https://www.trulia.com/for_rent/Queens,NY/',
                    'https://www.trulia.com/for_rent/Queens,NY/2_p/',
                    'https://www.trulia.com/for_rent/Queens,NY/3_p/'
                ]
            },
            {
                'name': 'Bronx, NY Rentals',
                'state': 'NY',
                'urls': [
                    'https://www.trulia.com/for_rent/Bronx,NY/',
                    'https://www.trulia.com/for_rent/Bronx,NY/2_p/',
                    'https://www.trulia.com/for_rent/Bronx,NY/3_p/'
                ]
            },
            {
                'name': 'Staten Island, NY Rentals',
                'state': 'NY',
                'urls': [
                    'https://www.trulia.com/for_rent/Staten-Island,NY/',
                    'https://www.trulia.com/for_rent/Staten-Island,NY/2_p/'
                ]
            }
        ]
        
        # Combine all locations for easy access
        self.all_locations = self.nj_locations + self.ny_locations
    
    def rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        self.session.headers.update({'User-Agent': random.choice(self.user_agents)})
    
    def extract_property_urls_from_page(self, url, location_name):
        """Extract property URLs from listing page"""
        logger.info(f"  Extracting property URLs from: {url}")
        
        try:
            time.sleep(random.uniform(5, 10))  # Increased delay to avoid blocking
            self.rotate_user_agent()  # Change user agent for each request
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"  ❌ HTTP {response.status_code} for {url}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            property_urls = []
            
            # Look for property links - try broader approach first
            all_links = soup.find_all('a', href=True)
            logger.info(f"    Found {len(all_links)} total links on page")
            
            # Filter for property-related links
            for link in all_links:
                href = link.get('href')
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        full_url = 'https://www.trulia.com' + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # Look for various property URL patterns
                    property_patterns = [
                        '/property/', '/rental/', '/homes/', '/p/', '/for_rent/',
                        '/apartments/', '/condos/', '/townhomes/', '/listing/'
                    ]
                    
                    if any(pattern in full_url.lower() for pattern in property_patterns):
                        # Additional filters to avoid non-property pages
                        avoid_patterns = [
                            '/for_rent/manhattan', '/for_rent/brooklyn', '/for_rent/queens',
                            '/homes/manhattan', '/homes/brooklyn', '/search', '/map',
                            '/neighborhood', '/schools', '/crime', '/commute'
                        ]
                        
                        if not any(avoid in full_url.lower() for avoid in avoid_patterns):
                            if full_url not in self.visited_urls:
                                property_urls.append(full_url)
                                self.visited_urls.add(full_url)
            
            # If we found property URLs, log some examples
            if property_urls:
                logger.info(f"    Found property URLs, examples:")
                for i, url in enumerate(property_urls[:3]):
                    logger.info(f"      {i+1}. {url}")
            
            # Also try specific selectors as backup
            if not property_urls:
                logger.info(f"    No URLs from broad search, trying specific selectors...")
                link_selectors = [
                    'a[href*="/property/"]',
                    'a[href*="/rental/"]', 
                    'a[href*="/homes/"]',
                    'a[href*="/p/"]',
                    '[class*="property"] a',
                    '.listing-item a',
                    '.property-card a'
                ]
                
                for selector in link_selectors:
                    links = soup.select(selector)
                    if links:
                        logger.info(f"    Found {len(links)} links using {selector}")
                        
                        for link in links:
                            href = link.get('href')
                            if href:
                                if href.startswith('/'):
                                    full_url = 'https://www.trulia.com' + href
                                elif href.startswith('http'):
                                    full_url = href
                                else:
                                    continue
                                
                                if full_url not in self.visited_urls:
                                    property_urls.append(full_url)
                                    self.visited_urls.add(full_url)
                        
                        if property_urls:
                            break
            
            # Also try to extract from JSON-LD data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    urls_from_json = self.extract_urls_from_json(data)
                    for json_url in urls_from_json:
                        if json_url not in self.visited_urls:
                            property_urls.append(json_url)
                            self.visited_urls.add(json_url)
                except:
                    continue
            
            # Debug: Show what types of links we found
            if not property_urls:
                logger.warning(f"    ❌ No property URLs found. Sample of all links:")
                sample_links = [link.get('href') for link in all_links[:10] if link.get('href')]
                for i, sample_url in enumerate(sample_links):
                    logger.info(f"      {i+1}. {sample_url}")
            
            logger.info(f"    ✅ Found {len(property_urls)} unique property URLs")
            return property_urls[:25]  # Limit to 25 per page for larger dataset
            
        except Exception as e:
            logger.error(f"  ❌ Error extracting URLs from {url}: {e}")
            return []
    
    def extract_urls_from_json(self, data):
        """Extract property URLs from JSON-LD data"""
        urls = []
        
        try:
            if isinstance(data, dict):
                # Check for URL in current object
                if data.get('url') and '/property/' in data['url']:
                    urls.append(data['url'])
                
                # Recursively check nested objects
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        urls.extend(self.extract_urls_from_json(value))
            
            elif isinstance(data, list):
                for item in data:
                    urls.extend(self.extract_urls_from_json(item))
        
        except:
            pass
        
        return urls
    
    def scrape_property_details(self, property_url):
        """Scrape detailed information from individual property page"""
        logger.info(f"    Scraping details: {property_url}")
        
        try:
            time.sleep(random.uniform(3, 7))  # Increased delay to avoid blocking
            self.rotate_user_agent()  # Change user agent for each request
            response = self.session.get(property_url, timeout=25)
            
            if response.status_code != 200:
                logger.warning(f"      ❌ HTTP {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            property_data = {
                'url': property_url,
                'source': 'Trulia',
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Extract property name/title
            title_selectors = [
                'h1[data-testid="property-title"]',
                'h1.property-title',
                'h1',
                '.property-header h1',
                '[data-testid="property-address"]'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    property_data['name'] = title_elem.get_text(strip=True)
                    break
            
            # Extract address
            address_selectors = [
                '[data-testid="property-address"]',
                '.property-address',
                '.address',
                'h1[data-testid="property-title"]'
            ]
            
            for selector in address_selectors:
                addr_elem = soup.select_one(selector)
                if addr_elem:
                    address_text = addr_elem.get_text(strip=True)
                    property_data['address'] = re.sub(r'\s+', ' ', address_text)
                    break
            
            # Extract price
            price_selectors = [
                '[data-testid="property-price"]',
                '.property-price',
                '.price',
                '.rent-price',
                '[class*="price"]'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Clean up price
                    price_match = re.search(r'\$[\d,]+', price_text)
                    if price_match:
                        property_data['price'] = price_match.group()
                        break
            
            # Extract beds, baths, sqft from property details
            detail_selectors = [
                '[data-testid="property-details"]',
                '.property-details',
                '.property-info',
                '.listing-details'
            ]
            
            details_text = ""
            for selector in detail_selectors:
                details_elem = soup.select_one(selector)
                if details_elem:
                    details_text = details_elem.get_text()
                    break
            
            # If no specific details section, use whole page
            if not details_text:
                details_text = soup.get_text()
            
            # Extract beds
            bed_patterns = [
                r'(\d+)\s*bed(?:room)?s?',
                r'(\d+)\s*br\b',
                r'(\d+)bd\b',
                r'Beds:\s*(\d+)',
                r'(\d+)\s*Bed'
            ]
            
            for pattern in bed_patterns:
                bed_match = re.search(pattern, details_text, re.IGNORECASE)
                if bed_match:
                    property_data['beds'] = bed_match.group(1)
                    break
            
            # Extract baths
            bath_patterns = [
                r'(\d+(?:\.\d+)?)\s*bath(?:room)?s?',
                r'(\d+(?:\.\d+)?)\s*ba\b',
                r'(\d+(?:\.\d+)?)ba\b',
                r'Baths:\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*Bath'
            ]
            
            for pattern in bath_patterns:
                bath_match = re.search(pattern, details_text, re.IGNORECASE)
                if bath_match:
                    property_data['baths'] = bath_match.group(1)
                    break
            
            # Extract square footage
            sqft_patterns = [
                r'([\d,]+)\s*sq\.?\s*ft',
                r'([\d,]+)\s*sqft',
                r'([\d,]+)\s*square\s*feet',
                r'Sq Ft:\s*([\d,]+)',
                r'Size:\s*([\d,]+)\s*sq'
            ]
            
            for pattern in sqft_patterns:
                sqft_match = re.search(pattern, details_text, re.IGNORECASE)
                if sqft_match:
                    property_data['sqft'] = sqft_match.group(1).replace(',', '')
                    break
            
            # Extract coordinates from JSON-LD or scripts
            coordinates = self.extract_coordinates_from_page(soup)
            if coordinates:
                property_data['latitude'] = coordinates['lat']
                property_data['longitude'] = coordinates['lng']
            
            # Create name if missing
            if not property_data.get('name') and property_data.get('address'):
                beds = property_data.get('beds', '')
                baths = property_data.get('baths', '')
                address = property_data['address']
                if beds and baths:
                    property_data['name'] = f"{beds}bd/{baths}ba - {address}"
                else:
                    property_data['name'] = address
            
            logger.info(f"      ✅ {property_data.get('name', 'Property')[:50]}...")
            return property_data
            
        except Exception as e:
            logger.error(f"      ❌ Error scraping {property_url}: {e}")
            return None
    
    def extract_coordinates_from_page(self, soup):
        """Extract coordinates from property page"""
        try:
            # Look in JSON-LD scripts
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    coords = self.find_coordinates_in_json(data)
                    if coords:
                        return coords
                except:
                    continue
            
            # Look in other script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and ('latitude' in script.string or 'lat' in script.string):
                    text = script.string
                    lat_match = re.search(r'"lat(?:itude)?":\s*([+-]?\d+\.?\d*)', text)
                    lng_match = re.search(r'"lng|longitude":\s*([+-]?\d+\.?\d*)', text)
                    
                    if lat_match and lng_match:
                        return {
                            'lat': float(lat_match.group(1)),
                            'lng': float(lng_match.group(1))
                        }
        except:
            pass
        
        return None
    
    def find_coordinates_in_json(self, data):
        """Recursively find coordinates in JSON data"""
        if isinstance(data, dict):
            # Check for geo data
            if 'geo' in data and isinstance(data['geo'], dict):
                geo = data['geo']
                if 'latitude' in geo and 'longitude' in geo:
                    return {'lat': geo['latitude'], 'lng': geo['longitude']}
            
            # Check for direct lat/lng
            if 'latitude' in data and 'longitude' in data:
                return {'lat': data['latitude'], 'lng': data['longitude']}
            
            if 'lat' in data and 'lng' in data:
                return {'lat': data['lat'], 'lng': data['lng']}
            
            # Recursively check nested objects
            for value in data.values():
                if isinstance(value, (dict, list)):
                    coords = self.find_coordinates_in_json(value)
                    if coords:
                        return coords
        
        elif isinstance(data, list):
            for item in data:
                coords = self.find_coordinates_in_json(item)
                if coords:
                    return coords
        
        return None
    
    def scrape_location(self, location, max_properties=10):
        """Scrape one location by getting property URLs then visiting each"""
        logger.info(f"Scraping {location['name']}")
        
        all_property_urls = []
        
        # Step 1: Get property URLs from listing pages
        for list_url in location['urls']:
            urls = self.extract_property_urls_from_page(list_url, location['name'])
            all_property_urls.extend(urls)
            
            if len(all_property_urls) >= max_properties:
                break
        
        # Step 2: Visit each property page to get details
        properties = []
        for property_url in all_property_urls[:max_properties]:
            property_data = self.scrape_property_details(property_url)
            
            if property_data:
                property_data['location_search'] = location['name']
                property_data['state'] = location.get('state', 'Unknown')
                properties.append(property_data)
                
                # Stop if we have enough
                if len(properties) >= max_properties:
                    break
        
        logger.info(f"  ✅ Scraped {len(properties)} properties from {location['name']}")
        return properties
    
    def scrape_all_locations(self, target_total=750):
        """Scrape all locations with 50-50 NJ/NY split"""
        all_properties = []
        nj_properties = []
        ny_properties = []
        
        # Calculate targets for 50-50 split
        nj_target = target_total // 2
        ny_target = target_total // 2
        
        logger.info(f"Starting enhanced Trulia scraper for Hoboken, NJ and Tri-State area")
        logger.info(f"Target: {target_total} total properties ({nj_target} NJ, {ny_target} NY)")
        logger.info(f"Will visit individual property pages for complete data\n")
        
        # Scrape NJ locations first (prioritizing Hoboken area)
        logger.info(f"🏠 Scraping New Jersey locations (target: {nj_target})")
        nj_per_location = max(1, nj_target // len(self.nj_locations))
        
        for location in self.nj_locations:
            if len(nj_properties) >= nj_target:
                break
            
            remaining_nj = nj_target - len(nj_properties)
            props_to_get = min(nj_per_location * 2, remaining_nj)  # Allow more per location if needed
            
            props = self.scrape_location(location, props_to_get)
            nj_properties.extend(props)
            
            logger.info(f"  NJ Progress: {len(nj_properties)}/{nj_target} properties")
            
            # Much longer delay between locations to avoid blocking
            time.sleep(random.uniform(20, 35))
        
        # Scrape NY locations
        logger.info(f"\n🗽 Scraping New York locations (target: {ny_target})")
        ny_per_location = max(1, ny_target // len(self.ny_locations))
        
        for location in self.ny_locations:
            if len(ny_properties) >= ny_target:
                break
            
            remaining_ny = ny_target - len(ny_properties)
            props_to_get = min(ny_per_location * 2, remaining_ny)  # Allow more per location if needed
            
            props = self.scrape_location(location, props_to_get)
            ny_properties.extend(props)
            
            logger.info(f"  NY Progress: {len(ny_properties)}/{ny_target} properties")
            
            # Much longer delay between locations to avoid blocking
            time.sleep(random.uniform(20, 35))
        
        # Combine results
        all_properties = nj_properties[:nj_target] + ny_properties[:ny_target]
        self.properties = all_properties
        
        # Log final statistics
        final_nj = len([p for p in self.properties if p.get('state') == 'NJ'])
        final_ny = len([p for p in self.properties if p.get('state') == 'NY'])
        
        logger.info(f"\n🎉 Scraping completed!")
        logger.info(f"📊 Total properties: {len(self.properties)}")
        logger.info(f"🏠 New Jersey: {final_nj} properties ({final_nj/len(self.properties)*100:.1f}%)")
        logger.info(f"🗽 New York: {final_ny} properties ({final_ny/len(self.properties)*100:.1f}%)")
        
        return self.properties
    
    def save_to_csv(self, filename='trulia_enhanced_properties.csv'):
        """Save properties to CSV with all details"""
        if not self.properties:
            logger.warning("No properties to save")
            return
        
        fieldnames = [
            'name', 'price', 'beds', 'baths', 'sqft', 'address', 
            'latitude', 'longitude', 'state', 'location_search', 'url', 
            'source', 'scraped_date'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for prop in self.properties:
                row = {field: prop.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Saved {len(self.properties)} properties to {filename}")

def main():
    scraper = TruliaEnhancedScraper()
    
    print("🏠 Enhanced Trulia Scraper - Hoboken & Tri-State Focus")
    print("📍 Hoboken, NJ and surrounding NYC Metro Area")
    print("🎯 Target: 500-1000 properties with 50-50 NJ/NY split")
    print("⚡ Gets prices, beds, baths, sqft, and coordinates\n")
    
    try:
        # Scrape properties with detailed information (500-1000 target)
        properties = scraper.scrape_all_locations(target_total=10)
        
        if properties:
            scraper.save_to_csv()
            
            # Show detailed summary
            with_addresses = len([p for p in properties if p.get('address')])
            with_prices = len([p for p in properties if p.get('price')])
            with_coordinates = len([p for p in properties if p.get('latitude')])
            with_beds = len([p for p in properties if p.get('beds')])
            with_baths = len([p for p in properties if p.get('baths')])
            with_sqft = len([p for p in properties if p.get('sqft')])
            with_urls = len([p for p in properties if p.get('url')])
            
            print(f"\n✅ Enhanced scraping completed!")
            print(f"📊 Total properties: {len(properties)}")
            print(f"🏠 With addresses: {with_addresses} ({with_addresses/len(properties)*100:.1f}%)")
            print(f"💰 With prices: {with_prices} ({with_prices/len(properties)*100:.1f}%)")
            print(f"🛏️ With bedroom info: {with_beds} ({with_beds/len(properties)*100:.1f}%)")
            print(f"🚿 With bathroom info: {with_baths} ({with_baths/len(properties)*100:.1f}%)")
            print(f"📐 With square footage: {with_sqft} ({with_sqft/len(properties)*100:.1f}%)")
            print(f"📍 With coordinates: {with_coordinates} ({with_coordinates/len(properties)*100:.1f}%)")
            print(f"🔗 With property URLs: {with_urls} ({with_urls/len(properties)*100:.1f}%)")
            print(f"📄 Saved to: trulia_enhanced_properties.csv")
            
            print(f"\n🎯 Data Quality Improvement:")
            print(f"   Previous: 0% prices, 0% beds/baths")
            print(f"   Current: {with_prices/len(properties)*100:.1f}% prices, {with_beds/len(properties)*100:.1f}% beds/baths")
            print(f"   This should dramatically improve your property analysis!")
            
        else:
            print("\n⚠️ No properties found.")
            print("This might indicate:")
            print("- Trulia has changed their URL structure")
            print("- Anti-bot measures have been enhanced")
            print("- Temporary site issues")
            
    except Exception as e:
        logger.error(f"Enhanced scraping failed: {e}")
        print(f"\n❌ Enhanced scraping failed: {e}")

if __name__ == "__main__":
    main()
