// tab-regions.js — Regions tab for Germany EV Charger Dashboard
// Loaded via <script src> in index.html
// Defines global: renderRegionsTab(stateFilter, districtFilter)

(function () {
  const style = document.createElement('style');
  style.textContent = `
    /* ─── regions tab ─── */
    .region-cards {
      display: flex;
      gap: 10px;
      margin-bottom: 18px;
    }

    .region-card {
      flex: 1;
      min-width: 0;
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .card-label {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: #9ca3af;
    }

    .card-value {
      font-size: 13px;
      font-weight: 600;
      color: #111827;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .card-detail {
      font-size: 11px;
      color: #6b7280;
      font-feature-settings: 'tnum';
    }

    /* ─── regions table ─── */
    .regions-table-scroll {
      max-height: 420px;
      overflow-y: auto;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
    }

    .regions-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
      font-feature-settings: 'tnum';
    }

    .regions-table thead th {
      position: sticky;
      top: 0;
      background: #fff;
      font-weight: 600;
      color: #374151;
      text-align: left;
      padding: 6px 4px 5px;
      border-bottom: 1px solid #e5e7eb;
      white-space: nowrap;
      z-index: 1;
    }

    .regions-table thead th.col-num {
      text-align: right;
    }

    .regions-table thead th.col-gap {
      text-align: left;
    }

    .regions-table tbody tr {
      cursor: pointer;
      transition: background 0.1s;
    }

    .regions-table tbody tr:hover td {
      background: #f3f4f6 !important;
    }

    .regions-table tbody tr.row-selected td {
      background: #f0f9ff !important;
    }

    .regions-table tbody tr:not(:last-child) td {
      border-bottom: 1px solid #f3f4f6;
    }

    .regions-table td {
      padding: 4px 4px;
      color: #374151;
      background: #fff;
    }

    .regions-table tbody tr:nth-child(even) td {
      background: #fafafa;
    }

    .regions-table td.col-name {
      max-width: 110px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-weight: 500;
      color: #111827;
    }

    .regions-table td.col-num {
      text-align: right;
      color: #4b5563;
    }

    .gap-bar-wrap {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .gap-bar-bg {
      flex: 0 0 36px;
      height: 6px;
      background: #e5e7eb;
      border-radius: 3px;
      overflow: hidden;
    }

    .gap-bar-fill {
      height: 100%;
      border-radius: 3px;
    }

    .gap-score-val {
      font-size: 11px;
      color: #6b7280;
      white-space: nowrap;
    }

    .sort-indicator {
      font-size: 9px;
      margin-left: 3px;
      color: #9ca3af;
    }

    .regions-empty {
      padding: 24px;
      text-align: center;
      color: #9ca3af;
      font-size: 13px;
    }
  `;
  document.head.appendChild(style);
})();

// ─── gap score color ──────────────────────────────────────────────────────────
function _gapColor(score) {
  // 0–15 green, 15–30 amber, 30+ red
  const t = Math.min(1, score / 50);
  if (t < 0.3) return '#10B981';
  if (t < 0.6) return '#F59E0B';
  return '#EF4444';
}

// ─── smart population format ──────────────────────────────────────────────────
function _fmtPopSmart(n, isDistrict) {
  if (!n || n === 0) return '—';
  if (isDistrict) {
    // districts: use fmtK (e.g. 635k)
    if (typeof fmtK === 'function') return fmtK(n);
    return n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : Math.round(n / 1000) + 'k';
  }
  // states: use fmtPop (e.g. 11.1M)
  if (typeof fmtPop === 'function') return fmtPop(n);
  return (n / 1e6).toFixed(1) + 'M';
}

