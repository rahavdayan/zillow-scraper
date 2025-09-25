#!/usr/bin/env python3
"""
Amenity Analyzer for Zillow Properties
Analyzes nearby amenities for scraped properties using Google Places API
"""

import pandas as pd
import requests
import time
import json
import logging
from typing import Dict, List, Tuple
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmenityAnalyzer:
    def __init__(self, google_api_key: str = None):
        """
        Initialize the amenity analyzer
        
        Args:
            google_api_key: Google Places API key (optional, will use mock data if not provided)
        """
        self.google_api_key = google_api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        
        # Define amenity categories and their search types
        self.amenity_categories = {
            'schools': ['school', 'elementary_school', 'secondary_school'],
            'gyms': ['gym', 'fitness_center', 'health'],
            'transport': ['subway_station', 'bus_station', 'train_station', 'transit_station'],
            'parks': ['park', 'amusement_park'],
            'groceries': ['grocery_or_supermarket', 'supermarket', 'food'],
            'restaurants': ['restaurant', 'meal_takeaway', 'cafe']
        }
        
        # Radius for nearby search (in meters)
        self.search_radius = 1000  # 1km radius
    
    def extract_coordinates_from_address(self, address: str) -> Tuple[float, float]:
        """
        Extract coordinates from address using Google Geocoding API
        Returns mock coordinates if no API key provided
        """
        if not self.google_api_key:
            # Return mock coordinates for demo purposes
            # In reality, you'd need to implement proper geocoding
            return (40.7589, -74.0278)  # Hoboken area coordinates
        
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': self.google_api_key
        }
        
        try:
            response = requests.get(geocode_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return (location['lat'], location['lng'])
            else:
                logger.warning(f"Geocoding failed for address: {address}")
                return None
                
        except Exception as e:
            logger.error(f"Error geocoding address {address}: {e}")
            return None
    
    def search_nearby_amenities(self, lat: float, lng: float, amenity_type: str) -> List[Dict]:
        """
        Search for nearby amenities using Google Places API
        Returns mock data if no API key provided
        """
        if not self.google_api_key:
            # Return mock amenity data for demo
            return self._generate_mock_amenities(amenity_type)
        
        nearby_url = f"{self.base_url}/nearbysearch/json"
        params = {
            'location': f"{lat},{lng}",
            'radius': self.search_radius,
            'type': amenity_type,
            'key': self.google_api_key
        }
        
        try:
            response = requests.get(nearby_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                return data.get('results', [])
            else:
                logger.warning(f"Places API request failed: {data.get('status')}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching for {amenity_type}: {e}")
            return []
    
    def _generate_mock_amenities(self, amenity_type: str) -> List[Dict]:
        """Generate mock amenity data for demonstration"""
        import random
        
        mock_data = {
            'school': [
                {'name': 'Hoboken Elementary School', 'rating': 4.2, 'vicinity': '0.3 miles'},
                {'name': 'Stevens Cooperative School', 'rating': 4.5, 'vicinity': '0.5 miles'}
            ],
            'gym': [
                {'name': 'Planet Fitness', 'rating': 4.0, 'vicinity': '0.2 miles'},
                {'name': 'Equinox Fitness', 'rating': 4.3, 'vicinity': '0.4 miles'}
            ],
            'subway_station': [
                {'name': 'Hoboken Terminal', 'rating': 3.8, 'vicinity': '0.6 miles'},
                {'name': 'PATH Station', 'rating': 3.9, 'vicinity': '0.3 miles'}
            ],
            'park': [
                {'name': 'Pier A Park', 'rating': 4.4, 'vicinity': '0.4 miles'},
                {'name': 'Stevens Park', 'rating': 4.1, 'vicinity': '0.7 miles'}
            ],
            'grocery_or_supermarket': [
                {'name': 'ShopRite', 'rating': 4.0, 'vicinity': '0.5 miles'},
                {'name': 'Whole Foods Market', 'rating': 4.2, 'vicinity': '0.3 miles'}
            ],
            'restaurant': [
                {'name': 'Grimaldis Pizza', 'rating': 4.3, 'vicinity': '0.2 miles'},
                {'name': 'The Brass Rail', 'rating': 4.1, 'vicinity': '0.4 miles'}
            ]
        }
        
        return mock_data.get(amenity_type, [])
    
    def analyze_property_amenities(self, address: str) -> Dict:
        """
        Analyze all amenities for a single property
        """
        logger.info(f"Analyzing amenities for: {address}")
        
        # Get coordinates
        coordinates = self.extract_coordinates_from_address(address)
        if not coordinates:
            return {'error': 'Could not geocode address'}
        
        lat, lng = coordinates
        amenity_scores = {}
        
        # Search for each amenity category
        for category, types in self.amenity_categories.items():
            category_amenities = []
            
            for amenity_type in types:
                amenities = self.search_nearby_amenities(lat, lng, amenity_type)
                category_amenities.extend(amenities)
                
                # Add small delay to respect API limits
                if self.google_api_key:
                    time.sleep(0.1)
            
            # Calculate category score
            if category_amenities:
                avg_rating = sum(a.get('rating', 0) for a in category_amenities) / len(category_amenities)
                amenity_count = len(category_amenities)
                
                amenity_scores[f'{category}_count'] = amenity_count
                amenity_scores[f'{category}_avg_rating'] = round(avg_rating, 2)
                amenity_scores[f'{category}_score'] = round((amenity_count * 0.3 + avg_rating * 0.7), 2)
            else:
                amenity_scores[f'{category}_count'] = 0
                amenity_scores[f'{category}_avg_rating'] = 0
                amenity_scores[f'{category}_score'] = 0
        
        # Calculate overall amenity score
        category_scores = [amenity_scores[f'{cat}_score'] for cat in self.amenity_categories.keys()]
        overall_score = round(sum(category_scores) / len(category_scores), 2)
        amenity_scores['overall_amenity_score'] = overall_score
        
        return amenity_scores
    
    def analyze_csv_properties(self, csv_file: str, output_file: str = None):
        """
        Analyze amenities for all properties in a CSV file
        """
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded {len(df)} properties from {csv_file}")
            
            # Analyze amenities for each property
            amenity_data = []
            
            for index, row in df.iterrows():
                address = row.get('address', '')
                if not address:
                    continue
                
                logger.info(f"Processing property {index + 1}/{len(df)}: {address}")
                
                amenities = self.analyze_property_amenities(address)
                amenity_data.append(amenities)
                
                # Add delay to avoid overwhelming APIs
                time.sleep(1)
            
            # Create amenities DataFrame
            amenities_df = pd.DataFrame(amenity_data)
            
            # Combine with original data
            result_df = pd.concat([df, amenities_df], axis=1)
            
            # Save to new CSV
            output_filename = output_file or csv_file.replace('.csv', '_with_amenities.csv')
            result_df.to_csv(output_filename, index=False)
            
            logger.info(f"Analysis complete. Results saved to {output_filename}")
            
            # Print summary statistics
            self.print_amenity_summary(result_df)
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error analyzing CSV properties: {e}")
            return None
    
    def print_amenity_summary(self, df: pd.DataFrame):
        """Print summary statistics of amenity analysis"""
        print("\n" + "="*50)
        print("AMENITY ANALYSIS SUMMARY")
        print("="*50)
        
        for category in self.amenity_categories.keys():
            count_col = f'{category}_count'
            score_col = f'{category}_score'
            
            if count_col in df.columns and score_col in df.columns:
                avg_count = df[count_col].mean()
                avg_score = df[score_col].mean()
                
                print(f"{category.upper()}:")
                print(f"  Average count: {avg_count:.1f}")
                print(f"  Average score: {avg_score:.2f}")
        
        if 'overall_amenity_score' in df.columns:
            overall_avg = df['overall_amenity_score'].mean()
            print(f"\nOVERALL AMENITY SCORE: {overall_avg:.2f}")
        
        print("="*50)

def main():
    """Main execution function for amenity analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze amenities for Zillow properties')
    parser.add_argument('csv_file', help='Path to CSV file with property data')
    parser.add_argument('--api-key', help='Google Places API key (optional)')
    parser.add_argument('--output', help='Output CSV filename')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = AmenityAnalyzer(google_api_key=args.api_key)
    
    # Analyze properties
    result_df = analyzer.analyze_csv_properties(args.csv_file, args.output)
    
    if result_df is not None:
        print(f"\nAmenity analysis completed successfully!")
        print(f"Enhanced data saved with amenity scores.")
    else:
        print("Amenity analysis failed.")

if __name__ == "__main__":
    main()
