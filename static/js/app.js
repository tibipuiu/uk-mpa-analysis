// UK MPA Fishing Analysis App

let selectedMPA = null;
let monthlyChart = null;
let gearChart = null;
let allVessels = [];
let displayedVessels = 10;
let currentAnalysisData = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    setupMPASearch();
    setupDateInputs();
    setupPresetButtons();
    setupAnalyzeButton();
    setupDownloadButtons();
    setupDateValidation();
});

// Setup MPA search with dropdown
function setupMPASearch() {
    const searchInput = document.getElementById('mpa-search');
    const dropdown = document.getElementById('mpa-dropdown');
    const browseBtn = document.getElementById('browse-all-btn');
    
    let currentPage = 0;
    const itemsPerPage = 15;
    let browseMode = false;
    let allMPAsDisplayed = [];
    
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        browseMode = false;
        
        if (searchTerm.length < 2) {
            dropdown.style.display = 'none';
            return;
        }
        
        // Filter MPAs
        const filtered = mpas.filter(mpa => 
            mpa.Site_Name.toLowerCase().includes(searchTerm)
        ).slice(0, 10); // Limit to 10 results
        
        displayMPAItems(filtered, false);
    });
    
    // Browse all MPAs functionality
    browseBtn.addEventListener('click', function() {
        browseMode = true;
        currentPage = 0;
        searchInput.value = '';
        showAllMPAs();
    });
    
    function showAllMPAs() {
        // Sort MPAs alphabetically
        const sortedMPAs = [...mpas].sort((a, b) => a.Site_Name.localeCompare(b.Site_Name));
        const startIndex = 0;
        const endIndex = (currentPage + 1) * itemsPerPage;
        const pageItems = sortedMPAs.slice(startIndex, endIndex);
        
        allMPAsDisplayed = pageItems;
        displayMPAItems(pageItems, true, endIndex < sortedMPAs.length);
    }
    
    function displayMPAItems(items, showPagination = false, hasMore = false) {
        dropdown.innerHTML = '';
        dropdown.style.display = items.length > 0 ? 'block' : 'none';
        
        if (browseMode && items.length === 0) {
            dropdown.innerHTML = '<div class="dropdown-item">No MPAs found</div>';
            dropdown.style.display = 'block';
            return;
        }
        
        // Add search within results for browse mode
        if (browseMode && items.length > 0) {
            const searchWithin = document.createElement('div');
            searchWithin.className = 'dropdown-search';
            searchWithin.innerHTML = `
                <input type="text" id="browse-search" placeholder="Search within results..." class="browse-search-input">
                <div class="browse-info">${mpas.length} total MPAs</div>
            `;
            dropdown.appendChild(searchWithin);
            
            document.getElementById('browse-search').addEventListener('input', function(e) {
                const searchTerm = e.target.value.toLowerCase();
                if (searchTerm.length === 0) {
                    showAllMPAs();
                    return;
                }
                const filtered = mpas.filter(mpa => 
                    mpa.Site_Name.toLowerCase().includes(searchTerm)
                ).slice(0, 20);
                displayMPAItems(filtered, false);
            });
        }
        
        items.forEach(mpa => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.innerHTML = `
                <strong>${mpa.Site_Name}</strong><br>
                <small>WDPA: ${mpa.WDPA_Code} | Area: ${Math.round(mpa.Area_ha)} ha</small>
            `;
            
            item.addEventListener('click', function() {
                selectMPA(mpa);
            });
            
            dropdown.appendChild(item);
        });
        
        // Add pagination controls for browse mode
        if (showPagination && hasMore) {
            const loadMore = document.createElement('div');
            loadMore.className = 'dropdown-item load-more';
            loadMore.innerHTML = '<strong>📄 Load More MPAs...</strong>';
            loadMore.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                currentPage++;
                showAllMPAs();
            });
            dropdown.appendChild(loadMore);
        }
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.form-group')) {
            dropdown.style.display = 'none';
            browseMode = false;
        }
    });
}

