#!/usr/bin/env python3
"""
Enhanced Zillow Property Scraper using Selenium
Handles dynamic content and JavaScript-rendered pages
"""

import csv
import time
import random
import json
import logging
from datetime import datetime
from typing import List, Dict
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZillowSeleniumScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.properties = []
        
        # Target locations for 50-50 NJ/NY split
        self.locations = {
            'nj': [
                {'name': 'Hoboken, NJ', 'url_part': 'hoboken-nj'},
                {'name': 'Jersey City, NJ', 'url_part': 'jersey-city-nj'},
                {'name': 'Weehawken, NJ', 'url_part': 'weehawken-nj'},
                {'name': 'Union City, NJ', 'url_part': 'union-city-nj'},
                {'name': 'North Bergen, NJ', 'url_part': 'north-bergen-nj'},
                {'name': 'Secaucus, NJ', 'url_part': 'secaucus-nj'},
                {'name': 'Bayonne, NJ', 'url_part': 'bayonne-nj'}
            ],
            'ny': [
                {'name': 'Manhattan, NY', 'url_part': 'manhattan-new-york-ny'},
                {'name': 'Brooklyn, NY', 'url_part': 'brooklyn-new-york-ny'},
                {'name': 'Queens, NY', 'url_part': 'queens-new-york-ny'},
                {'name': 'Bronx, NY', 'url_part': 'bronx-new-york-ny'},
                {'name': 'Long Island City, NY', 'url_part': 'long-island-city-ny'},
                {'name': 'Astoria, NY', 'url_part': 'astoria-ny'},
                {'name': 'Williamsburg, Brooklyn, NY', 'url_part': 'williamsburg-brooklyn-ny'}
            ]
        }
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with enhanced anti-detection options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")  # Use new headless mode
        
        # Enhanced anti-detection arguments
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        chrome_options.add_argument("--disable-javascript")  # May help avoid detection
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Additional stealth options
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("detach", True)
        
        # Disable automation indicators
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "media_stream": 2,
            },
            "profile.managed_default_content_settings": {
                "images": 2
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute scripts to remove automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            # Set realistic viewport
            self.driver.set_window_size(1366, 768)
            
            logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def build_search_url(self, location_data, page=1, property_type='rentals'):
        """Build Zillow search URL"""
        base_url = "https://www.zillow.com"
        location_part = location_data['url_part']
        
        if property_type == 'rentals':
            return f"{base_url}/{location_part}/rentals/{page}_p/"
        else:
            return f"{base_url}/{location_part}/{page}_p/"
    
    def wait_and_find_elements(self, by, value, timeout=10, multiple=True):
        """Wait for elements to load and return them"""
        try:
            if multiple:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                return self.driver.find_elements(by, value)
            else:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for elements: {value}")
            return [] if multiple else None
    
    def extract_property_data(self, property_element) -> Dict:
        """Extract property data from a property card element"""
        try:
            property_data = {}
            
            # Extract address
            try:
                address_elem = property_element.find_element(By.CSS_SELECTOR, "[data-test='property-card-addr']")
                property_data['address'] = address_elem.text.strip()
            except NoSuchElementException:
                try:
                    address_elem = property_element.find_element(By.TAG_NAME, "address")
                    property_data['address'] = address_elem.text.strip()
                except NoSuchElementException:
                    property_data['address'] = "Address not found"
            
            # Extract price
            try:
                price_elem = property_element.find_element(By.CSS_SELECTOR, "[data-test='property-card-price']")
                property_data['price'] = price_elem.text.strip()
            except NoSuchElementException:
                property_data['price'] = "Price not available"
            
            # Extract beds, baths, sqft
            try:
                details_elem = property_element.find_element(By.CSS_SELECTOR, "[data-test='property-card-details']")
                details_text = details_elem.text.strip()
                
                # Parse details like "2 bds | 1 ba | 800 sqft"
                if 'bd' in details_text:
                    beds_match = re.search(r'(\d+)\s*bd', details_text)
                    property_data['beds'] = beds_match.group(1) if beds_match else "N/A"
                
                if 'ba' in details_text:
                    baths_match = re.search(r'(\d+(?:\.\d+)?)\s*ba', details_text)
                    property_data['baths'] = baths_match.group(1) if baths_match else "N/A"
                
                if 'sqft' in details_text:
                    sqft_match = re.search(r'([\d,]+)\s*sqft', details_text)
                    property_data['sqft'] = sqft_match.group(1) if sqft_match else "N/A"
                    
            except NoSuchElementException:
                property_data['beds'] = "N/A"
                property_data['baths'] = "N/A"
                property_data['sqft'] = "N/A"
            
            # Extract property link
            try:
                link_elem = property_element.find_element(By.CSS_SELECTOR, "a[data-test='property-card-link']")
                href = link_elem.get_attribute('href')
                property_data['zillow_url'] = href if href else "URL not found"
            except NoSuchElementException:
                property_data['zillow_url'] = "URL not found"
            
            # Extract property type
            try:
                type_elem = property_element.find_element(By.CSS_SELECTOR, "[data-test='property-card-type']")
                property_data['property_type'] = type_elem.text.strip()
            except NoSuchElementException:
                property_data['property_type'] = "Type not specified"
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error extracting property data: {e}")
            return None
    
    def scrape_location(self, location_data, state, max_pages=5, property_type='rentals'):
        """Scrape properties from a specific location"""
        location_name = location_data['name']
        logger.info(f"Scraping {location_name} ({state.upper()}) - {property_type}")
        
        location_properties = []
        
        for page in range(1, max_pages + 1):
            try:
                url = self.build_search_url(location_data, page, property_type)
                logger.info(f"Fetching page {page} for {location_name}: {url}")
                
                self.driver.get(url)
                
                # Wait for page to load
                time.sleep(random.uniform(3, 6))
                
                # Look for property cards with various selectors
                property_selectors = [
                    "[data-test='property-card']",
                    "article[data-test='property-card']",
                    ".ListItem-c11n-8-84-3__sc-10e22w8-0",
                    ".property-card"
                ]
                
                property_cards = []
                for selector in property_selectors:
                    property_cards = self.wait_and_find_elements(By.CSS_SELECTOR, selector, timeout=10)
                    if property_cards:
                        logger.info(f"Found {len(property_cards)} property cards with selector: {selector}")
                        break
                
                if not property_cards:
                    logger.warning(f"No property cards found on page {page} for {location_name}")
                    # Try scrolling to load more content
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    # Try again after scrolling
                    for selector in property_selectors:
                        property_cards = self.wait_and_find_elements(By.CSS_SELECTOR, selector, timeout=5)
                        if property_cards:
                            break
                
                if not property_cards:
                    logger.warning(f"Still no property cards found after scrolling. Moving to next page.")
                    continue
                
                # Extract data from each property card
                for i, card in enumerate(property_cards):
                    try:
                        property_data = self.extract_property_data(card)
                        if property_data and property_data.get('address') != "Address not found":
                            property_data['location'] = location_name
                            property_data['state'] = state.upper()
                            property_data['property_category'] = property_type
                            property_data['scraped_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            location_properties.append(property_data)
                            logger.debug(f"Extracted property {i+1}: {property_data.get('address', 'Unknown')}")
                    except Exception as e:
                        logger.error(f"Error processing property card {i+1}: {e}")
                        continue
                
                logger.info(f"Page {page} completed. Found {len([p for p in location_properties if p.get('scraped_date') == datetime.now().strftime('%Y-%m-%d %H:%M:%S')])} properties")
                
                # Random delay between pages
                time.sleep(random.uniform(4, 8))
                
            except Exception as e:
                logger.error(f"Error scraping page {page} for {location_name}: {e}")
                continue
        
        logger.info(f"Completed scraping {location_name}. Total properties: {len(location_properties)}")
        return location_properties
    
    def scrape_all_locations(self, target_count=800):
        """Scrape all target locations with 50-50 NJ/NY split"""
        if not self.setup_driver():
            logger.error("Failed to setup WebDriver")
            return []
        
        try:
            logger.info("Starting comprehensive scrape of tri-state area")
            
            nj_target = target_count // 2
            ny_target = target_count // 2
            
            all_properties = []
            
            # Scrape NJ locations
            nj_properties = []
            properties_per_location = max(1, nj_target // len(self.locations['nj']))
            pages_per_location = max(2, properties_per_location // 15)  # Assuming ~15 properties per page
            
            for location_data in self.locations['nj']:
                if len(nj_properties) >= nj_target:
                    break
                    
                # Scrape both rentals and sales
                for prop_type in ['rentals']:  # Focus on rentals as requested
                    location_props = self.scrape_location(location_data, 'nj', pages_per_location, prop_type)
                    nj_properties.extend(location_props)
                    
                    if len(nj_properties) >= nj_target:
                        break
            
            # Scrape NY locations
            ny_properties = []
            properties_per_location = max(1, ny_target // len(self.locations['ny']))
            pages_per_location = max(2, properties_per_location // 15)
            
            for location_data in self.locations['ny']:
                if len(ny_properties) >= ny_target:
                    break
                    
                # Scrape both rentals and sales
                for prop_type in ['rentals']:  # Focus on rentals as requested
                    location_props = self.scrape_location(location_data, 'ny', pages_per_location, prop_type)
                    ny_properties.extend(location_props)
                    
                    if len(ny_properties) >= ny_target:
                        break
            
            # Combine and limit to target count
            all_properties = nj_properties[:nj_target] + ny_properties[:ny_target]
            
            logger.info(f"Scraping completed!")
            logger.info(f"Total properties scraped: {len(all_properties)}")
            logger.info(f"NJ properties: {len([p for p in all_properties if p['state'] == 'NJ'])}")
            logger.info(f"NY properties: {len([p for p in all_properties if p['state'] == 'NY'])}")
            
            self.properties = all_properties
            return all_properties
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return self.properties
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
    
    def save_to_csv(self, filename='zillow_properties_selenium.csv'):
        """Save scraped properties to CSV file"""
        if not self.properties:
            logger.error("No properties to save")
            return
        
        # Define CSV columns
        fieldnames = [
            'address', 'price', 'beds', 'baths', 'sqft', 'property_type',
            'property_category', 'location', 'state', 'zillow_url', 'scraped_date'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for property_data in self.properties:
                    # Ensure all fields exist
                    row = {field: property_data.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            logger.info(f"Saved {len(self.properties)} properties to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Zillow properties using Selenium')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--target-count', type=int, default=800, help='Target number of properties to scrape')
    parser.add_argument('--output', default='tri_state_properties_selenium.csv', help='Output CSV filename')
    
    args = parser.parse_args()
    
    scraper = ZillowSeleniumScraper(headless=args.headless)
    
    try:
        # Scrape properties
        properties = scraper.scrape_all_locations(target_count=args.target_count)
        
        # Save to CSV
        scraper.save_to_csv(args.output)
        
        print(f"\nScraping completed successfully!")
        print(f"Total properties collected: {len(properties)}")
        print(f"Data saved to: {args.output}")
        
        # Print sample data
        if properties:
            print(f"\nSample property:")
            sample = properties[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        if scraper.properties:
            scraper.save_to_csv('partial_' + args.output)
            print(f"Partial data saved to: partial_{args.output}")
    
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        if scraper.properties:
            scraper.save_to_csv('error_' + args.output)

if __name__ == "__main__":
    main()
