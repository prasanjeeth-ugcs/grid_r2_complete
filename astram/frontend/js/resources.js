/* ═══════════════════════════════════════════════════════════════════
   Page 4 — Resource Copilot
   ═══════════════════════════════════════════════════════════════════ */

window.addEventListener('page:resources', renderResourcePage);

function renderResourcePage() {
    const res = ASTRAM.lastResources;
    const pred = ASTRAM.lastPrediction;
    const params = ASTRAM.lastParams;

    if (!res || !pred) {
        return; // placeholder already showing
    }

    renderResourceDetail(res, pred, params);
    renderMultipliers(res);
}

function renderResourceDetail(res, pred, params) {
    const container = document.getElementById('resource-detail');
    if (!container) return;

    container.innerHTML = `
        <div style="margin-bottom:20px;padding:16px;background:rgba(255,255,255,0.03);border-radius:var(--radius-sm);border:1px solid var(--border)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <div>
                    <div style="font-size:18px;font-weight:700">${formatLabel(params.event_cause)}</div>
                    <div style="font-size:13px;color:var(--text-secondary)">${params.corridor || 'Non-corridor'} · ${String(params.hour).padStart(2,'0')}:00</div>
                </div>
                <div style="text-align:right">
                    <span class="impact-badge ${pred.impact_class}">${pred.impact_class}</span>
                    <div style="font-size:13px;color:var(--text-muted);margin-top:4px">Score: ${pred.score}</div>
                </div>
            </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px">
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
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div class="resource-item">
                <div class="resource-icon">🔄</div>
                <div class="resource-value" style="font-size:16px">${res.diversion}</div>
                <div class="resource-label">Diversion Advisory</div>
            </div>
            <div class="resource-item">
                <div class="resource-icon">⏱️</div>
                <div class="resource-value" style="font-size:16px">${res.est_duration}</div>
                <div class="resource-label">Est. Duration</div>
            </div>
        </div>

        ${res.crew_needed ? `
            <div style="margin-top:16px;padding:12px 16px;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:var(--radius-sm);display:flex;align-items:center;gap:12px">
                <span style="font-size:20px">🔧</span>
                <div>
                    <div style="font-weight:600;color:var(--high)">${res.crew_type}</div>
                    <div style="font-size:12px;color:var(--text-secondary)">Specialized crew deployment required</div>
                </div>
            </div>
        ` : ''}

        ${res.vehicle_note ? `
            <div style="margin-top:12px;padding:12px 16px;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);border-radius:var(--radius-sm);display:flex;align-items:center;gap:12px">
                <span style="font-size:20px">🚗</span>
                <div>
                    <div style="font-weight:600;color:var(--blue)">Vehicle Note</div>
                    <div style="font-size:12px;color:var(--text-secondary)">${res.vehicle_note}</div>
                </div>
            </div>
        ` : ''}
    `;
}

function renderMultipliers(res) {
    const container = document.getElementById('resource-multipliers');
    if (!container || !res.multipliers) return;

    const m = res.multipliers;
    container.innerHTML = `
        <div class="multiplier-card">
            <div class="multiplier-value">${m.total}</div>
            <div class="multiplier-label">Total Multiplier</div>
        </div>
        <div class="multiplier-card">
            <div class="multiplier-value" style="font-size:14px">${m.corridor_tier}</div>
            <div class="multiplier-label">Corridor Factor</div>
        </div>
        <div class="multiplier-card">
            <div class="multiplier-value" style="font-size:14px">${m.risk_class}</div>
            <div class="multiplier-label">Risk Factor</div>
        </div>
        <div class="multiplier-card">
            <div class="multiplier-value" style="font-size:14px">${m.rush_hour}</div>
            <div class="multiplier-label">Time Factor</div>
        </div>
    `;
}
