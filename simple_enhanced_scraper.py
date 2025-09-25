#!/usr/bin/env python3
"""
Simplified Enhanced Craigslist Scraper
- Single address field
- Keep titles intact
"""

import requests
import csv
import time
import random
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedCraigslistScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(self.headers)
        
        self.locations = [
            'hoboken', 'jersey+city', 'manhattan', 'brooklyn', 
            'queens', 'bronx', 'astoria', 'williamsburg'
        ]
        
        self.properties = []
        
        # Simplified address patterns
        self.address_patterns = [
            r'([A-Za-z0-9\s\-]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Pl|Place|Way|Court|Ct)(?:\s*,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5})?)',
            r'(\d+(?:-\d+)?\s+[A-Za-z0-9\s]+(?:st|nd|rd|th)?\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Pl|Place|Way|Court|Ct))',
            r'([NSEW]?\s*\d+(?:st|nd|rd|th)?\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Pl|Place|Way|Court|Ct))',
            r'(\d+(?:st|nd|rd|th)?\s+and\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Pl|Place|Way|Court|Ct))',
            r'\(([A-Za-z\s]+)\)',
            r'([A-Za-z\s]+,\s*[A-Z\s]+,\s*[A-Z]{2}(?:\s*\d{5})?)',
        ]
    
    def extract_address(self, text):
        """Extract single best address"""
        text = re.sub(r'\s+', ' ', text.strip())
        
        best_address = None
        best_score = 0
        
        for pattern in self.address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                if len(match) > 3:
                    score = 0
                    if re.search(r'\d{5}', match): score += 10
                    if re.search(r'\d+', match): score += 5
                    if re.search(r'(?:St|Street|Ave|Avenue)', match, re.IGNORECASE): score += 3
                    
                    if score > best_score:
                        best_score = score
                        best_address = match
        
        return best_address
    
    def get_address_from_listing_page(self, listing_url):
        """Fetch address from individual listing page"""
        try:
            time.sleep(random.uniform(2, 4))  # Be respectful
            response = self.session.get(listing_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for the street-address element
                address_elem = soup.select_one('.street-address')
                if address_elem:
                    return address_elem.get_text(strip=True)
                
                # Fallback: look for other address patterns
                address_selectors = [
                    '.mapaddress',
                    '.postinginfos .attrgroup',
                    '[class*="address"]'
                ]
                
                for selector in address_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        if text and len(text) > 5:
                            return text
                
        except Exception as e:
            logger.debug(f"Could not fetch address from {listing_url}: {e}")
        
        return None
    
    def scrape_location(self, location, max_per_location=50):
        """Scrape one location with simplified extraction"""
        logger.info(f"Scraping {location}")
        
        url = f"https://newyork.craigslist.org/search/apa?query={location}&sort=date"
        
        try:
            time.sleep(random.uniform(4, 7))
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                listings = soup.select('li[class*="result"]')
                
                logger.info(f"Found {len(listings)} listings for {location}")
                
                location_properties = []
                
                for i, listing in enumerate(listings[:max_per_location]):
                    try:
                        property_data = {}
                        
                        # Get URL first
                        title_elem = listing.select_one('a')
                        if title_elem:
                            listing_url = title_elem.get('href', '')
                            if listing_url and not listing_url.startswith('http'):
                                listing_url = 'https://newyork.craigslist.org' + listing_url
                            property_data['url'] = listing_url
                        
                        # Extract name from specific element: #titletextonly
                        name_elem = listing.select_one('#titletextonly')
                        if name_elem:
                            property_data['name'] = name_elem.get_text(strip=True)
                        elif title_elem:
                            # Fallback to link text if #titletextonly not found
                            property_data['name'] = title_elem.get_text(strip=True)
                        
                        # Extract address from specific element: .street-address
                        # This element is on the individual listing page, not search results
                        address_elem = listing.select_one('.street-address')
                        if address_elem:
                            property_data['address'] = address_elem.get_text(strip=True)
                        else:
                            # Need to fetch individual listing page for address
                            if property_data.get('url') and i < 5:  # Only fetch first 5 to avoid being blocked
                                address = self.get_address_from_listing_page(property_data['url'])
                                if address:
                                    property_data['address'] = address
                        
                        # Extract price from specific element: .price
                        price_elem = listing.select_one('.price')
                        if price_elem:
                            property_data['price'] = price_elem.get_text(strip=True)
                        else:
                            # Fallback to regex if .price element not found
                            text = listing.get_text()
                            price_match = re.search(r'\$[\d,]+', text)
                            if price_match:
                                property_data['price'] = price_match.group()
                        
                        # Extract bedrooms from .housing element or fallback to regex
                        housing_elem = listing.select_one('.housing')
                        if housing_elem:
                            housing_text = housing_elem.get_text()
                            bed_match = re.search(r'(\d+)br', housing_text.lower())
                            if bed_match:
                                property_data['beds'] = bed_match.group(1)
                        else:
                            # Fallback to regex
                            text = listing.get_text()
                            bed_match = re.search(r'(\d+)\s*br|\d+\s*bed', text.lower())
                            if bed_match:
                                property_data['beds'] = bed_match.group()
                        
                        # Basic info
                        property_data['location_search'] = location.replace('+', ' ')
                        property_data['source'] = 'Craigslist'
                        property_data['scraped_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        if property_data.get('name') and len(property_data['name']) > 10:
                            location_properties.append(property_data)
                            
                            if property_data.get('address'):
                                logger.info(f"  ✅ Address: {property_data['address']}")
                    
                    except Exception as e:
                        continue
                
                return location_properties
            
        except Exception as e:
            logger.error(f"Error scraping {location}: {e}")
            return []
    
    def scrape_all(self, target_total=100):
        """Scrape all locations"""
        all_properties = []
        per_location = target_total // len(self.locations)
        
        for location in self.locations:
            props = self.scrape_location(location, per_location)
            all_properties.extend(props)
            
            if len(all_properties) >= target_total:
                break
        
        self.properties = all_properties[:target_total]
        return self.properties
    
    def save_to_csv(self, filename='simplified_properties.csv'):
        """Save with simplified fields"""
        fieldnames = ['name', 'price', 'beds', 'address', 'location_search', 'url', 'source', 'scraped_date']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for prop in self.properties:
                row = {field: prop.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Saved {len(self.properties)} properties to {filename}")

def main():
    scraper = SimplifiedCraigslistScraper()
    
    print("🏠 Simplified Craigslist Scraper")
    print("📍 Single address field, intact titles")
    
    properties = scraper.scrape_all(target_total=10)
    scraper.save_to_csv()
    
    with_addresses = len([p for p in properties if p.get('address')])
    print(f"\n✅ Completed! {len(properties)} properties, {with_addresses} with addresses")

if __name__ == "__main__":
    main()
