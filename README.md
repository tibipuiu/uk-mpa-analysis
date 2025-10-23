# UK MPA Fishing Activity Analysis App

A Flask web application that analyzes fishing activity in UK Marine Protected Areas using Global Fishing Watch data.

## Features

- **MPA Search**: Search and select from 275+ UK Marine Protected Areas
- **Dynamic Date Range**: Choose any date range for analysis
- **Real-time Data**: Queries Global Fishing Watch 4Wings API
- **Key Metrics**: 
  - Total fishing hours
  - Number of unique vessels
  - Activity by gear type
  - Most active vessels breakdown
- **Conservation Alerts**: Identifies harmful fishing practices (trawling, dredging)
- **Interactive Charts**: Monthly activity trends and gear type distribution
- **Data Tables**: Top vessels and flag state analysis

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
cd mpa_app
python app.py
```

3. Open browser to http://localhost:5000

## Usage

1. **Search MPA**: Type MPA name in search box (e.g. "Lyme Bay")
2. **Select Dates**: Choose start and end dates (default: last 30 days)
3. **Analyze**: Click "Analyze Fishing Activity"
4. **View Results**: 
   - Summary metrics cards
   - Conservation alerts for harmful practices
   - Monthly activity chart
   - Gear type distribution
   - Most active vessels
   - Flag state breakdown

## API Pattern

Based on working `lyme_bay_analysis.py` script:
- Uses `gfwapiclient` Python package
- Queries with MPA WDPA code
- Returns vessel-level data with gear types
- Processes into structured analysis

## Data Source

- **UK MPAs**: From `data/uk_mpas_master.csv` (275 MPAs)
- **Fishing Data**: Global Fishing Watch 4Wings API
- **Real-time**: All data fetched on-demand