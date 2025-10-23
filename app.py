#!/usr/bin/env python3
"""
UK MPA Fishing Activity Analysis Web Application
Dynamic analysis for any UK MPA with custom date ranges
"""

from flask import Flask, render_template, jsonify, request, Response, make_response
import pandas as pd
import asyncio
import os
import gfwapiclient as gfw
import json
from datetime import datetime, timedelta
from collections import defaultdict
import io
import requests
from concurrent.futures import ThreadPoolExecutor
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

app = Flask(__name__)

# GFW API configuration
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtpZEtleSJ9.eyJkYXRhIjp7Im5hbWUiOiJVSyBNUEFzIGZpc2hpbmcgYWN0aXZpdHkiLCJ1c2VySWQiOjQ3NzEzLCJhcHBsaWNhdGlvbk5hbWUiOiJVSyBNUEFzIGZpc2hpbmcgYWN0aXZpdHkiLCJpZCI6MjkxNSwidHlwZSI6InVzZXItYXBwbGljYXRpb24ifSwiaWF0IjoxNzUxMDIwMjM4LCJleHAiOjIwNjYzODAyMzgsImF1ZCI6ImdmdyIsImlzcyI6ImdmdyJ9.ZHzGOlBXJSV05eDupoNTTt-6O0CzRAAMorobQdDuAl0e-0wiGzE_LBNhy1r0VPTACV828brKldhHpbSgrAmLC9mE_anxJ81ZAWwAOO6qUP7QnbhhSVMOizyGR6F1LAVpP_T5lH612r1FnAAT9QAVrGn8WG3RMZdmQjfwvQQvjbev1WG_W4A_yUVXdY659KEQYQuAvksqaVjpwjcXkmBjTbvUR5FTBq91Yci1TnUO-JZTbq7_RpogvPHaI9-9zTN0isaiOw4MM97rv_GJRkX0-a2jEO7aPsMz2AbXgfQkLz3Duk-SqNR0kr8IbBcMlVXpBsOMtQST4N_3UMZlzbzMOW9JDT_Ww_uZD1RkS32yJOhI1Rjxja2sQfhdsxcNzi1glfXYZXN-6XaTqZ4oCMjlwtoni1LIzO6rNtOCjpZYYCEi06X8-1jfUaRdoVs1wF2Vo-tdzXgSDvD0P8JGZqVQ9ACLDBifIAKiUtsZgR5febvrwLrNV-PciNQmPEVoGKKL"

# Cache for vessel details to avoid repeated API calls
vessel_cache = {}

# Load UK MPAs from master dataset
def load_uk_mpas():
    try:
        # Try container path first, then local development path
        data_paths = ['data/uk_mpas_master.csv', '../data/uk_mpas_master.csv']
        df = None
        for path in data_paths:
            try:
                df = pd.read_csv(path)
                break
            except FileNotFoundError:
                continue
        
        if df is None:
            raise FileNotFoundError("Could not find uk_mpas_master.csv in any expected location")
        # Clean the data
        df['WDPA_Code'] = df['WDPA_Code'].astype(float).astype(int).astype(str)
        # Get unique MPAs with valid WDPA codes
        mpas = df[['Site_Name', 'WDPA_Code', 'Latitude', 'Longitude', 'Area_ha']].dropna()
        # Remove duplicates and sort by name
        mpas = mpas.drop_duplicates(subset=['Site_Name']).sort_values('Site_Name')
        return mpas.to_dict('records')
    except Exception as e:
        print(f"Error loading MPAs: {e}")
        return []

# Load protected features for MPAs
def get_protected_features(mpa_name):
    try:
        # Try container path first, then local development path
        data_paths = ['data/all_mpas_and_features.csv', '../data/all_mpas_and_features.csv']
        features_df = None
        for path in data_paths:
            try:
                features_df = pd.read_csv(path)
                break
            except FileNotFoundError:
                continue
        
        if features_df is None:
            raise FileNotFoundError("Could not find all_mpas_and_features.csv in any expected location")
        # Find matching MPA (case insensitive)
        match = features_df[features_df['Site_Name'].str.contains(mpa_name, case=False, na=False)]
        
        if not match.empty:
            features_str = match.iloc[0]['Features']
            if pd.notna(features_str):
                # Split by semicolon and clean up
                features = [f.strip() for f in features_str.split(';') if f.strip()]
                return features
        return []
    except Exception as e:
        print(f"Error loading protected features: {e}")
        return []

