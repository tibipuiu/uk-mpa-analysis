# MPA Web Application - Technical Documentation

## Overview
This is the main Flask web application that provides an interactive interface for analyzing fishing activity in UK Marine Protected Areas using Global Fishing Watch data.

## Architecture

### Backend (`app.py`)

#### Key Components:

1. **Flask Application**
   - RESTful API design
   - Async support for GFW API calls
   - CORS-enabled for frontend integration

2. **Global Fishing Watch Integration**
   ```python
   ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtpZEtleSJ9..."
   client = gfw.Client(access_token=ACCESS_TOKEN)
   ```

3. **Core Functions**:
   - `load_uk_mpas()`: Loads MPA data from CSV, handles WDPA code formatting
   - `get_protected_features(mpa_name)`: Retrieves conservation features for MPAs
   - `analyze_mpa_fishing()`: Async function querying GFW 4Wings API
   - `analyze_fishing_data()`: Processes raw data into structured analysis

4. **API Endpoints**:
   - `GET /` - Main application page
   - `GET /api/mpa_list` - Returns all UK MPAs for search
   - `POST /api/analyze_mpa` - Main analysis endpoint
   - `POST /api/export_csv` - CSV export generation
   - `POST /api/export_pdf` - PDF report generation

#### Data Processing Pipeline:
```
User Request → GFW API Query → DataFrame Processing → 
Analysis Generation → JSON Response → Frontend Display
```

#### Key Analysis Metrics:
- Total fishing hours
- Unique vessel count
- Trawling hours and percentage
- Vessel rankings by activity
- Gear type distribution
- Monthly activity trends

### Frontend Architecture

#### HTML Structure (`templates/index.html`)
- Search section with autocomplete
- Results section with:
  - Protected features display
  - Summary cards
  - Interactive charts
  - Vessel activity table
  - Download buttons

#### JavaScript (`static/js/app.js`)

**State Management**:
```javascript
let selectedMPA = null;          // Currently selected MPA
let monthlyChart = null;         // Chart.js instance
let gearChart = null;           // Chart.js instance
let allVessels = [];            // All vessel data
let displayedVessels = 10;      // Progressive loading count
let currentAnalysisData = null; // For exports
```

**Key Functions**:
- `setupMPASearch()`: Implements autocomplete with dropdown
- `analyzeMPA()`: Handles API calls and loading states
- `displayResults()`: Orchestrates result rendering
- `updateVesselsTable()`: Progressive vessel loading
- `downloadCSV/PDF()`: Export functionality

**Chart Configuration**:
- Monthly activity: Line chart with temporal trends
- Gear types: Doughnut chart with harmful gear highlighting

#### Styling (`static/css/style.css`)

**Design System**:
- Primary color: `#0066cc` (blue)
- Danger color: `#dc3545` (red for harmful practices)
- Card-based layout with shadows
- Responsive grid system

**Key Components**:
- `.summary-cards`: Metric display grid
- `.features-section`: Protected features tags
- `.chart-container`: Fixed height chart wrappers
- `.flag-badge`: Country code styling
- `.harmful-gear`: Red highlighting for trawling

## Data Flow

1. **MPA Selection**:
   ```
   User types → Autocomplete filters → MPA selected → 
   WDPA code retrieved
   ```

2. **Analysis Request**:
   ```
   Date range + MPA → API call → GFW 4Wings query → 
   Raw vessel data → Processing → Structured JSON
   ```

3. **Progressive Loading**:
   ```
   Initial 10 vessels → User clicks "Load More" → 
   Next 10 vessels → Update UI
   ```

## Export Functionality

### CSV Export
- Structured format with sections
- All vessel data included
- Comma-separated with headers

### PDF Export  
- ReportLab library
- Professional formatting
- Tables for summary and vessels
- A4 page size with margins

## Performance Considerations

1. **API Optimization**:
   - Single API call per analysis
   - Efficient region-based queries
   - Monthly temporal resolution

2. **Frontend Optimization**:
   - Progressive vessel loading
   - Chart.js for efficient rendering
   - Minimal DOM manipulation

3. **Data Processing**:
   - Pandas for efficient DataFrame operations
   - Aggregation at database level
   - Client-side caching of analysis data

## Security

- API token stored server-side
- Input validation for all parameters
- Safe string formatting for exports
- XSS protection through proper escaping

## Error Handling

- Try-catch blocks for API calls
- User-friendly error messages
- Graceful degradation for missing data
- Console logging for debugging

## Future Enhancements

1. **Caching Layer**: Redis for API response caching
2. **WebSocket Support**: Real-time updates
3. **Advanced Filtering**: By gear type, flag, date
4. **Batch Analysis**: Multiple MPAs comparison
5. **Historical Trends**: Year-over-year analysis

## Dependencies

- **Backend**: Flask, pandas, gfwapiclient, reportlab
- **Frontend**: Chart.js, vanilla JavaScript
- **Styling**: Custom CSS, responsive design

## Testing Checklist

- [ ] MPA search autocomplete
- [ ] Date range selection
- [ ] API connectivity
- [ ] Data processing accuracy
- [ ] Chart rendering
- [ ] Progressive loading
- [ ] CSV export
- [ ] PDF export
- [ ] Error states
- [ ] Mobile responsiveness