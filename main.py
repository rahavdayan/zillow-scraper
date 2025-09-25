#!/usr/bin/env python3
"""
Zillow Property Scraper for Tri-State Area
Scrapes residential properties from Zillow in NJ and NY areas
"""

import requests
import csv
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse
import json
import re
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZillowScraper:
    def __init__(self):
        self.session = requests.Session()
        # Enhanced headers to avoid 403 errors
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Referer': 'https://www.google.com/',
        }
        self.session.headers.update(self.headers)
        
        # Target locations for 50-50 NJ/NY split
        self.locations = {
            'nj': [
                'hoboken-nj',
                'jersey-city-nj', 
                'weehawken-nj',
                'union-city-nj',
                'north-bergen-nj',
                'secaucus-nj',
                'bayonne-nj'
            ],
            'ny': [
                'manhattan-new-york-ny',
                'brooklyn-new-york-ny',
                'queens-new-york-ny',
                'bronx-new-york-ny',
                'long-island-city-ny',
                'astoria-ny',
                'williamsburg-brooklyn-ny'
            ]
        }
        
        self.properties = []
        
    def build_search_url(self, location, page=1):
        """Build Zillow search URL for rentals and sales"""
        base_url = "https://www.zillow.com"
        # Search for both rentals and for-sale properties
        search_path = f"/{location}/rentals/"
        params = {
            'searchQueryState': json.dumps({
                'pagination': {'currentPage': page},
                'usersSearchTerm': location.replace('-', ' '),
                'mapBounds': {},
                'regionSelection': [{'regionId': None, 'regionType': 6}],
                'isMapVisible': True,
                'filterState': {
                    'isForSaleByAgent': {'value': False},
                    'isForSaleByOwner': {'value': False},
                    'isNewConstruction': {'value': False},
                    'isForSaleForeclosure': {'value': False},
                    'isComingSoon': {'value': False},
                    'isAuction': {'value': False},
                    'isPreMarketForeclosure': {'value': False},
                    'isPreMarketPreForeclosure': {'value': False},
                    'isMakeMeMove': {'value': False},
                    'isForRent': {'value': True}
                },
                'isListVisible': True
            })
        }
        
        return f"{base_url}{search_path}?{urlencode(params)}"
    
    def extract_property_data(self, property_element):
        """Extract property data from HTML element"""
        try:
            property_data = {}
            
            # Extract basic info
            address_elem = property_element.find('address')
            if address_elem:
                property_data['address'] = address_elem.get_text(strip=True)
            
            # Extract price
            price_elem = property_element.find('span', {'data-test': 'property-card-price'})
            if price_elem:
                property_data['price'] = price_elem.get_text(strip=True)
            
            # Extract beds/baths
            bed_bath_elem = property_element.find('ul', {'class': 'StyledPropertyCardHomeDetailsList'})
            if bed_bath_elem:
                details = bed_bath_elem.find_all('li')
                for detail in details:
                    text = detail.get_text(strip=True)
                    if 'bd' in text:
                        property_data['beds'] = text
                    elif 'ba' in text:
                        property_data['baths'] = text
                    elif 'sqft' in text:
                        property_data['sqft'] = text
            
            # Extract property link
            link_elem = property_element.find('a', {'data-test': 'property-card-link'})
            if link_elem:
                property_data['zillow_url'] = 'https://www.zillow.com' + link_elem.get('href', '')
            
            # Extract property type
            type_elem = property_element.find('span', {'data-test': 'property-card-type'})
            if type_elem:
                property_data['property_type'] = type_elem.get_text(strip=True)
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error extracting property data: {e}")
            return None
    
    def scrape_location(self, location, state, max_pages=5):
        """Scrape properties from a specific location"""
        logger.info(f"Scraping {location} ({state.upper()})")
        location_properties = []
        
        for page in range(1, max_pages + 1):
            try:
                url = self.build_search_url(location, page)
                logger.info(f"Fetching page {page} for {location}")
                
                # Add random delay before request
                time.sleep(random.uniform(5, 10))
                
                response = self.session.get(url, timeout=15)
                
                # Check for 403 or other errors
                if response.status_code == 403:
                    logger.warning(f"403 Forbidden for {url}. Zillow may be blocking requests.")
                    logger.info("Try using the Selenium scraper instead: python selenium_scraper.py")
                    time.sleep(30)  # Long delay before continuing
                    continue
                elif response.status_code != 200:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    continue
                
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find property cards
                property_cards = soup.find_all('article', {'data-test': 'property-card'})
                
                if not property_cards:
                    logger.warning(f"No property cards found on page {page} for {location}")
                    break
                
                for card in property_cards:
                    property_data = self.extract_property_data(card)
                    if property_data:
                        property_data['location'] = location
                        property_data['state'] = state.upper()
                        property_data['scraped_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        location_properties.append(property_data)
                
                # Random delay to avoid being blocked
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Error scraping page {page} for {location}: {e}")
                continue
        
        logger.info(f"Found {len(location_properties)} properties in {location}")
        return location_properties
    
    def scrape_all_locations(self, target_count=1000):
        """Scrape all target locations aiming for 50-50 NJ/NY split"""
        logger.info("Starting comprehensive scrape of tri-state area")
        
        nj_target = target_count // 2
        ny_target = target_count // 2
        
        # Scrape NJ locations
        nj_properties = []
        properties_per_nj_location = nj_target // len(self.locations['nj'])
        pages_per_location = max(1, properties_per_nj_location // 20)  # Assuming ~20 properties per page
        
        for location in self.locations['nj']:
            location_props = self.scrape_location(location, 'nj', pages_per_location)
            nj_properties.extend(location_props)
            if len(nj_properties) >= nj_target:
                break
        
        # Scrape NY locations
        ny_properties = []
        properties_per_ny_location = ny_target // len(self.locations['ny'])
        pages_per_location = max(1, properties_per_ny_location // 20)
        
        for location in self.locations['ny']:
            location_props = self.scrape_location(location, 'ny', pages_per_location)
            ny_properties.extend(location_props)
            if len(ny_properties) >= ny_target:
                break
        
        # Combine and limit to target count
        all_properties = nj_properties[:nj_target] + ny_properties[:ny_target]
        
        logger.info(f"Total properties scraped: {len(all_properties)}")
        logger.info(f"NJ properties: {len([p for p in all_properties if p['state'] == 'NJ'])}")
        logger.info(f"NY properties: {len([p for p in all_properties if p['state'] == 'NY'])}")
        
        self.properties = all_properties
        return all_properties
    
    def save_to_csv(self, filename='zillow_properties.csv'):
        """Save scraped properties to CSV file"""
        if not self.properties:
            logger.error("No properties to save")
            return
        
        # Define CSV columns
        fieldnames = [
            'address', 'price', 'beds', 'baths', 'sqft', 'property_type',
            'location', 'state', 'zillow_url', 'scraped_date'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for property_data in self.properties:
                # Ensure all fields exist
                row = {field: property_data.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Saved {len(self.properties)} properties to {filename}")

def main():
    """Main execution function"""
    scraper = ZillowScraper()
    
    try:
        # Scrape properties (targeting 500-1000 properties)
        properties = scraper.scrape_all_locations(target_count=800)
        
        # Save to CSV
        scraper.save_to_csv('tri_state_properties.csv')
        
        print(f"\nScraping completed successfully!")
        print(f"Total properties collected: {len(properties)}")
        print(f"Data saved to: tri_state_properties.csv")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        if scraper.properties:
            scraper.save_to_csv('partial_tri_state_properties.csv')
            print(f"Partial data saved to: partial_tri_state_properties.csv")
    
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        if scraper.properties:
            scraper.save_to_csv('error_tri_state_properties.csv')

if __name__ == "__main__":
    main()
