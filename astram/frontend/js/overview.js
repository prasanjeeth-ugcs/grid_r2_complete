/*
 * ASTRAM AI - Command Center Page
 * Clean, Professional UI with Real Data
 */

let overviewMap = null;
let overviewLoaded = false;

// Load on page activation
window.addEventListener('page:overview', loadOverview);

// Load on initial page load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(loadOverview, 300);
});

async function loadOverview() {
    if (overviewLoaded) return;

    try {
        // Fetch all required data in parallel
        const [cityPulse, riskWindow, shiftBriefing, stressIndex] = await Promise.all([
            fetch('/api/city-pulse').then(r => r.json()),
            fetch('/api/risk-window').then(r => r.json()),
            fetch('/api/shift-briefing').then(r => r.json()),
            fetch('/api/corridor-intelligence').then(r => r.json()).catch(() => null)
        ]);

        // Render all sections
        renderKPIs(cityPulse.kpi);
        renderMap(cityPulse.map_events);
        renderFeed(cityPulse.live_feed);
        renderStressIndex(stressIndex);
        renderShiftBriefing(shiftBriefing);
        renderRiskHeatmap(riskWindow);

        overviewLoaded = true;
    } catch (error) {
        console.error('Overview load error:', error);
    }
}

function renderKPIs(kpi) {
    document.getElementById('stat-total').textContent = kpi.total_events.toLocaleString();
    document.getElementById('stat-critical').textContent = kpi.critical_count;
    document.getElementById('stat-closures').textContent = kpi.closure_count;
    document.getElementById('stat-avg-impact').textContent = kpi.avg_impact.toFixed(1);
}

function renderStressIndex(data) {
    if (!data || !data.stress_rankings) return;

    const container = document.getElementById('stress-bar-container');
    const top10 = data.stress_rankings.slice(0, 10);
    const maxScore = Math.max(...top10.map(c => c.stress_index));

    container.innerHTML = top10.map(corridor => {
        const pct = (corridor.stress_index / maxScore) * 100;
        return `
            <div class="stress-item">
                <span class="stress-label">${corridor.corridor}</span>
                <div class="stress-bar">
                    <div class="stress-fill" style="width: ${pct}%">
                        <span class="stress-value">${corridor.stress_index.toFixed(1)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderShiftBriefing(data) {
    const container = document.getElementById('shift-panel');

    container.innerHTML = `
        <div class="shift-item">
            <div class="shift-label">Current Shift</div>
            <div class="shift-value">${data.shift_name}</div>
            <div class="shift-desc">${data.shift_hours}</div>
        </div>
        <div class="shift-item">
            <div class="shift-label">Alert Level</div>
            <div class="shift-value">${data.alert_level}</div>
        </div>
        <div class="shift-item">
            <div class="shift-label">Historical Events</div>
            <div class="shift-value">${data.historical_events.toLocaleString()}</div>
        </div>
        <div class="shift-item">
            <div class="shift-label">Critical Rate</div>
            <div class="shift-value">${(data.critical_rate * 100).toFixed(1)}%</div>
        </div>
        <div class="shift-item">
            <div class="shift-label">Top Corridors</div>
            ${Object.entries(data.top_corridors).slice(0, 5).map(([name, count]) =>
                `<div class="shift-desc">${name}: ${count}</div>`
            ).join('')}
        </div>
        <div class="shift-item">
            <div class="shift-label">Top Causes</div>
            ${Object.entries(data.top_causes).slice(0, 4).map(([cause, count]) =>
                `<div class="shift-desc">${formatLabel(cause)}: ${count}</div>`
            ).join('')}
        </div>
    `;
}

function renderRiskHeatmap(data) {
    const container = document.getElementById('risk-heatmap');
    const hourLabelsContainer = document.getElementById('risk-hour-labels');
    if (!data || !data.risk_window) return;

    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    // Convert array to lookup map
    const riskMap = {};
    data.risk_window.forEach(slot => {
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

function renderMap(events) {
    const container = document.getElementById('overview-map');
    if (!container || overviewMap) return;

    overviewMap = L.map(container, {
        zoomControl: false,
        attributionControl: false,
    }).setView([12.9716, 77.5946], 12);

    L.control.zoom({ position: 'topright' }).addTo(overviewMap);

    // Light tile layer for light theme
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 18,
    }).addTo(overviewMap);

    // Add event markers
    const classColors = {
        'Critical': '#dc2626',
        'High': '#ea580c',
        'Medium': '#f59e0b',
        'Low': '#16a34a',
    };

    events.slice(0, 200).forEach(evt => {
        const color = classColors[evt.impact_class] || '#64748b';
        const circle = L.circleMarker([evt.latitude, evt.longitude], {
            radius: evt.impact_class === 'Critical' ? 6 : evt.impact_class === 'High' ? 5 : 4,
            fillColor: color,
            color: '#fff',
            fillOpacity: 0.7,
            opacity: 1,
            weight: 1,
        });

        circle.bindPopup(`
            <div style="font-family: 'DM Sans', sans-serif; font-size: 13px; color: #0f172a; min-width: 180px; padding: 4px;">
                <strong style="font-size: 14px; color: ${color};">${formatLabel(evt.event_cause)}</strong><br>
                <div style="margin-top: 6px; color: #64748b; font-size: 12px;">
                    <div>Corridor: ${evt.corridor || 'Non-corridor'}</div>
                    <div style="margin-top: 4px;">
                        <span style="color: ${color}; font-weight: 600;">Score: ${Math.round(evt.impact_score)}</span> ·
                        <span style="font-weight: 500;">${evt.impact_class}</span>
                    </div>
                </div>
            </div>
        `);

        circle.addTo(overviewMap);
    });

    // Force map resize
    setTimeout(() => overviewMap.invalidateSize(), 200);
}

function renderFeed(feed) {
    const container = document.getElementById('live-feed');
    if (!feed || !feed.length) return;

    container.innerHTML = feed.slice(0, 15).map(item => {
        const classColors = {
            'Critical': '#dc2626',
            'High': '#ea580c',
            'Medium': '#f59e0b',
            'Low': '#16a34a',
        };
        const color = classColors[item.impact_class] || '#64748b';

        return `
            <div class="feed-item" style="border-left-color: ${color};">
                <div class="feed-time">${item.timestamp_ago}</div>
                <div class="feed-cause">${formatLabel(item.event_cause)}</div>
                <div class="feed-location">${item.corridor || 'Non-corridor'} · Score: ${Math.round(item.impact_score)}</div>
            </div>
        `;
    }).join('');
}

function getRiskColor(score) {
    if (score >= 75) return '#dc2626';
    if (score >= 50) return '#ea580c';
    if (score >= 25) return '#f59e0b';
    return '#16a34a';
}

function formatLabel(str) {
    if (!str) return 'Unknown';
    return str.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
