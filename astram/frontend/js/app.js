/* ═══════════════════════════════════════════════════════════════════
   ASTRAM AI V1.0 — Frontend Application
   Bengaluru Traffic Operational Intelligence Platform
   ═══════════════════════════════════════════════════════════════════ */

const API = '';
let map = null;
let charts = {};

// ─── Router ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            navigateTo(link.dataset.page);
        });
    });

    // Hour slider
    document.getElementById('sim-hour').addEventListener('input', e => {
        const h = parseInt(e.target.value);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const h12 = h % 12 || 12;
        document.getElementById('sim-hour-label').textContent =
            `${h12.toString().padStart(2, '0')}:${h === 5 ? '30' : '00'} ${ampm}`;
    });

    document.getElementById('sim-analyze').addEventListener('click', runAnalysis);
    document.getElementById('sim-whatif-closure').addEventListener('change', runWhatIf);

    // Load data
    loadMetadata();
    loadCityPulse();
    loadRiskWindow();
    loadShiftBriefing();

    navigateTo('overview');
});

function navigateTo(page) {
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const target = document.getElementById(`page-${page}`);
    if (target) {
        target.classList.add('active');
        if (page === 'overview' && map) setTimeout(() => map.invalidateSize(), 100);
        if (page === 'intelligence') loadIntelligence();
    }
}

// ─── API Helpers ─────────────────────────────────────────────────────
async function apiGet(endpoint) {
    const res = await fetch(API + endpoint);
    return res.json();
}

async function apiPost(endpoint, data) {
    const res = await fetch(API + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    return res.json();
}

function formatLabel(s) {
    if (!s) return '';
    return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function fillSelect(id, options) {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.innerHTML = '';
    options.forEach(opt => {
        const o = document.createElement('option');
        o.value = opt;
        o.textContent = formatLabel(opt);
        sel.appendChild(o);
    });
}

// ─── Load Metadata ──────────────────────────────────────────────────
async function loadMetadata() {
    try {
        const m = await apiGet('/api/metadata');
        fillSelect('sim-cause', m.event_causes);
        fillSelect('sim-corridor', m.corridors);
        fillSelect('sim-veh', m.veh_types);
        // Demo defaults
        document.getElementById('sim-cause').value = 'tree_fall';
        document.getElementById('sim-corridor').value = 'Bellary Road 1';
    } catch (e) {
        console.error('Metadata load failed:', e);
    }
}

// ═══════════════════════════════════════════════════════════════════
// PAGE 1: COMMAND CENTER
// ═══════════════════════════════════════════════════════════════════

async function loadCityPulse() {
    try {
        const data = await apiGet('/api/city-pulse');

        // KPI Strip
        const kpi = data.kpi;
        document.getElementById('stat-total').textContent = kpi.total_events.toLocaleString();
        document.getElementById('stat-critical').textContent = kpi.critical_count;
        document.getElementById('stat-closures').textContent = kpi.closure_count;
        document.getElementById('stat-avg-impact').textContent = kpi.avg_impact;

        // Stress Bar
        renderStressBar(data.stress_bar);

        // Map
        if (!map) {
            map = L.map('overview-map').setView([12.9716, 77.5946], 11);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap &copy; CARTO'
            }).addTo(map);
        }

        data.map_events.forEach(ev => {
            if (ev.latitude && ev.longitude) {
                const color = getRiskColor(ev.impact_class);
                L.circleMarker([ev.latitude, ev.longitude], {
                    radius: 4, color, fillColor: color, fillOpacity: 0.65, weight: 1
                }).addTo(map).bindPopup(
                    `<b>${formatLabel(ev.event_cause)}</b><br>${ev.corridor}<br>Score: ${Math.round(ev.impact_score)} (${ev.impact_class})`
                );
            }
        });

        // Live Feed
        renderFeed(data.feed);

    } catch (e) {
        console.error('City pulse error:', e);
    }
}

