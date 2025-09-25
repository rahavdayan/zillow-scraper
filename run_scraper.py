#!/usr/bin/env python3
"""
Main runner script for Zillow scraper
Provides options to run different scraping methods and analysis
"""

import argparse
import sys
import os
from datetime import datetime

def run_basic_scraper(target_count=800):
    """Run the basic requests-based scraper"""
    print("Running basic scraper (requests + BeautifulSoup)...")
    try:
        from main import ZillowScraper
        
        scraper = ZillowScraper()
        properties = scraper.scrape_all_locations(target_count=target_count)
        scraper.save_to_csv('tri_state_properties_basic.csv')
        
        return len(properties)
    except Exception as e:
        print(f"Basic scraper failed: {e}")
        return 0

def run_selenium_scraper(target_count=800, headless=True):
    """Run the Selenium-based scraper"""
    print("Running Selenium scraper (handles JavaScript)...")
    try:
        from selenium_scraper import ZillowSeleniumScraper
        
        scraper = ZillowSeleniumScraper(headless=headless)
        properties = scraper.scrape_all_locations(target_count=target_count)
        scraper.save_to_csv('tri_state_properties_selenium.csv')
        
        return len(properties)
    except Exception as e:
        print(f"Selenium scraper failed: {e}")
        return 0

def run_amenity_analysis(csv_file, api_key=None):
    """Run amenity analysis on scraped data"""
    print(f"Running amenity analysis on {csv_file}...")
    try:
        from amenity_analyzer import AmenityAnalyzer
        
        analyzer = AmenityAnalyzer(google_api_key=api_key)
        result_df = analyzer.analyze_csv_properties(csv_file)
        
        if result_df is not None:
            return len(result_df)
        else:
            return 0
    except Exception as e:
        print(f"Amenity analysis failed: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Zillow Tri-State Area Property Scraper')
    parser.add_argument('--method', choices=['basic', 'selenium', 'both'], default='selenium',
                       help='Scraping method to use (default: selenium)')
    parser.add_argument('--target-count', type=int, default=800,
                       help='Target number of properties to scrape (default: 800)')
    parser.add_argument('--headless', action='store_true',
                       help='Run Selenium in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_true',
                       help='Run Selenium with visible browser')
    parser.add_argument('--analyze-amenities', action='store_true',
                       help='Run amenity analysis after scraping')
    parser.add_argument('--google-api-key', type=str,
                       help='Google Places API key for amenity analysis')
    parser.add_argument('--csv-file', type=str,
                       help='Analyze amenities for existing CSV file (skip scraping)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("ZILLOW TRI-STATE AREA PROPERTY SCRAPER")
    print("="*60)
    print(f"Target: {args.target_count} properties (50% NJ, 50% NY)")
    print(f"Focus: Hoboken, NJ and surrounding tri-state areas")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    total_properties = 0
    csv_files = []
    
    # If analyzing existing CSV, skip scraping
    if args.csv_file:
        if os.path.exists(args.csv_file):
            print(f"Analyzing existing CSV file: {args.csv_file}")
            if args.analyze_amenities:
                run_amenity_analysis(args.csv_file, args.google_api_key)
            else:
                print("Use --analyze-amenities flag to run amenity analysis")
        else:
            print(f"Error: CSV file {args.csv_file} not found")
        return
    
    # Determine headless mode
    headless = not args.no_headless
    
    # Run scraping
    if args.method == 'basic':
        count = run_basic_scraper(args.target_count)
        total_properties += count
        if count > 0:
            csv_files.append('tri_state_properties_basic.csv')
    
    elif args.method == 'selenium':
        count = run_selenium_scraper(args.target_count, headless)
        total_properties += count
        if count > 0:
            csv_files.append('tri_state_properties_selenium.csv')
    
    elif args.method == 'both':
        print("Running both scraping methods...")
        
        # Try basic first
        count1 = run_basic_scraper(args.target_count // 2)
        if count1 > 0:
            csv_files.append('tri_state_properties_basic.csv')
        
        # Then Selenium
        count2 = run_selenium_scraper(args.target_count // 2, headless)
        if count2 > 0:
            csv_files.append('tri_state_properties_selenium.csv')
        
        total_properties = count1 + count2
    
    # Run amenity analysis if requested
    if args.analyze_amenities and csv_files:
        print("\n" + "="*60)
        print("RUNNING AMENITY ANALYSIS")
        print("="*60)
        
        for csv_file in csv_files:
            run_amenity_analysis(csv_file, args.google_api_key)
    
    # Summary
    print("\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)
    print(f"Total properties scraped: {total_properties}")
    print(f"CSV files created: {len(csv_files)}")
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            size = os.path.getsize(csv_file) / 1024  # KB
            print(f"  - {csv_file} ({size:.1f} KB)")
    
    if total_properties > 0:
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Ready for analysis of {total_properties} tri-state properties")
        
        if not args.analyze_amenities:
            print(f"\n💡 Tip: Run with --analyze-amenities to add nearby amenity data")
            print(f"   Example: python run_scraper.py --csv-file {csv_files[0]} --analyze-amenities")
    else:
        print(f"\n❌ Scraping failed. No properties were collected.")
        print(f"💡 Try running with --no-headless to see what's happening in the browser")
    
    print("="*60)

if __name__ == "__main__":
    main()
