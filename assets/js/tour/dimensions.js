// The Dimensions sheet (#planmodal): the architect's schedule of rooms, windows and doors beside the
// dimensioned plan. Ported from the single-file page with the same ids and behaviour; the data now comes
// from assets/data/measurements.json and the drawing from assets/plans/dimension-plan.svg (fetched,
// then put into #dimensionPlan).
//
// opts: data (measurements.json), planSvg (text of the SVG file), ui (createUI()), visit(node, at) (go to a
// sweep in 3D, looking at `at` = {x, z, y} when given: the middle of an opening; absent when there is no
// 3D view).
// Returns {select(id), list(tab), format(v), csv(), open(id?), lookAt(item), selected, units}; also
// window.MEASURE.
//
// What a width means (measurements.json since the owner's eighth round): a door's `width` is its clear
// opening between the jamb liners or frames, and `wall_start` / `wall_end` keep the cut in the wall; a
// window and the two sliding glass doors give the wall opening of the unit (`clear_start` / `clear_end`
// between the frame's jambs, `way_start` / `way_end` the way as shown open). `sill` and `head` are
// measured from the floor the opening stands on, and `floor` is that floor's level when it is not the
// house floor (the garage's doors). `spaces` lists what the plan shows without a room tag (closed
// closets, the hall's legs, the garage with its floor level and step, the porch, the rear landings) and
// `overall` the outside sizes; both are optional and are shown under the Rooms list and in the footnote.