function renderStressBar(stressData) {
    const container = document.getElementById('stress-bar-container');
    if (!container || !stressData) return;
    container.innerHTML = '';

    const top = stressData.slice(0, 10);
    top.forEach((item, i) => {
        const cls = item.stress_index >= 75 ? 'critical' : item.stress_index >= 50 ? 'high' : item.stress_index >= 25 ? 'medium' : 'low';
        const div = document.createElement('div');
        div.className = 'stress-bar-item';
        div.innerHTML = `
            <span class="stress-bar-label">${item.corridor}</span>
            <div class="stress-bar-track">
                <div class="stress-bar-fill ${cls}" style="width: 0%">${item.stress_index}</div>
            </div>
        `;
        container.appendChild(div);
        // Animate
        setTimeout(() => {
            div.querySelector('.stress-bar-fill').style.width = `${item.stress_index}%`;
        }, 100 + i * 80);
    });
}

function renderFeed(feedData) {
    const feedEl = document.getElementById('live-feed');
    if (!feedEl) return;
    feedEl.innerHTML = '';

    (feedData || []).forEach(item => {
        const row = document.createElement('div');
        row.className = 'feed-item';
        row.innerHTML = `
            <div class="feed-row">
                <span class="feed-cause">${formatLabel(item.cause)}</span>
                <span class="feed-time">${item.timestamp}</span>
            </div>
            <div class="feed-row">
                <span class="feed-corridor">${item.corridor}</span>
                <span class="feed-status ${item.status}">${item.status}</span>
            </div>
        `;
        row.addEventListener('click', () => {
            document.getElementById('sim-cause').value = item.cause;
            document.getElementById('sim-corridor').value = item.corridor;
            document.getElementById('sim-hour').value = item.hour;
            try { document.getElementById('sim-veh').value = item.veh_type || 'Others'; } catch(e) {}
            document.getElementById('sim-closure').checked = item.closure;

            const h12 = item.hour % 12 || 12;
            const ampm = item.hour >= 12 ? 'PM' : 'AM';
            document.getElementById('sim-hour-label').textContent = `${h12.toString().padStart(2,'0')}:00 ${ampm}`;

            navigateTo('copilot');
            runAnalysis();
        });
        feedEl.appendChild(row);
    });
}

// ─── Risk Window Heatmap ─────────────────────────────────────────
async function loadRiskWindow() {
    try {
        const data = await apiGet('/api/risk-window');
        renderRiskHeatmap(data.risk_window);
    } catch (e) {
        console.error('Risk window error:', e);
    }
}

function renderRiskHeatmap(slots) {
    const container = document.getElementById('risk-heatmap');
    if (!container || !slots) return;

    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const now = new Date();
    const currentDay = (now.getDay() + 6) % 7; // JS Sunday=0, we want Monday=0
    const currentHour = now.getHours();

    let html = '<div class="heatmap-grid">';

    // Header row
    html += '<div class="heatmap-header"></div>';
    for (let h = 0; h < 24; h++) {
        html += `<div class="heatmap-header">${h}</div>`;
    }

    // Find max event count for color scaling
    const maxCount = Math.max(...slots.map(s => s.event_count), 1);

    // Data rows
    days.forEach((day, dayIdx) => {
        html += `<div class="heatmap-row-label">${day}</div>`;
        for (let h = 0; h < 24; h++) {
            const slot = slots.find(s => s.weekday === dayIdx && s.hour === h);
            const count = slot ? slot.event_count : 0;
            const intensity = count / maxCount;
            const critRate = slot ? slot.critical_rate : 0;

            let bg;
            if (intensity === 0) {
                bg = 'rgba(255,255,255,0.02)';
            } else if (critRate >= 10) {
                bg = `rgba(239,68,68,${0.2 + intensity * 0.6})`;
            } else if (intensity > 0.6) {
                bg = `rgba(249,115,22,${0.15 + intensity * 0.5})`;
            } else if (intensity > 0.3) {
                bg = `rgba(234,179,8,${0.1 + intensity * 0.4})`;
            } else {
                bg = `rgba(99,102,241,${0.08 + intensity * 0.3})`;
            }

            const isCurrent = dayIdx === currentDay && h === currentHour;
            const tooltip = slot
                ? `${slot.weekday_name} ${h}:00\n${count} incidents\nCritical: ${critRate}%\nAvg Impact: ${slot.avg_impact}`
                : '';

            html += `<div class="heatmap-cell${isCurrent ? ' current-slot' : ''}"
                          style="background:${bg}"
                          title="${tooltip}"></div>`;
        }
    });

    html += '</div>';
    container.innerHTML = html;
}

