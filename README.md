# Zillow Tri-State Area Property Scraper

This project scrapes residential property listings from Zillow in the tri-state area (New Jersey and New York) and analyzes nearby amenities to help identify the most suitable properties for renters or buyers.

## Features

- **Property Scraping**: Collects 500-1000 property listings from target locations
- **Geographic Coverage**: Focuses on Hoboken, NJ and surrounding tri-state areas including NYC
- **50-50 Split**: Aims for approximately equal representation of NJ and NY properties
- **Amenity Analysis**: Evaluates proximity to schools, gyms, transport, parks, groceries, and restaurants
- **CSV Export**: Saves all data in structured CSV format for further analysis

## Target Locations

### New Jersey
- Hoboken, NJ
- Jersey City, NJ
- Weehawken, NJ
- Union City, NJ
- North Bergen, NJ
- Secaucus, NJ
- Bayonne, NJ

### New York
- Manhattan, NY
- Brooklyn, NY
- Queens, NY
- Bronx, NY
- Long Island City, NY
- Astoria, NY
- Williamsburg, Brooklyn, NY

## Installation

1. Clone or download this project
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Property Scraping

Run the main scraper to collect property data:

```bash
python main.py
```

This will:
- Scrape properties from all target locations
- Aim for 800 total properties (400 NJ + 400 NY)
- Save results to `tri_state_properties.csv`

### Amenity Analysis (Optional)

To enhance the property data with nearby amenity information:

```bash
python amenity_analyzer.py tri_state_properties.csv
```

For better results with real amenity data, provide a Google Places API key:

```bash
python amenity_analyzer.py tri_state_properties.csv --api-key YOUR_GOOGLE_API_KEY
```

## Data Structure

The CSV output includes the following columns:

### Basic Property Data
- `address`: Full property address
- `price`: Current rent/sale price
- `beds`: Number of bedrooms
- `baths`: Number of bathrooms
- `sqft`: Square footage
- `property_type`: Type of property (apartment, house, etc.)
- `location`: Specific location/neighborhood
- `state`: NJ or NY
- `zillow_url`: Direct link to Zillow listing
- `scraped_date`: When the data was collected

### Amenity Analysis (if run)
- `schools_count`: Number of nearby schools
- `schools_avg_rating`: Average rating of nearby schools
- `schools_score`: Composite school score
- `gyms_count`: Number of nearby fitness centers
- `gyms_avg_rating`: Average rating of nearby gyms
- `gyms_score`: Composite gym score
- `transport_count`: Number of nearby transit options
- `transport_avg_rating`: Average rating of transit stations
- `transport_score`: Composite transport score
- `parks_count`: Number of nearby parks
- `parks_avg_rating`: Average rating of nearby parks
- `parks_score`: Composite park score
- `groceries_count`: Number of nearby grocery stores
- `groceries_avg_rating`: Average rating of grocery stores
- `groceries_score`: Composite grocery score
- `restaurants_count`: Number of nearby restaurants
- `restaurants_avg_rating`: Average rating of restaurants
- `restaurants_score`: Composite restaurant score
- `overall_amenity_score`: Overall amenity desirability score

## Configuration

### Adjusting Target Count
Modify the `target_count` parameter in `main.py`:

```python
properties = scraper.scrape_all_locations(target_count=1000)  # Adjust as needed
```

### Adding New Locations
Add new locations to the `locations` dictionary in `main.py`:

```python
self.locations = {
    'nj': [
        'hoboken-nj',
        'your-new-location-nj',  # Add here
        # ... existing locations
    ],
    'ny': [
        'manhattan-new-york-ny',
        'your-new-location-ny',  # Add here
        # ... existing locations
    ]
}
```

## API Requirements

### Google Places API (Optional)
For amenity analysis, you can obtain a Google Places API key:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Places API and Geocoding API
4. Create credentials (API key)
5. Use the API key with the amenity analyzer

**Note**: The amenity analyzer will work without an API key using mock data for demonstration purposes.

## Rate Limiting and Ethics

- The scraper includes random delays between requests (2-5 seconds)
- Respects robots.txt and website terms of service
- Uses appropriate headers to identify as a legitimate browser
- Implements error handling and retry logic

## Output Files

- `tri_state_properties.csv`: Main output with property data
- `tri_state_properties_with_amenities.csv`: Enhanced with amenity analysis
- `partial_tri_state_properties.csv`: Saved if scraping is interrupted
- `error_tri_state_properties.csv`: Saved if errors occur

## Troubleshooting

### Common Issues

1. **No properties found**: Zillow may have changed their HTML structure
2. **Rate limiting**: Increase delays between requests
3. **Geocoding failures**: Check address format or API key

### Error Handling

The scraper includes comprehensive error handling:
- Continues scraping if individual pages fail
- Saves partial data if interrupted
- Logs all errors for debugging

## Legal Considerations

- This tool is for educational and research purposes
- Respect Zillow's terms of service and robots.txt
- Do not use scraped data for commercial purposes without permission
- Consider using official APIs when available

## Contributing

Feel free to submit issues or pull requests to improve the scraper:
- Add new target locations
- Improve data extraction accuracy
- Enhance amenity analysis
- Add new features

## License

This project is provided as-is for educational purposes. Please use responsibly and in accordance with website terms of service.
