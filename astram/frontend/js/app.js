// ============================================
// ASTRAM AI - Complete 3-Page Application
// ============================================

let mainMap = null;
let cityData = null;
let corridorData = null;
let riskData = null;
let incidentMarkers = [];
let corridorLayers = [];

// ============================================
// 1. INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initializeSidebarNavigation();
    initializeMap();
    loadAllData();
    initializeAIPredictor();
});

// ============================================
// 2. SIDEBAR NAVIGATION
// ============================================

function initializeSidebarNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = link.dataset.page;
            switchPage(targetPage);

            // Update active state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
}

function switchPage(pageName) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));

    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');

        // Special handling for different pages
        if (pageName === 'overview' && mainMap) {
            setTimeout(() => mainMap.invalidateSize(), 100);
        } else if (pageName === 'intelligence') {
            renderIntelligenceCharts();
        }
    }
}

// ============================================
// 3. MAP INITIALIZATION (PAGE 1)
// ============================================

function initializeMap() {
    mainMap = L.map('main-map', {
        zoomControl: true,
        attributionControl: false
    }).setView([12.9716, 77.5946], 12);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd'
    }).addTo(mainMap);

    // Map control buttons
    const overlayButtons = document.querySelectorAll('.map-control-btn');
    overlayButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const overlay = btn.dataset.overlay;

            // Update active state
            overlayButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Switch overlay
            switchOverlay(overlay);
        });
    });
}

// ============================================
// 4. DATA LOADING
// ============================================

async function loadAllData() {
    showKPILoading();
    try {
        const [cityRes, corridorRes, riskRes] = await Promise.all([
            fetch('/api/city-pulse'),
            fetch('/api/corridor-intelligence'),
            fetch('/api/risk-window'),
        ]);

        if (!cityRes.ok || !corridorRes.ok || !riskRes.ok) throw new Error('API error');

        cityData     = await cityRes.json();
        corridorData = await corridorRes.json();
        const riskRaw = await riskRes.json();
        riskData = riskRaw.risk_window || [];

        renderCommandCenter();
    } catch (error) {
        console.error('Error loading data:', error);
        showKPIError();
    }
}

function showKPILoading() {
    ['kpi-total','kpi-critical','kpi-closures','kpi-impact'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '<span class="spinner" style="width:18px;height:18px;display:inline-block;vertical-align:middle;"></span>';
    });
}

function showKPIError() {
    ['kpi-total','kpi-critical','kpi-closures','kpi-impact'].forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.textContent = '—'; el.style.color = 'var(--critical)'; }
    });
}

// ============================================
// 5. COMMAND CENTER RENDERING (PAGE 1)
// ============================================

function renderCommandCenter() {
    if (!cityData) return;

    // Render KPIs
    renderKPIs();

    // Render map incidents
    renderMapIncidents();

    // Render stress bars
    renderStressBars();

    // Render risk heatmap
    renderRiskHeatmap();

    // Render recent incidents feed
    renderIncidentFeed();
}

function renderKPIs() {
    const kpis = cityData.kpi || {};
    document.getElementById('kpi-total').textContent = kpis.total_events || 0;
    document.getElementById('kpi-critical').textContent = kpis.critical_count || 0;
    document.getElementById('kpi-closures').textContent = kpis.closure_count || 0;
    document.getElementById('kpi-impact').textContent = kpis.avg_impact ? kpis.avg_impact.toFixed(1) : '0';
}