// ─── Shift Briefing ──────────────────────────────────────────────
async function loadShiftBriefing() {
    try {
        const data = await apiGet('/api/shift-briefing');
        renderShiftBriefing(data);
    } catch (e) {
        console.error('Shift briefing error:', e);
    }
}

function renderShiftBriefing(shift) {
    const panel = document.getElementById('shift-panel');
    if (!panel || !shift) return;

    panel.innerHTML = `
        <div class="shift-header">
            <div>
                <div class="shift-name">${shift.shift_name} Shift</div>
                <div class="shift-hours">${shift.shift_hours}</div>
            </div>
            <span class="shift-stress ${shift.stress_level}">${shift.stress_level}</span>
        </div>
        <div class="shift-stats">
            <div class="shift-stat">
                <div class="shift-stat-value">${shift.total_events.toLocaleString()}</div>
                <div class="shift-stat-label">Historical Events</div>
            </div>
            <div class="shift-stat">
                <div class="shift-stat-value">${shift.critical_rate}%</div>
                <div class="shift-stat-label">Critical Rate</div>
            </div>
        </div>
        <h4 style="font-size:0.8rem;color:var(--text-tertiary);margin-bottom:8px;">Top Corridors</h4>
        <ul class="shift-list">
            ${shift.top_corridors.slice(0, 5).map(c =>
                `<li><span>${c.corridor}</span><span class="count">${c.count}</span></li>`
            ).join('')}
        </ul>
        <h4 style="font-size:0.8rem;color:var(--text-tertiary);margin:12px 0 8px;">Top Causes</h4>
        <ul class="shift-list">
            ${shift.top_causes.slice(0, 4).map(c =>
                `<li><span>${formatLabel(c.cause)}</span><span class="count">${c.count}</span></li>`
            ).join('')}
        </ul>
    `;
}

// ═══════════════════════════════════════════════════════════════════
// PAGE 2: INCIDENT RESPONSE COPILOT
// ═══════════════════════════════════════════════════════════════════

let lastPrediction = null;