// Select MPA
function selectMPA(mpa) {
    selectedMPA = mpa;
    document.getElementById('mpa-search').value = mpa.Site_Name;
    document.getElementById('mpa-dropdown').style.display = 'none';
}

// Setup date inputs with defaults
function setupDateInputs() {
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
    document.getElementById('end-date').value = new Date().toISOString().split('T')[0];
    
    // Set default preset button as active
    document.querySelector('.preset-chip[data-days="30"]').classList.add('active');
    updateDateInfo();
}

// Setup preset date range buttons
function setupPresetButtons() {
    const presetButtons = document.querySelectorAll('.preset-chip');
    
    presetButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            presetButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Calculate date range
            const days = parseInt(this.dataset.days);
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - days);
            
            // Update inputs
            document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
            document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
            
            // Update info display
            updateDateInfo();
        });
    });
}

// Setup date validation
function setupDateValidation() {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    
    // Add event listeners for manual date changes
    [startDateInput, endDateInput].forEach(input => {
        input.addEventListener('change', function() {
            // Clear active preset button when manually changing dates
            document.querySelectorAll('.preset-chip').forEach(btn => btn.classList.remove('active'));
            updateDateInfo();
        });
    });
}

// Update date info display
function updateDateInfo() {
    const startDate = new Date(document.getElementById('start-date').value);
    const endDate = new Date(document.getElementById('end-date').value);
    const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
    
    // Update selected range text
    const selectedRangeElement = document.getElementById('selected-range');
    const estimatedTimeElement = document.getElementById('estimated-time');
    const dateWarningElement = document.getElementById('date-warning');
    
    if (daysDiff <= 0) {
        selectedRangeElement.textContent = 'Invalid date range';
        estimatedTimeElement.textContent = 'N/A';
        dateWarningElement.style.display = 'none';
        return;
    }
    
    // Format date range
    const formatDate = (date) => date.toLocaleDateString('en-GB', { 
        day: 'numeric', month: 'short', year: 'numeric' 
    });
    selectedRangeElement.textContent = `${formatDate(startDate)} - ${formatDate(endDate)} (${daysDiff} days)`;
    
    // Show warning for multi-year queries
    if (daysDiff > 365) {
        dateWarningElement.style.display = 'block';
        const years = Math.ceil(daysDiff / 365);
        estimatedTimeElement.textContent = `~${years * 10}-${years * 20} seconds (${years} API calls)`;
    } else {
        dateWarningElement.style.display = 'none';
        if (daysDiff <= 30) {
            estimatedTimeElement.textContent = '~5-10 seconds';
        } else if (daysDiff <= 90) {
            estimatedTimeElement.textContent = '~8-15 seconds';
        } else {
            estimatedTimeElement.textContent = '~10-20 seconds';
        }
    }
}

// Setup analyze button
function setupAnalyzeButton() {
    document.getElementById('analyze-btn').addEventListener('click', analyzeMPA);
}

