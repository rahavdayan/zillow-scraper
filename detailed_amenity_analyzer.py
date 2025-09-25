#!/usr/bin/env python3
"""
Detailed Amenity Analyzer for Property Data
Analyzes comprehensive amenity information using OpenStreetMap data (free)
Outputs detailed CSV with all amenity categories and metrics
"""

import csv
import requests
import time
import logging
from datetime import datetime
from geopy.geocoders import Nominatim
import math

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DetailedAmenityAnalyzer:
    def __init__(self):
        """Initialize the detailed amenity analyzer"""
        self.properties = []
        self.geocoder = Nominatim(user_agent="detailed_property_amenity_analyzer")
        self.overpass_url = "http://overpass-api.de/api/interpreter"
        
        # Detailed amenity categories
        self.amenity_types = {
            'elementary_school': ['school', 'kindergarten'],
            'middle_school': ['school'],
            'high_school': ['school'],
            'university': ['university', 'college'],
            'subway_station': ['subway_entrance', 'railway_station'],
            'bus_stop': ['bus_station', 'bus_stop'],
            'train_station': ['railway_station'],
            'gym': ['gym', 'fitness_centre'],
            'fitness_center': ['fitness_centre', 'sports_centre'],
            'hospital': ['hospital'],
            'clinic': ['clinic', 'doctors'],
            'pharmacy': ['pharmacy'],
            'park': ['park'],
            'playground': ['playground'],
            'sports_facility': ['sports_centre', 'stadium'],
            'museum': ['museum'],
            'theater': ['theatre', 'cinema'],
            'library': ['library'],
            'supermarket': ['supermarket'],
            'convenience_store': ['convenience'],
            'shopping_mall': ['mall'],
            'bank': ['bank'],
            'atm': ['atm'],
            'post_office': ['post_office'],
            'restaurant': ['restaurant'],
            'fast_food': ['fast_food'],
            'cafe': ['cafe'],
            'bar': ['bar', 'pub'],
            'police_station': ['police'],
            'fire_station': ['fire_station']
        }
    
    def load_properties(self, csv_file):
        """Load properties from CSV"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.properties = list(reader)
            
            logger.info(f"Loaded {len(self.properties)} properties from {csv_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading properties: {e}")
            return False
    
    def geocode_address(self, address, location_search):
        """Geocode address to coordinates"""
        if not address or address.strip() == '':
            address = location_search + ', NY'
        
        try:
            time.sleep(1)  # Respect rate limits
            location = self.geocoder.geocode(address, timeout=10)
            if location:
                return location.latitude, location.longitude
            
            # Fallback
            if address != location_search:
                location = self.geocoder.geocode(location_search + ', NY', timeout=10)
                if location:
                    return location.latitude, location.longitude
            
        except Exception as e:
            logger.debug(f"Geocoding failed for {address}: {e}")
        
        return None, None
    
    def get_amenity_details(self, lat, lon, amenity_type, osm_tags, radius=1000):
        """Get detailed amenity information including count and closest distance"""
        # Build query for specific amenity type
        tag_conditions = '|'.join(osm_tags)
        query = f"""
        [out:json][timeout:20];
        (
          node["amenity"~"{tag_conditions}"](around:{radius},{lat},{lon});
          way["amenity"~"{tag_conditions}"](around:{radius},{lat},{lon});
        );
        out geom;
        """
        
        try:
            time.sleep(0.5)  # Be respectful
            response = requests.post(self.overpass_url, data=query, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                
                if not elements:
                    return 0, None
                
                # Calculate distances to all amenities
                distances = []
                for element in elements:
                    if 'lat' in element and 'lon' in element:
                        # Calculate distance using Haversine formula
                        distance = self.calculate_distance(lat, lon, element['lat'], element['lon'])
                        distances.append(distance)
                
                count = len(distances)
                closest_distance = min(distances) if distances else None
                
                return count, closest_distance
            
        except Exception as e:
            logger.debug(f"Query failed for {amenity_type}: {e}")
        
        return 0, None
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula (returns meters)"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def analyze_properties(self, max_properties=20):
        """Analyze detailed amenities for properties"""
        if not self.properties:
            logger.error("No properties loaded")
            return []
        
        logger.info(f"Analyzing detailed amenities for up to {max_properties} properties")
        
        enhanced_properties = []
        successful_geocodes = 0
        
        for i, prop in enumerate(self.properties[:max_properties], 1):
            logger.info(f"Processing {i}/{min(len(self.properties), max_properties)}: {prop.get('name', 'Unknown')[:50]}...")
            
            # Get coordinates
            address = prop.get('address', '')
            location_search = prop.get('location_search', '')
            
            lat, lon = self.geocode_address(address, location_search)
            
            enhanced_prop = prop.copy()
            enhanced_prop['analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            enhanced_prop['analysis_radius'] = 1000
            
            if lat and lon:
                successful_geocodes += 1
                enhanced_prop['latitude'] = round(lat, 6)
                enhanced_prop['longitude'] = round(lon, 6)
                
                # Analyze each amenity type
                total_amenities = 0
                
                for amenity_type, osm_tags in self.amenity_types.items():
                    count, closest_distance = self.get_amenity_details(lat, lon, amenity_type, osm_tags)
                    
                    enhanced_prop[f'{amenity_type}_count'] = count
                    enhanced_prop[f'{amenity_type}_closest_distance'] = round(closest_distance, 0) if closest_distance else None
                    total_amenities += count
                    
                    logger.debug(f"  {amenity_type}: {count} found")
                
                enhanced_prop['total_amenities_count'] = total_amenities
                
                logger.info(f"  ✅ Geocoded! Total amenities: {total_amenities}")
            else:
                # Add empty amenity data
                enhanced_prop['latitude'] = ''
                enhanced_prop['longitude'] = ''
                for amenity_type in self.amenity_types.keys():
                    enhanced_prop[f'{amenity_type}_count'] = 0
                    enhanced_prop[f'{amenity_type}_closest_distance'] = None
                
                enhanced_prop['total_amenities_count'] = 0
                logger.warning(f"  ❌ Could not geocode")
            
            enhanced_properties.append(enhanced_prop)
        
        logger.info(f"Successfully geocoded {successful_geocodes}/{len(enhanced_properties)} properties")
        return enhanced_properties
    
    def save_detailed_data(self, enhanced_properties, output_file):
        """Save detailed amenity data to CSV"""
        if not enhanced_properties:
            logger.error("No enhanced properties to save")
            return
        
        # Define comprehensive fieldnames
        base_fields = ['name', 'price', 'beds', 'address', 'location_search', 'url', 'source', 'scraped_date']
        location_fields = ['latitude', 'longitude', 'analysis_date', 'analysis_radius']
        
        # Amenity count and distance fields
        amenity_fields = []
        for amenity_type in self.amenity_types.keys():
            amenity_fields.extend([f'{amenity_type}_count', f'{amenity_type}_closest_distance'])
        
        # Total count field
        total_fields = ['total_amenities_count']
        
        fieldnames = base_fields + location_fields + amenity_fields + total_fields
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enhanced_properties)
        
        logger.info(f"Saved {len(enhanced_properties)} detailed properties to {output_file}")

def main():
    analyzer = DetailedAmenityAnalyzer()
    
    print("🏠 Detailed Amenity Analyzer")
    print("📊 Comprehensive amenity analysis with counts and distances")
    print("🆓 Uses free OpenStreetMap data\n")
    
    # Analyze the properties
    input_file = 'simplified_properties.csv'
    output_file = 'detailed_amenities.csv'
    
    try:
        if not analyzer.load_properties(input_file):
            print(f"❌ Could not load {input_file}")
            return
        
        enhanced_properties = analyzer.analyze_properties(max_properties=5)
        analyzer.save_detailed_data(enhanced_properties, output_file)
        
        print(f"\n✅ Detailed analysis complete!")
        print(f"📊 Enhanced data saved to: {output_file}")
        print(f"🆓 Total cost: $0.00 (completely free)")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")

if __name__ == "__main__":
    main()