function renderMapIncidents() {
    // Clear existing markers
    incidentMarkers.forEach(marker => mainMap.removeLayer(marker));
    incidentMarkers = [];

    if (!cityData.map_events) return;

    cityData.map_events.forEach(event => {
        if (!event.latitude || !event.longitude) return;

        // Determine color based on impact score
        const impact = event.impact_score || 0;
        let color = '#16a34a'; // low
        if (impact >= 75) color = '#dc2626'; // critical
        else if (impact >= 50) color = '#ea580c'; // high
        else if (impact >= 25) color = '#f59e0b'; // medium

        const marker = L.circleMarker([event.latitude, event.longitude], {
            radius: 8,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(mainMap);

        // Popup
        const popupContent = `
            <div style="font-family: 'DM Sans', sans-serif;">
                <strong style="font-size: 14px; color: #0f172a;">${event.event_cause || 'Unknown'}</strong><br>
                <span style="font-size: 12px; color: #64748b;">${event.corridor || 'Unknown corridor'}</span><br>
                <span style="font-size: 13px; font-weight: 600; color: ${color};">Impact: ${impact.toFixed(0)}</span>
            </div>
        `;
        marker.bindPopup(popupContent);

        incidentMarkers.push(marker);
    });
}

function renderStressBars() {
    const container = document.getElementById('stress-bars');
    if (!container || !corridorData) return;

    container.innerHTML = '';

    const topCorridors = (corridorData.stress_rankings || corridorData.stress_leaderboard || []).slice(0, 8);

    topCorridors.forEach(corridor => {
        const stress = corridor.stress_index || 0;

        // Color based on stress
        let color = '#16a34a';
        if (stress >= 75) color = '#dc2626';
        else if (stress >= 50) color = '#ea580c';
        else if (stress >= 25) color = '#f59e0b';

        const item = document.createElement('div');
        item.className = 'stress-bar-item';
        item.innerHTML = `
            <div class="stress-bar-label">${corridor.corridor}</div>
            <div class="stress-bar-track">
                <div class="stress-bar-fill" style="width: ${stress}%; background: ${color};"></div>
            </div>
            <div class="stress-bar-value">${stress.toFixed(0)}</div>
        `;
        container.appendChild(item);
    });
}

function renderRiskHeatmap() {
    const hourLabelsContainer = document.getElementById('risk-hour-labels');
    const heatmapContainer = document.getElementById('risk-heatmap');

    if (!hourLabelsContainer || !heatmapContainer || !riskData) return;

    // Convert array to lookup map
    const riskMap = {};
    riskData.forEach(slot => {
        riskMap[`${slot.weekday}_${slot.hour}`] = slot.event_count;
    });

    // Find max for color scaling
    const maxCount = Math.max(...riskData.map(s => s.event_count), 1);

    // Hour labels (0-23)
    hourLabelsContainer.innerHTML = '<div></div>'; // Empty corner
    for (let h = 0; h < 24; h++) {
        const label = document.createElement('div');
        label.className = 'risk-hour-label';
        label.textContent = h;
        hourLabelsContainer.appendChild(label);
    }

    // Days grid
    heatmapContainer.innerHTML = '';
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    for (let dayIdx = 0; dayIdx < 7; dayIdx++) {
        // Day label
        const dayLabel = document.createElement('div');
        dayLabel.className = 'risk-day-label';
        dayLabel.textContent = days[dayIdx];
        heatmapContainer.appendChild(dayLabel);

        // Hour cells for this day
        for (let h = 0; h < 24; h++) {
            const count = riskMap[`${dayIdx}_${h}`] || 0;
            const intensity = count / maxCount;

            let color = '#f1f5f9';
            if (intensity > 0.7) color = '#dc2626';
            else if (intensity > 0.5) color = '#ea580c';
            else if (intensity > 0.3) color = '#f59e0b';
            else if (intensity > 0.1) color = '#fbbf24';

            const cell = document.createElement('div');
            cell.className = 'risk-cell';
            cell.style.backgroundColor = color;
            cell.title = `${days[dayIdx]} ${h}:00 - ${count} incidents`;
            heatmapContainer.appendChild(cell);
        }
    }
}

function renderIncidentFeed() {
    const container = document.getElementById('live-feed');
    const feedItems = cityData.feed || cityData.map_events || [];
    if (!container || !feedItems.length) return;

    container.innerHTML = '';

    feedItems.slice(0, 10).forEach(event => {
        const item = document.createElement('div');
        item.className = 'feed-item';

        // Backend feed items have a pre-formatted timestamp string
        const timeStr = event.timestamp || (event.start_datetime
            ? new Date(event.start_datetime).toLocaleString('en-US', {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            })
            : 'Recent');

        item.innerHTML = `
            <span class="feed-time">${timeStr}</span>
            <span class="feed-cause">${(event.cause || event.event_cause || 'Unknown').replace(/_/g, ' ')}</span>
            <span class="feed-location">${event.corridor || 'Unknown location'}</span>
        `;

        container.appendChild(item);
    });
}

// ============================================
// 6. OVERLAY SWITCHING (PAGE 1 MAP)
// ============================================

function switchOverlay(overlayType) {
    if (overlayType === 'incidents') {
        showIncidentsOverlay();
    } else if (overlayType === 'corridors') {
        showCorridorsOverlay();
    } else if (overlayType === 'heatmap') {
        showHeatmapOverlay();
    }
}

function showIncidentsOverlay() {
    // Clear corridor layers
    corridorLayers.forEach(layer => mainMap.removeLayer(layer));
    corridorLayers = [];

    // Show all incident markers
    incidentMarkers.forEach(marker => {
        if (!mainMap.hasLayer(marker)) {
            marker.addTo(mainMap);
        }
    });
}

function showCorridorsOverlay() {
    // Hide incident markers
    incidentMarkers.forEach(marker => mainMap.removeLayer(marker));

    // Clear previous corridor layers
    corridorLayers.forEach(layer => mainMap.removeLayer(layer));
    corridorLayers = [];

    if (!corridorData || !cityData) return;

    // Show top 10 stressed corridors as large circles
    const topCorridors = (corridorData.stress_rankings || corridorData.stress_leaderboard || []).slice(0, 10);

    topCorridors.forEach(corridor => {
        // Find incidents in this corridor to get average location
        const corridorIncidents = cityData.map_events.filter(e => e.corridor === corridor.corridor);

        if (corridorIncidents.length > 0) {
            const avgLat = corridorIncidents.reduce((sum, e) => sum + (e.latitude || 0), 0) / corridorIncidents.length;
            const avgLon = corridorIncidents.reduce((sum, e) => sum + (e.longitude || 0), 0) / corridorIncidents.length;

            const stress = corridor.stress_index;
            let color = stress >= 75 ? '#dc2626' : stress >= 50 ? '#ea580c' : stress >= 25 ? '#f59e0b' : '#16a34a';

            const circle = L.circle([avgLat, avgLon], {
                radius: 1000 + (stress * 20),
                color: color,
                fillColor: color,
                fillOpacity: 0.25,
                weight: 3,
                opacity: 0.8
            }).addTo(mainMap);

            circle.bindPopup(`
                <div style="font-family: 'DM Sans', sans-serif;">
                    <strong style="font-size: 14px; color: #0f172a;">${corridor.corridor}</strong><br>
                    <span style="font-size: 13px; color: #64748b;">Stress Index: <strong style="color: ${color};">${stress.toFixed(0)}</strong></span><br>
                    <span style="font-size: 12px; color: #64748b;">Incidents: ${corridor.incident_count}</span>
                </div>
            `);

            corridorLayers.push(circle);
        }
    });
}

function showHeatmapOverlay() {
    // Hide incident markers
    incidentMarkers.forEach(marker => mainMap.removeLayer(marker));

    // Clear previous corridor layers
    corridorLayers.forEach(layer => mainMap.removeLayer(layer));
    corridorLayers = [];

    if (!cityData) return;

    // Create density-based heatmap visualization with LARGER, more visible circles
    const heatData = cityData.map_events
        .filter(e => e.latitude && e.longitude)
        .map(e => {
            const weight = (e.impact_score || 0) / 100;
            return [e.latitude, e.longitude, weight, e.impact_score];
        });

    heatData.forEach(([lat, lon, weight, impactScore]) => {
        const intensity = weight;

        // Determine color
        let color = '#16a34a';
        if (intensity > 0.75) color = '#dc2626';
        else if (intensity > 0.5) color = '#ea580c';
        else if (intensity > 0.25) color = '#f59e0b';

        // MUCH LARGER circles with gradient effect
        const circle = L.circleMarker([lat, lon], {
            radius: 15 + (intensity * 25), // Larger base size
            fillColor: color,
            color: color,
            fillOpacity: 0.35,
            opacity: 0.7,
            weight: 2
        }).addTo(mainMap);

        circle.bindPopup(`
            <div style="font-family: 'DM Sans', sans-serif;">
                <strong style="font-size: 14px; color: ${color};">Heat Intensity</strong><br>
                <span style="font-size: 13px; color: #64748b;">Impact Score: ${impactScore.toFixed(0)}</span>
            </div>
        `);

        corridorLayers.push(circle);
    });
}

// ============================================
// 7. AI PREDICTOR (PAGE 2)
// ============================================

function initializeAIPredictor() {
    populatePredictorDropdowns();

    // Show placeholder before first prediction
    const resultsContainer = document.getElementById('prediction-results');
    if (resultsContainer) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M12 1v6m0 6v6M5.6 5.6l4.2 4.2m4.2 4.2l4.2 4.2M1 12h6m6 0h6M5.6 18.4l4.2-4.2m4.2-4.2l4.2-4.2"/>
                </svg>
                <strong>No prediction yet</strong>
                <p>Fill in the incident details on the left and click Analyze Impact.</p>
            </div>`;
    }

    const predictBtn = document.getElementById('btn-predict');
    if (predictBtn) {
        predictBtn.addEventListener('click', handlePrediction);
    }
}

async function populatePredictorDropdowns() {
    try {
        const response = await fetch('/api/metadata');
        const options = await response.json();

        // Populate Event Cause
        const causeSelect = document.getElementById('input-cause');
        if (causeSelect && options.event_causes) {
            causeSelect.innerHTML = options.event_causes.map(cause =>
                `<option value="${cause}">${cause.replace(/_/g, ' ')}</option>`
            ).join('');
        }

        // Populate Corridor
        const corridorSelect = document.getElementById('input-corridor');
        if (corridorSelect && options.corridors) {
            corridorSelect.innerHTML = options.corridors.map(corridor =>
                `<option value="${corridor}">${corridor}</option>`
            ).join('');
        }

        // Populate Vehicle Type
        const vehicleSelect = document.getElementById('input-vehicle');
        if (vehicleSelect && options.vehicle_types) {
            vehicleSelect.innerHTML = options.vehicle_types.map(veh =>
                `<option value="${veh}">${veh.replace(/_/g, ' ')}</option>`
            ).join('');
        }

    } catch (error) {
        console.error('Error loading predictor options:', error);
    }
}

async function handlePrediction() {
    const cause    = document.getElementById('input-cause').value;
    const corridor = document.getElementById('input-corridor').value;
    const vehicle  = document.getElementById('input-vehicle').value;
    const hour     = parseInt(document.getElementById('input-hour').value);
    const weekday  = parseInt(document.getElementById('input-weekday').value);
    const closure  = document.getElementById('input-closure').checked;

    const btn = document.getElementById('btn-predict');
    const resultsContainer = document.getElementById('prediction-results');

    // Loading state
    btn.disabled = true;
    btn.textContent = 'Analyzing…';
    resultsContainer.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <span>Running CatBoost model…</span>
        </div>`;

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cause, corridor, vehicle_type: vehicle, hour, weekday, closure })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        renderPredictionResult(result);

    } catch (error) {
        resultsContainer.innerHTML = `
            <div class="error-banner">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                Prediction failed — is the backend running?
            </div>`;
        console.error('Prediction error:', error);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyze Impact';
    }
}

