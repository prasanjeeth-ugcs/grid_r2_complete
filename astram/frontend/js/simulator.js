/* ═══════════════════════════════════════════════════════════════════
   Page 3 — Incident Simulator (★ The Demo Page)
   ═══════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    const hourSlider = document.getElementById('sim-hour');
    const hourLabel = document.getElementById('sim-hour-label');
    const analyzeBtn = document.getElementById('sim-analyze');
    const causeSelect = document.getElementById('sim-cause');

    if (hourSlider && hourLabel) {
        hourSlider.addEventListener('input', () => {
            hourLabel.textContent = String(hourSlider.value).padStart(2, '0') + ':00';
        });
    }

    // Show/hide vehicle type based on cause
    if (causeSelect) {
        causeSelect.addEventListener('change', () => {
            const vehGroup = document.getElementById('sim-veh-group');
            if (vehGroup) {
                const showVeh = ['vehicle_breakdown', 'accident'].includes(causeSelect.value);
                vehGroup.style.display = showVeh ? 'block' : 'none';
            }
        });
    }

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', runSimulation);
    }
});

async function runSimulation() {
    const btn = document.getElementById('sim-analyze');
    btn.textContent = 'Analyzing...';
    btn.disabled = true;

    const params = getSimulatorParams();
    ASTRAM.lastParams = params;

    try {
        // Run prediction + SHAP + resources in parallel
        const [prediction, shapData, resources] = await Promise.all([
            apiPost('/api/predict', params),
            apiPost('/api/shap', params),
            apiPost('/api/resources', {
                event_cause: params.event_cause,
                impact_class: 'Medium', // will update after prediction
                corridor_tier: params.corridor_tier || 0,
                veh_type: params.veh_type,
                is_rush_hour: params.hour >= 8 && params.hour <= 10 || params.hour >= 17 && params.hour <= 19,
            }),
        ]);

        // Update resources with actual class
        const resourcesUpdated = await apiPost('/api/resources', {
            event_cause: params.event_cause,
            impact_class: prediction.impact_class,
            corridor_tier: getCorrTier(params.corridor),
            veh_type: params.veh_type,
            is_rush_hour: params.hour >= 8 && params.hour <= 10 || params.hour >= 17 && params.hour <= 19,
        });

        ASTRAM.lastPrediction = prediction;
        ASTRAM.lastShap = shapData;
        ASTRAM.lastResources = resourcesUpdated;

        // Render each section independently so one failure doesn't block others
        try { renderSimulatorResult(prediction); } catch(e) { console.error('Score render error:', e); }
        try { renderSimShapChart(shapData); } catch(e) {
            console.error('SHAP render error:', e);
            const c = document.getElementById('sim-shap-chart');
            if (c) c.innerHTML = `<p class="placeholder-text" style="color:var(--critical)">SHAP unavailable: ${e.message}</p>`;
        }
        try { renderSimResources(resourcesUpdated); } catch(e) { console.error('Resources render error:', e); }

    } catch (e) {
        console.error('Simulation error:', e);
    } finally {
        btn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            Analyze Incident
        `;
        btn.disabled = false;
    }
}

function getSimulatorParams() {
    const corridor = document.getElementById('sim-corridor').value;
    return {
        event_cause: document.getElementById('sim-cause').value,
        veh_type: document.getElementById('sim-veh').value,
        corridor: corridor,
        police_station: document.getElementById('sim-station').value,
        latitude: parseFloat(document.getElementById('sim-lat').value),
        longitude: parseFloat(document.getElementById('sim-lng').value),
        hour: parseInt(document.getElementById('sim-hour').value),
        weekday: parseInt(document.getElementById('sim-weekday').value),
        month: new Date().getMonth() + 1,
        requires_road_closure: document.getElementById('sim-closure').checked,
    };
}

function getCorrTier(corridor) {
    const tiers = {
        "Mysore Road": 1, "Bellary Road 1": 1, "Tumkur Road": 1,
        "Bellary Road 2": 1, "Hosur Road": 1,
        "ORR North 1": 2, "Old Madras Road": 2, "Magadi Road": 2,
        "ORR East 1": 2, "ORR North 2": 2, "Bannerghatta Road": 2,
        "ORR East 2": 2, "West of Chord Road": 2,
    };
    return tiers[corridor] || (corridor === "Non-corridor" ? 0 : 3);
}

function renderSimulatorResult(pred) {
    const scoreEl = document.getElementById('sim-score');
    const classEl = document.getElementById('sim-class');
    const confEl = document.getElementById('sim-confidence');

    if (scoreEl) animateValue(scoreEl, 0, pred.score);
    updateScoreRing('sim-ring-circle', pred.score);

    if (classEl) {
        classEl.textContent = pred.impact_class;
        classEl.className = 'impact-badge ' + pred.impact_class;
    }
    if (confEl) {
        confEl.textContent = `Confidence: ${Math.round(pred.confidence * 100)}%`;
    }
}

function renderSimShapChart(shapData) {
    const container = document.getElementById('sim-shap-chart');
    if (!container) return;

    const features = shapData.features.slice(0, 8);
    const maxAbs = Math.max(...features.map(f => Math.abs(f.shap_value)), 1);

    container.innerHTML = features.map(f => {
        const pct = (Math.abs(f.shap_value) / maxAbs * 45).toFixed(1);
        const isPositive = f.shap_value > 0;
        const barClass = isPositive ? 'positive' : 'negative';
        const sign = isPositive ? '+' : '';

        return `
            <div class="shap-bar">
                <span class="shap-label">${f.feature}</span>
                <div class="shap-bar-container">
                    <div class="shap-bar-fill ${barClass}" style="width:${pct}%"></div>
                </div>
                <span class="shap-value" style="color:${isPositive ? 'var(--critical)' : 'var(--blue)'}">${sign}${f.shap_value.toFixed(1)}</span>
            </div>
        `;
    }).join('');
}

function renderSimResources(res) {
    const container = document.getElementById('sim-resources');
    if (!container) return;

    container.innerHTML = `
        <div class="resource-item">
            <div class="resource-icon">👮</div>
            <div class="resource-value">${res.police_units}</div>
            <div class="resource-label">Police Units</div>
        </div>
        <div class="resource-item">
            <div class="resource-icon">🚛</div>
            <div class="resource-value">${res.tow_trucks}</div>
            <div class="resource-label">${res.tow_type}</div>
        </div>
        <div class="resource-item">
            <div class="resource-icon">🚧</div>
            <div class="resource-value">${res.barricades}</div>
            <div class="resource-label">Barricades</div>
        </div>
        <div class="resource-item">
            <div class="resource-icon">🔄</div>
            <div class="resource-value" style="font-size:16px">${res.diversion}</div>
            <div class="resource-label">Diversion</div>
        </div>
        ${res.crew_needed ? `
            <div class="resource-item" style="grid-column:span 2">
                <div class="resource-icon">🔧</div>
                <div class="resource-value" style="font-size:16px">${res.crew_type}</div>
                <div class="resource-label">Specialized Crew</div>
            </div>
        ` : ''}
        <div class="resource-item" style="grid-column:span 2">
            <div class="resource-icon">⏱️</div>
            <div class="resource-value" style="font-size:18px">${res.est_duration}</div>
            <div class="resource-label">Estimated Duration</div>
        </div>
    `;
}
