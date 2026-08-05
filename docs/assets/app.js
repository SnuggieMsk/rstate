/* Chennai Real Estate Intelligence — shared utilities */
const CRI = (() => {
  const DATA_BASE = 'data/';

  async function loadJSON(name) {
    const res = await fetch(DATA_BASE + name);
    if (!res.ok) throw new Error('Failed to load ' + name + ': ' + res.status);
    return res.json();
  }

  async function loadAll() {
    const [projects, localities, infrastructure, meta, distressed] = await Promise.all([
      loadJSON('projects.json'), loadJSON('localities.json'),
      loadJSON('infrastructure.json'), loadJSON('meta.json'),
      loadJSON('distressed.json').catch(() => ({ distressed: [] })),
    ]);
    return { projects: projects.projects, localities: localities.localities,
             infrastructure: infrastructure.infrastructure, meta,
             distressed: distressed.distressed };
  }

  // A record stays in the dataset forever, but these three states mean it should
  // not be counted, ranked or mapped alongside live projects.
  const RETIRED = new Set(['withdrawn', 'superseded', 'unverified']);
  function isLive(p) { return !RETIRED.has(p.status); }

  // ---- Persona lens ----------------------------------------------------
  const PERSONAS = [
    ['all', 'All'],
    ['boardroom', 'Boardroom · ₹3Cr+'],
    ['executive', 'Executive · ₹1–2.5Cr'],
    ['value', 'Value & Distressed'],
  ];
  const PERSONA_TAG = { boardroom: 'Boardroom', executive: 'Executive', value: 'Value' };

  function persona() { return localStorage.getItem('cri-persona') || 'all'; }

  function matchesPersona(p) {
    const cur = persona();
    if (cur === 'all') return true;
    return (p.tags || []).includes(PERSONA_TAG[cur]);
  }

  // Injects the persona switcher bar under the header; calls onChange after switching.
  function initPersonaBar(onChange) {
    const header = document.querySelector('header.site');
    if (!header) return;
    const bar = document.createElement('div');
    bar.className = 'persona-bar';
    bar.innerHTML = '<div class="wrap"><span class="pb-label">Client lens:</span>' +
      PERSONAS.map(([k, label]) =>
        `<button data-p="${k}" class="${persona() === k ? 'on' : ''}" aria-pressed="${persona() === k}">${label}</button>`).join('') +
      '</div>';
    header.after(bar);
    bar.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
      localStorage.setItem('cri-persona', b.dataset.p);
      bar.querySelectorAll('button').forEach(x => {
        x.classList.toggle('on', x === b);
        x.setAttribute('aria-pressed', x === b);
      });
      if (onChange) onChange(b.dataset.p);
    }));
  }

  // Loading skeletons: fill a container with shimmer placeholders until data lands.
  function skeletons(el, kind, n) {
    if (typeof el === 'string') el = document.getElementById(el);
    if (el) el.innerHTML = Array.from({ length: n }, () => `<div class="skel skel-${kind}"></div>`).join('');
  }

  function money(inr) {
    if (inr == null) return '—';
    if (inr >= 1e7) return '₹' + (inr / 1e7).toFixed(2).replace(/\.?0+$/, '') + ' Cr';
    return '₹' + Math.round(inr / 1e5) + ' L';
  }

  function ticketHTML(p) {
    const a = p.ticket_min_lakh, b = p.ticket_max_lakh;
    if (a == null && b == null) return null;
    const f = v => v >= 100 ? '₹' + (v / 100).toFixed(2).replace(/\.?0+$/, '') + ' Cr' : '₹' + Math.round(v) + ' L';
    if (a != null && b != null && a !== b) return f(a) + '–' + f(b);
    return f(a != null ? a : b);
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
    if (c === 'verified') return '<span class="verified-badge">✓ verified on RERA portal</span>';
    const label = { reported: 'reported', estimated: 'estimated' }[c] || c;
    return `<span class="conf">${label}</span>`;
  }

  // TNRERA publishes no prices, so a registration verified against the official
  // export still carries only researched pricing. Say which claim is which.
  function priceConfHTML(p) {
    if (!p.price_sqft_min && !p.ticket_min_lakh) return '';
    const c = p.price_confidence || p.data_confidence;
    if (c === 'verified') return '';
    return `<span class="conf" title="TNRERA does not publish prices — this rate comes from developer or portal listings">price ${c || 'reported'}</span>`;
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
      btn.setAttribute('aria-label', 'Toggle light/dark theme');
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

  // ---- Compare drawer ---------------------------------------------------
  const CMP_KEY = 'cri-compare';
  function compareList() { try { return JSON.parse(localStorage.getItem(CMP_KEY) || '[]'); } catch (e) { return []; } }
  function setCompareList(ids) { localStorage.setItem(CMP_KEY, JSON.stringify(ids)); }

  function toggleCompare(id) {
    let ids = compareList();
    if (ids.includes(id)) ids = ids.filter(x => x !== id);
    else if (ids.length < 3) ids = [...ids, id];
    else return false;
    setCompareList(ids);
    return true;
  }

  function tierBadge(tier) {
    return tier ? `<span class="tier tier-${tier}">${tier}</span>` : '';
  }

  // Renders the fixed bottom compare bar; call refreshCompareBar() after any toggle.
  function initCompareBar(allProjects) {
    let bar = document.querySelector('.cmp-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.className = 'cmp-bar';
      bar.innerHTML = '<span class="cmp-count"></span>' +
        '<button class="ghost" data-act="clear">Clear</button>' +
        '<button data-act="open">Compare →</button>';
      document.body.appendChild(bar);
    }
    let overlay = document.querySelector('.cmp-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'cmp-overlay';
      overlay.innerHTML = '<div class="cmp-sheet"></div>';
      overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('show'); });
      document.addEventListener('keydown', e => { if (e.key === 'Escape') overlay.classList.remove('show'); });
      document.body.appendChild(overlay);
    }

    function refresh() {
      const ids = compareList();
      bar.classList.toggle('show', ids.length > 0);
      bar.querySelector('.cmp-count').textContent = ids.length + ' selected for comparison';
    }
    bar.querySelector('[data-act="clear"]').addEventListener('click', () => { setCompareList([]); refresh(); });
    bar.querySelector('[data-act="open"]').addEventListener('click', () => {
      const ids = compareList();
      const rows = ids.map(id => allProjects.find(p => p.id === id)).filter(Boolean);
      if (!rows.length) return;
      const fields = [
        ['Locality', p => p.locality + (p.corridor ? ' (' + p.corridor + ')' : '')],
        ['Builder', p => p.promoter || '—'],
        ['Stage', p => stageLabel(p.stage)],
        ['Config', p => p.config_mix || '—'],
        ['Ticket size', p => ticketHTML(p) || priceHTML(p)],
        ['Upside Score', p => scoreHTML(p.upside_score)],
        ['Risk', p => riskHTML(p.risk)],
        ['Segments', p => tagsHTML(p.tags)],
        ['Expected completion', p => p.expected_completion || '—'],
        ['RERA no.', p => p.rera_no || 'not found'],
      ];
      const sheet = overlay.querySelector('.cmp-sheet');
      sheet.innerHTML = '<button class="cmp-close" aria-label="Close comparison">✕</button>' +
        '<h2 style="margin-top:0">Compare projects</h2>' +
        '<div class="table-scroll"><table><tbody>' +
        '<tr><th></th>' + rows.map(p => `<th>${p.name}</th>`).join('') + '</tr>' +
        fields.map(([label, fn]) =>
          `<tr><td>${label}</td>` + rows.map(p => `<td>${fn(p)}</td>`).join('') + '</tr>').join('') +
        '</tbody></table></div>' +
        '<p style="margin:14px 0 0"><button onclick="window.print()" style="font:inherit;font-size:13px;font-weight:600;padding:8px 16px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer">Print / save as PDF</button></p>';
      sheet.querySelector('.cmp-close').addEventListener('click', () => overlay.classList.remove('show'));
      overlay.classList.add('show');
    });
    refresh();
    return refresh;
  }

  return { loadAll, loadJSON, isLive, scoreBand, BAND_COLORS, scoreHTML, riskHTML, tagsHTML,
           priceHTML, fmtN, confHTML, priceConfHTML, stageLabel, sourcesHTML, breakdownHTML,
           initTheme, setRefreshed,
           persona, matchesPersona, initPersonaBar, money, ticketHTML,
           compareList, toggleCompare, tierBadge, initCompareBar, skeletons };
})();
