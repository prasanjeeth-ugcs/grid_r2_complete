/*
 * ASTRAM AI - Interactive Map-First Interface
 * Modern, Click-Driven UI
 */

const API = '';
let mainMap = null;
let incidentMarkers = [];
let corridorLayers = [];
let currentOverlay = 'incidents';

// Data storage
let cityData = null;
let corridorData = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    loadAllData();
    setupEventHandlers();
});

// ===== MAP INITIALIZATION =====
function initializeMap() {
    mainMap = L.map('main-map', {
        zoomControl: false,
        attributionControl: false
    }).setView([12.9716, 77.5946], 12);

    L.control.zoom({ position: 'topright' }).addTo(mainMap);

    // Light theme tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 18
    }).addTo(mainMap);

    setTimeout(() => mainMap.invalidateSize(), 200);
}

// ===== DATA LOADING =====
async function loadAllData() {
    try {
        const [cityPulse, corridorIntel, riskWindow] = await Promise.all([
            fetch('/api/city-pulse').then(r => r.json()),
            fetch('/api/corridor-intelligence').then(r => r.json()).catch(() => null),
            fetch('/api/risk-window').then(r => r.json())
        ]);

        cityData = cityPulse;
        corridorData = corridorIntel;

        // Update nav stats
        document.getElementById('nav-total').textContent = cityPulse.kpi.total_events.toLocaleString();
        document.getElementById('nav-critical').textContent = cityPulse.kpi.critical_count;

        // Update panel stats
        document.getElementById('stat-total').textContent = cityPulse.kpi.total_events.toLocaleString();
        document.getElementById('stat-critical').textContent = cityPulse.kpi.critical_count;
        document.getElementById('stat-closures').textContent = cityPulse.kpi.closure_count;
        document.getElementById('stat-avg-impact').textContent = cityPulse.kpi.avg_impact.toFixed(1);

        // Render components
        renderIncidents(cityPulse.map_events);
        renderStressList(corridorIntel);
        renderLiveFeed(cityPulse.live_feed);
        renderRiskHeatmap(riskWindow.risk_window);

    } catch (error) {
        console.error('Data loading error:', error);
    }
}

// ===== RENDER INCIDENTS ON MAP =====
function renderIncidents(events) {
    // Clear existing markers
    incidentMarkers.forEach(m => mainMap.removeLayer(m));
    incidentMarkers = [];

    const classColors = {
        'Critical': '#dc2626',
        'High': '#ea580c',
        'Medium': '#f59e0b',
        'Low': '#16a34a'
    };

    events.slice(0, 200).forEach(evt => {
        if (!evt.latitude || !evt.longitude) return;

        const color = classColors[evt.impact_class] || '#64748b';
        const marker = L.circleMarker([evt.latitude, evt.longitude], {
            radius: evt.impact_class === 'Critical' ? 6 : evt.impact_class === 'High' ? 5 : 4,
            fillColor: color,
            color: '#fff',
            fillOpacity: 0.7,
            opacity: 1,
            weight: 1
        });

        marker.bindPopup(`
            <div style="font-family: 'DM Sans', sans-serif; font-size: 13px; min-width: 180px;">
                <strong style="color: ${color};">${formatLabel(evt.event_cause)}</strong><br>
                <div style="margin-top: 6px; color: #64748b; font-size: 12px;">
                    <div>${evt.corridor || 'Non-corridor'}</div>
                    <div style="margin-top: 4px;">
                        <span style="color: ${color}; font-weight: 600;">Score: ${Math.round(evt.impact_score)}</span> ·
                        <span>${evt.impact_class}</span>
                    </div>
                </div>
            </div>
        `);

        // Click handler to show incident details
        marker.on('click', () => showIncidentDetails(evt));

        marker.addTo(mainMap);
        incidentMarkers.push(marker);
    });
}

// ===== RENDER STRESS LIST =====
function renderStressList(data) {
    if (!data || !data.stress_rankings) return;

    const container = document.getElementById('stress-list');
    const top5 = data.stress_rankings.slice(0, 5);

    container.innerHTML = top5.map(corridor => `
        <div class="stress-item" onclick="showCorridorDetails('${corridor.corridor}', ${corridor.stress_index})">
            <span class="stress-label">${corridor.corridor}</span>
            <span class="stress-value">${corridor.stress_index.toFixed(1)}</span>
        </div>
    `).join('');
}