// Analyze MPA fishing activity
async function analyzeMPA() {
    if (!selectedMPA) {
        alert('Please select an MPA first');
        return;
    }
    
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    if (!startDate || !endDate) {
        alert('Please select both start and end dates');
        return;
    }
    
    // Show loading and hide app description
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    
    // Hide the app description section when analysis starts
    const appDescription = document.querySelector('.app-description');
    if (appDescription) {
        appDescription.style.display = 'none';
    }
    
    try {
        const response = await fetch('/api/analyze_mpa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mpa_name: selectedMPA.Site_Name,
                wdpa_code: selectedMPA.WDPA_Code,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            currentAnalysisData = data; // Store for downloads
            displayResults(data);
        } else {
            alert('Error: ' + (data.error || 'Unknown error occurred'));
        }
    } catch (error) {
        alert('Error analyzing MPA: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Display protected features
function displayProtectedFeatures(features) {
    const featuresSection = document.getElementById('protected-features');
    const featuresList = document.getElementById('features-list');
    
    if (!features || features.length === 0) {
        featuresSection.style.display = 'none';
        return;
    }
    
    featuresSection.style.display = 'block';
    featuresList.innerHTML = '';
    
    features.forEach(feature => {
        const tag = document.createElement('div');
        tag.className = 'feature-tag';
        tag.textContent = feature;
        featuresList.appendChild(tag);
    });
}

// Display analysis results
function displayResults(data) {
    // Show results section
    document.getElementById('results').style.display = 'block';
    
    // Update title
    document.getElementById('results-title').textContent = 
        `Fishing Activity Analysis: ${data.mpa_name}`;
    
    // Display protected features
    displayProtectedFeatures(data.protected_features);
    
    // Update summary metrics
    document.getElementById('total-hours').textContent = 
        data.summary.total_fishing_hours.toFixed(1);
    document.getElementById('unique-vessels').textContent = 
        data.summary.unique_vessels;
    
    // Update harmful fishing metric with percentage (trawling + dredging)
    const harmfulFishingElement = document.getElementById('harmful-fishing-hours');
    harmfulFishingElement.innerHTML = `${data.summary.harmful_fishing_hours.toFixed(1)} <span style="font-size: 20px; font-weight: normal;">(${data.summary.harmful_fishing_percentage.toFixed(1)}%)</span>`;
    
    // Display multi-year analysis if available
    displayMultiYearAnalysis(data.multi_year);
    
    // Update charts
    updateMonthlyChart(data.temporal);
    updateGearChart(data.gear_types);
    
    // Update tables
    updateVesselsTable(data.vessels);
    
    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

// Display multi-year analysis
function displayMultiYearAnalysis(multiYearData) {
    const multiYearSection = document.getElementById('multi-year-section');
    
    // Safe check - only show if multiYearData exists and has meaningful content
    if (!multiYearData || 
        typeof multiYearData !== 'object' || 
        !multiYearData.total_years || 
        multiYearData.total_years <= 1) {
        multiYearSection.style.display = 'none';
        return;
    }
    
    multiYearSection.style.display = 'block';
    
    // Update summary cards with safe property access
    const totalYearsElement = document.getElementById('total-years');
    if (totalYearsElement && multiYearData.total_years) {
        totalYearsElement.textContent = `${multiYearData.total_years.toFixed(1)} years`;
    }
    
    // Trend direction with safe property access
    const trendElement = document.getElementById('trend-direction');
    if (trendElement) {
        if (multiYearData.trend_analysis && multiYearData.trend_analysis.trend_direction) {
            const direction = multiYearData.trend_analysis.trend_direction;
            const strength = multiYearData.trend_analysis.trend_strength || '';
            
            let trendIcon = '→';
            let trendClass = 'trend-stable';
            
            if (direction === 'increasing') {
                trendIcon = '↗️';
                trendClass = 'trend-increasing';
            } else if (direction === 'decreasing') {
                trendIcon = '↘️';
                trendClass = 'trend-decreasing';
            }
            
            trendElement.innerHTML = `<span class="trend-indicator ${trendClass}">${trendIcon}</span> ${direction}`;
            
            if (strength) {
                trendElement.innerHTML += ` <small>(${strength})</small>`;
            }
        } else {
            trendElement.textContent = 'Insufficient data';
        }
    }
    
    // Peak season with safe property access
    const peakSeasonElement = document.getElementById('peak-season');
    if (peakSeasonElement) {
        if (multiYearData.seasonal_patterns && multiYearData.seasonal_patterns.peak_month) {
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const peakMonth = monthNames[multiYearData.seasonal_patterns.peak_month - 1];
            peakSeasonElement.textContent = peakMonth || 'N/A';
        } else {
            peakSeasonElement.textContent = 'N/A';
        }
    }
    
    // Yearly breakdown with safe property access
    const yearlyBreakdown = document.getElementById('yearly-breakdown');
    if (yearlyBreakdown) {
        yearlyBreakdown.innerHTML = '';
        
        if (multiYearData.yearly_summary && typeof multiYearData.yearly_summary === 'object') {
            const years = Object.keys(multiYearData.yearly_summary).sort();
            
            years.forEach(year => {
                const yearData = multiYearData.yearly_summary[year];
                if (yearData && yearData.total_hours !== undefined && yearData.unique_vessels !== undefined) {
                    const yearItem = document.createElement('div');
                    yearItem.className = 'yearly-breakdown-item';
                    
                    yearItem.innerHTML = `
                        <div class="year-label">${year}</div>
                        <div class="year-stats">
                            <span>${yearData.total_hours.toFixed(1)} hours</span>
                            <span>${yearData.unique_vessels} vessels</span>
                        </div>
                    `;
                    
                    yearlyBreakdown.appendChild(yearItem);
                }
            });
        }
    }
}


// Update monthly activity chart
function updateMonthlyChart(temporalData) {
    const ctx = document.getElementById('monthly-chart').getContext('2d');
    
    if (monthlyChart) {
        monthlyChart.destroy();
    }
    
    if (!temporalData || !temporalData.monthly_hours) {
        ctx.canvas.parentElement.innerHTML = '<p>No temporal data available</p>';
        return;
    }
    
    const labels = Object.keys(temporalData.monthly_hours);
    const totalValues = Object.values(temporalData.monthly_hours);
    
    // Prepare datasets
    const datasets = [{
        label: 'Total Fishing Hours',
        data: totalValues,
        borderColor: '#0066cc',
        backgroundColor: 'rgba(0, 102, 204, 0.1)',
        tension: 0.1,
        fill: false
    }];
    
    // Add trawling data if available
    if (temporalData.monthly_trawling && Object.keys(temporalData.monthly_trawling).length > 0) {
        const trawlingValues = labels.map(date => temporalData.monthly_trawling[date] || 0);
        datasets.push({
            label: 'Trawling Hours',
            data: trawlingValues,
            borderColor: '#dc3545',
            backgroundColor: 'rgba(220, 53, 69, 0.1)',
            tension: 0.1,
            fill: false
        });
    }
    
    // Add dredging data if available
    if (temporalData.monthly_dredging && Object.keys(temporalData.monthly_dredging).length > 0) {
        const dredgingValues = labels.map(date => temporalData.monthly_dredging[date] || 0);
        datasets.push({
            label: 'Dredging Hours',
            data: dredgingValues,
            borderColor: '#ff6b35',
            backgroundColor: 'rgba(255, 107, 53, 0.1)',
            tension: 0.1,
            fill: false
        });
    }
    
    monthlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.map(date => new Date(date).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Fishing Hours'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Update gear type chart
function updateGearChart(gearData) {
    const ctx = document.getElementById('gear-chart').getContext('2d');
    
    if (gearChart) {
        gearChart.destroy();
    }
    
    if (!gearData || Object.keys(gearData).length === 0) {
        ctx.canvas.parentElement.innerHTML = '<p>No gear type data available</p>';
        return;
    }
    
    const labels = Object.keys(gearData);
    const values = labels.map(gear => gearData[gear].total_hours);
    
    // Color harmful gear types in red
    // Separate trawling and dredging gear types
    const trawlingGears = ['trawlers', 'bottom_trawl', 'beam_trawl', 'trawl'];
    const dredgingGears = ['dredge_fishing', 'dredge'];
    const colors = labels.map(gear => {
        const gearLower = gear.toLowerCase();
        if (trawlingGears.some(h => gearLower.includes(h))) {
            return '#dc3545'; // Red for trawling
        } else if (dredgingGears.some(h => gearLower.includes(h))) {
            return '#ff6b35'; // Orange-red for dredging
        } else {
            return '#0066cc'; // Blue for other gear types
        }
    });
    
    gearChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const gear = context.label;
                            const hours = context.parsed;
                            const vessels = gearData[gear].vessel_count;
                            return `${gear}: ${hours.toFixed(1)} hours (${vessels} vessels)`;
                        }
                    }
                }
            }
        }
    });
}

