/* ═══════════════════════════════════════════════════════════════════
   Page 2 — Risk Forecast
   ═══════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    const hourSlider = document.getElementById('fc-hour');
    const hourLabel = document.getElementById('fc-hour-label');
    const runBtn = document.getElementById('fc-run');

    if (hourSlider && hourLabel) {
        hourSlider.addEventListener('input', () => {
            hourLabel.textContent = String(hourSlider.value).padStart(2, '0') + ':00';
        });
    }

    if (runBtn) {
        runBtn.addEventListener('click', runForecast);
    }
});

async function runForecast() {
    const corridor = document.getElementById('fc-corridor').value;
    const weekday = document.getElementById('fc-weekday').value;
    const hour = document.getElementById('fc-hour').value;

    try {
        // Fetch single corridor forecast
        const fc = await apiGet(`/api/forecast?corridor=${encodeURIComponent(corridor)}&weekday=${weekday}&hour=${hour}`);
        renderForecastScore(fc);
        renderForecastDetails(fc, corridor);

        // Fetch all corridors
        const all = await apiGet(`/api/forecast/all?weekday=${weekday}&hour=${hour}`);
        renderAllCorridors(all);
    } catch (e) {
        console.error('Forecast error:', e);
    }
}

function renderForecastScore(fc) {
    const scoreEl = document.getElementById('fc-risk-score');
    if (scoreEl) {
        animateValue(scoreEl, 0, fc.risk_score);
    }
    updateScoreRing('fc-ring-circle', fc.risk_score);
}

function renderForecastDetails(fc, corridor) {
    const container = document.getElementById('fc-details');
    if (!container) return;

    container.innerHTML = `
        <div class="forecast-stat">
            <span class="forecast-stat-label">Corridor</span>
            <span class="forecast-stat-value">${corridor}</span>
        </div>
        <div class="forecast-stat">
            <span class="forecast-stat-label">Expected Events</span>
            <span class="forecast-stat-value">${fc.expected_events}</span>
        </div>
        <div class="forecast-stat">
            <span class="forecast-stat-label">Closure Probability</span>
            <span class="forecast-stat-value">${fc.closure_probability}%</span>
        </div>
        <div class="forecast-stat">
            <span class="forecast-stat-label">Max Observed Score</span>
            <span class="forecast-stat-value">${fc.max_observed_score || '—'}</span>
        </div>
        <div class="forecast-stat">
            <span class="forecast-stat-label">Confidence</span>
            <span class="forecast-stat-value" style="text-transform:capitalize">${fc.confidence}</span>
        </div>
        ${fc.top_causes.length > 0 ? `
            <div style="margin-top:12px">
                <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Top Causes</div>
                ${fc.top_causes.map(c => `
                    <div class="dist-row">
                        <span class="dist-label">${formatLabel(c.event_cause)}</span>
                        <div class="dist-bar-bg">
                            <div class="dist-bar-fill" style="width:${(c.count / fc.top_causes[0].count * 100)}%;background:var(--purple)"></div>
                        </div>
                        <span class="dist-count">${c.count}</span>
                    </div>
                `).join('')}
            </div>
        ` : ''}
    `;
}

function renderAllCorridors(corridors) {
    const container = document.getElementById('fc-all-corridors');
    if (!container) return;

    container.innerHTML = corridors.map(c => {
        const color = getRiskColor(c.risk_score);
        const tierBadge = c.tier > 0 ? `<span style="font-size:10px;color:var(--text-muted);margin-left:4px">T${c.tier}</span>` : '';
        return `
            <div class="corridor-item">
                <span class="corridor-name">${c.corridor}${tierBadge}</span>
                <span class="corridor-score" style="background:${color}20;color:${color}">${Math.round(c.risk_score)}</span>
            </div>
        `;
    }).join('');
}
