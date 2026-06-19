/* ═══════════════════════════════════════════════════════════════════
   Page 5 — Explainability + What-If Analysis
   ═══════════════════════════════════════════════════════════════════ */

window.addEventListener('page:explainability', renderExplainPage);

function renderExplainPage() {
    const shapData = ASTRAM.lastShap;
    const pred = ASTRAM.lastPrediction;
    const params = ASTRAM.lastParams;

    if (!shapData || !pred || !params) return;

    renderFullShap(shapData, pred);
    renderWhatIfControls(params, pred);
}

function renderFullShap(shapData, pred) {
    const container = document.getElementById('explain-shap');
    if (!container) return;

    const features = shapData.features.slice(0, 12);
    const maxAbs = Math.max(...features.map(f => Math.abs(f.shap_value)), 1);

    let html = `
        <div style="text-align:center;margin-bottom:20px">
            <div style="font-size:13px;color:var(--text-muted)">Base Score</div>
            <div style="font-size:20px;font-weight:700">${shapData.base_value.toFixed(1)}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:4px">→ Final: <span style="color:${getClassColor(pred.impact_class)};font-weight:700">${pred.score}</span> (${pred.impact_class})</div>
        </div>
        <div style="display:flex;justify-content:center;gap:24px;margin-bottom:16px;font-size:11px">
            <span style="display:flex;align-items:center;gap:4px">
                <span style="width:12px;height:12px;border-radius:2px;background:rgba(239,68,68,0.6)"></span>
                Pushes score UP
            </span>
            <span style="display:flex;align-items:center;gap:4px">
                <span style="width:12px;height:12px;border-radius:2px;background:rgba(59,130,246,0.6)"></span>
                Pushes score DOWN
            </span>
        </div>
    `;

    html += features.map(f => {
        const pct = (Math.abs(f.shap_value) / maxAbs * 45).toFixed(1);
        const isPositive = f.shap_value > 0;
        const barClass = isPositive ? 'positive' : 'negative';
        const sign = isPositive ? '+' : '';
        const color = isPositive ? 'var(--critical)' : 'var(--blue)';

        return `
            <div class="shap-bar">
                <span class="shap-label">${f.feature}</span>
                <div class="shap-bar-container">
                    <div class="shap-bar-fill ${barClass}" style="width:${pct}%"></div>
                </div>
                <span class="shap-value" style="color:${color}">${sign}${f.shap_value.toFixed(2)}</span>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

function renderWhatIfControls(params, pred) {
    const panel = document.getElementById('whatif-panel');
    if (!panel) return;

    const scenarios = [
        {
            label: 'Road Closure',
            currentValue: params.requires_road_closure ? 'Yes' : 'No',
            change: { requires_road_closure: !params.requires_road_closure },
            newValue: params.requires_road_closure ? 'No' : 'Yes',
        },
        {
            label: 'Corridor → Non-corridor',
            currentValue: params.corridor,
            change: { corridor: 'Non-corridor' },
            newValue: 'Non-corridor',
            skip: params.corridor === 'Non-corridor',
        },
        {
            label: 'Corridor → Bellary Road 1 (Tier 1)',
            currentValue: params.corridor,
            change: { corridor: 'Bellary Road 1' },
            newValue: 'Bellary Road 1',
            skip: params.corridor === 'Bellary Road 1',
        },
        {
            label: 'Time → Rush Hour (09:00)',
            currentValue: `${String(params.hour).padStart(2,'0')}:00`,
            change: { hour: 9 },
            newValue: '09:00',
            skip: params.hour === 9,
        },
        {
            label: 'Time → Night (02:00)',
            currentValue: `${String(params.hour).padStart(2,'0')}:00`,
            change: { hour: 2 },
            newValue: '02:00',
            skip: params.hour === 2,
        },
        {
            label: 'Weekend → Weekday',
            currentValue: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][params.weekday],
            change: { weekday: params.weekday >= 5 ? 2 : 5 },
            newValue: params.weekday >= 5 ? 'Wednesday' : 'Saturday',
        },
    ];

    const validScenarios = scenarios.filter(s => !s.skip);

    panel.innerHTML = `
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:12px">
            Click any scenario to see how the impact score changes
        </div>
        ${validScenarios.map((s, i) => `
            <div class="whatif-toggle" style="cursor:pointer" onclick="runWhatIf(${i})">
                <div>
                    <div style="font-weight:600;color:var(--text-primary)">${s.label}</div>
                    <div style="font-size:11px;color:var(--text-muted)">Current: ${s.currentValue}</div>
                </div>
                <span style="font-size:18px;color:var(--blue)">→</span>
            </div>
        `).join('')}
    `;

    // Store scenarios for click handler
    window._whatifScenarios = validScenarios;
}

async function runWhatIf(index) {
    const scenario = window._whatifScenarios[index];
    if (!scenario || !ASTRAM.lastParams) return;

    const resultDiv = document.getElementById('whatif-result');
    if (!resultDiv) return;

    resultDiv.innerHTML = '<p style="text-align:center;color:var(--text-muted)">Computing...</p>';

    try {
        const result = await apiPost('/api/whatif', {
            base: ASTRAM.lastParams,
            changes: scenario.change,
        });

        const deltaColor = result.delta > 0 ? 'positive' : 'negative';
        const deltaSign = result.delta > 0 ? '+' : '';

        resultDiv.innerHTML = `
            <div style="text-align:center;margin-bottom:12px;font-weight:600;color:var(--text-secondary)">
                ${scenario.label}
            </div>
            <div class="whatif-comparison">
                <div class="whatif-box original">
                    <div class="whatif-score" style="color:${getClassColor(result.original.impact_class)}">${result.original.score}</div>
                    <div class="whatif-label">${result.original.impact_class}</div>
                    <div style="font-size:10px;color:var(--text-muted);margin-top:4px">Original</div>
                </div>
                <div class="whatif-arrow">→</div>
                <div class="whatif-box modified">
                    <div class="whatif-score" style="color:${getClassColor(result.modified.impact_class)}">${result.modified.score}</div>
                    <div class="whatif-label">${result.modified.impact_class}</div>
                    <div style="font-size:10px;color:var(--text-muted);margin-top:4px">Modified</div>
                </div>
            </div>
            <div class="whatif-delta ${deltaColor}">
                ${deltaSign}${result.delta} points
            </div>
        `;
    } catch (e) {
        resultDiv.innerHTML = '<p style="text-align:center;color:var(--critical)">Error computing counterfactual</p>';
    }
}