// ─── main render function ─────────────────────────────────────────────────────
function renderRegionsTab(stateFilter, districtFilter) {
  const summaryEl = document.getElementById('regions-summary');
  const tableEl = document.getElementById('regions-table-wrap');

  if (!summaryEl || !tableEl) return;

  if (!analyticsData || !analyticsData.regions) {
    summaryEl.innerHTML = '';
    tableEl.innerHTML = '<div class="regions-empty">No analytics data available.</div>';
    return;
  }

  const regData = analyticsData.regions;
  const isDistrict = !!stateFilter;

  let rows;
  let showingDistricts = false;

  if (!stateFilter) {
    // Germany view: show all 16 states
    rows = (regData.states || []).slice().sort((a, b) => b.gap_score - a.gap_score);
    showingDistricts = false;
  } else {
    // State selected: show districts within that state
    rows = (regData.districts || [])
      .filter(d => d.state_id === stateFilter)
      .slice()
      .sort((a, b) => b.gap_score - a.gap_score);
    showingDistricts = true;
  }

  // ─── summary cards ────────────────────────────────────────────────────────

  const worst = rows.length > 0 ? rows[0] : null;
  const best  = rows.length > 0 ? rows[rows.length - 1] : null;

  // National/state avg: weighted average of per_100k
  let avgPer100k = 0;
  if (rows.length > 0) {
    const totalPop = rows.reduce((s, r) => s + (r.population || 0), 0);
    if (totalPop > 0) {
      // per_100k = charge_points / population * 100000
      const totalCP = rows.reduce((s, r) => s + (r.charge_points || 0), 0);
      avgPer100k = totalCP / totalPop * 100000;
    } else {
      // fallback: simple mean
      avgPer100k = rows.reduce((s, r) => s + (r.per_100k || 0), 0) / rows.length;
    }
  }

  function truncName(name, max) {
    if (!name) return '—';
    return name.length > max ? name.slice(0, max - 1) + '…' : name;
  }

  const avgLabel = stateFilter ? 'State avg' : 'National avg';

  summaryEl.innerHTML = `
    <div class="region-cards">
      <div class="region-card">
        <span class="card-label">Largest gap</span>
        <span class="card-value" title="${worst ? worst.name : ''}">${worst ? truncName(worst.name, 22) : '—'}</span>
        <span class="card-detail">${worst ? 'Score: ' + worst.gap_score.toFixed(1) : ''}</span>
      </div>
      <div class="region-card">
        <span class="card-label">Best covered</span>
        <span class="card-value" title="${best ? best.name : ''}">${best ? truncName(best.name, 22) : '—'}</span>
        <span class="card-detail">${best ? 'Score: ' + best.gap_score.toFixed(1) : ''}</span>
      </div>
      <div class="region-card">
        <span class="card-label">${avgLabel}</span>
        <span class="card-value">${avgPer100k.toFixed(1)}</span>
        <span class="card-detail">chargers / 100k pop</span>
      </div>
    </div>
  `;

  // ─── KPI table ────────────────────────────────────────────────────────────

  if (rows.length === 0) {
    tableEl.innerHTML = '<div class="regions-empty">No data for selected region.</div>';
    return;
  }

  const headerLabel = showingDistricts ? 'District' : 'State';

  let bodyHtml = '';
  for (const row of rows) {
    const isSelected = showingDistricts && districtFilter && row.id === districtFilter;
    const pop = row.population;
    const hasPop = pop && pop > 0;

    const popStr = hasPop ? _fmtPopSmart(pop, showingDistricts) : '—';
    const sitesStr = row.sites != null ? row.sites.toLocaleString('de-DE') : '—';
    const per100kStr = hasPop ? row.per_100k.toFixed(1) : '—';
    const coverageStr = row.coverage_pct_5km != null ? row.coverage_pct_5km.toFixed(1) + '%' : '—';
    const hpcStr = row.pct_hpc_plus != null ? row.pct_hpc_plus.toFixed(1) + '%' : '—';
    const gapScore = row.gap_score != null ? row.gap_score : 0;
    const gapPct = Math.min(1, gapScore / 50) * 100;
    const gapColor = _gapColor(gapScore);

    bodyHtml += `
      <tr class="${isSelected ? 'row-selected' : ''}" data-id="${row.id}" data-level="${showingDistricts ? 'district' : 'state'}">
        <td class="col-name" title="${row.name || ''}">${row.name || '—'}</td>
        <td class="col-num">${popStr}</td>
        <td class="col-num">${sitesStr}</td>
        <td class="col-num">${per100kStr}</td>
        <td class="col-num">${coverageStr}</td>
        <td class="col-num">${hpcStr}</td>
        <td>
          <div class="gap-bar-wrap">
            <div class="gap-bar-bg">
              <div class="gap-bar-fill" style="width:${gapPct.toFixed(1)}%;background:${gapColor};"></div>
            </div>
            <span class="gap-score-val">${gapScore.toFixed(1)}</span>
          </div>
        </td>
      </tr>
    `;
  }

  tableEl.innerHTML = `
    <div class="regions-table-scroll">
      <table class="regions-table">
        <thead>
          <tr>
            <th>${headerLabel}</th>
            <th class="col-num">Pop</th>
            <th class="col-num">Sites</th>
            <th class="col-num">/100k</th>
            <th class="col-num">Cov%</th>
            <th class="col-num">HPC+%</th>
            <th class="col-gap">Gap ▼</th>
          </tr>
        </thead>
        <tbody>
          ${bodyHtml}
        </tbody>
      </table>
    </div>
  `;

  // ─── row click handlers ───────────────────────────────────────────────────

  tableEl.querySelectorAll('tbody tr').forEach(tr => {
    tr.addEventListener('click', () => {
      const id = tr.dataset.id;
      const level = tr.dataset.level;
      if (!id) return;

      if (level === 'state') {
        if (typeof stateSelect !== 'undefined') {
          stateSelect.value = id;
          stateSelect.dispatchEvent(new Event('change'));
        }
      } else if (level === 'district') {
        if (typeof districtSelect !== 'undefined') {
          districtSelect.value = id;
          districtSelect.dispatchEvent(new Event('change'));
        }
      }
    });
  });

  // ─── scroll selected row into view ───────────────────────────────────────

  if (districtFilter) {
    const selectedRow = tableEl.querySelector('tr.row-selected');
    if (selectedRow) {
      selectedRow.scrollIntoView({ block: 'nearest' });
    }
  }
}