async function runAnalysis() {
    const btn = document.getElementById('sim-analyze');
    btn.disabled = true;
    btn.innerHTML = '<span style="animation:pulse-dot 1s infinite">&#9679;</span> Analyzing...';

    const req = {
        cause: document.getElementById('sim-cause').value,
        corridor: document.getElementById('sim-corridor').value,
        vehicle_type: document.getElementById('sim-veh').value,
        hour: parseInt(document.getElementById('sim-hour').value),
        weekday: parseInt(document.getElementById('sim-weekday').value),
        closure: document.getElementById('sim-closure').checked,
    };

    try {
        const res = await apiPost('/api/predict', req);
        lastPrediction = res;
        renderCopilotResults(res);
        // Reset whatif toggle
        document.getElementById('sim-whatif-closure').checked = false;
        document.getElementById('whatif-result').textContent = '';
    } catch (e) {
        console.error('Analysis error:', e);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Analyze Incident`;
    }
}

async function runWhatIf() {
    if (!lastPrediction) return;

    const whatifActive = document.getElementById('sim-whatif-closure').checked;
    if (!whatifActive) {
        document.getElementById('whatif-result').textContent = '';
        renderCopilotResults(lastPrediction);
        return;
    }

    // Re-run with closure toggled off
    const req = {
        cause: document.getElementById('sim-cause').value,
        corridor: document.getElementById('sim-corridor').value,
        vehicle_type: document.getElementById('sim-veh').value,
        hour: parseInt(document.getElementById('sim-hour').value),
        weekday: parseInt(document.getElementById('sim-weekday').value),
        closure: false,
    };

    try {
        const res = await apiPost('/api/predict', req);
        renderCopilotResults(res);

        const delta = res.impact_score - lastPrediction.impact_score;
        const arrow = delta > 0 ? '↑' : '↓';
        document.getElementById('whatif-result').innerHTML =
            `Without closure: <b>${res.risk_class}</b> (${res.impact_score}) — ${arrow} ${Math.abs(delta).toFixed(1)} points from ${lastPrediction.risk_class}`;
    } catch (e) {
        console.error('What-if error:', e);
    }
}

function renderCopilotResults(res) {
    // Panel A: Impact Assessment
    animateValue(document.getElementById('sim-score'), 0, res.impact_score);
    updateScoreRing('sim-ring-circle', res.impact_score);

    const clsEl = document.getElementById('sim-class');
    clsEl.textContent = res.risk_class;
    clsEl.style.backgroundColor = getClassBg(res.risk_class);
    clsEl.style.color = getClassColor(res.risk_class);

    // Confidence
    const conf = res.confidence;
    document.getElementById('sim-confidence').textContent = conf.level;
    document.getElementById('sim-confidence').style.color =
        conf.level === 'High' ? 'var(--low)' : conf.level === 'Medium' ? 'var(--medium)' : 'var(--critical)';
    document.getElementById('sim-conf-count').textContent = `(${conf.matching_count} matches)`;

    // Similar incidents
    const hist = res.historical_evidence;
    document.getElementById('sim-hist-count').textContent = `${hist.count} Similar Incidents`;

    // Panel B: Resolution Estimate
    const reso = res.resource_plan.resolution;
    document.getElementById('res-median').textContent = `Median: ${reso.median}`;
    document.getElementById('res-range').textContent = `Range: ${reso.range}`;

    // Panel C: Resource Timeline
    renderTimeline(res.resource_plan);

    // Panel D: Historical Evidence
    renderHistoricalEvidence(hist);

    // Panel E: Formula vs AI
    renderFormulaVsAI(res.formula_vs_ai);

    // Panel F: Corridor DNA
    renderCorridorDNA(res.corridor_dna);

    // Panel G: Transit Chain
    renderTransitChain(res.transit_chain);
}

function renderTimeline(plan) {
    const container = document.getElementById('resource-timeline');
    if (!container) return;

    const timeline = plan.timeline || [];
    const resources = plan.resources || {};

    let html = '<div class="timeline">';
    timeline.forEach(item => {
        html += `
            <div class="timeline-item">
                <div class="timeline-phase">${item.phase}</div>
                <div class="timeline-actions">${item.actions.join(', ')}</div>
            </div>
        `;
    });
    html += '</div>';

    // Resource summary
    html += '<div style="padding:12px 0 0;border-top:1px solid var(--border);margin-top:12px;">';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.82rem;">';
    if (resources.police_units > 0) html += `<div>Police Units: <b>${resources.police_units}</b></div>`;
    if (resources.tow_trucks > 0) html += `<div>Tow Trucks: <b>${resources.tow_trucks}</b></div>`;
    if (resources.barricades > 0) html += `<div>Barricades: <b>${resources.barricades}</b></div>`;
    html += `<div>Diversion: <b>${resources.diversion_required ? 'Required' : 'Not needed'}</b></div>`;
    if (resources.special_team && resources.special_team !== 'None') html += `<div>Team: <b>${resources.special_team}</b></div>`;
    html += '</div>';

    if (plan.vehicle_note) {
        html += `<div style="margin-top:8px;padding:8px;background:var(--high-bg);border-radius:var(--radius-sm);font-size:0.82rem;color:var(--high);">
            ⚠ ${plan.vehicle_note}
        </div>`;
    }

    html += `<div style="margin-top:8px;font-size:0.72rem;color:var(--text-muted);">Multiplier: ${plan.multipliers.total}</div>`;
    html += '</div>';

    container.innerHTML = html;
}

function renderHistoricalEvidence(hist) {
    const container = document.getElementById('historical-evidence');
    if (!container) return;

    if (hist.count === 0) {
        container.innerHTML = '<p class="placeholder-text">No similar incidents found</p>';
        return;
    }

    const dist = hist.score_distribution;
    const total = dist.Low + dist.Medium + dist.High + dist.Critical || 1;

    let html = `
        <div class="hist-stats">
            <div class="hist-stat">
                <div class="hist-stat-value" style="color:var(--accent-light)">${hist.count}</div>
                <div class="hist-stat-label">Similar Incidents</div>
            </div>
            <div class="hist-stat">
                <div class="hist-stat-value" style="color:var(--critical)">${hist.critical_rate}%</div>
                <div class="hist-stat-label">Critical Rate</div>
            </div>
            <div class="hist-stat">
                <div class="hist-stat-value" style="color:var(--medium)">${hist.average_score}</div>
                <div class="hist-stat-label">Avg Score</div>
            </div>
            <div class="hist-stat">
                <div class="hist-stat-value" style="color:var(--text-primary)">${dist.Critical + dist.High}</div>
                <div class="hist-stat-label">High/Critical</div>
            </div>
        </div>
        <div style="font-size:0.75rem;color:var(--text-tertiary);margin-bottom:6px;">Score Distribution</div>
        <div class="hist-dist">
            ${dist.Low > 0 ? `<div class="hist-dist-bar" style="width:${dist.Low/total*100}%;background:var(--low)">${dist.Low}</div>` : ''}
            ${dist.Medium > 0 ? `<div class="hist-dist-bar" style="width:${dist.Medium/total*100}%;background:var(--medium)">${dist.Medium}</div>` : ''}
            ${dist.High > 0 ? `<div class="hist-dist-bar" style="width:${dist.High/total*100}%;background:var(--high)">${dist.High}</div>` : ''}
            ${dist.Critical > 0 ? `<div class="hist-dist-bar" style="width:${dist.Critical/total*100}%;background:var(--critical)">${dist.Critical}</div>` : ''}
        </div>
    `;

    container.innerHTML = html;
}

function renderFormulaVsAI(fva) {
    const container = document.getElementById('formula-vs-ai');
    if (!container) return;

    const baseline = fva.operational_baseline;
    const pattern = fva.historical_pattern;

    let formulaHtml = `<div class="formula-section">
        <div class="section-title"><span class="icon-formula">&#9638;</span> Operational Baseline</div>`;

    baseline.components.forEach(c => {
        formulaHtml += `<div class="formula-component">
            <span class="formula-factor">${c.factor}</span>
            <span class="formula-delta">${c.delta}</span>
        </div>`;
    });

    formulaHtml += `<div class="formula-total">
        <span>Baseline</span>
        <span class="formula-delta">${baseline.baseline_score}</span>
    </div></div>`;

    let aiHtml = `<div class="ai-section">
        <div class="section-title"><span class="icon-ai">&#10047;</span> Historical Pattern Intelligence</div>
        <p class="ai-narrative">${pattern.narrative}</p>
        <div class="ai-stat">
            <span class="ai-stat-label">Similar Incidents</span>
            <span class="ai-stat-value">${pattern.similar_count}</span>
        </div>
        <div class="ai-stat">
            <span class="ai-stat-label">Historical Avg Impact</span>
            <span class="ai-stat-value">${pattern.average_historical_impact}</span>
        </div>
        <div class="ai-stat">
            <span class="ai-stat-label">AI Predicted</span>
            <span class="ai-stat-value">${pattern.predicted_score}</span>
        </div>
    </div>`;

    container.innerHTML = formulaHtml + aiHtml;
}

function renderCorridorDNA(dna) {
    const panel = document.getElementById('corridor-dna-panel');
    const grid = document.getElementById('corridor-dna-grid');
    const nameEl = document.getElementById('dna-corridor-name');

    if (!dna || !panel) {
        if (panel) panel.style.display = 'none';
        return;
    }

    panel.style.display = 'block';
    nameEl.textContent = dna.corridor;

    grid.innerHTML = `
        <div class="dna-stat">
            <div class="dna-stat-value">${dna.total_incidents}</div>
            <div class="dna-stat-label">Total Incidents</div>
        </div>
        <div class="dna-stat">
            <div class="dna-stat-value">Tier ${dna.tier}</div>
            <div class="dna-stat-label">Corridor Tier</div>
        </div>
        <div class="dna-stat">
            <div class="dna-stat-value">${dna.stress_index || 0}</div>
            <div class="dna-stat-label">Stress Index</div>
        </div>
        <div class="dna-stat">
            <div class="dna-stat-value">${formatLabel(dna.dominant_cause)}</div>
            <div class="dna-stat-label">Dominant Cause</div>
        </div>
        <div class="dna-stat">
            <div class="dna-stat-value">${dna.peak_hour}:00</div>
            <div class="dna-stat-label">Peak Hour</div>
        </div>
        <div class="dna-stat">
            <div class="dna-stat-value">${dna.closure_rate}%</div>
            <div class="dna-stat-label">Closure Rate</div>
        </div>
    `;
}

function renderTransitChain(tc) {
    const panel = document.getElementById('transit-chain-panel');
    const content = document.getElementById('transit-flag-content');
    if (!panel) return;

    if (!tc || !tc.triggered) {
        panel.style.display = 'none';
        return;
    }

    panel.style.display = 'block';
    content.innerHTML = `
        <div class="transit-flag-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
            Transit Chain Risk Detected
        </div>
        <div class="transit-flag-body">
            <strong>${tc.bus_type}</strong> bus breakdown on a Tier 1 corridor.<br>
            <b>${tc.historical_cases}</b> historical cases with similar characteristics.<br>
            Estimated cumulative passenger disruption across history: <b>${tc.estimated_passenger_disruption.toLocaleString()}</b>.<br>
            <em>${tc.bus_type} depot coordination advised.</em>
        </div>
    `;
}

// ═══════════════════════════════════════════════════════════════════
// PAGE 3: CORRIDOR INTELLIGENCE
// ═══════════════════════════════════════════════════════════════════

let intelligenceLoaded = false;

async function loadIntelligence() {
    if (intelligenceLoaded) return;

    try {
        const data = await apiGet('/api/corridor-intelligence');

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = 'Inter';
        Chart.defaults.plugins.legend.display = false;

        // Q1: Heatmap (as bubble chart)
        renderHeatmapChart(data.heatmap);

        // Q2: Closure Rate
        renderClosureChart(data.closure_rates);

        // Q3: Stress Leaderboard
        renderStressChart(data.stress_leaderboard);

        // Q4: Station Scatter
        renderStationChart(data.station_scatter);

        // Q5: Fleet Demand
        renderFleetChart(data.fleet_demand);

        intelligenceLoaded = true;
    } catch (e) {
        console.error('Intelligence error:', e);
    }
}

function renderHeatmapChart(heatData) {
    const ctx = document.getElementById('intel-heatmap')?.getContext('2d');
    if (!ctx) return;

    const corridors = [...new Set(heatData.map(d => d.corridor))];
    const datasets = corridors.map((c, i) => ({
        label: c,
        data: heatData
            .filter(d => d.corridor === c)
            .map(d => ({ x: d.hour, y: i, r: Math.min(18, Math.max(3, Math.sqrt(d.count) * 1.5)) })),
        backgroundColor: `hsla(${230 + i * 12}, 70%, 60%, 0.6)`,
    }));

    charts.heatmap = new Chart(ctx, {
        type: 'bubble',
        data: { datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Hour of Day', color: '#64748b' }, min: -1, max: 24, grid: { color: 'rgba(255,255,255,0.04)' } },
                y: {
                    ticks: { callback: v => corridors[v] || '', color: '#94a3b8', font: { size: 11 } },
                    min: -1, max: corridors.length,
                    grid: { color: 'rgba(255,255,255,0.04)' }
                }
            },
        }
    });
}

