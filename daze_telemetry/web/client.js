/* Daze of Thunder local OBS overlay. Read-only. Never shows last-session telemetry. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const mode = document.body.dataset.mode;
  const setText = (id, value) => { const e = $(id); if (e) e.textContent = value == null ? '' : String(value); };
  const show = (id, yes) => { const e = $(id); if (e) e.style.display = yes ? (id === 'session-header' ? 'flex' : id === 'standings' || id === 'demo-warning' ? 'block' : 'flex') : 'none'; };
  const displayPos = p => Number.isInteger(p) && p > 0 ? `P${p}` : '';
  const lastLap = time => {
    if (!Number.isFinite(time) || time <= 0) return '';
    const min = Math.floor(time / 60), sec = (time % 60).toFixed(3).padStart(6, '0');
    return min ? `${min}:${sec}` : sec;
  };
  const clean = s => typeof s === 'string' ? s.trim() : '';
  let consecutiveFailures = 0;

  function blank() {
    ['status', 'flag', 'session-header', 'standings', 'driver-panel', 'focus-card', 'demo-warning'].forEach(id => show(id, false));
    const rows = $('standings-rows'); if (rows) rows.replaceChildren();
  }

  function buildRow(row, index, focusIdx, fast) {
    const line = document.createElement('div'); line.className = 'board-row';
    if (row.idx === focusIdx) line.classList.add('is-focused');
    const parts = [
      ['board-pos', String(fast ? index + 1 : row.position || '')],
      ['board-num', clean(row.number) ? `#${row.number}` : ''],
      ['board-name', clean(row.name)],
      ['board-extra', row.in_pit ? 'PIT' : (fast ? lastLap(row.best_lap) : clean(row.class_name))],
    ];
    for (const [cls, val] of parts) {
      const node = document.createElement('div'); node.className = cls; node.textContent = val; line.append(node);
    }
    return line;
  }

  function draw(state) {
    const fresh = state && state.connected && typeof state.updated_at === 'number' && Date.now() / 1000 - state.updated_at < 3;
    if (!fresh) { blank(); return; }
    const s = state.session || {};
    show('status', true);
    setText('status-text', 'LIVE TELEMETRY');
    show('demo-warning', Boolean(state.demo));
    show('flag', Boolean(s.flag));
    if (s.flag) { $('flag').dataset.flag = s.flag; setText('flag-label', `${s.flag.toUpperCase()} FLAG`); }

    if (mode === 'driver') {
      const d = state.driver;
      const available = d && (clean(d.name) || clean(d.number));
      show('driver-panel', Boolean(available));
      if (!available) return;
      setText('driver-number', d.number ? `#${d.number}` : '');
      setText('driver-name', clean(d.name));
      const detail = [clean(d.class_name), s.lap_text, d.best_lap ? `BEST ${lastLap(d.best_lap)}` : ''].filter(Boolean).join('  •  ');
      setText('driver-line', detail);
      setText('driver-position', displayPos(d.position));
      return;
    }

    const header = [clean(s.track), clean(s.series)].filter(Boolean);
    show('session-header', Boolean(header.length || s.lap_text || clean(s.kind)));
    setText('session-track', clean(s.track) || clean(s.series));
    setText('session-details', [clean(s.kind), s.lap_text, (s.track && s.series) ? clean(s.series) : ''].filter(Boolean).join('   •   '));

    const rows = Array.isArray(state.leaderboard) ? state.leaderboard : [];
    const fast = state.table_type === 'fastest_laps';
    const hasTable = rows.length > 0;
    show('standings', hasTable);
    if (hasTable) {
      setText('standings-label', fast ? 'FASTEST LAPS' : 'RUNNING ORDER');
      const node = $('standings-rows');
      const ordered = rows.slice(0, 10);
      node.replaceChildren(...ordered.map((r, i) => buildRow(r, i, state.focus && state.focus.idx, fast)));
    }

    const f = state.focus;
    const hasFocus = f && (clean(f.name) || clean(f.number));
    show('focus-card', Boolean(hasFocus));
    if (hasFocus) {
      setText('focus-number', f.number ? `#${f.number}` : '');
      setText('focus-name', clean(f.name));
      setText('focus-meta', [clean(f.class_name), f.in_pit ? 'PIT ROAD' : '', f.best_lap ? `BEST ${lastLap(f.best_lap)}` : ''].filter(Boolean).join('  •  '));
      setText('focus-position', fast ? '' : displayPos(f.position));
    }
  }

  async function refresh() {
    try {
      const controller = new AbortController();
      // If telemetry is unavailable or a local instance stops, drop all dynamic data.
      const timeout = setTimeout(() => controller.abort(), 1800);
      try {
        const r = await fetch('/api/state', { cache: 'no-store', signal: controller.signal });
        if (!r.ok) throw new Error('offline');
        const state = await r.json();
        consecutiveFailures = 0;
        draw(state);
      } finally { clearTimeout(timeout); }
    } catch (_) {
      consecutiveFailures++;
      blank();
    }
  }
  blank(); refresh(); setInterval(refresh, 500);
})();