def get_vessel_details(vessel_id, mmsi=None):
    """Fetch vessel details including length from GFW Vessels API v2."""
    # Use MMSI as cache key if available, otherwise vessel_id
    cache_key = mmsi if mmsi else vessel_id
    
    # Check cache first
    if cache_key in vessel_cache:
        return vessel_cache[cache_key]
    
    try:
        # If we have MMSI, search by that instead
        if mmsi:
            # Search for vessel by MMSI using v3 API
            url = "https://gateway.api.globalfishingwatch.org/v3/vessels/search"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            params = {
                "query": mmsi,
                "datasets[0]": "public-global-vessel-identity:latest",
                "limit": 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])
                if entries:
                    vessel = entries[0]
                    # Extract from registryInfo which contains the vessel details
                    registry_info = vessel.get("registryInfo", [])
                    if registry_info:
                        reg = registry_info[0]  # Get first registry entry
                        vessel_info = {
                            "length": reg.get("lengthM", None),
                            "tonnage": reg.get("tonnageGt", None),
                            "imo": reg.get("imo", None),
                            "engine_power": None,  # Not in v3 response
                            "built_year": None  # Would need to extract from extraFields
                        }
                        
                        # Try to get built year from extraFields
                        extra_fields = reg.get("extraFields", [])
                        if extra_fields:
                            built_year_info = extra_fields[0].get("builtYear", {})
                            if built_year_info:
                                vessel_info["built_year"] = built_year_info.get("value", None)
                    else:
                        vessel_info = {"length": None, "tonnage": None, "imo": None, "engine_power": None, "built_year": None}
                    # Cache the result
                    vessel_cache[cache_key] = vessel_info
                    return vessel_info
        else:
            # For vessel ID without MMSI, we can't use v3 search API
            # Return empty data for now
            vessel_info = {"length": None, "tonnage": None, "imo": None, "engine_power": None, "built_year": None}
            vessel_cache[cache_key] = vessel_info
            return vessel_info
        
        # If we get here, no data found
        vessel_info = {"length": None, "tonnage": None, "imo": None, "engine_power": None, "built_year": None}
        vessel_cache[cache_key] = vessel_info
        return vessel_info
            
    except Exception as e:
        print(f"Error fetching vessel details for {cache_key}: {e}")
        vessel_cache[cache_key] = {"length": None, "tonnage": None, "imo": None}
        return {"length": None, "tonnage": None, "imo": None}

def enrich_vessels_with_details(vessels):
    """Enrich vessel data with length and other details from Vessels API."""
    # Use ThreadPoolExecutor for parallel requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Create a mapping of vessel_id to future
        future_to_vessel = {
            executor.submit(get_vessel_details, vessel['vessel_id'], vessel.get('mmsi')): vessel 
            for vessel in vessels if vessel.get('vessel_id')
        }
        
        # Process completed futures
        for future in future_to_vessel:
            vessel = future_to_vessel[future]
            try:
                vessel_details = future.result()
                # Add vessel details to the vessel dict
                vessel['length'] = vessel_details.get('length')
                vessel['tonnage'] = vessel_details.get('tonnage')
                vessel['imo'] = vessel_details.get('imo')
                vessel['engine_power'] = vessel_details.get('engine_power')
                vessel['built_year'] = vessel_details.get('built_year')
            except Exception as e:
                print(f"Error enriching vessel {vessel.get('vessel_id')}: {e}")
                vessel['length'] = None
                vessel['tonnage'] = None
                vessel['imo'] = None
    
    return vessels

@app.route('/')
def index():
    mpas = load_uk_mpas()
    return render_template('index.html', mpas=mpas)