// Get flag display for country codes
function getFlagEmoji(countryCode) {
    // Using country codes with styled display instead of emojis
    // which may not render properly in all browsers
    return countryCode || 'UNK';
}

// Update vessels table
function updateVesselsTable(vesselsData) {
    const tbody = document.querySelector('#vessels-table tbody');
    tbody.innerHTML = '';
    
    if (!vesselsData || !vesselsData.most_active || vesselsData.most_active.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No vessel data available</td></tr>';
        document.getElementById('load-more-container').style.display = 'none';
        return;
    }
    
    // Store all vessels
    allVessels = vesselsData.most_active;
    displayedVessels = 10; // Reset to initial display count
    
    // Display initial vessels
    const vesselsToShow = allVessels.slice(0, displayedVessels);
    vesselsToShow.forEach((vessel, index) => {
        const row = tbody.insertRow();
        
        // Rank
        const rankCell = row.insertCell(0);
        rankCell.innerHTML = `<strong>${index + 1}</strong>`;
        rankCell.style.textAlign = 'center';
        
        // Vessel name cell with bold styling
        const nameCell = row.insertCell(1);
        nameCell.innerHTML = `<strong>${vessel.ship_name || 'Unknown Vessel'}</strong>`;
        
        // Flag as styled badge
        const flagCell = row.insertCell(2);
        const flagCode = vessel.flag || 'UNK';
        flagCell.innerHTML = `<span class="flag-badge">${flagCode}</span>`;
        
        // Hours
        const hoursCell = row.insertCell(3);
        hoursCell.textContent = vessel.fishing_hours.toFixed(1);
        hoursCell.style.textAlign = 'center';
        
        // Gear type with trawling/dredging highlighting and formatting
        const gearCell = row.insertCell(4);
        const gearType = vessel.primary_gear_type || 'UNKNOWN';
        // Format gear type: replace underscores with spaces and capitalize properly
        const formattedGear = gearType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        const trawlingGears = ['trawlers', 'bottom_trawl', 'beam_trawl', 'trawl'];
        const dredgingGears = ['dredge_fishing', 'dredge'];
        const gearLower = gearType.toLowerCase();
        
        const isTrawling = trawlingGears.some(h => gearLower.includes(h));
        const isDredging = dredgingGears.some(h => gearLower.includes(h));
        
        if (isTrawling) {
            gearCell.innerHTML = `<span class="trawling-gear"><strong>${formattedGear}</strong></span>`;
        } else if (isDredging) {
            gearCell.innerHTML = `<span class="dredging-gear"><strong>${formattedGear}</strong></span>`;
        } else {
            gearCell.textContent = formattedGear;
        }
        
        // MMSI
        row.insertCell(5).textContent = vessel.mmsi || '-';
    });
    
    // Show/hide load more button
    const loadMoreContainer = document.getElementById('load-more-container');
    const vesselsInfo = document.getElementById('vessels-info');
    
    if (allVessels.length > displayedVessels) {
        loadMoreContainer.style.display = 'block';
        vesselsInfo.textContent = `Showing ${displayedVessels} of ${allVessels.length} vessels`;
        
        // Setup load more button if not already done
        const loadMoreBtn = document.getElementById('load-more-btn');
        loadMoreBtn.onclick = loadMoreVessels;
    } else {
        loadMoreContainer.style.display = 'none';
    }
}

