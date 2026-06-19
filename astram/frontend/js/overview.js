/* ═══════════════════════════════════════════════════════════════════
   Page 1 — Executive Overview
   ═══════════════════════════════════════════════════════════════════ */

let overviewMap = null;
let overviewLoaded = false;

window.addEventListener('page:overview', loadOverview);

// Load on initial page
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(loadOverview, 500);
});

async function loadOverview() {
    if (overviewLoaded) return;

    try {
        const data = await apiGet('/api/overview');
        renderOverviewCards(data);
        renderMap(data.map_events);
        renderCorridorRisks(data.top_corridors);
        renderClassDistribution(data.class_counts);
        renderCauseDistribution(data.cause_counts);
        overviewLoaded = true;
    } catch (e) {
        console.error('Overview load error:', e);
    }
}

function renderOverviewCards(data) {
    const total = document.getElementById('stat-total');
    const critical = document.getElementById('stat-critical');

    if (total) animateValue(total, 0, data.total_events);
    if (critical) animateValue(critical, 0, data.class_counts['Critical'] || 0);
}

function renderMap(events) {
    const container = document.getElementById('overview-map');
    if (!container || overviewMap) return;

    overviewMap = L.map(container, {
        zoomControl: false,
        attributionControl: false,
    }).setView([12.9716, 77.5946], 12);

    L.control.zoom({ position: 'topright' }).addTo(overviewMap);

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 18,
    }).addTo(overviewMap);

    // Add event markers
    const classColors = {
        'Critical': '#ef4444',
        'High': '#f59e0b',
        'Medium': '#eab308',
        'Low': '#22c55e',
    };

    events.forEach(evt => {
        const color = classColors[evt.impact_class] || '#64748b';
        const circle = L.circleMarker([evt.latitude, evt.longitude], {
            radius: evt.impact_class === 'Critical' ? 7 : 4,
            fillColor: color,
            color: color,
            fillOpacity: 0.6,
            opacity: 0.8,
            weight: 1,
        });

        circle.bindPopup(`
            <div style="font-family:Inter,sans-serif;font-size:12px;color:#333;min-width:160px">
                <strong style="font-size:13px">${formatLabel(evt.event_cause)}</strong><br>
                <span style="color:#666">Corridor: ${evt.corridor || 'Non-corridor'}</span><br>
                <span style="color:${color};font-weight:700">Score: ${Math.round(evt.impact_score)} · ${evt.impact_class}</span>
            </div>
        `);

        circle.addTo(overviewMap);
    });

    // Force map resize
    setTimeout(() => overviewMap.invalidateSize(), 200);
}

function renderCorridorRisks(corridors) {
    const container = document.getElementById('corridor-risks');
    if (!container) return;

    container.innerHTML = Object.entries(corridors)
        .map(([name, score]) => {
            const color = getRiskColor(score);
            return `
                <div class="corridor-item">
                    <span class="corridor-name">${name}</span>
                    <span class="corridor-score" style="background:${color}20;color:${color}">${Math.round(score)}</span>
                </div>
            `;
        }).join('');
}

function renderClassDistribution(counts) {
    const container = document.getElementById('class-distribution');
    if (!container) return;

    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    const order = ['Critical', 'High', 'Medium', 'Low'];
    const colors = { 'Critical': 'var(--critical)', 'High': 'var(--high)', 'Medium': 'var(--medium)', 'Low': 'var(--low)' };

    container.innerHTML = order.map(cls => {
        const count = counts[cls] || 0;
        const pct = (count / total * 100).toFixed(1);
        return `
            <div class="dist-row">
                <span class="dist-label" style="color:${colors[cls]}">${cls}</span>
                <div class="dist-bar-bg">
                    <div class="dist-bar-fill" style="width:${pct}%;background:${colors[cls]}"></div>
                </div>
                <span class="dist-count">${count}</span>
            </div>
        `;
    }).join('');
}

function renderCauseDistribution(counts) {
    const container = document.getElementById('cause-distribution');
    if (!container) return;

    const max = Math.max(...Object.values(counts));
    container.innerHTML = Object.entries(counts).map(([cause, count]) => {
        const pct = (count / max * 100).toFixed(1);
        return `
            <div class="dist-row">
                <span class="dist-label">${formatLabel(cause)}</span>
                <div class="dist-bar-bg">
                    <div class="dist-bar-fill" style="width:${pct}%;background:var(--blue)"></div>
                </div>
                <span class="dist-count">${count}</span>
            </div>
        `;
    }).join('');
}
