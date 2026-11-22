// The Design sheet (#designmodal): one tab per design view (render, text, the owner's reference photos)
// with buttons into the 3D view and the Dimensions sheet. Ported from the single-file page with the same
// ids and behaviour; views, tab order and image paths now come from assets/data/design.json.
//
// opts: data (design.json), ui, suffix ('?v=...' for the images), thumb(id) (panorama thumbnail for a view
// without an image), visit(node), exterior(view), dimensions (createDimensions() result).
// Returns {show(id), open(id?), data, views, selected}; also window.DESIGN.
// The sheet's pictures are fetched when it is first opened (or show() is called), not when the page starts:
// until then the line belongs to the tour itself.

export function createDesign(opts) {
  const { ui } = opts;
  const { $, esc, closeModals, openModal } = ui;
  const D = opts.data || { order: [], views: {}, references: {} };
  const src = (path) => (path ? path + (opts.suffix || '') : '');
  const images = Object.fromEntries(Object.entries(D.views).map(([k, x]) => [k, x.image]));
  let selected = D.order[0] || null, shown = false;

  $('designTabs').innerHTML = D.order.map((id) => '<button data-design="' + esc(id) + '" data-testid="design-tab-' + esc(id) + '">' + esc(D.views[id].label || id) + '</button>').join('');

  function show(id) {
    const d = D.views[id];
    if (!d) return;
    selected = id;
    shown = true;
    $('frontHomeActions').hidden = id !== 'front';
    $('designModel').textContent = id === 'front' ? 'Explore outside in 3D' : id === 'roof' ? 'View roof in 3D' : 'Inspect in 3D';
    $('designModel').style.display = id === 'front' || id === 'roof' ? '' : 'none';
    $('designTitle').textContent = d.title;
    $('designText').textContent = d.text;
    $('designHero').src = src(d.image) || (opts.thumb ? opts.thumb(d.node) : '');
    $('designHero').alt = d.title;
    $('designHero').style.objectFit = ['roof', 'B3', 'front'].includes(id) ? 'contain' : 'cover';
    $('designCaption').textContent = id === 'roof' ? 'Roof plan · proposed geometry' : id === 'front' ? 'Front elevation · render' : 'Revised room · render';
    document.querySelectorAll('[data-design]').forEach((b) => {
      b.classList.toggle('active', b.dataset.design === id);
      b.setAttribute('aria-pressed', String(b.dataset.design === id));
    });
    $('designRefs').innerHTML = (d.refs || []).map((f) => '<div><img src="' + esc(src(D.references[f])) + '" alt="Your reference: ' + esc(f) + '" loading="lazy" decoding="async"/><p>' + esc(f) + '</p></div>').join('');
    $('designVisit').textContent = id === 'roof' ? 'Inspect the roof in 3D' : id === 'front' ? 'Step into the entry' : 'Walk into this room';
    $('designMeasure').textContent = id === 'roof' ? 'Entry window details' : id === 'A1' ? 'Room dimensions' : 'Opening details';
  }

  // the owner's rounds of changes (design.json `owner_changes`), newest first
  const rounds = (D.owner_changes || []).slice().reverse();
  if (rounds.length) {
    const ordinal = ['', 'First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth'];
    $('designChangeList').innerHTML = rounds.map((r) => '<h4>' + esc((ordinal[r.round] ? ordinal[r.round] + ' round' : 'Round ' + r.round) + (r.date ? ' · ' + r.date : '')) + '</h4><ul>' + (r.changes || []).map((c) => '<li>' + esc(c) + '</li>').join('') + '</ul>').join('');
    $('designChanges').hidden = false;
  }

  const need3d = (f) => { closeModals(); if (f) return true; ui.toast('3D view unavailable in this browser.'); return false; };
  $('designTabs').addEventListener('click', (e) => { const b = e.target.closest('[data-design]'); if (b) show(b.dataset.design); });
  $('designVisit').addEventListener('click', () => {
    if (selected === 'roof') { if (need3d(opts.exterior)) opts.exterior('roof'); }
    else if (need3d(opts.visit)) opts.visit(D.views[selected].node);
  });
  $('designModel').addEventListener('click', () => {
    if (selected === 'roof') { if (need3d(opts.exterior)) opts.exterior('roof'); }
    else if (selected === 'front') { if (need3d(opts.exterior)) opts.exterior('front'); }
    else if (need3d(opts.visit)) opts.visit(D.views[selected].node);
  });
  $('designMeasure').addEventListener('click', () => { if (opts.dimensions) opts.dimensions.open(D.views[selected].opening); });
  $('homeExterior').addEventListener('click', () => { if (need3d(opts.exterior)) opts.exterior('front'); });
  $('homeInterior').addEventListener('click', () => { if (need3d(opts.visit)) opts.visit(null); });

  const api = {
    show, data: D.views, views: images,
    open(id) { if (id || !shown) show(id || selected); openModal('designmodal'); },
    get selected() { return selected; },
  };
  window.DESIGN = api;
  return api;
}