// ===== RENDER LIVE FEED =====
function renderLiveFeed(feed) {
    const container = document.getElementById('live-feed');
    if (!feed || !feed.length) return;

    container.innerHTML = feed.slice(0, 10).map(item => {
        const classColors = {
            'Critical': '#dc2626',
            'High': '#ea580c',
            'Medium': '#f59e0b',
            'Low': '#16a34a'
        };
        const color = classColors[item.impact_class] || '#64748b';

        return `
            <div class="feed-item" style="border-left-color: ${color};" onclick='showIncidentFromFeed(${JSON.stringify(item)})'>
                <span class="feed-time">${item.timestamp_ago}</span>
                <span class="feed-cause">${formatLabel(item.event_cause)}</span>
                <span class="feed-location">${item.corridor || 'Non-corridor'} · Score: ${Math.round(item.impact_score)}</span>
            </div>
        `;
    }).join('');
}

// ===== RENDER RISK HEATMAP =====
function renderRiskHeatmap(data) {
    const container = document.getElementById('risk-heatmap');
    const hourLabelsContainer = document.getElementById('risk-hour-labels');
    if (!data) return;

    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    // Convert array to lookup map
    const riskMap = {};
    data.forEach(slot => {
        riskMap[`${slot.weekday}_${slot.hour}`] = slot.event_count;
    });

    // Get max count for color scaling
    const maxCount = Math.max(...Object.values(riskMap));

    // Render hour labels
    hourLabelsContainer.innerHTML = '<div></div>'; // Empty cell for day label column
    for (let h = 0; h < 24; h++) {
        const label = document.createElement('div');
        label.className = 'risk-hour-label';
        label.textContent = h;
        hourLabelsContainer.appendChild(label);
    }

    container.innerHTML = '';

    // Render in grid: 7 rows (days) x 24 columns (hours)
    for (let dayIdx = 0; dayIdx < 7; dayIdx++) {
        // Day label
        const dayLabel = document.createElement('div');
        dayLabel.className = 'risk-day-label';
        dayLabel.textContent = days[dayIdx];
        container.appendChild(dayLabel);

        // Hour cells for this day
        for (let hour = 0; hour < 24; hour++) {
            const key = `${dayIdx}_${hour}`;
            const count = riskMap[key] || 0;
            const intensity = maxCount > 0 ? (count / maxCount) : 0;

            const cell = document.createElement('div');
            cell.className = 'risk-cell';

            // Color based on intensity
            if (intensity > 0.75) {
                cell.style.backgroundColor = '#dc2626';
            } else if (intensity > 0.5) {
                cell.style.backgroundColor = '#ea580c';
            } else if (intensity > 0.25) {
                cell.style.backgroundColor = '#f59e0b';
            } else if (count > 0) {
                cell.style.backgroundColor = '#16a34a';
            } else {
                cell.style.backgroundColor = '#e2e8f0';
            }

            cell.title = `${days[dayIdx]} ${hour.toString().padStart(2, '0')}:00\n${count} incidents`;
            container.appendChild(cell);
        }
    }
}

// ===== PANEL SWITCHING =====
function showDefaultPanel() {
    document.querySelectorAll('.panel-view').forEach(p => p.classList.remove('active'));
    document.getElementById('panel-default').classList.add('active');
}

function showIncidentPanel() {
    document.querySelectorAll('.panel-view').forEach(p => p.classList.remove('active'));
    document.getElementById('panel-incident').classList.add('active');
}

function showCorridorPanel() {
    document.querySelectorAll('.panel-view').forEach(p => p.classList.remove('active'));
    document.getElementById('panel-corridor').classList.add('active');
}

// ===== INCIDENT DETAILS =====
async function showIncidentDetails(incident) {
    showIncidentPanel();

    const detailsContainer = document.getElementById('incident-details');
    detailsContainer.innerHTML = `
        <div style="background: var(--bg-primary); padding: 16px; border-radius: var(--radius-md); margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: var(--text-primary);">${formatLabel(incident.event_cause)}</div>
                    <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">${incident.corridor || 'Non-corridor'}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 24px; font-weight: 700; color: ${getRiskColor(incident.impact_class)};">${Math.round(incident.impact_score)}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">${incident.impact_class}</div>
                </div>
            </div>
        </div>
    `;

    // Run AI prediction
    await runPrediction({
        cause: incident.event_cause,
        corridor: incident.corridor || 'Non-corridor',
        vehicle_type: incident.vehicle_type || 'others',
        hour: new Date().getHours(),
        weekday: new Date().getDay(),
        closure: incident.requires_road_closure || false
    });
}

function showIncidentFromFeed(item) {
    showIncidentDetails(item);
}