// Load more vessels function
function loadMoreVessels() {
    const tbody = document.querySelector('#vessels-table tbody');
    const startIndex = displayedVessels;
    const endIndex = Math.min(displayedVessels + 10, allVessels.length);
    
    // Add next batch of vessels
    for (let i = startIndex; i < endIndex; i++) {
        const vessel = allVessels[i];
        const row = tbody.insertRow();
        
        // Rank
        const rankCell = row.insertCell(0);
        rankCell.innerHTML = `<strong>${i + 1}</strong>`;
        rankCell.style.textAlign = 'center';
        
        // Vessel name
        const nameCell = row.insertCell(1);
        nameCell.innerHTML = `<strong>${vessel.ship_name || 'Unknown Vessel'}</strong>`;
        
        // Flag
        const flagCell = row.insertCell(2);
        const flagCode = vessel.flag || 'UNK';
        flagCell.innerHTML = `<span class="flag-badge">${flagCode}</span>`;
        
        // Hours
        const hoursCell = row.insertCell(3);
        hoursCell.textContent = vessel.fishing_hours.toFixed(1);
        hoursCell.style.textAlign = 'center';
        
        // Gear type with trawling/dredging highlighting
        const gearCell = row.insertCell(4);
        const gearType = vessel.primary_gear_type || 'UNKNOWN';
        const formattedGear = gearType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        const trawlingGears = ['trawlers', 'bottom_trawl', 'beam_trawl', 'trawl'];
        const dredgingGears = ['dredge_fishing', 'dredge'];
        const gearLower = gearType.toLowerCase();
        
        const isTrawling = trawlingGears.some(h => gearLower.includes(h));
        const isDredging = dredgingGears.some(h => gearLower.includes(h));
        
        if (isTrawling) {
            gearCell.innerHTML = `<span class="trawling-gear"><strong>${formattedGear}</strong></span>`;
        } else if (isDredging) {
            gearCell.innerHTML = `<span class="dredging-gear"><strong>${formattedGear}</strong></span>`;
        } else {
            gearCell.textContent = formattedGear;
        }
        
        // MMSI
        row.insertCell(5).textContent = vessel.mmsi || '-';
    }
    
    displayedVessels = endIndex;
    
    // Update info and hide button if all vessels shown
    const vesselsInfo = document.getElementById('vessels-info');
    vesselsInfo.textContent = `Showing ${displayedVessels} of ${allVessels.length} vessels`;
    
    if (displayedVessels >= allVessels.length) {
        document.getElementById('load-more-btn').style.display = 'none';
        vesselsInfo.textContent = `Showing all ${allVessels.length} vessels`;
    }
}

