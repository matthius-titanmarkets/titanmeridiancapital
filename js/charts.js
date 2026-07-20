/* ════════════════════════════════════════════════════════════════
   TITAN MERIDIAN CAPITAL — chart engine
   Dependency-free SVG renderers tuned to the house style:
   hairline grids, ivory strokes, bronze accents, animated draws.
   ════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function el(tag, attrs) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  const MONTHS_S = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function fmtDate(d) { return MONTHS_S[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear(); }
  function fmtTick(d, spanDays) {
    if (spanDays > 500) return MONTHS_S[d.getMonth()] + " '" + String(d.getFullYear()).slice(2);
    if (spanDays > 80) return MONTHS_S[d.getMonth()] + " '" + String(d.getFullYear()).slice(2);
    return MONTHS_S[d.getMonth()] + ' ' + d.getDate();
  }
  function niceTicks(min, max, count) {
    const span = max - min || 1;
    const step0 = span / count;
    const mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const norm = step0 / mag;
    const step = (norm >= 5 ? 5 : norm >= 2.5 ? 2.5 : norm >= 2 ? 2 : 1) * mag;
    const t0 = Math.ceil(min / step) * step;
    const out = [];
    for (let t = t0; t <= max + 1e-9; t += step) out.push(t);
    return out;
  }

  /* ── multi-series line chart with crosshair tooltip ──
     cfg: { series:[{label,color,points:[{d,v}],area?,width?}], height, fmt, fmtTip } */
  function lineChart(container, cfg) {
    container.classList.add('chart-wrap');
    container.innerHTML = '';
    const W = Math.max(280, container.clientWidth || 600);
    const H = cfg.height || 300;
    const P = { t: 14, r: 12, b: 30, l: cfg.padL != null ? cfg.padL : 58 };
    const iw = W - P.l - P.r, ih = H - P.t - P.b;

    let lo = Infinity, hi = -Infinity;
    cfg.series.forEach(s => s.points.forEach(p => { lo = Math.min(lo, p.v); hi = Math.max(hi, p.v); }));
    const pad = (hi - lo) * 0.07 || 1;
    lo -= pad; hi += pad;
    if (cfg.zero && lo > 0) lo = 0;

    const pts0 = cfg.series[0].points;
    const n = pts0.length;
    const X = i => P.l + (i / Math.max(1, n - 1)) * iw;
    const Y = v => P.t + (1 - (v - lo) / (hi - lo)) * ih;

    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', height: H, 'aria-hidden': 'true' });
    const uid = 'g' + Math.random().toString(36).slice(2, 8);

    /* gridlines + y labels */
    niceTicks(lo, hi, 4).forEach(t => {
      svg.appendChild(el('line', { x1: P.l, x2: W - P.r, y1: Y(t), y2: Y(t), stroke: 'rgba(232,226,212,.07)', 'stroke-width': 1 }));
      const lbl = el('text', { x: P.l - 10, y: Y(t) + 3.5, 'text-anchor': 'end', fill: '#5E6B80', 'font-size': 10, 'font-family': 'Inter,sans-serif' });
      lbl.textContent = cfg.fmt ? cfg.fmt(t) : t.toFixed(0);
      svg.appendChild(lbl);
    });
    /* x labels */
    const spanDays = (pts0[n - 1].d - pts0[0].d) / 86400000;
    const xCount = W < 460 ? 4 : 6;
    for (let k = 0; k < xCount; k++) {
      const i = Math.round(k * (n - 1) / (xCount - 1));
      const lbl = el('text', {
        x: X(i), y: H - 8, 'text-anchor': k === 0 ? 'start' : k === xCount - 1 ? 'end' : 'middle',
        fill: '#5E6B80', 'font-size': 9.5, 'font-family': 'Inter,sans-serif', 'letter-spacing': '.06em',
      });
      lbl.textContent = fmtTick(pts0[i].d, spanDays);
      svg.appendChild(lbl);
    }

    const defs = el('defs', {});
    svg.appendChild(defs);

    cfg.series.forEach((s, si) => {
      const d = s.points.map((p, i) => (i ? 'L' : 'M') + X(i).toFixed(2) + ',' + Y(p.v).toFixed(2)).join('');
      if (si === 0 && s.area !== false) {
        const gid = uid + 'a';
        const grad = el('linearGradient', { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 });
        grad.appendChild(el('stop', { offset: '0%', 'stop-color': s.color, 'stop-opacity': .22 }));
        grad.appendChild(el('stop', { offset: '100%', 'stop-color': s.color, 'stop-opacity': 0 }));
        defs.appendChild(grad);
        const area = el('path', {
          d: d + `L${X(n - 1)},${P.t + ih}L${X(0)},${P.t + ih}Z`,
          fill: `url(#${gid})`, opacity: 0,
        });
        svg.appendChild(area);
        requestAnimationFrame(() => {
          area.style.transition = REDUCED ? 'none' : 'opacity 1.1s ease .35s';
          area.style.opacity = 1;
        });
      }
      const path = el('path', {
        d, fill: 'none', stroke: s.color, 'stroke-width': s.width || (si === 0 ? 2 : 1.4),
        'stroke-linejoin': 'round', 'stroke-linecap': 'round',
        'stroke-dasharray': s.dash || 'none', opacity: si === 0 ? 1 : .8,
      });
      svg.appendChild(path);
      if (!REDUCED && !s.dash) {
        requestAnimationFrame(() => {
          try {
            const L = path.getTotalLength();
            path.style.strokeDasharray = L;
            path.style.strokeDashoffset = L;
            path.getBoundingClientRect();
            path.style.transition = `stroke-dashoffset ${1 + si * .25}s cubic-bezier(.22,.8,.28,1)`;
            path.style.strokeDashoffset = 0;
            setTimeout(() => { path.style.strokeDasharray = s.dash || 'none'; }, 1400 + si * 250);
          } catch (e) { /* non-rendered path */ }
        });
      }
    });

    /* crosshair + tooltip */
    const cross = el('line', { y1: P.t, y2: P.t + ih, stroke: 'rgba(237,231,218,.28)', 'stroke-width': 1, 'stroke-dasharray': '3 4', opacity: 0 });
    svg.appendChild(cross);
    const dots = cfg.series.map(s => {
      const c = el('circle', { r: 3.5, fill: s.color, stroke: '#0A1220', 'stroke-width': 1.5, opacity: 0 });
      svg.appendChild(c); return c;
    });
    container.appendChild(svg);

    const tip = document.createElement('div');
    tip.className = 'chart-tip';
    container.appendChild(tip);

    function showAt(clientX) {
      const rect = svg.getBoundingClientRect();
      const scale = W / rect.width;
      const gx = (clientX - rect.left) * scale;
      let i = Math.round((gx - P.l) / iw * (n - 1));
      i = Math.max(0, Math.min(n - 1, i));
      const x = X(i);
      cross.setAttribute('x1', x); cross.setAttribute('x2', x);
      cross.setAttribute('opacity', 1);
      let rows = '';
      cfg.series.forEach((s, si) => {
        const p = s.points[i];
        dots[si].setAttribute('cx', x);
        dots[si].setAttribute('cy', Y(p.v));
        dots[si].setAttribute('opacity', 1);
        rows += `<div class="tt-row"><span class="tt-key"><i style="background:${s.color}"></i>${s.label}</span>` +
                `<span class="tt-val">${(cfg.fmtTip || cfg.fmt || (v => v))(p.v)}</span></div>`;
      });
      tip.innerHTML = `<div class="tt-date">${fmtDate(pts0[i].d)}</div>` + rows;
      tip.style.opacity = 1;
      const tw = tip.offsetWidth;
      const px = x / scale;
      tip.style.left = Math.max(4, Math.min(rect.width - tw - 4, px + (px > rect.width / 2 ? -tw - 16 : 16))) + 'px';
      tip.style.top = '10px';
    }
    function hide() {
      cross.setAttribute('opacity', 0);
      dots.forEach(d => d.setAttribute('opacity', 0));
      tip.style.opacity = 0;
    }
    svg.addEventListener('mousemove', e => showAt(e.clientX));
    svg.addEventListener('mouseleave', hide);
    svg.addEventListener('touchstart', e => showAt(e.touches[0].clientX), { passive: true });
    svg.addEventListener('touchmove', e => showAt(e.touches[0].clientX), { passive: true });
    svg.addEventListener('touchend', hide);
  }

  /* ── drawdown area (values ≤ 0, in %) ── */
  function drawdownChart(container, points, opts) {
    container.classList.add('chart-wrap');
    container.innerHTML = '';
    const W = Math.max(280, container.clientWidth || 600);
    const H = (opts && opts.height) || 190;
    const P = { t: 8, r: 12, b: 26, l: 46 };
    const iw = W - P.l - P.r, ih = H - P.t - P.b;
    const lo = Math.min(...points.map(p => p.v)) * 1.15 - 0.002;
    const n = points.length;
    const X = i => P.l + (i / (n - 1)) * iw;
    const Y = v => P.t + ((0 - v) / (0 - lo)) * ih;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', height: H });

    niceTicks(lo, 0, 3).forEach(t => {
      svg.appendChild(el('line', { x1: P.l, x2: W - P.r, y1: Y(t), y2: Y(t), stroke: 'rgba(232,226,212,.07)' }));
      const lbl = el('text', { x: P.l - 8, y: Y(t) + 3.5, 'text-anchor': 'end', fill: '#5E6B80', 'font-size': 10, 'font-family': 'Inter,sans-serif' });
      lbl.textContent = (t * 100).toFixed(0) + '%';
      svg.appendChild(lbl);
    });
    const spanDays = (points[n - 1].d - points[0].d) / 86400000;
    for (let k = 0; k < 5; k++) {
      const i = Math.round(k * (n - 1) / 4);
      const lbl = el('text', { x: X(i), y: H - 6, 'text-anchor': k === 0 ? 'start' : k === 4 ? 'end' : 'middle', fill: '#5E6B80', 'font-size': 9.5, 'font-family': 'Inter,sans-serif' });
      lbl.textContent = fmtTick(points[i].d, spanDays);
      svg.appendChild(lbl);
    }
    const uid = 'dd' + Math.random().toString(36).slice(2, 7);
    const grad = el('linearGradient', { id: uid, x1: 0, y1: 0, x2: 0, y2: 1 });
    grad.appendChild(el('stop', { offset: '0%', 'stop-color': '#C97B6F', 'stop-opacity': .05 }));
    grad.appendChild(el('stop', { offset: '100%', 'stop-color': '#C97B6F', 'stop-opacity': .3 }));
    const defs = el('defs', {}); defs.appendChild(grad); svg.appendChild(defs);

    const line = points.map((p, i) => (i ? 'L' : 'M') + X(i).toFixed(2) + ',' + Y(p.v).toFixed(2)).join('');
    const area = el('path', { d: line + `L${X(n - 1)},${Y(0)}L${X(0)},${Y(0)}Z`, fill: `url(#${uid})`, opacity: 0 });
    svg.appendChild(area);
    svg.appendChild(el('path', { d: line, fill: 'none', stroke: '#C97B6F', 'stroke-width': 1.6, 'stroke-linejoin': 'round' }));
    svg.appendChild(el('line', { x1: P.l, x2: W - P.r, y1: Y(0), y2: Y(0), stroke: 'rgba(232,226,212,.25)', 'stroke-width': 1 }));
    requestAnimationFrame(() => { area.style.transition = REDUCED ? 'none' : 'opacity 1s ease .2s'; area.style.opacity = 1; });
    container.appendChild(svg);
  }

  /* ── donut allocation ── */
  function donut(container, slices, centerLabel) {
    container.innerHTML = '';
    const size = 210, r = 78, cx = size / 2, cy = size / 2;
    const C = 2 * Math.PI * r;
    const svg = el('svg', { viewBox: `0 0 ${size} ${size}`, width: '100%', height: 'auto', style: 'max-width:230px;margin:0 auto;display:block' });
    let acc = 0;
    slices.forEach((s, i) => {
      const frac = s.pct / 100;
      const seg = el('circle', {
        cx, cy, r, fill: 'none', stroke: s.color, 'stroke-width': 16,
        'stroke-dasharray': `0 ${C}`, 'stroke-dashoffset': -acc * C + C * .25,
        transform: `rotate(0 ${cx} ${cy})`, 'stroke-linecap': 'butt', opacity: .92,
      });
      svg.appendChild(seg);
      const target = `${Math.max(0, frac * C - 2.5)} ${C}`;
      if (REDUCED) seg.setAttribute('stroke-dasharray', target);
      else requestAnimationFrame(() => {
        seg.style.transition = `stroke-dasharray 1.1s cubic-bezier(.22,.8,.28,1) ${.15 + i * .07}s`;
        seg.setAttribute('stroke-dasharray', target);
      });
      acc += frac;
    });
    const t1 = el('text', { x: cx, y: cy - 4, 'text-anchor': 'middle', fill: '#F7F3E8', 'font-size': 22, 'font-family': "'Playfair Display',serif" });
    t1.textContent = centerLabel[0];
    const t2 = el('text', { x: cx, y: cy + 16, 'text-anchor': 'middle', fill: '#5E6B80', 'font-size': 8.5, 'letter-spacing': '.2em', 'font-family': 'Inter,sans-serif' });
    t2.textContent = centerLabel[1];
    svg.appendChild(t1); svg.appendChild(t2);
    container.appendChild(svg);
  }

  /* ── sparkline (tiny, no axes) ── */
  function spark(container, values, color, opts) {
    container.innerHTML = '';
    const W = container.clientWidth || 200, H = container.clientHeight || 42;
    const lo = Math.min(...values), hi = Math.max(...values);
    const n = values.length;
    const X = i => (i / (n - 1)) * W;
    const Y = v => 4 + (1 - (v - lo) / ((hi - lo) || 1)) * (H - 8);
    const d = values.map((v, i) => (i ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(v).toFixed(1)).join('');
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', height: '100%', preserveAspectRatio: 'none' });
    if (opts && opts.fill) {
      const uid = 'sp' + Math.random().toString(36).slice(2, 7);
      const grad = el('linearGradient', { id: uid, x1: 0, y1: 0, x2: 0, y2: 1 });
      grad.appendChild(el('stop', { offset: '0%', 'stop-color': color, 'stop-opacity': .25 }));
      grad.appendChild(el('stop', { offset: '100%', 'stop-color': color, 'stop-opacity': 0 }));
      const defs = el('defs', {}); defs.appendChild(grad); svg.appendChild(defs);
      svg.appendChild(el('path', { d: d + `L${W},${H}L0,${H}Z`, fill: `url(#${uid})` }));
    }
    svg.appendChild(el('path', { d, fill: 'none', stroke: color, 'stroke-width': 1.6, 'stroke-linejoin': 'round' }));
    container.appendChild(svg);
  }

  window.TMC_CHARTS = { lineChart, drawdownChart, donut, spark };
})();