// ===== CORRIDOR DETAILS =====
async function showCorridorDetails(corridorName, stressIndex) {
    showCorridorPanel();

    document.getElementById('corridor-name').textContent = corridorName;

    try {
        const response = await fetch('/api/corridor-intelligence');
        const data = await response.json();

        // Find corridor in stress rankings
        const corridor = data.stress_rankings.find(c => c.corridor === corridorName);

        if (corridor) {
            document.getElementById('corridor-total').textContent = corridor.total_incidents || '-';
            document.getElementById('corridor-stress').textContent = corridor.stress_index.toFixed(1);
            document.getElementById('corridor-tier').textContent = corridor.tier || '-';
            document.getElementById('corridor-closure-rate').textContent = (corridor.closure_rate || 0) + '%';
            document.getElementById('corridor-cause').textContent = formatLabel(corridor.dominant_cause || '-');
            document.getElementById('corridor-peak').textContent = (corridor.peak_hour || '-') + ':00';
        }
    } catch (error) {
        console.error('Corridor details error:', error);
    }
}

// ===== AI PREDICTION =====
async function runPrediction(params) {
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });

        const result = await response.json();

        // Update score ring
        document.getElementById('incident-score').textContent = Math.round(result.impact_score);
        updateScoreRing('incident-ring', result.impact_score);

        // Update class
        const classEl = document.getElementById('incident-class');
        classEl.textContent = result.risk_class;
        classEl.style.color = getRiskColor(result.risk_class);

        // Update confidence
        document.getElementById('incident-confidence').textContent =
            `${result.confidence.level} confidence (${result.confidence.matching_count} similar cases)`;

        // Update resources
        const resourcesContainer = document.getElementById('incident-resources');
        const resources = result.resource_plan.resources;
        resourcesContainer.innerHTML = `
            <div style="background: var(--bg-primary); padding: 14px; border-radius: var(--radius-md);">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 13px;">
                    ${resources.police_units > 0 ? `<div><strong>Police Units:</strong> ${resources.police_units}</div>` : ''}
                    ${resources.tow_trucks > 0 ? `<div><strong>Tow Trucks:</strong> ${resources.tow_trucks}</div>` : ''}
                    ${resources.barricades > 0 ? `<div><strong>Barricades:</strong> ${resources.barricades}</div>` : ''}
                    <div><strong>Diversion:</strong> ${resources.diversion_required ? 'Required' : 'Not needed'}</div>
                </div>
                <div style="margin-top: 10px; font-size: 12px; color: var(--text-secondary);">
                    Expected Resolution: <strong>${result.resource_plan.resolution.median}</strong>
                </div>
            </div>
        `;

        // Update historical
        const hist = result.historical_evidence;
        const histContainer = document.getElementById('incident-historical');
        histContainer.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                <div style="text-align: center; background: var(--bg-primary); padding: 12px; border-radius: var(--radius-md);">
                    <div style="font-size: 20px; font-weight: 700; color: var(--brand-primary);">${hist.count}</div>
                    <div style="font-size: 11px; color: var(--text-tertiary);">Similar Cases</div>
                </div>
                <div style="text-align: center; background: var(--bg-primary); padding: 12px; border-radius: var(--radius-md);">
                    <div style="font-size: 20px; font-weight: 700; color: var(--critical);">${hist.critical_rate}%</div>
                    <div style="font-size: 11px; color: var(--text-tertiary);">Critical Rate</div>
                </div>
            </div>
        `;

    } catch (error) {
        console.error('Prediction error:', error);
    }
}

// ===== EVENT HANDLERS =====
function setupEventHandlers() {
    // Map overlay toggles
    document.querySelectorAll('.map-control-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.map-control-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const overlay = btn.dataset.overlay;
            currentOverlay = overlay;

            // TODO: Implement overlay switching (corridors, heatmap)
            if (overlay === 'incidents') {
                // Already showing incidents
            } else if (overlay === 'corridors') {
                // Show corridor polygons
            } else if (overlay === 'heatmap') {
                // Show heatmap overlay
            }
        });
    });
}

// ===== UTILITIES =====
function formatLabel(str) {
    if (!str) return 'Unknown';
    return str.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getRiskColor(cls) {
    if (cls === 'Critical') return '#dc2626';
    if (cls === 'High') return '#ea580c';
    if (cls === 'Medium') return '#f59e0b';
    return '#16a34a';
}

function updateScoreRing(circleId, score, maxScore = 100) {
    const circle = document.getElementById(circleId);
    if (!circle) return;

    const r = parseFloat(circle.getAttribute('r'));
    const circumference = 2 * Math.PI * r;
    const offset = circumference - (score / maxScore) * circumference;

    circle.style.strokeDasharray = circumference;
    circle.style.strokeDashoffset = offset;

    // Color by risk class
    const cls = score >= 75 ? 'Critical' : score >= 50 ? 'High' : score >= 25 ? 'Medium' : 'Low';
    circle.style.stroke = getRiskColor(cls);
}