export function createDimensions(opts) {
  const { ui } = opts;
  const { $, ft, toast, closeModals, openModal, downloadBlob, esc } = ui;
  const M = opts.data || { rooms: [], windows: [], doors: [] };
  const spaces = Array.isArray(M.spaces) ? M.spaces.filter((x) => x && x.name) : [];
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
  // a floor level against the house floor: "11″ below the house floor" (0 = the house floor itself)
  const short = (v) => (units === 'mm' ? format(v) : ft(v).replace(/^0′/, ''));
  const level = (v) => (Math.abs(v) < 0.004 ? 'The house floor' : short(Math.abs(v)) + (v < 0 ? ' below' : ' above') + ' the house floor');
  const span = (a, b) => (Number.isFinite(a) && Number.isFinite(b) && b > a ? b - a : null);
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
      // beside the opening's own size: the cut in the wall when it differs (a door between liners or frames),
      // the clear width and the open way of a sliding glass door, the level of the floor it stands on
      const wall = span(o.wall_start, o.wall_end), clear = span(o.clear_start, o.clear_end), way = span(o.way_start, o.way_end), more = [];
      if (wall !== null && Math.abs(wall - o.width) > 0.004) more.push(['Wall opening', format(wall)]);
      if (clear !== null && Math.abs(clear - o.width) > 0.004) more.push(['Clear between the frame’s jambs', format(clear)]);
      if (way !== null) more.push(['Open way as shown', format(way)]);
      if (Number.isFinite(o.floor) && Math.abs(o.floor) >= 0.004) more.push(['Floor it stands on', level(o.floor)]);
      c += stats([['Opening width', format(o.width)], [roof ? 'Opening depth' : 'Opening height', format(o.height)], ...(roof ? [] : [['Sill above floor', format(o.sill)], ['Head above floor', format(o.head)]]), ...more]);
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
    let html = '<h3>' + items.length + ' ' + t + '</h3>' + table(headers, rows);
    // under the rooms: what the plan shows without a room tag, with its size and its floor level
    const others = t === 'rooms' ? spaces.filter((x) => (x.name + ' ' + (x.label || '')).toLowerCase().includes(q)) : [];
    if (others.length) {
      html += '<h3 id="dimensionSpacesTitle">Closets, levels and landings</h3><div id="dimensionSpaces">' + table(['Space', 'Clear width × depth', 'Floor'],
        others.map((x) => '<tr data-space="' + esc(x.key || '') + '"><td class="dimension-space"><strong>' + esc(x.name) + '</strong>' + (x.note ? '<span>' + esc(x.note) + '</span>' : '') + '</td><td>' + format(x.width_ft) + ' × ' + format(x.depth_ft) + '</td><td>' + esc(level(x.floor || 0)) + '</td></tr>')) + '</div>';
    }
    $('dimensionListing').innerHTML = html;
  }
  // The outside sizes of the house (measurements.json `overall`), in the sheet's footnote.
  function overall() {
    const el = $('dimensionOverall'), o = M.overall;
    if (!el) return;
    if (!o || !(o.outer_width_ft > 0) || !(o.outer_depth_ft > 0)) { el.hidden = true; return; }
    let text = 'Outside faces of the walls: ' + format(o.outer_width_ft) + ' wide × ' + format(o.outer_depth_ft) + ' deep';
    if (o.outer_depth_garage_side_ft > 0 && Math.abs(o.outer_depth_garage_side_ft - o.outer_depth_ft) > 0.004) text += ' (' + format(o.outer_depth_garage_side_ft) + ' on the garage side)';
    if (o.wall_thickness_ft > 0) text += ', every wall ' + short(o.wall_thickness_ft) + ' thick';
    text += '.';
    if (Number.isFinite(o.garage_floor_ft) && Math.abs(o.garage_floor_ft) >= 0.004) text += ' Garage floor ' + level(o.garage_floor_ft).replace(/^T/, 't') + '.';
    el.textContent = text + ' ';
    el.hidden = false;
  }
  function csv() {
    const rows = [['Category', 'ID', 'Description', 'Width_ft', 'Depth_or_height_ft', 'Room_area_sqft', 'Sill_ft', 'Basis', 'Notes']];
    for (const r of M.rooms) rows.push(['Room', r.id, r.name, r.width_ft, r.depth_ft, r.area_sqft, '', r.basis, r.note]);
    for (const o of [...M.windows, ...M.doors]) rows.push([o.kind, o.id, o.name, o.width, o.height, '', o.sill, o.basis, o.type + '; proposed opening; existing size requires measurement.']);
    // what the plan shows without a room tag: its key in the ID column, its floor level (ft against the house floor) in the notes
    for (const x of spaces) rows.push(['Space', x.key || '', x.name, x.width_ft, x.depth_ft, x.area_sqft, '', '', (Number.isFinite(x.floor) ? 'Floor ' + x.floor + ' ft against the house floor. ' : '') + (x.note || '')]);
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
    for (const [key, title] of [['rooms', 'Rooms'], ['windows', 'Windows and skylights'], ['doors', 'Doors']]) {
      t += '<h2>' + title + '</h2><table><thead><tr><th>Opening / room</th><th>Size</th><th>Notes</th></tr></thead><tbody>' + M[key].map((o) => '<tr><td>' + esc(o.id + ' · ' + o.name) + '</td><td>' + format(o.width_ft ?? o.width) + ' × ' + format(o.depth_ft ?? o.height) + '</td><td>' + esc(o.note || o.type || '') + '</td></tr>').join('') + '</tbody></table>';
    }
    if (spaces.length) t += '<h2>Closets, levels and landings</h2><table><thead><tr><th>Space</th><th>Size</th><th>Floor</th><th>Notes</th></tr></thead><tbody>' + spaces.map((x) => '<tr><td>' + esc(x.name) + '</td><td>' + format(x.width_ft) + ' × ' + format(x.depth_ft) + '</td><td>' + esc(level(x.floor || 0)) + '</td><td>' + esc(x.note || '') + '</td></tr>').join('') + '</tbody></table>';
    const outside = $('dimensionOverall') && !$('dimensionOverall').hidden ? '<p>' + esc($('dimensionOverall').textContent.trim()) + '</p>' : '';
    return '<!doctype html><html><head><title>1095 McKinley — revised dimensions</title><style>body{font:12px Arial;color:#263c35;margin:30px}h1{font-size:26px}h2{margin-top:25px}svg{width:100%;height:auto;max-height:900px}table{width:100%;border-collapse:collapse}th,td{padding:8px;border-bottom:1px solid #ddd;text-align:left}th{background:#edf1e8}tr{break-inside:avoid}section{break-after:page}@page{size:A4;margin:12mm}</style></head><body><h1>1095 W McKinley · Room dimensions + opening details</h1><p>Dimensions follow the architect’s plan · sizes/sizes.pdf, sheet SKA002 · Nov 13 2026 · clear interior sizes</p><section>' + p + '</section>' + t + outside + '<p>Bay area is separate from the Bedroom 3 main rectangle. A door’s width is its clear opening; windows and sliding glass doors give the wall opening of the unit. New heights and openings are proposed, not manufacturer rough openings.</p></body></html>';
  }

  $('dimensionItem').innerHTML = [['rooms', 'Rooms'], ['windows', 'Windows / skylights'], ['doors', 'Doors / closet openings']].map(([k, label]) => '<optgroup label="' + label + '">' + (M[k] || []).map((o) => '<option value="' + o.id + '">' + o.id + ' · ' + esc(o.name) + '</option>').join('') + '</optgroup>').join('');
  $('dimensionItem').addEventListener('change', (e) => select(e.target.value));
  $('dimensionUnits').addEventListener('change', (e) => { units = e.target.value; select(selected); list(tab); overall(); });
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
  // What "Visit in 3D" looks at: the middle of an opening, between a foot above its sill and a foot below its
  // head (the visitor's eye height where that range holds it); a skylight at its glass. A room has none: it
  // is entered on its sweep's own view.
  function lookAt(o) {
    if (!o || o.kind === 'room') return undefined;
    if (o.axis === 'roof') return Array.isArray(o.p) && o.p.length === 3 ? { x: o.p[0], z: o.p[2], y: o.p[1] } : undefined;
    if (![o.c, o.start, o.end, o.sill, o.head].every(Number.isFinite)) return undefined;
    const mid = (o.start + o.end) / 2, base = Number.isFinite(o.floor) ? o.floor : 0, middle = base + (o.sill + o.head) / 2;
    const y = [Math.min(base + o.sill + 1, middle), Math.max(base + o.head - 1, middle)];
    return o.axis === 'x' ? { x: mid, z: o.c, y } : o.axis === 'z' ? { x: o.c, z: mid, y } : undefined;
  }
  $('dimensionVisit').addEventListener('click', () => {
    const o = map[selected];
    if (!opts.visit) { toast('3D view unavailable in this browser.'); return; }
    closeModals();
    opts.visit(o && o.node, lookAt(o));
  });
  if (selected) select(selected);
  list('rooms');
  overall();

  const api = {
    data: M, select, list, format, csv,
    open(id) { openModal('planmodal'); if (id) select(id); },
    lookAt,
    get selected() { return selected; },
    get units() { return units; },
  };
  window.MEASURE = api;
  return api;
}
