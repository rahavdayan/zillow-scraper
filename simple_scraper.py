#!/usr/bin/env python3
"""
Simple Property Scraper - Alternative approach
Uses different real estate sites that are less restrictive than Zillow
"""

import requests
import csv
import time
import random
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplePropertyScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
        
        # Target locations
        self.locations = {
            'nj': [
                'Hoboken, NJ',
                'Jersey City, NJ',
                'Weehawken, NJ',
                'Union City, NJ'
            ],
            'ny': [
                'Manhattan, NY',
                'Brooklyn, NY',
                'Queens, NY',
                'Long Island City, NY'
            ]
        }
        
        self.properties = []
    
    def scrape_apartments_com(self, location, max_results=50):
        """Scrape Apartments.com (usually less restrictive than Zillow)"""
        logger.info(f"Scraping Apartments.com for {location}")
        
        # Format location for Apartments.com URL
        location_formatted = location.replace(' ', '-').replace(',', '').lower()
        
        base_url = f"https://www.apartments.com/{location_formatted}/"
        
        try:
            # Increase timeout and add retry logic
            response = self.session.get(base_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for property listings (Apartments.com structure)
                properties = soup.find_all('article', class_='placard')
                
                location_properties = []
                
                for prop in properties[:max_results]:
                    try:
                        property_data = {}
                        
                        # Extract title/name
                        title_elem = prop.find('a', class_='property-link')
                        if title_elem:
                            property_data['name'] = title_elem.get_text(strip=True)
                            property_data['url'] = 'https://www.apartments.com' + title_elem.get('href', '')
                        
                        # Extract address
                        address_elem = prop.find('div', class_='property-address')
                        if address_elem:
                            property_data['address'] = address_elem.get_text(strip=True)
                        
                        # Extract price
                        price_elem = prop.find('span', class_='rent-range')
                        if price_elem:
                            property_data['price'] = price_elem.get_text(strip=True)
                        
                        # Extract beds/baths
                        beds_elem = prop.find('span', class_='bed-range')
                        if beds_elem:
                            property_data['beds'] = beds_elem.get_text(strip=True)
                        
                        property_data['location'] = location
                        property_data['source'] = 'Apartments.com'
                        property_data['scraped_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        if property_data.get('name') or property_data.get('address'):
                            location_properties.append(property_data)
                    
                    except Exception as e:
                        logger.debug(f"Error extracting property: {e}")
                        continue
                
                logger.info(f"Found {len(location_properties)} properties on Apartments.com for {location}")
                return location_properties
            
            else:
                logger.warning(f"HTTP {response.status_code} for Apartments.com {location}")
                return []
        
        except Exception as e:
            logger.error(f"Error scraping Apartments.com for {location}: {e}")
            return []
    
    def scrape_rent_com(self, location, max_results=50):
        """Scrape Rent.com as alternative"""
        logger.info(f"Scraping Rent.com for {location}")
        
        # Format location for Rent.com search
        location_encoded = quote_plus(location)
        search_url = f"https://www.rent.com/search?location={location_encoded}"
        
        try:
            time.sleep(random.uniform(2, 4))  # Be respectful
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for property cards (Rent.com structure may vary)
                properties = soup.find_all('div', class_='property-card') or soup.find_all('article')
                
                location_properties = []
                
                for prop in properties[:max_results]:
                    try:
                        property_data = {}
                        
                        # Try to extract basic info (structure may vary)
                        title = prop.find('h2') or prop.find('h3') or prop.find('a')
                        if title:
                            property_data['name'] = title.get_text(strip=True)
                        
                        # Look for price
                        price_selectors = ['.price', '.rent', '[class*="price"]', '[class*="rent"]']
                        for selector in price_selectors:
                            price_elem = prop.select_one(selector)
                            if price_elem:
                                property_data['price'] = price_elem.get_text(strip=True)
                                break
                        
                        property_data['location'] = location
                        property_data['source'] = 'Rent.com'
                        property_data['scraped_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        if property_data.get('name'):
                            location_properties.append(property_data)
                    
                    except Exception as e:
                        logger.debug(f"Error extracting property: {e}")
                        continue
                
                logger.info(f"Found {len(location_properties)} properties on Rent.com for {location}")
                return location_properties
            
            else:
                logger.warning(f"HTTP {response.status_code} for Rent.com {location}")
                return []
        
        except Exception as e:
            logger.error(f"Error scraping Rent.com for {location}: {e}")
            return []
    
    def scrape_craigslist(self, location, max_results=50):
        """Scrape Craigslist housing section (usually very permissive)"""
        logger.info(f"Scraping Craigslist for {location}")
        
        # Map locations to Craigslist subdomains
        craigslist_mapping = {
            'Hoboken, NJ': 'newyork',
            'Jersey City, NJ': 'newyork', 
            'Weehawken, NJ': 'newyork',
            'Union City, NJ': 'newyork',
            'Manhattan, NY': 'newyork',
            'Brooklyn, NY': 'newyork',
            'Queens, NY': 'newyork',
            'Long Island City, NY': 'newyork'
        }
        
        subdomain = craigslist_mapping.get(location, 'newyork')
        search_term = location.split(',')[0].lower().replace(' ', '+')
        
        url = f"https://{subdomain}.craigslist.org/search/apa?query={search_term}&sort=date"
        
        try:
            time.sleep(random.uniform(3, 6))  # Be extra respectful to Craigslist
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple Craigslist selectors (structure changes frequently)
                listings = (soup.find_all('li', class_='cl-search-result') or 
                           soup.find_all('li', class_='result-row') or
                           soup.find_all('div', class_='result-info'))
                
                location_properties = []
                
                for listing in listings[:max_results]:
                    try:
                        property_data = {}
                        
                        # Extract title
                        title_elem = listing.find('a', class_='cl-app-anchor')
                        if title_elem:
                            property_data['name'] = title_elem.get_text(strip=True)
                            property_data['url'] = title_elem.get('href', '')
                        
                        # Extract price
                        price_elem = listing.find('span', class_='priceinfo')
                        if price_elem:
                            property_data['price'] = price_elem.get_text(strip=True)
                        
                        # Extract location info
                        location_elem = listing.find('div', class_='location')
                        if location_elem:
                            property_data['neighborhood'] = location_elem.get_text(strip=True)
                        
                        property_data['location'] = location
                        property_data['source'] = 'Craigslist'
                        property_data['scraped_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        if property_data.get('name'):
                            location_properties.append(property_data)
                    
                    except Exception as e:
                        logger.debug(f"Error extracting Craigslist listing: {e}")
                        continue
                
                logger.info(f"Found {len(location_properties)} properties on Craigslist for {location}")
                return location_properties
            
            else:
                logger.warning(f"HTTP {response.status_code} for Craigslist {location}")
                return []
        
        except Exception as e:
            logger.error(f"Error scraping Craigslist for {location}: {e}")
            return []
    
    def scrape_all_sources(self, target_count=500):
        """Scrape from multiple sources to reach target count"""
        logger.info("Starting multi-source property scraping")
        
        all_properties = []
        
        # Calculate properties per location
        total_locations = len(self.locations['nj']) + len(self.locations['ny'])
        properties_per_location = max(10, target_count // total_locations)
        
        # Scrape NJ locations
        for location in self.locations['nj']:
            logger.info(f"Processing {location}")
            
            # Try multiple sources for each location
            sources = [
                self.scrape_apartments_com,
                self.scrape_craigslist,
                self.scrape_rent_com
            ]
            
            location_total = []
            
            for source_func in sources:
                try:
                    props = source_func(location, properties_per_location // 3)
                    location_total.extend(props)
                    
                    # Add delay between sources
                    time.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    logger.error(f"Error with source {source_func.__name__} for {location}: {e}")
                    continue
            
            all_properties.extend(location_total)
            logger.info(f"Total for {location}: {len(location_total)} properties")
            
            # Longer delay between locations
            time.sleep(random.uniform(5, 10))
        
        # Scrape NY locations
        for location in self.locations['ny']:
            logger.info(f"Processing {location}")
            
            sources = [
                self.scrape_apartments_com,
                self.scrape_craigslist,
                self.scrape_rent_com
            ]
            
            location_total = []
            
            for source_func in sources:
                try:
                    props = source_func(location, properties_per_location // 3)
                    location_total.extend(props)
                    
                    time.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    logger.error(f"Error with source {source_func.__name__} for {location}: {e}")
                    continue
            
            all_properties.extend(location_total)
            logger.info(f"Total for {location}: {len(location_total)} properties")
            
            time.sleep(random.uniform(5, 10))
        
        self.properties = all_properties
        logger.info(f"Total properties collected: {len(all_properties)}")
        
        return all_properties
    
    def save_to_csv(self, filename='multi_source_properties.csv'):
        """Save properties to CSV"""
        if not self.properties:
            logger.error("No properties to save")
            return
        
        # Define fieldnames based on available data
        fieldnames = set()
        for prop in self.properties:
            fieldnames.update(prop.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for prop in self.properties:
                row = {field: prop.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Saved {len(self.properties)} properties to {filename}")

def main():
    scraper = SimplePropertyScraper()
    
    try:
        properties = scraper.scrape_all_sources(target_count=200)  # Start smaller
        scraper.save_to_csv('alternative_properties.csv')
        
        print(f"\nScraping completed!")
        print(f"Total properties: {len(properties)}")
        print(f"Sources used: Apartments.com, Craigslist, Rent.com")
        print(f"Data saved to: alternative_properties.csv")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted")
        if scraper.properties:
            scraper.save_to_csv('partial_alternative_properties.csv')

if __name__ == "__main__":
    main()