function buildRecommendationList(result) {
    // result.recommendations is a plain array (legacy)
    // result.resource_plan is the backend's V2 structure: {units: [...], actions: [...], ...}
    if (result.recommendations && result.recommendations.length) {
        return result.recommendations.map(r => `<li>• ${r}</li>`).join('');
    }
    const plan = result.resource_plan;
    if (!plan) return '<li>No recommendations available</li>';

    const lines = [];
    if (plan.units && plan.units.length) {
        plan.units.forEach(u => lines.push(`• Deploy ${u.count || ''} ${u.type || u} — ${u.location || ''}`));
    }
    if (plan.actions && plan.actions.length) {
        plan.actions.forEach(a => lines.push(`• ${a}`));
    }
    if (plan.priority) lines.push(`• Priority: ${plan.priority}`);
    if (plan.estimated_clearance_mins) lines.push(`• Est. clearance: ${plan.estimated_clearance_mins} min`);

    return lines.length ? lines.map(l => `<li>${l}</li>`).join('') : '<li>No recommendations available</li>';
}

function renderPredictionResult(result) {
    const container = document.getElementById('prediction-results');

    const score       = result.impact_score || 0;
    const impactClass = (result.risk_class || result.impact_class || 'Unknown').toLowerCase();
    const confidence  = result.confidence ? Math.round(result.confidence * 100) : null;

    // Color per severity
    const colorMap = { critical: '#dc2626', high: '#ea580c', medium: '#f59e0b', low: '#16a34a' };
    const color = colorMap[impactClass] || '#2563eb';
    const labelClass = colorMap[impactClass] ? impactClass : 'low';

    // SVG ring
    const circumference = 2 * Math.PI * 50;
    const offset = circumference - (score / 100) * circumference;

    const confidenceHTML = confidence !== null ? `
        <div class="confidence-row">
            <div class="confidence-label">
                <span>Model Confidence</span>
                <span>${confidence}%</span>
            </div>
            <div class="confidence-track">
                <div class="confidence-fill" style="width: ${confidence}%"></div>
            </div>
        </div>` : '';

    container.innerHTML = `
        <div class="prediction-card">
            <div class="score-circle">
                <svg viewBox="0 0 120 120">
                    <circle class="ring-bg" cx="60" cy="60" r="50"></circle>
                    <circle class="ring-fg" cx="60" cy="60" r="50"
                        style="stroke:${color}; stroke-dasharray:${circumference}; stroke-dashoffset:${offset};"></circle>
                </svg>
                <div class="score-text" style="color:${color};">${score.toFixed(0)}</div>
            </div>

            <div class="impact-label ${labelClass}"
                 style="background:${color}18; color:${color};">
                ${(result.risk_class || result.impact_class || 'Unknown')}
            </div>

            ${confidenceHTML}

            <div class="recommendation-section">
                <h4>Recommendations</h4>
                <ul>${buildRecommendationList(result)}</ul>
            </div>
        </div>`;
}

