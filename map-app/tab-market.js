// tab-market.js — Market tab for Germany EV Charger Dashboard
// Defines window.renderMarketTab(stateFilter)
// Loaded via <script src> in index.html

(function () {
  const style = document.createElement('style');
  style.textContent = `
    /* ── market tab ─────────────────────────────────────────────────── */
    .market-stats {
      display: flex;
      gap: 0;
      margin-bottom: 20px;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      overflow: hidden;
    }
    .market-stat {
      flex: 1 1 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 12px 8px 10px;
      border-right: 1px solid #e5e7eb;
      min-width: 0;
    }
    .market-stat:last-child { border-right: none; }
    .stat-value {
      font-size: 20px;
      font-weight: 600;
      color: #1a1a1a;
      line-height: 1.1;
      letter-spacing: -0.02em;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }
    .stat-label {
      font-size: 11px;
      color: #9ca3af;
      margin-top: 3px;
      font-weight: 400;
      letter-spacing: 0.01em;
      white-space: nowrap;
    }

    /* ── operators table ─────────────────────────────────────────────── */
    .market-section-label {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #9ca3af;
      margin-bottom: 8px;
      margin-top: 20px;
    }
    .ops-wrap {
      max-height: 290px;
      overflow-y: auto;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      -webkit-overflow-scrolling: touch;
    }
    .ops-wrap::-webkit-scrollbar { width: 5px; }
    .ops-wrap::-webkit-scrollbar-track { background: transparent; }
    .ops-wrap::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
    .ops-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      font-family: inherit;
    }
    .ops-table thead th {
      position: sticky;
      top: 0;
      background: #f9fafb;
      border-bottom: 1px solid #e5e7eb;
      padding: 5px 8px;
      text-align: right;
      font-weight: 600;
      color: #6b7280;
      font-size: 11px;
      white-space: nowrap;
      z-index: 1;
    }
    .ops-table thead th:first-child { text-align: center; width: 28px; }
    .ops-table thead th:nth-child(2) { text-align: left; }
    .ops-table tbody tr {
      border-bottom: 1px solid #f3f4f6;
      transition: background 0.1s;
    }
    .ops-table tbody tr:last-child { border-bottom: none; }
    .ops-table tbody tr:hover { background: #f9fafb; }
    .ops-table td {
      padding: 4px 8px;
      text-align: right;
      color: #374151;
      font-feature-settings: 'tnum';
      white-space: nowrap;
    }
    .ops-table td:first-child {
      text-align: center;
      color: #9ca3af;
      font-size: 11px;
    }
    .ops-table td:nth-child(2) {
      text-align: left;
      max-width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: #111;
    }
    .ops-table td.num {
      font-family: 'JetBrains Mono', 'SF Mono', 'Menlo', monospace;
      font-feature-settings: 'tnum';
    }
    .ops-table td.hpc-pct {
      color: #f59e0b;
    }
    .ops-state-note {
      font-size: 11px;
      color: #9ca3af;
      margin-top: 5px;
      font-style: italic;
    }

    /* ── growth chart ────────────────────────────────────────────────── */
    .growth-section { margin-top: 20px; }
    .growth-legend {
      display: flex;
      gap: 12px;
      margin-bottom: 8px;
      font-size: 11px;
      color: #6b7280;
      flex-wrap: wrap;
    }
    .growth-legend-item {
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .growth-legend-swatch {
      width: 10px;
      height: 10px;
      border-radius: 2px;
      flex-shrink: 0;
    }
    .growth-chart-wrap {
      position: relative;
    }
    #growth-chart { width: 100%; display: block; cursor: crosshair; }
    .growth-tooltip {
      position: absolute;
      pointer-events: none;
      display: none;
      background: rgba(0,0,0,0.82);
      color: #fff;
      font-size: 11px;
      padding: 6px 10px;
      border-radius: 5px;
      white-space: nowrap;
      transform: translateX(-50%);
      line-height: 1.5;
      max-width: 260px;
      white-space: normal;
      text-align: center;
    }
  `;
  document.head.appendChild(style);
})();

