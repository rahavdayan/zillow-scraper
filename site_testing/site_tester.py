#!/usr/bin/env python3
"""
Real Estate Site Accessibility Tester
Tests 10 major real estate platforms for scraping feasibility
Analyzes anti-bot measures, data structure, and accessibility
"""

import requests
import time
import random
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import json
import csv
from urllib.parse import urljoin, urlparse
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealEstateSiteTester:
    def __init__(self):
        """Initialize the site tester"""
        self.session = requests.Session()
        self.results = []
        
        # Professional headers to mimic real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(self.headers)
        
        # Top 10 real estate platforms to test
        self.platforms = {
            'Zillow': {
                'base_url': 'https://www.zillow.com',
                'search_urls': [
                    'https://www.zillow.com/manhattan-ny/',
                    'https://www.zillow.com/homes/for_rent/Manhattan-NY/',
                    'https://www.zillow.com/apartments/manhattan-ny/'
                ],
                'type': 'Marketplace',
                'focus': 'Buy/Rent/Sell'
            },
            'Realtor.com': {
                'base_url': 'https://www.realtor.com',
                'search_urls': [
                    'https://www.realtor.com/realestateandhomes-search/Manhattan_NY',
                    'https://www.realtor.com/apartments/Manhattan_NY',
                    'https://www.realtor.com/rentals/Manhattan_NY'
                ],
                'type': 'MLS Listings',
                'focus': 'Buy/Sell'
            },
            'Redfin': {
                'base_url': 'https://www.redfin.com',
                'search_urls': [
                    'https://www.redfin.com/city/30749/NY/New-York/Manhattan',
                    'https://www.redfin.com/apartments-for-rent/Manhattan-NY',
                    'https://www.redfin.com/neighborhood/193375/NY/New-York/Manhattan'
                ],
                'type': 'Brokerage',
                'focus': 'Buy/Sell'
            },
            'Trulia': {
                'base_url': 'https://www.trulia.com',
                'search_urls': [
                    'https://www.trulia.com/NY/Manhattan/',
                    'https://www.trulia.com/for_rent/Manhattan,NY/',
                    'https://www.trulia.com/NY/New_York/Manhattan/'
                ],
                'type': 'Marketplace',
                'focus': 'Buy/Rent'
            },
            'Homes.com': {
                'base_url': 'https://www.homes.com',
                'search_urls': [
                    'https://www.homes.com/manhattan-ny/',
                    'https://www.homes.com/rentals/manhattan-ny/',
                    'https://www.homes.com/apartments/manhattan-ny/'
                ],
                'type': 'Listings',
                'focus': 'Buy/Rent'
            },
            'Apartments.com': {
                'base_url': 'https://www.apartments.com',
                'search_urls': [
                    'https://www.apartments.com/manhattan-ny/',
                    'https://www.apartments.com/new-york-ny/manhattan/',
                    'https://www.apartments.com/apartments/manhattan-ny/'
                ],
                'type': 'Rentals',
                'focus': 'Rent Only'
            },
            'LoopNet': {
                'base_url': 'https://www.loopnet.com',
                'search_urls': [
                    'https://www.loopnet.com/search/commercial-real-estate/manhattan-ny/',
                    'https://www.loopnet.com/manhattan-ny/',
                    'https://www.loopnet.com/new-york-ny/manhattan-commercial-real-estate/'
                ],
                'type': 'Commercial',
                'focus': 'Commercial RE'
            },
            'Homefinder': {
                'base_url': 'https://www.homefinder.com',
                'search_urls': [
                    'https://www.homefinder.com/NY/Manhattan/',
                    'https://www.homefinder.com/real-estate/NY/Manhattan/',
                    'https://www.homefinder.com/rentals/NY/Manhattan/'
                ],
                'type': 'Listings',
                'focus': 'Buy/Sell'
            },
            'RealtyTrac': {
                'base_url': 'https://www.realtytrac.com',
                'search_urls': [
                    'https://www.realtytrac.com/NY/Manhattan/',
                    'https://www.realtytrac.com/foreclosures/NY/Manhattan/',
                    'https://www.realtytrac.com/real-estate/NY/Manhattan/'
                ],
                'type': 'Foreclosures',
                'focus': 'Distressed'
            },
            'Coldwell Banker': {
                'base_url': 'https://www.coldwellbanker.com',
                'search_urls': [
                    'https://www.coldwellbanker.com/property-search/Manhattan-NY',
                    'https://www.coldwellbanker.com/rentals/Manhattan-NY',
                    'https://www.coldwellbanker.com/homes-for-sale/Manhattan-NY'
                ],
                'type': 'Brokerage',
                'focus': 'Buy/Sell'
            }
        }
    
    def check_robots_txt(self, base_url):
        """Check robots.txt for scraping permissions"""
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            response = self.session.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                robots_content = response.text
                
                # Check for common restrictions
                restrictions = {
                    'disallow_all': 'Disallow: /' in robots_content,
                    'crawl_delay': 'Crawl-delay:' in robots_content,
                    'user_agent_restrictions': 'User-agent: *' in robots_content,
                    'sitemap_provided': 'Sitemap:' in robots_content
                }
                
                # Extract crawl delay if present
                crawl_delay_match = re.search(r'Crawl-delay:\s*(\d+)', robots_content)
                if crawl_delay_match:
                    restrictions['crawl_delay_seconds'] = int(crawl_delay_match.group(1))
                
                return restrictions
            else:
                return {'robots_accessible': False}
                
        except Exception as e:
            logger.debug(f"Error checking robots.txt for {base_url}: {e}")
            return {'robots_error': str(e)}
    
    def detect_anti_bot_measures(self, soup, response):
        """Detect common anti-bot measures"""
        measures = {
            'captcha': False,
            'cloudflare': False,
            'rate_limiting': False,
            'javascript_required': False,
            'ip_blocking': False
        }
        
        # Check response status and headers
        if response.status_code == 403:
            measures['ip_blocking'] = True
        elif response.status_code == 429:
            measures['rate_limiting'] = True
        
        # Check for Cloudflare
        if 'cloudflare' in response.headers.get('Server', '').lower():
            measures['cloudflare'] = True
        
        # Check page content for anti-bot indicators
        page_text = soup.get_text().lower()
        
        if any(term in page_text for term in ['captcha', 'verify you are human', 'prove you are not a robot']):
            measures['captcha'] = True
        
        if any(term in page_text for term in ['enable javascript', 'javascript is required', 'js is disabled']):
            measures['javascript_required'] = True
        
        if any(term in page_text for term in ['access denied', 'blocked', 'forbidden']):
            measures['ip_blocking'] = True
        
        return measures
    
    def analyze_data_structure(self, soup):
        """Analyze the structure of property data on the page"""
        structure = {
            'property_listings_found': False,
            'structured_data': False,
            'property_count': 0,
            'data_elements': []
        }
        
        # Common property listing selectors
        property_selectors = [
            '[data-test="property-card"]',
            '.property-card',
            '.listing-item',
            '.property-item',
            '.search-result',
            '.property',
            '.listing',
            '[class*="property"]',
            '[class*="listing"]'
        ]
        
        for selector in property_selectors:
            elements = soup.select(selector)
            if elements:
                structure['property_listings_found'] = True
                structure['property_count'] = len(elements)
                structure['primary_selector'] = selector
                break
        
        # Check for structured data (JSON-LD)
        json_scripts = soup.find_all('script', type='application/ld+json')
        if json_scripts:
            structure['structured_data'] = True
            structure['json_ld_count'] = len(json_scripts)
        
        # Look for common data elements
        data_indicators = {
            'prices': ['price', 'rent', '$', 'cost'],
            'addresses': ['address', 'location', 'street'],
            'bedrooms': ['bed', 'br', 'bedroom'],
            'bathrooms': ['bath', 'ba', 'bathroom'],
            'square_feet': ['sqft', 'sq ft', 'square feet', 'size']
        }
        
        page_text = soup.get_text().lower()
        for data_type, indicators in data_indicators.items():
            if any(indicator in page_text for indicator in indicators):
                structure['data_elements'].append(data_type)
        
        return structure
    
    def test_platform(self, platform_name, platform_info):
        """Test a single platform for scraping feasibility"""
        logger.info(f"Testing {platform_name}...")
        
        result = {
            'platform': platform_name,
            'type': platform_info['type'],
            'focus': platform_info['focus'],
            'base_url': platform_info['base_url'],
            'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'accessibility_score': 0,
            'recommendation': 'Unknown'
        }
        
        # Check robots.txt
        robots_info = self.check_robots_txt(platform_info['base_url'])
        result['robots_txt'] = robots_info
        
        # Test each search URL
        url_results = []
        
        for i, url in enumerate(platform_info['search_urls']):
            logger.info(f"  Testing URL {i+1}: {url}")
            
            try:
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(2, 5))
                
                response = self.session.get(url, timeout=20)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                url_result = {
                    'url': url,
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'content_length': len(response.content),
                    'success': response.status_code == 200
                }
                
                if response.status_code == 200:
                    # Analyze anti-bot measures
                    anti_bot = self.detect_anti_bot_measures(soup, response)
                    url_result['anti_bot_measures'] = anti_bot
                    
                    # Analyze data structure
                    data_structure = self.analyze_data_structure(soup)
                    url_result['data_structure'] = data_structure
                    
                    # Calculate accessibility score for this URL
                    score = 100
                    if anti_bot['captcha']: score -= 30
                    if anti_bot['cloudflare']: score -= 20
                    if anti_bot['ip_blocking']: score -= 40
                    if anti_bot['rate_limiting']: score -= 25
                    if anti_bot['javascript_required']: score -= 15
                    
                    if data_structure['property_listings_found']: score += 20
                    if data_structure['structured_data']: score += 10
                    if len(data_structure['data_elements']) > 3: score += 15
                    
                    url_result['accessibility_score'] = max(0, min(100, score))
                    
                    logger.info(f"    ✅ Status: {response.status_code}, Score: {url_result['accessibility_score']}")
                else:
                    url_result['accessibility_score'] = 0
                    logger.warning(f"    ❌ Status: {response.status_code}")
                
                url_results.append(url_result)
                
            except Exception as e:
                logger.error(f"    ❌ Error: {e}")
                url_results.append({
                    'url': url,
                    'error': str(e),
                    'success': False,
                    'accessibility_score': 0
                })
        
        # Calculate overall platform score
        successful_tests = [r for r in url_results if r.get('success', False)]
        if successful_tests:
            result['accessibility_score'] = sum(r['accessibility_score'] for r in successful_tests) / len(successful_tests)
        else:
            result['accessibility_score'] = 0
        
        result['url_tests'] = url_results
        
        # Generate recommendation
        if result['accessibility_score'] >= 70:
            result['recommendation'] = '✅ Highly Scrapable'
        elif result['accessibility_score'] >= 40:
            result['recommendation'] = '⚠️ Moderately Scrapable'
        else:
            result['recommendation'] = '❌ Difficult to Scrape'
        
        return result
    
    def test_all_platforms(self):
        """Test all platforms and generate comprehensive report"""
        logger.info("🏠 Starting Real Estate Site Accessibility Testing")
        logger.info(f"Testing {len(self.platforms)} platforms...\n")
        
        for platform_name, platform_info in self.platforms.items():
            result = self.test_platform(platform_name, platform_info)
            self.results.append(result)
            
            # Add delay between platforms
            time.sleep(random.uniform(3, 8))
        
        return self.results
    
    def generate_report(self):
        """Generate comprehensive testing report"""
        if not self.results:
            logger.error("No test results available")
            return
        
        # Sort by accessibility score
        sorted_results = sorted(self.results, key=lambda x: x['accessibility_score'], reverse=True)
        
        print("\n" + "="*80)
        print("🏠 REAL ESTATE SITE ACCESSIBILITY REPORT")
        print("="*80)
        
        print(f"\n📊 SUMMARY")
        print(f"Platforms Tested: {len(self.results)}")
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Categorize results
        highly_scrapable = [r for r in self.results if r['accessibility_score'] >= 70]
        moderately_scrapable = [r for r in self.results if 40 <= r['accessibility_score'] < 70]
        difficult_to_scrape = [r for r in self.results if r['accessibility_score'] < 40]
        
        print(f"\n✅ Highly Scrapable: {len(highly_scrapable)}")
        print(f"⚠️ Moderately Scrapable: {len(moderately_scrapable)}")
        print(f"❌ Difficult to Scrape: {len(difficult_to_scrape)}")
        
        print(f"\n📈 DETAILED RESULTS")
        print("-" * 80)
        
        for result in sorted_results:
            print(f"\n🏢 {result['platform']} ({result['type']})")
            print(f"   Score: {result['accessibility_score']:.1f}/100")
            print(f"   Status: {result['recommendation']}")
            print(f"   Focus: {result['focus']}")
            
            # Show successful URLs
            successful_urls = [r for r in result['url_tests'] if r.get('success', False)]
            if successful_urls:
                print(f"   Working URLs: {len(successful_urls)}/{len(result['url_tests'])}")
                for url_result in successful_urls[:1]:  # Show first working URL
                    if url_result.get('data_structure', {}).get('property_listings_found'):
                        count = url_result['data_structure'].get('property_count', 0)
                        print(f"   Properties Found: {count}")
            else:
                print(f"   Working URLs: 0/{len(result['url_tests'])}")
        
        print(f"\n🎯 RECOMMENDATIONS")
        print("-" * 40)
        
        if highly_scrapable:
            print("✅ Start with these platforms:")
            for result in highly_scrapable:
                print(f"   • {result['platform']} (Score: {result['accessibility_score']:.1f})")
        
        if moderately_scrapable:
            print("\n⚠️ Try these with caution:")
            for result in moderately_scrapable:
                print(f"   • {result['platform']} (Score: {result['accessibility_score']:.1f})")
        
        print(f"\n💡 NEXT STEPS")
        print("1. Build scrapers for highly scrapable platforms")
        print("2. Test rate limiting and proxy requirements")
        print("3. Implement data quality validation")
        print("4. Compare data completeness across platforms")
    
    def save_results(self, filename='site_accessibility_results.json'):
        """Save detailed results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        logger.info(f"Detailed results saved to {filename}")
    
    def save_summary_csv(self, filename='site_accessibility_summary.csv'):
        """Save summary results to CSV"""
        fieldnames = ['platform', 'type', 'focus', 'accessibility_score', 'recommendation', 'working_urls', 'total_urls']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                working_urls = len([r for r in result['url_tests'] if r.get('success', False)])
                total_urls = len(result['url_tests'])
                
                row = {
                    'platform': result['platform'],
                    'type': result['type'],
                    'focus': result['focus'],
                    'accessibility_score': round(result['accessibility_score'], 1),
                    'recommendation': result['recommendation'],
                    'working_urls': working_urls,
                    'total_urls': total_urls
                }
                writer.writerow(row)
        
        logger.info(f"Summary saved to {filename}")

def main():
    tester = RealEstateSiteTester()
    
    print("🏠 Real Estate Site Accessibility Tester")
    print("📍 Testing 10 Major Platforms")
    print("🎯 Identifying Scrapable Sources")
    print("⚡ Analyzing Data Structure & Anti-Bot Measures\n")
    
    try:
        # Test all platforms
        results = tester.test_all_platforms()
        
        # Generate and display report
        tester.generate_report()
        
        # Save results
        tester.save_results()
        tester.save_summary_csv()
        
        print(f"\n📄 Results saved to:")
        print(f"   • site_accessibility_results.json (detailed)")
        print(f"   • site_accessibility_summary.csv (summary)")
        
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        print(f"\n❌ Testing failed: {e}")

if __name__ == "__main__":
    main()