// ============================================
// 8. INTELLIGENCE CHARTS (PAGE 3)
// ============================================

let charts = {};

async function renderIntelligenceCharts() {
    if (!corridorData) {
        // Show spinners in each chart section while loading
        document.querySelectorAll('.chart-section canvas').forEach(c => {
            c.style.display = 'none';
            const loading = document.createElement('div');
            loading.className = 'loading-state chart-loading';
            loading.innerHTML = '<div class="spinner"></div><span>Loading…</span>';
            c.parentNode.appendChild(loading);
        });
        try {
            const response = await fetch('/api/corridor-intelligence');
            corridorData = await response.json();
        } catch (error) {
            console.error('Error loading corridor intelligence:', error);
            return;
        } finally {
            document.querySelectorAll('.chart-section canvas').forEach(c => c.style.display = '');
            document.querySelectorAll('.chart-loading').forEach(el => el.remove());
        }
    }

    // Destroy existing charts
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    charts = {};

    renderStressChart();
    renderHourlyChart();
    renderCausesChart();
    renderClosuresChart();
}

function renderStressChart() {
    const ctx = document.getElementById('chart-stress');
    if (!ctx || !corridorData) return;

    const topCorridors = (corridorData.stress_rankings || corridorData.stress_leaderboard || []).slice(0, 10);

    charts.stress = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topCorridors.map(c => c.corridor),
            datasets: [{
                label: 'Stress Index',
                data: topCorridors.map(c => c.stress_index),
                backgroundColor: topCorridors.map(c => {
                    const s = c.stress_index;
                    if (s >= 75) return '#dc2626';
                    if (s >= 50) return '#ea580c';
                    if (s >= 25) return '#f59e0b';
                    return '#16a34a';
                }),
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, max: 100 } }
        }
    });
}