// ── constants ────────────────────────────────────────────────────────────────
const GROWTH_CLASSES = [
  { key: 'ac_normal', label: 'AC Normal',  color: '#3B82F6' },
  { key: 'fast_50',   label: 'DC Fast',    color: '#10B981' },
  { key: 'hpc_150',   label: 'HPC 150+',  color: '#F59E0B' },
  { key: 'ultra_300', label: 'Ultra 300+', color: '#EF4444' },
];

// ── helpers ──────────────────────────────────────────────────────────────────
function _fmtK(n) {
  if (typeof fmtK === 'function') return fmtK(n);
  if (n >= 1000) return (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'k';
  return n.toLocaleString('de-DE');
}

function _fmtNum(n) {
  return Number(n).toLocaleString('de-DE');
}

// ── growth chart state ────────────────────────────────────────────────────────
let _growthHoverYear = -1;
let _growthBound = false;

// ── main render function ──────────────────────────────────────────────────────
function renderMarketTab(stateFilter) {
  const data = analyticsData;
  if (!data) {
    document.getElementById('market-summary').innerHTML =
      '<p style="color:#9ca3af;font-size:13px;padding:8px 0">Loading market data…</p>';
    document.getElementById('market-operators').innerHTML = '';
    return;
  }

  // Resolve state name from stateFilter ID (e.g. "08" → "Baden-Württemberg")
  let stateName = null;
  if (stateFilter && regions && regions.states) {
    const s = regions.states.find(st => st.id === stateFilter);
    if (s) stateName = s.name;
  }

  renderSummary(data, stateName);
  renderOperators(data, stateName);
  renderGrowthChart(data);
}

// ── summary cards ─────────────────────────────────────────────────────────────
function renderSummary(data, stateName) {
  const el = document.getElementById('market-summary');
  const ms = data.market_summary || {};

  let ops, sites, cps, avgKw;

  if (stateName) {
    // Compute filtered totals from operators list
    const stateOps = (data.operators || []).filter(op =>
      op.by_state && op.by_state[stateName] > 0
    );
    ops = stateOps.length;
    sites = stateOps.reduce((s, op) => s + (op.by_state[stateName] || 0), 0);
    // CPs in state: use proportional estimate (by_state gives sites only in most schemas)
    // Try to get CPs from by_state if available, else estimate
    cps = stateOps.reduce((s, op) => {
      const stateSites = op.by_state[stateName] || 0;
      const totalSites = op.sites || 1;
      const frac = totalSites > 0 ? stateSites / totalSites : 0;
      return s + Math.round((op.charge_points || 0) * frac);
    }, 0);
    avgKw = stateOps.length > 0
      ? (stateOps.reduce((s, op) => s + (op.avg_kw_per_site || 0), 0) / stateOps.length)
      : 0;
  } else {
    ops  = ms.total_operators || 0;
    sites = ms.total_sites || 0;
    cps   = ms.total_charge_points || 0;
    avgKw = ms.avg_site_power_kw || 0;
  }

  el.innerHTML = `
    <div class="market-stats">
      <div class="market-stat">
        <span class="stat-value">${_fmtNum(ops)}</span>
        <span class="stat-label">Operators</span>
      </div>
      <div class="market-stat">
        <span class="stat-value">${_fmtNum(sites)}</span>
        <span class="stat-label">Sites</span>
      </div>
      <div class="market-stat">
        <span class="stat-value">${_fmtK(cps)}</span>
        <span class="stat-label">Charge Points</span>
      </div>
      <div class="market-stat">
        <span class="stat-value">${Number(avgKw).toFixed(1)} kW</span>
        <span class="stat-label">Avg Site Power</span>
      </div>
    </div>
  `;
}

// ── operators table ────────────────────────────────────────────────────────────
function renderOperators(data, stateName) {
  const el = document.getElementById('market-operators');

  let operators = data.operators || [];
  let isFiltered = false;

  if (stateName) {
    isFiltered = true;
    // Filter to operators with sites in this state, sort by state CPs (estimated)
    operators = operators
      .filter(op => op.by_state && op.by_state[stateName] > 0)
      .map(op => {
        const stateSites = op.by_state[stateName] || 0;
        const totalSites = op.sites || 1;
        const frac = totalSites > 0 ? stateSites / totalSites : 0;
        return {
          ...op,
          _stateSites: stateSites,
          _stateCPs: Math.round((op.charge_points || 0) * frac),
        };
      })
      .sort((a, b) => b._stateCPs - a._stateCPs);
  }

  // Always sort the "Other (…)" aggregate to the bottom, regardless of charge point count
  const otherEntries = operators.filter(op => (op.name || '').startsWith('Other ('));
  const normalEntries = operators.filter(op => !(op.name || '').startsWith('Other ('));
  operators = [...normalEntries, ...otherEntries];

  const rows = operators.slice(0, 100).map((op, i) => {
    const sitesVal  = isFiltered ? op._stateSites : (op.sites || 0);
    const cpsVal    = isFiltered ? op._stateCPs   : (op.charge_points || 0);
    const avgKw     = Number(op.avg_kw_per_site || 0).toFixed(1);
    const hpcPct    = Number(op.pct_hpc_plus || 0).toFixed(1);
    const name      = op.name || '—';

    return `
      <tr title="${_escHtml(name)}">
        <td>${i + 1}</td>
        <td>${_escHtml(name)}</td>
        <td class="num">${_fmtNum(sitesVal)}</td>
        <td class="num">${_fmtK(cpsVal)}</td>
        <td class="num">${avgKw}</td>
        <td class="num hpc-pct">${hpcPct}%</td>
      </tr>
    `;
  }).join('');

  const note = isFiltered
    ? `<div class="ops-state-note">Showing operators active in ${_escHtml(stateName)}. Sites/CPs reflect that state only.</div>`
    : '';

  el.innerHTML = `
    <div class="market-section-label">Top Operators</div>
    ${note}
    <div class="ops-wrap">
      <table class="ops-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Operator</th>
            <th>Sites</th>
            <th>CPs</th>
            <th>kW avg</th>
            <th>HPC+%</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

// ── growth stacked area chart ─────────────────────────────────────────────────
function renderGrowthChart(data) {
  const wrap = document.getElementById('market-growth-wrap');

  // Inject legend + tooltip wrapper once
  if (!wrap.querySelector('.growth-section')) {
    const legendItems = GROWTH_CLASSES.map(cls => `
      <div class="growth-legend-item">
        <div class="growth-legend-swatch" style="background:${cls.color}"></div>
        <span>${cls.label}</span>
      </div>
    `).join('');

    wrap.innerHTML = `
      <div class="growth-section">
        <div class="market-section-label">Infrastructure Growth (Cumulative Sites)</div>
        <div class="growth-legend">${legendItems}</div>
        <div class="growth-chart-wrap">
          <canvas id="growth-chart" height="240"></canvas>
          <div class="growth-tooltip" id="growth-tooltip"></div>
        </div>
      </div>
    `;
  }

  const growthData = data.growth || [];
  if (growthData.length === 0) {
    wrap.innerHTML += '<p style="color:#9ca3af;font-size:12px">No growth data available.</p>';
    return;
  }

  _drawGrowthChart(growthData);

  if (!_growthBound) {
    _growthBound = true;
    const canvas = document.getElementById('growth-chart');
    const tooltip = document.getElementById('growth-tooltip');

    canvas.addEventListener('mousemove', (e) => {
      const ci = canvas._chartInfo;
      if (!ci) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const { pad, years, pw, xS } = ci;
      if (x < pad.l || x > pad.l + pw) {
        tooltip.style.display = 'none';
        _growthHoverYear = -1;
        _drawGrowthChart(ci.growthData);
        return;
      }
      const fraction = (x - pad.l) / pw;
      const yearIndex = Math.round(fraction * (years.length - 1));
      const year = years[Math.max(0, Math.min(years.length - 1, yearIndex))];

      if (year !== _growthHoverYear) {
        _growthHoverYear = year;
        _drawGrowthChart(ci.growthData);
      }

      // Build tooltip
      const entry = ci.growthData.find(g => g.year === year);
      if (!entry) { tooltip.style.display = 'none'; return; }
      const n = entry.new || {};
      const ac   = n.ac_normal  || 0;
      const fast = n.fast_50    || 0;
      const hpc  = n.hpc_150   || 0;
      const ultra= n.ultra_300  || 0;
      const total = entry.total_new || (ac + fast + hpc + ultra);
      tooltip.innerHTML =
        `<strong>${year}</strong>: +${_fmtK(total)} sites<br>` +
        `${_fmtK(ac)} AC · ${_fmtK(fast)} Fast · ${_fmtK(hpc)} HPC · ${_fmtK(ultra)} Ultra`;

      const cx = xS(year);
      tooltip.style.display = 'block';
      // Keep tooltip within chart bounds
      const tooltipX = Math.min(Math.max(cx, 60), rect.width - 60);
      tooltip.style.left = tooltipX + 'px';
      tooltip.style.top = (pad.t - 4) + 'px';
    });

    canvas.addEventListener('mouseleave', () => {
      tooltip.style.display = 'none';
      _growthHoverYear = -1;
      const ci = document.getElementById('growth-chart')._chartInfo;
      if (ci) _drawGrowthChart(ci.growthData);
    });
  }
}

function _drawGrowthChart(growthData) {
  const canvas = document.getElementById('growth-chart');
  if (!canvas) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  const w = Math.floor(rect.width) || 360;
  const h = 240;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const pad = { t: 14, r: 14, b: 32, l: 48 };
  const pw = w - pad.l - pad.r;
  const ph = h - pad.t - pad.b;

  ctx.clearRect(0, 0, w, h);

  // Collect years
  const sorted = [...growthData].sort((a, b) => a.year - b.year);
  const years = sorted.map(g => g.year);
  const minYear = years[0];
  const maxYear = years[years.length - 1];

  const xS = (year) => pad.l + ((year - minYear) / (maxYear - minYear)) * pw;
  const yS = (val)  => pad.t + (1 - val / maxCumulative) * ph;

  // Compute stacked cumulative totals per year
  // stack order: ac_normal, fast_50, hpc_150, ultra_300 (bottom to top)
  const stackedData = sorted.map(g => {
    const cum = g.cumulative || {};
    const ac    = cum.ac_normal  || 0;
    const fast  = cum.fast_50   || 0;
    const hpc   = cum.hpc_150  || 0;
    const ultra = cum.ultra_300 || 0;
    return {
      year: g.year,
      ac, fast, hpc, ultra,
      // stacked bases (cumulative from bottom)
      s0: 0,
      s1: ac,
      s2: ac + fast,
      s3: ac + fast + hpc,
      s4: ac + fast + hpc + ultra,
    };
  });

  const maxCumulative = Math.max(...stackedData.map(d => d.s4)) * 1.05 || 1;

  // Draw grid lines
  ctx.strokeStyle = '#f3f4f6';
  ctx.lineWidth = 1;
  const yTicks = 4;
  for (let i = 0; i <= yTicks; i++) {
    const v = (i / yTicks) * maxCumulative;
    const y = yS(v);
    ctx.beginPath();
    ctx.moveTo(pad.l, y);
    ctx.lineTo(pad.l + pw, y);
    ctx.stroke();
  }

  // Stacked area drawing (bottom to top: ac, fast, hpc, ultra)
  const layers = [
    { topKey: 's1', botKey: 's0', color: GROWTH_CLASSES[0].color }, // ac_normal
    { topKey: 's2', botKey: 's1', color: GROWTH_CLASSES[1].color }, // fast_50
    { topKey: 's3', botKey: 's2', color: GROWTH_CLASSES[2].color }, // hpc_150
    { topKey: 's4', botKey: 's3', color: GROWTH_CLASSES[3].color }, // ultra_300
  ];

  for (const layer of layers) {
    const topPts = stackedData.map(d => ({ x: xS(d.year), y: yS(d[layer.topKey]) }));
    const botPts = [...stackedData].reverse().map(d => ({ x: xS(d.year), y: yS(d[layer.botKey]) }));

    ctx.beginPath();
    _catmullRomPath(ctx, topPts);
    _catmullRomPath(ctx, botPts, true);
    ctx.closePath();

    // Fill with semi-transparent color
    ctx.fillStyle = layer.color + 'bb';
    ctx.fill();

    // Draw top stroke
    ctx.beginPath();
    _catmullRomPath(ctx, topPts);
    ctx.strokeStyle = layer.color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  // Hover vertical line
  if (_growthHoverYear >= minYear && _growthHoverYear <= maxYear) {
    const hx = xS(_growthHoverYear);
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(0,0,0,0.35)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.moveTo(hx, pad.t);
    ctx.lineTo(hx, pad.t + ph);
    ctx.stroke();
    ctx.setLineDash([]);

    // Dots on each layer top
    const d = stackedData.find(dd => dd.year === _growthHoverYear);
    if (d) {
      const tops = [d.s1, d.s2, d.s3, d.s4];
      for (let i = 0; i < 4; i++) {
        ctx.beginPath();
        ctx.arc(hx, yS(tops[i]), 3.5, 0, Math.PI * 2);
        ctx.fillStyle = GROWTH_CLASSES[i].color;
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }
  }

  // Y-axis labels
  ctx.fillStyle = '#9ca3af';
  ctx.font = '10px -apple-system, Inter, sans-serif';
  ctx.textAlign = 'right';
  for (let i = 0; i <= yTicks; i++) {
    const v = (i / yTicks) * maxCumulative;
    const y = yS(v);
    ctx.fillText(_fmtK(Math.round(v)), pad.l - 5, y + 3.5);
  }

  // X-axis year labels
  ctx.textAlign = 'center';
  ctx.fillStyle = '#9ca3af';
  ctx.font = '10px -apple-system, Inter, sans-serif';
  const xTickStep = years.length <= 12 ? 1 : 2;
  years.forEach((yr, idx) => {
    if (idx % xTickStep !== 0) return;
    const x = xS(yr);
    ctx.fillText(String(yr), x, pad.t + ph + 18);
    // Tick mark
    ctx.beginPath();
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    ctx.moveTo(x, pad.t + ph);
    ctx.lineTo(x, pad.t + ph + 4);
    ctx.stroke();
  });

  // Store chart info for hover
  canvas._chartInfo = { pad, years, minYear, maxYear, pw, ph, xS, yS, growthData: sorted };
}

// Catmull-Rom spline path helper
function _catmullRomPath(ctx, pts, reverse) {
  if (!pts || pts.length === 0) return;
  if (reverse) {
    // Draw lines back for the bottom of the area
    ctx.lineTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) {
      const p0 = pts[Math.max(0, i - 2)];
      const p1 = pts[i - 1];
      const p2 = pts[i];
      const p3 = pts[Math.min(pts.length - 1, i + 1)];
      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;
      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
    }
  } else {
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) {
      const p0 = pts[Math.max(0, i - 2)];
      const p1 = pts[i - 1];
      const p2 = pts[i];
      const p3 = pts[Math.min(pts.length - 1, i + 1)];
      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;
      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
    }
  }
}

// HTML escape helper
function _escHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Expose as global
window.renderMarketTab = renderMarketTab;