@app.route('/api/analyze_mpa', methods=['POST'])
def analyze_mpa():
    data = request.json
    mpa_name = data.get('mpa_name')
    wdpa_code = data.get('wdpa_code')
    start_date = data.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    if not all([mpa_name, wdpa_code]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Run the async analysis
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            analyze_mpa_fishing(mpa_name, wdpa_code, start_date, end_date)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

async def analyze_mpa_fishing(mpa_name, wdpa_code, start_date, end_date):
    """Analyze fishing activity for a specific MPA using GFW API."""
    
    client = gfw.Client(access_token=ACCESS_TOKEN)
    
    # Define MPA region following working pattern
    mpa_region = {
        "dataset": "public-mpa-all",
        "id": str(wdpa_code)
    }
    
    print(f"Analyzing: {mpa_name} (ID: {wdpa_code})")
    print(f"Time period: {start_date} to {end_date}")
    
    try:
        # Query 4Wings API - exact pattern from working script
        report = await client.fourwings.create_report(
            spatial_resolution="HIGH",
            temporal_resolution="MONTHLY",
            group_by="VESSEL_ID",
            datasets=["public-global-fishing-effort:latest"],
            start_date=start_date,
            end_date=end_date,
            region=mpa_region
        )
        
        # Get data as DataFrame
        df = report.df()
        print(f"Retrieved {len(df)} fishing activity records")
        
        if len(df) == 0:
            return {
                "status": "success",
                "mpa_name": mpa_name,
                "wdpa_code": wdpa_code,
                "date_range": {"start": start_date, "end": end_date},
                "summary": {
                    "total_fishing_hours": 0,
                    "unique_vessels": 0,
                    "message": "No fishing activity detected in this period"
                }
            }
        
        # Process data using same analysis function
        analysis = analyze_fishing_data(df, mpa_name)
        
        # Add protected features
        protected_features = get_protected_features(mpa_name)
        
        # Add request metadata
        analysis["wdpa_code"] = wdpa_code
        analysis["date_range"] = {"start": start_date, "end": end_date}
        analysis["protected_features"] = protected_features
        analysis["status"] = "success"
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing MPA data: {e}")
        return {
            "status": "error",
            "error": str(e),
            "mpa_name": mpa_name,
            "wdpa_code": wdpa_code
        }

def analyze_fishing_data(df, mpa_name):
    """Process fishing data and generate analysis - from working script."""
    
    analysis = {
        "mpa_name": mpa_name,
        "total_records": len(df),
        "generated_at": datetime.now().isoformat(),
        "summary": {},
        "temporal": {},
        "gear_types": {},
        "vessels": {},
        "conservation_alerts": []
    }
    
    # Summary statistics
    total_hours = df['hours'].sum() if 'hours' in df.columns else 0
    unique_vessels = df['vessel_id'].nunique() if 'vessel_id' in df.columns else 0
    
    # Calculate trawling and dredging hours separately
    trawling_hours = 0
    dredging_hours = 0
    if 'gear_type' in df.columns and 'hours' in df.columns:
        # Separate trawling keywords (excluding dredge)
        trawling_keywords = ['trawl', 'trawler', 'bottom', 'otter', 'beam']
        trawling_df = df[df['gear_type'].str.lower().str.contains('|'.join(trawling_keywords), na=False)]
        trawling_hours = trawling_df['hours'].sum()
        
        # Separate dredging keywords
        dredging_keywords = ['dredge']
        dredging_df = df[df['gear_type'].str.lower().str.contains('|'.join(dredging_keywords), na=False)]
        dredging_hours = dredging_df['hours'].sum()
    
    # Calculate harmful fishing as sum of trawling and dredging
    harmful_fishing_hours = trawling_hours + dredging_hours
    harmful_fishing_percentage = (harmful_fishing_hours / total_hours * 100) if total_hours > 0 else 0
    
    analysis["summary"] = {
        "total_fishing_hours": round(float(total_hours), 2),
        "unique_vessels": int(unique_vessels),
        "harmful_fishing_hours": round(float(harmful_fishing_hours), 2),
        "harmful_fishing_percentage": round(float(harmful_fishing_percentage), 1),
        "trawling_hours": round(float(trawling_hours), 2),
        "dredging_hours": round(float(dredging_hours), 2)
    }
    
    # Monthly breakdown
    if 'date' in df.columns and 'hours' in df.columns:
        monthly_hours = df.groupby('date')['hours'].sum()
        analysis["temporal"]["monthly_hours"] = {
            str(date): round(float(hours), 2) 
            for date, hours in monthly_hours.items()
        }
        
        # Monthly breakdown by gear type for harmful fishing
        if 'gear_type' in df.columns:
            # Monthly trawling hours
            monthly_trawling = trawling_df.groupby('date')['hours'].sum() if not trawling_df.empty else pd.Series()
            analysis["temporal"]["monthly_trawling"] = {
                str(date): round(float(hours), 2) 
                for date, hours in monthly_trawling.items()
            }
            
            # Monthly dredging hours
            monthly_dredging = dredging_df.groupby('date')['hours'].sum() if not dredging_df.empty else pd.Series()
            analysis["temporal"]["monthly_dredging"] = {
                str(date): round(float(hours), 2) 
                for date, hours in monthly_dredging.items()
            }
        
        # Identify trends
        if len(monthly_hours) > 1:
            analysis["temporal"]["trend"] = "increasing" if monthly_hours.iloc[-1] > monthly_hours.iloc[0] else "decreasing"
    
    # Gear type analysis
    if 'gear_type' in df.columns:
        gear_stats = df.groupby('gear_type').agg({
            'hours': 'sum',
            'vessel_id': 'nunique'
        })
        
        analysis["gear_types"] = {
            str(gear): {
                "total_hours": round(float(gear_stats.loc[gear, 'hours']), 2),
                "vessel_count": int(gear_stats.loc[gear, 'vessel_id'])
            } for gear in gear_stats.index if pd.notna(gear)
        }
        
        # Check for harmful gear types
        harmful_gears = ['trawlers', 'dredge_fishing', 'bottom_trawl', 'beam_trawl']
        detected_harmful = [g for g in analysis["gear_types"].keys() 
                          if any(h in g.lower() for h in harmful_gears)]
        
        if detected_harmful:
            analysis["conservation_alerts"].append({
                "type": "harmful_gear",
                "severity": "high",
                "message": f"Harmful fishing methods detected: {', '.join(detected_harmful)}",
                "gear_types": detected_harmful
            })
    
    # Top vessels by activity with full details
    if 'vessel_id' in df.columns and 'hours' in df.columns:
        # Group by vessel to get aggregated data
        vessel_data = []
        
        for vessel_id in df['vessel_id'].unique():
            if pd.isna(vessel_id):
                continue
                
            vessel_df = df[df['vessel_id'] == vessel_id]
            
            # Get vessel details from the most recent record
            latest_record = vessel_df.iloc[0]
            
            # Calculate total hours and primary gear type
            total_hours = vessel_df['hours'].sum()
            
            # Get primary gear type (most used)
            if 'gear_type' in vessel_df.columns:
                gear_counts = vessel_df['gear_type'].value_counts()
                primary_gear = gear_counts.index[0] if len(gear_counts) > 0 else 'UNKNOWN'
            else:
                primary_gear = 'UNKNOWN'
            
            vessel_info = {
                "vessel_id": str(vessel_id),
                "ship_name": str(latest_record.get('ship_name', 'Unknown Vessel')) if 'ship_name' in latest_record else 'Unknown Vessel',
                "flag": str(latest_record.get('flag', 'UNK')) if 'flag' in latest_record else 'UNK',
                "mmsi": str(latest_record.get('mmsi', '')) if 'mmsi' in latest_record else '',
                "primary_gear_type": primary_gear,
                "fishing_hours": round(float(total_hours), 2)
            }
            
            vessel_data.append(vessel_info)
        
        # Sort by fishing hours and return all vessels
        vessel_data.sort(key=lambda x: x['fishing_hours'], reverse=True)
        
        # Enrich vessels with length data from Vessels API
        vessel_data = enrich_vessels_with_details(vessel_data)
        
        analysis["vessels"]["most_active"] = vessel_data  # Return all vessels
    
    # Flag state analysis
    if 'flag' in df.columns:
        flag_counts = df['flag'].value_counts()
        analysis["vessels"]["flag_states"] = {
            str(flag): int(count) 
            for flag, count in flag_counts.items() if pd.notna(flag)
        }
    
    return analysis

@app.route('/api/mpa_list')
def get_mpa_list():
    """Return list of MPAs for search/autocomplete."""
    mpas = load_uk_mpas()
    return jsonify(mpas)

@app.route('/api/export_csv', methods=['POST'])
def export_csv():
    """Export analysis results as CSV."""
    data = request.json
    
    # Create CSV in memory
    output = io.StringIO()
    
    # Summary section
    output.write(f"MPA Fishing Activity Analysis Report\n")
    output.write(f"MPA Name,{data.get('mpa_name', '')}\n")
    output.write(f"WDPA Code,{data.get('wdpa_code', '')}\n")
    output.write(f"Analysis Date,{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    output.write(f"Date Range,{data['date_range']['start']} to {data['date_range']['end']}\n")
    output.write(f"\n")
    
    # Protected Features
    if data.get('protected_features'):
        output.write(f"Protected Features\n")
        for feature in data['protected_features']:
            output.write(f",{feature}\n")
        output.write(f"\n")
    
    # Summary Statistics
    summary = data.get('summary', {})
    output.write(f"Summary Statistics\n")
    output.write(f"Total Fishing Hours,{summary.get('total_fishing_hours', 0)}\n")
    output.write(f"Unique Vessels,{summary.get('unique_vessels', 0)}\n")
    output.write(f"Harmful Fishing Hours (Trawling + Dredging),{summary.get('harmful_fishing_hours', 0)}\n")
    output.write(f"Harmful Fishing Percentage,{summary.get('harmful_fishing_percentage', 0)}%\n")
    output.write(f"Trawling Hours,{summary.get('trawling_hours', 0)}\n")
    output.write(f"Dredging Hours,{summary.get('dredging_hours', 0)}\n")
    output.write(f"\n")
    
    # Vessel Details
    vessels = data.get('vessels', {}).get('most_active', [])
    if vessels:
        output.write(f"Most Active Vessels\n")
        output.write(f"Rank,Vessel Name,Flag,Length (m),Fishing Hours,Primary Gear,MMSI\n")
        for i, vessel in enumerate(vessels, 1):
            length = vessel.get('length', '')
            length_str = f"{length:.1f}" if length else "N/A"
            output.write(f"{i},{vessel.get('ship_name', 'Unknown')},{vessel.get('flag', 'UNK')},{length_str},")
            output.write(f"{vessel.get('fishing_hours', 0)},{vessel.get('primary_gear_type', 'UNKNOWN')},")
            output.write(f"{vessel.get('mmsi', '')}\n")
    
    # Create response
    csv_data = output.getvalue()
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename=MPA_Analysis_{data.get('mpa_name', 'Unknown').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-Type"] = "text/csv"
    
    return response

@app.route('/api/export_pdf', methods=['POST'])
def export_pdf():
    """Export analysis results as PDF."""
    data = request.json
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=30,
        alignment=1  # Center
    )
    elements.append(Paragraph("MPA Fishing Activity Analysis Report", title_style))
    
    # ZME Science branding
    try:
        logo_path = os.path.join(app.static_folder, 'logo-zmescience.png')
        if os.path.exists(logo_path):
            # ZME Science logo is 2406x261 pixels (aspect ratio ~9.2:1)
            # Calculate proportional height for 2 inch width
            logo_width = 2*inch
            logo_height = logo_width * (261/2406)  # Maintain original aspect ratio
            logo = Image(logo_path, width=logo_width, height=logo_height)
            logo.hAlign = 'CENTER'
            elements.append(logo)
        
        branding_style = ParagraphStyle(
            'Branding',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#0066cc'),
            alignment=1,  # Center
            spaceAfter=10
        )
        elements.append(Paragraph('Created by <a href="https://zmescience.com" color="#0066cc">ZME Science</a>', branding_style))
        elements.append(Paragraph('Report generated on ukmpas.zmescience.com', branding_style))
    except Exception as e:
        print(f"Warning: Could not add logo: {e}")
    
    elements.append(Spacer(1, 20))
    
    # MPA Information
    info_style = styles['Normal']
    elements.append(Paragraph(f"<b>MPA Name:</b> {data.get('mpa_name', '')}", info_style))
    elements.append(Paragraph(f"<b>WDPA Code:</b> {data.get('wdpa_code', '')}", info_style))
    elements.append(Paragraph(f"<b>Analysis Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", info_style))
    elements.append(Paragraph(f"<b>Date Range:</b> {data['date_range']['start']} to {data['date_range']['end']}", info_style))
    elements.append(Spacer(1, 20))
    
    # Protected Features
    if data.get('protected_features'):
        elements.append(Paragraph("<b>Protected Features:</b>", styles['Heading2']))
        for feature in data['protected_features']:
            elements.append(Paragraph(f"• {feature}", info_style))
        elements.append(Spacer(1, 20))
    
    # Summary Statistics
    summary = data.get('summary', {})
    elements.append(Paragraph("<b>Summary Statistics</b>", styles['Heading2']))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Fishing Hours', f"{summary.get('total_fishing_hours', 0):.1f}"],
        ['Unique Vessels', str(summary.get('unique_vessels', 0))],
        ['Harmful Fishing Hours (Trawling + Dredging)', f"{summary.get('harmful_fishing_hours', 0):.1f}"],
        ['Harmful Fishing Percentage', f"{summary.get('harmful_fishing_percentage', 0):.1f}%"],
        ['Trawling Hours', f"{summary.get('trawling_hours', 0):.1f}"],
        ['Dredging Hours', f"{summary.get('dredging_hours', 0):.1f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Most Active Vessels
    vessels = data.get('vessels', {}).get('most_active', [])
    if vessels:
        elements.append(Paragraph("<b>Most Active Vessels</b>", styles['Heading2']))
        
        vessel_data = [['Rank', 'Vessel Name', 'Flag', 'Hours', 'Gear Type', 'MMSI']]
        for i, vessel in enumerate(vessels[:10], 1):  # Show top 10 in PDF
            vessel_data.append([
                str(i),
                vessel.get('ship_name', 'Unknown'),
                vessel.get('flag', 'UNK'),
                f"{vessel.get('fishing_hours', 0):.1f}",
                vessel.get('primary_gear_type', 'UNKNOWN').replace('_', ' '),
                vessel.get('mmsi', '-')
            ])
        
        vessel_table = Table(vessel_data, colWidths=[0.5*inch, 2*inch, 0.7*inch, 0.7*inch, 1.5*inch, 1*inch])
        vessel_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(vessel_table)
    
    # Data Limitations and Attribution
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b>Data Limitations and Attribution</b>", styles['Heading2']))
    
    limitations_style = ParagraphStyle(
        'Limitations',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=6,
        leftIndent=12
    )
    
    limitations = [
        "• Data only includes vessels with AIS (Automatic Identification System) transponders",
        "• Small vessels (<15m) often lack AIS and are not captured in this analysis",
        "• Some fishing activity may be misclassified as non-fishing and vice versa",
        "• Vessel gear types are derived from registries and may not reflect actual gear used",
        "• Data quality varies by region and time period",
        "• 'Harmful fishing' refers to trawling and dredging activities that impact seafloor habitats",
        "• 'Apparent fishing' represents vessel behavior patterns indicating likely fishing activity"
    ]
    
    for limitation in limitations:
        elements.append(Paragraph(limitation, limitations_style))
    
    elements.append(Spacer(1, 15))
    
    attribution_style = ParagraphStyle(
        'Attribution',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=1  # Center
    )
    
    elements.append(Paragraph(
        'Data sourced from <a href="https://globalfishingwatch.org" color="#0066cc">Global Fishing Watch</a>. '
        'Fishing activity data represents apparent fishing as defined by GFW methodology.',
        attribution_style
    ))
    
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        'This report was generated using the UK MPA Fishing Activity Analysis tool at '
        '<a href="https://ukmpas.zmescience.com" color="#0066cc">ukmpas.zmescience.com</a>',
        attribution_style
    ))
    
    # Build PDF
    doc.build(elements)
    
    # Create response
    pdf_data = buffer.getvalue()
    buffer.close()
    
    response = make_response(pdf_data)
    response.headers["Content-Disposition"] = f"attachment; filename=MPA_Analysis_{data.get('mpa_name', 'Unknown').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    response.headers["Content-Type"] = "application/pdf"
    
    return response

if __name__ == '__main__':
    import os
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)