// Update flags table
function updateFlagsTable(vesselsData) {
    const tbody = document.querySelector('#flags-table tbody');
    tbody.innerHTML = '';
    
    if (!vesselsData || !vesselsData.flag_states || Object.keys(vesselsData.flag_states).length === 0) {
        tbody.innerHTML = '<tr><td colspan="2">No flag data available</td></tr>';
        return;
    }
    
    Object.entries(vesselsData.flag_states)
        .sort((a, b) => b[1] - a[1])
        .forEach(([flag, count]) => {
            const row = tbody.insertRow();
            row.insertCell(0).textContent = flag;
            row.insertCell(1).textContent = count;
        });
}

// Setup download buttons
function setupDownloadButtons() {
    document.getElementById('download-csv').addEventListener('click', downloadCSV);
    document.getElementById('download-pdf').addEventListener('click', downloadPDF);
}

// Download as CSV
async function downloadCSV() {
    if (!currentAnalysisData) {
        alert('No analysis data available to download');
        return;
    }
    
    try {
        const response = await fetch('/api/export_csv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(currentAnalysisData)
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `MPA_Analysis_${currentAnalysisData.mpa_name.replace(/ /g, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            alert('Error downloading CSV file');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Download as PDF
async function downloadPDF() {
    if (!currentAnalysisData) {
        alert('No analysis data available to download');
        return;
    }
    
    try {
        const response = await fetch('/api/export_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(currentAnalysisData)
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `MPA_Analysis_${currentAnalysisData.mpa_name.replace(/ /g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            alert('Error downloading PDF file');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}