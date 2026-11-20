// The Dimensions sheet (#planmodal): the architect's schedule of rooms, windows and doors beside the
// dimensioned plan. Ported from the single-file page with the same ids and behaviour; the data now comes
// from assets/data/measurements.json and the drawing from assets/plans/dimension-plan.svg (fetched,
// then put into #dimensionPlan).
//
// opts: data (measurements.json), planSvg (text of the SVG file), ui (createUI()), visit(node) (go to a
// sweep in 3D; absent when there is no 3D view).
// Returns {select(id), list(tab), format(v), csv(), open(id?), selected, units}; also window.MEASURE.

export function createDimensions(opts) {
  const { ui } = opts;
  const { $, ft, toast, closeModals, openModal, downloadBlob, esc } = ui;
  const M = opts.data || { rooms: [], windows: [], doors: [] };
  const map = Object.fromEntries([...M.rooms, ...M.windows, ...M.doors].map((x) => [x.id, x]));
  let units = 'ft', tab = 'rooms', selected = M.rooms[0] ? M.rooms[0].id : null, zoom = 100;

  // the plan drawing
  if (opts.planSvg) {
    const doc = new DOMParser().parseFromString(opts.planSvg, 'image/svg+xml');
    const svg = doc.documentElement;
    if (svg && svg.nodeName.toLowerCase() === 'svg') $('dimensionPlan').replaceChildren(document.importNode(svg, true));
  }
  if (!$('dimensionPlan').firstElementChild) $('dimensionPlan').innerHTML = '<p class="dimension-small" style="padding:20px">The plan drawing could not be loaded. The schedules on the right are complete.</p>';

  function format(v) {
    if (v === null || v === undefined) return '—';
    return units === 'mm' ? Math.round(v * 304.8).toLocaleString() + ' mm' : ft(v);
  }
  const table = (headers, rows) => '<div class="dimension-table-wrap"><table><thead><tr>' + headers.map((h) => '<th>' + h + '</th>').join('') + '</tr></thead><tbody>' + rows.join('') + '</tbody></table></div>';
  const link = (id, label) => '<button class="dimension-link" data-select-measure="' + id + '">' + esc(label || id) + '</button>';
  const stats = (items) => '<div class="dimension-stats">' + items.map(([label, value]) => '<div><small>' + label + '</small><strong>' + value + '</strong></div>').join('') + '</div>';

  function select(id) {
    const o = map[id];
    if (!o) return;
    selected = id;
    $('dimensionItem').value = id;
    $('dimensionDetailTitle').textContent = o.name;
    let c = '<span class="review-basis">' + o.basis + ' · ' + (o.basis === 'R' ? 'Retained original room label' : 'Proposed design size') + '</span>';
    if (o.kind === 'room') {
      c += stats([['Clear width', format(o.width_ft)], ['Clear depth', format(o.depth_ft)], ['Room area · excludes walls', o.area_sqft.toFixed(1) + ' sq ft']]) + '<p class="dimension-small">' + esc(o.note) + '</p>';
    } else {
      const roof = o.kind === 'skylight';
      c += stats([['Opening width', format(o.width)], [roof ? 'Opening depth' : 'Opening height', format(o.height)], ...(roof ? [] : [['Sill above floor', format(o.sill)], ['Head above floor', format(o.head)]])]);
      c += '<p class="dimension-small">' + esc(o.type) + '. Design opening dimensions; confirm existing sizes before ordering. These are not manufacturer rough-opening specifications.</p>';
    }
    $('dimensionDetail').innerHTML = c;
    document.querySelectorAll('#dimensionPlan [data-measure]').forEach((e) => e.classList.toggle('selected', e.dataset.measure === id));
  }
  function list(t) {
    tab = t;
    document.querySelectorAll('[data-dimension-tab]').forEach((b) => {
      b.classList.toggle('active', b.dataset.dimensionTab === t);
      b.setAttribute('aria-pressed', String(b.dataset.dimensionTab === t));
    });
    const q = $('dimensionSearch').value.toLowerCase().trim(), items = (M[t] || []).filter((x) => (x.id + ' ' + x.name).toLowerCase().includes(q));
    const headers = t === 'rooms' ? ['Room', 'Clear width × depth', 'Room sq ft', 'Basis'] : ['Opening', 'Width × height/depth', 'Sill', 'Basis'];
    const rows = items.map((o) => '<tr><td>' + link(o.id, t === 'rooms' ? o.name : o.id + ' · ' + o.name) + '</td><td>' + format(o.width_ft ?? o.width) + ' × ' + format(o.depth_ft ?? o.height) + '</td><td>' + (t === 'rooms' ? o.area_sqft.toFixed(1) : o.kind === 'skylight' ? 'Roof' : format(o.sill)) + '</td><td>' + o.basis + '</td></tr>');
    $('dimensionListing').innerHTML = '<h3>' + items.length + ' ' + t + '</h3>' + table(headers, rows);
  }
  function csv() {
    const rows = [['Category', 'ID', 'Description', 'Width_ft', 'Depth_or_height_ft', 'Room_area_sqft', 'Sill_ft', 'Basis', 'Notes']];
    for (const r of M.rooms) rows.push(['Room', r.id, r.name, r.width_ft, r.depth_ft, r.area_sqft, '', r.basis, r.note]);
    for (const o of [...M.windows, ...M.doors]) rows.push([o.kind, o.id, o.name, o.width, o.height, '', o.sill, o.basis, o.type + '; proposed opening; existing size requires measurement.']);
    return rows.map((r) => r.map((v) => '"' + String(v ?? '').replace(/"/g, '""') + '"').join(',')).join('\r\n');
  }
  function setZoom(v) {
    zoom = Math.max(80, Math.min(240, v));
    $('dimensionPlan').style.width = zoom + '%';
    $('dimensionZoomLabel').textContent = zoom + '%';
  }
  // Print the live schedules with the plan.
  function planDocument() {
    const p = $('dimensionPlan').innerHTML;
    let t = '';
    for (const [key, title] of [['rooms', 'Rooms'], ['windows', 'Windows and skylight'], ['doors', 'Doors']]) {
      t += '<h2>' + title + '</h2><table><thead><tr><th>Opening / room</th><th>Size</th><th>Notes</th></tr></thead><tbody>' + M[key].map((o) => '<tr><td>' + esc(o.id + ' · ' + o.name) + '</td><td>' + format(o.width_ft ?? o.width) + ' × ' + format(o.depth_ft ?? o.height) + '</td><td>' + esc(o.note || o.type || '') + '</td></tr>').join('') + '</tbody></table>';
    }
    return '<!doctype html><html><head><title>1095 McKinley — revised dimensions</title><style>body{font:12px Arial;color:#263c35;margin:30px}h1{font-size:26px}h2{margin-top:25px}svg{width:100%;height:auto;max-height:900px}table{width:100%;border-collapse:collapse}th,td{padding:8px;border-bottom:1px solid #ddd;text-align:left}th{background:#edf1e8}tr{break-inside:avoid}section{break-after:page}@page{size:A4;margin:12mm}</style></head><body><h1>1095 W McKinley · Room dimensions + opening details</h1><p>Dimensions follow the architect’s plan · sizes/sizes.pdf, sheet SKA002 · Nov 13 2026 · clear interior sizes</p><section>' + p + '</section>' + t + '<p>Bay area is separate from the Bedroom 3 main rectangle. New heights and openings are proposed, not manufacturer rough openings.</p></body></html>';
  }

  $('dimensionItem').innerHTML = [['rooms', 'Rooms'], ['windows', 'Windows / skylight'], ['doors', 'Doors / closet openings']].map(([k, label]) => '<optgroup label="' + label + '">' + (M[k] || []).map((o) => '<option value="' + o.id + '">' + o.id + ' · ' + esc(o.name) + '</option>').join('') + '</optgroup>').join('');
  $('dimensionItem').addEventListener('change', (e) => select(e.target.value));
  $('dimensionUnits').addEventListener('change', (e) => { units = e.target.value; select(selected); list(tab); });
  $('dimensionSearch').addEventListener('input', () => list(tab));
  document.querySelectorAll('[data-dimension-tab]').forEach((b) => b.addEventListener('click', () => list(b.dataset.dimensionTab)));
  document.querySelectorAll('#dimensionPlan [data-measure]').forEach((e) => {
    const pick = () => {
      select(e.dataset.measure);
      if (innerWidth < 950) $('dimensionDetailTitle').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    };
    e.addEventListener('click', pick);
    e.addEventListener('keydown', (v) => { if (v.key === 'Enter' || v.key === ' ') { v.preventDefault(); pick(); } });
  });
  $('planmodal').addEventListener('click', (e) => { const b = e.target.closest('[data-select-measure]'); if (b) select(b.dataset.selectMeasure); });
  $('dimensionZoomIn').addEventListener('click', () => setZoom(zoom + 20));
  $('dimensionZoomOut').addEventListener('click', () => setZoom(zoom - 20));
  $('dimensionCsv').addEventListener('click', () => downloadBlob(new Blob([csv()], { type: 'text/csv;charset=utf-8' }), '1095-mckinley-review-dimensions.csv'));
  $('dimensionPrint').addEventListener('click', () => {
    const w = window.open('', '_blank');
    if (!w) { toast('Allow a new tab to print the revised plan.'); return; }
    w.document.write(planDocument());
    w.document.close();
    w.focus();
    w.print();
  });
  $('reviewDownload').addEventListener('click', () => downloadBlob(new Blob([planDocument()], { type: 'text/html' }), '1095-mckinley-revised-dimensions.html'));
  $('dimensionVisit').addEventListener('click', () => {
    const o = map[selected];
    if (!opts.visit) { toast('3D view unavailable in this browser.'); return; }
    closeModals();
    opts.visit(o && o.node);
  });
  if (selected) select(selected);
  list('rooms');

  const api = {
    data: M, select, list, format, csv,
    open(id) { openModal('planmodal'); if (id) select(id); },
    get selected() { return selected; },
    get units() { return units; },
  };
  window.MEASURE = api;
  return api;
}