function renderClosureChart(closureData) {
    const ctx = document.getElementById('intel-closure')?.getContext('2d');
    if (!ctx) return;

    const colors = closureData.map(d => {
        const rate = d.requires_road_closure;
        if (rate >= 15) return '#ef4444';
        if (rate >= 8) return '#f97316';
        if (rate >= 3) return '#eab308';
        return '#22c55e';
    });

    charts.closure = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: closureData.map(d => formatLabel(d.event_cause)),
            datasets: [{ data: closureData.map(d => d.requires_road_closure), backgroundColor: colors, borderRadius: 4 }]
        },
        options: {
            indexAxis: 'y',
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Closure Rate %', color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } },
                y: { grid: { display: false }, ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderStressChart(stressData) {
    const ctx = document.getElementById('intel-stress')?.getContext('2d');
    if (!ctx) return;

    const top = stressData.slice(0, 12);
    const colors = top.map(d => {
        if (d.stress_index >= 75) return '#ef4444';
        if (d.stress_index >= 50) return '#f97316';
        if (d.stress_index >= 25) return '#eab308';
        return '#22c55e';
    });

    charts.stress = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top.map(d => d.corridor),
            datasets: [{ data: top.map(d => d.stress_index), backgroundColor: colors, borderRadius: 4 }]
        },
        options: {
            indexAxis: 'y',
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Stress Index (0-100)', color: '#64748b' }, max: 100, grid: { color: 'rgba(255,255,255,0.04)' } },
                y: { grid: { display: false }, ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderStationChart(stationData) {
    const ctx = document.getElementById('intel-station')?.getContext('2d');
    if (!ctx) return;

    const stations = Object.values(stationData);
    const halasuru = stations.find(s => s.station && s.station.toLowerCase().includes('halasuru'));

    charts.station = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Stations',
                data: stations.map(s => ({ x: s.event_count, y: s.avg_impact, label: s.station })),
                backgroundColor: stations.map(s =>
                    (s.station && s.station.toLowerCase().includes('halasuru'))
                        ? 'rgba(239,68,68,0.8)' : 'rgba(99,102,241,0.5)'
                ),
                pointRadius: stations.map(s =>
                    (s.station && s.station.toLowerCase().includes('halasuru')) ? 8 : 5
                ),
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Event Count', color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } },
                y: { title: { display: true, text: 'Avg Impact Score', color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const d = ctx.raw;
                            return `${d.label}: ${d.x} events, Avg ${d.y}`;
                        }
                    }
                }
            }
        }
    });
}