function renderHourlyChart() {
    const ctx = document.getElementById('chart-hourly');
    if (!ctx || !riskData) return;

    const hourlyData = Array(24).fill(0);
    riskData.forEach(slot => {
        hourlyData[slot.hour] += slot.event_count;
    });

    charts.hourly = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [{
                label: 'Incidents',
                data: hourlyData,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37,99,235,0.08)',
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: '#2563eb'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderCausesChart() {
    const ctx = document.getElementById('chart-causes');
    if (!ctx || !corridorData) return;

    const causeData = corridorData.cause_distribution || {};
    const labels = Object.keys(causeData).slice(0, 8);
    const values = labels.map(l => causeData[l]);

    charts.causes = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => l.replace(/_/g, ' ')),
            datasets: [{
                data: values,
                backgroundColor: [
                    '#dc2626','#ea580c','#f59e0b','#fbbf24',
                    '#16a34a','#2563eb','#7c3aed','#db2777'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { boxWidth: 12, font: { size: 11 } }
                }
            }
        }
    });
}

function renderClosuresChart() {
    const ctx = document.getElementById('chart-closures');
    if (!ctx || !corridorData) return;

    const closureData = corridorData.closure_analysis || {};
    const labels = Object.keys(closureData).slice(0, 8);
    const values = labels.map(l => closureData[l]);

    charts.closures = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(l => l.replace(/_/g, ' ')),
            datasets: [{
                label: 'Closure Rate (%)',
                data: values,
                backgroundColor: '#ea580c',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { callback: v => v + '%' }
                }
            }
        }
    });
}
