/* Chennai Real Estate Intelligence — shared utilities */
const CRI = (() => {
  const DATA_BASE = 'data/';

  async function loadJSON(name) {
    const res = await fetch(DATA_BASE + name);
    if (!res.ok) throw new Error('Failed to load ' + name + ': ' + res.status);
    return res.json();
  }

  async function loadAll() {
    const [projects, localities, infrastructure, meta] = await Promise.all([
      loadJSON('projects.json'), loadJSON('localities.json'),
      loadJSON('infrastructure.json'), loadJSON('meta.json'),
    ]);
    return { projects: projects.projects, localities: localities.localities,
             infrastructure: infrastructure.infrastructure, meta };
  }

  function scoreBand(score) {
    if (score == null) return 1;
    if (score >= 75) return 4;
    if (score >= 60) return 3;
    if (score >= 45) return 2;
    return 1;
  }

  const BAND_COLORS = { 1: '#86b6ef', 2: '#3987e5', 3: '#1c5cab', 4: '#0d366b' };

  function scoreHTML(score) {
    if (score == null) return '<span class="conf">n/a</span>';
    const b = scoreBand(score);
    return `<span class="score score-band-${b}"><i></i>${score}</span>`;
  }

  function riskHTML(risk) {
    if (!risk) return '';
    const icon = risk === 'Low' ? '✓' : risk === 'Medium' ? '⚠' : '⛔';
    return `<span class="risk risk-${risk}"><i></i>${icon} ${risk} risk</span>`;
  }

  function tagsHTML(tags) {
    return (tags || []).map(t =>
      `<span class="tag${t === 'Early Entrant' || t === 'High Upside' ? ' hot' : ''}">${t}</span>`
    ).join('');
  }

  function priceHTML(p) {
    if (p.price_sqft_min && p.price_sqft_max && p.price_sqft_min !== p.price_sqft_max)
      return `₹${fmtN(p.price_sqft_min)}–${fmtN(p.price_sqft_max)}/sqft`;
    if (p.price_sqft_min) return `₹${fmtN(p.price_sqft_min)}/sqft`;
    if (p.ticket_note) return p.ticket_note;
    return '—';
  }

  function fmtN(n) { return n == null ? '—' : Number(n).toLocaleString('en-IN'); }

  function confHTML(c) {
    const label = { verified: 'verified (RERA portal)', reported: 'reported', estimated: 'estimated' }[c] || c;
    return `<span class="conf">${label}</span>`;
  }

  function stageLabel(s) {
    return { 'pre-launch': 'Pre-launch', 'new-launch': 'New launch',
             'under-construction': 'Under construction',
             'nearing-possession': 'Nearing possession', 'completed': 'Completed' }[s] || s || '—';
  }

  function sourcesHTML(sources) {
    return (sources || []).map((u, i) => {
      let host = 'source';
      try { host = new URL(u).hostname.replace(/^www\./, ''); } catch (e) {}
      return `<a href="${u}" target="_blank" rel="noopener">[${i + 1}] ${host}</a>`;
    }).join(' · ');
  }

  function breakdownHTML(p) {
    const f = p.score_breakdown || {};
    const rows = [
      ['Entry stage', f.entry_stage, 25], ['Infrastructure', f.infrastructure, 20],
      ['Locality momentum', f.locality_momentum, 20], ['Relative pricing', f.relative_pricing, 15],
      ['Developer record', f.developer_track_record, 10], ['Rental yield', f.rental_yield, 10],
    ];
    return '<div class="bd">' + rows.map(([lbl, v, max]) => {
      const val = v == null ? 0 : v;
      return `<div class="row"><span class="lbl">${lbl}</span>` +
        `<span class="bar"><span style="width:${Math.round((val / max) * 100)}%"></span></span>` +
        `<span class="val">${v == null ? '—' : val + '/' + max}</span></div>`;
    }).join('') + '</div>';
  }

  // Theme toggle: stamp data-theme on <html>; persists in localStorage.
  function initTheme() {
    const saved = localStorage.getItem('cri-theme');
    if (saved) document.documentElement.dataset.theme = saved;
    const btn = document.querySelector('.theme-toggle');
    if (btn) {
      btn.addEventListener('click', () => {
        const cur = document.documentElement.dataset.theme ||
          (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        const next = cur === 'dark' ? 'light' : 'dark';
        document.documentElement.dataset.theme = next;
        localStorage.setItem('cri-theme', next);
      });
    }
  }

  function setRefreshed(meta) {
    document.querySelectorAll('.refreshed').forEach(el => {
      el.textContent = 'Data refreshed: ' + (meta.last_refreshed || 'unknown');
    });
  }

  return { loadAll, loadJSON, scoreBand, BAND_COLORS, scoreHTML, riskHTML, tagsHTML,
           priceHTML, fmtN, confHTML, stageLabel, sourcesHTML, breakdownHTML,
           initTheme, setRefreshed };
})();