function renderFleetChart(fleetData) {
    const ctx = document.getElementById('intel-fleet')?.getContext('2d');
    if (!ctx) return;

    const top = fleetData.slice(0, 10);

    charts.fleet = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top.map(d => d.corridor),
            datasets: [
                {
                    label: 'Tow Trucks/day',
                    data: top.map(d => d.tow_trucks_per_day),
                    backgroundColor: 'rgba(249,115,22,0.7)',
                    borderRadius: 4,
                },
                {
                    label: 'Officers/day',
                    data: top.map(d => d.officers_per_day),
                    backgroundColor: 'rgba(99,102,241,0.7)',
                    borderRadius: 4,
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'top', labels: { boxWidth: 12, padding: 16, color: '#94a3b8' } } },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 45 } },
                y: { title: { display: true, text: 'Units per Day', color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } }
            }
        }
    });
}

// ═══════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════

function getRiskColor(cls) {
    if (cls === 'Critical') return '#ef4444';
    if (cls === 'High') return '#f97316';
    if (cls === 'Medium') return '#eab308';
    return '#22c55e';
}

function getClassColor(cls) {
    return getRiskColor(cls);
}

function getClassBg(cls) {
    if (cls === 'Critical') return 'rgba(239,68,68,0.15)';
    if (cls === 'High') return 'rgba(249,115,22,0.15)';
    if (cls === 'Medium') return 'rgba(234,179,8,0.15)';
    return 'rgba(34,197,94,0.15)';
}

function animateValue(el, start, end, duration = 900) {
    const range = end - start;
    const startTime = performance.now();
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + range * eased;
        el.textContent = Math.round(current);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
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
