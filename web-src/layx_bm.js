/* ================= BM 0.24.87: pengayaan lembar Layout & Plot PDF (layx_bm.js) =================
   Pemilik 15 Nov 2026: "Tahap 1 kerjakan semua, tahap 2 kerjakan kecuali inset penampang. Jika user tidak menginginkan,
   kasih opsi untuk mematikan fitur ini."
   Satu pintu: semuanya di panel Layout & Plot PDF > "Pengayaan lembar"; sakelar induk L.lx mematikan seluruhnya (lembar
   kembali persis seperti 0.24.86), dan tiap bagian punya sakelar sendiri.
     Tahap 1  1. Inset lokasi (L.inset)        2. Kop lengkap (L.kopX)       3. Gaya grid (L.gridStyle: line | plus | edge)
              4. Elemen bisa digeser di pratinjau (L.drag; posisi = L.pos, fraksi bingkai)
     Tahap 2  6. Tabel koordinat patok (L.tKoord, halaman satu dig block)    7. Label di dalam dig block (L.lblIn, halaman gabungan)
              8. Catatan & panah bebas (L.notes, koordinat dunia)
   Satuan lembar = mm, sumbu Y ke atas (sama dengan lyPage). Elemen yang bisa digeser diberi op.el; op.pv = hanya pratinjau. */
(function () {
  if (typeof lyPage !== 'function' || window.LX) return;
  var LX = window.LX = {};
  var on = function (L, k) { return L.lx !== false && !!L[k]; };
  LX.kopH = function (L) { return on(L, 'kopX') ? 54 : 34; };

  /* ---------- nilai bawaan ---------- */
  var _def = lyDef;
  lyDef = function () {
    var d = _def();
    d.lx = true; d.inset = true; d.insetSrc = 'pit'; d.kopX = true; d.by = ''; d.chk = ''; d.apr = ''; d.rev = '0'; d.crs = ''; d.src = '';
    d.gridStyle = 'line'; d.lblIn = true; d.tKoord = true; d.drag = true; d.pos = {}; d.notes = [];
    return d;
  };

  var shift = function (p, dx, dy) {
    if (p.pts) p.pts = p.pts.map(function (q) { return [q[0] + dx, q[1] + dy]; });
    if (p.r) p.r = p.r.map(function (q) { return [q[0] + dx, q[1] + dy, q[2], q[3]]; });
    if (typeof p.x === 'number') { p.x += dx; p.y += dy; }
  };
  var wid = function (s, sz) { var w = 0; String(s).split('').forEach(function (c) { w += /[il.,:;|!'1]/.test(c) ? 0.28 : /[mwMW@]/.test(c) ? 0.85 : /[A-Z0-9]/.test(c) ? 0.64 : 0.5; }); return w * sz; };
  var srcTxt = function (L) {
    if (L.src) return L.src; var a = [];
    try { if (BX.m && BX.m.name) a.push('BM ' + BX.m.name); } catch (e) { }
    try { var sp = window.SA && SA.sp; ['topo', 'pit'].forEach(function (r) { var f = sp && sp[r] && sp[r].files && sp[r].files[0]; if (f && f.name) a.push((r === 'topo' ? 'topografi ' : 'pit ') + f.name); }); } catch (e) { }
    return a.join(' | ');
  };

  /* ---------- 2. kop lengkap: baris tambahan di antara baris Scale / Plan No. / Date dan judul ---------- */
  var kop = function (ops, c, L) {
    var tx = c.fx + c.fw - c.tbw, ty = c.fy, w = c.tbw, C = '#233a7e', n0 = ops.length;
    [13, 19, 27].forEach(function (y) { ops.push({ t: 'line', pts: [[tx, ty + y], [tx + w, ty + y]], col: C, lw: 0.25 }); });
    [1, 2].forEach(function (i) { ops.push({ t: 'line', pts: [[tx + w * i / 3, ty + 6], [tx + w * i / 3, ty + 13]], col: C, lw: 0.25 }); });
    [['Dibuat', L.by], ['Diperiksa', L.chk], ['Disetujui', L.apr]].forEach(function (a, i) {
      var x = tx + w * i / 3 + 1.5; ops.push({ t: 'text', x: x, y: ty + 10.6, s: 1.6, txt: a[0], col: '#555555' }); ops.push({ t: 'text', x: x, y: ty + 7.4, s: 2.3, txt: a[1] || '', col: '#000000', font: 'B' });
    });
    ops.push({ t: 'line', pts: [[tx + w / 3, ty + 13], [tx + w / 3, ty + 19]], col: C, lw: 0.25 });
    ops.push({ t: 'text', x: tx + 1.5, y: ty + 14.8, s: 2.2, txt: 'Revisi  ' + (L.rev || '0'), col: '#000000', font: 'T' });
    ops.push({ t: 'text', x: tx + w / 3 + 1.5, y: ty + 14.8, s: 2.2, txt: 'Koordinat  ' + (L.crs || '-'), col: '#000000', font: 'T' });
    var st = 'Sumber data: ' + (srcTxt(L) || '-'), ln = [], cur = '';
    st.split(' ').forEach(function (wd) { if (wid(cur + ' ' + wd, 1.75) > w - 3 && cur) { ln.push(cur); cur = wd; } else cur = cur ? cur + ' ' + wd : wd; }); if (cur) ln.push(cur);
    ln.slice(0, 3).forEach(function (t, i) { ops.push({ t: 'text', x: tx + 1.5, y: ty + 24.6 - i * 2.4, s: 1.75, txt: t, col: '#333333' }); });
    return ops.length - n0;
  };

  /* ---------- 3. gaya grid ---------- */
  var grid = function (ops, c, L) {
    var st = L.gridStyle; if (st !== 'plus' && st !== 'edge') return;
    var at = -1, xs = [], ys = [];
    for (var i = ops.length - 1; i >= 0; i--) if (ops[i].g) { (ops[i].g === 1 ? xs : ys).push(ops[i].g === 1 ? ops[i].pts[0][0] : ops[i].pts[0][1]); at = i; ops.splice(i, 1); }
    if (at < 0) return; var add = [], a = st === 'plus' ? 1.3 : 2.2;
    if (st === 'plus') xs.forEach(function (x) { ys.forEach(function (y) { add.push({ t: 'line', pts: [[x - a, y], [x + a, y]], col: '#000000', lw: 0.25 }); add.push({ t: 'line', pts: [[x, y - a], [x, y + a]], col: '#000000', lw: 0.25 }); }); });
    xs.forEach(function (x) { add.push({ t: 'line', pts: [[x, c.fy], [x, c.fy + a]], col: '#000000', lw: 0.3 }); add.push({ t: 'line', pts: [[x, c.fy + c.fh - a], [x, c.fy + c.fh]], col: '#000000', lw: 0.3 }); });
    ys.forEach(function (y) { add.push({ t: 'line', pts: [[c.fx, y], [c.fx + a, y]], col: '#000000', lw: 0.3 }); var xr = c.grp ? c.fx + c.fw - c.tbw - 3 : c.fx + c.fw; add.push({ t: 'line', pts: [[xr - a, y], [xr, y]], col: '#000000', lw: 0.3 }); });
    Array.prototype.splice.apply(ops, [at, 0].concat(add));
  };

  /* ---------- 1. inset lokasi ---------- */
  var inset = function (ops, c, L) {
    var o = window.OV && (L.insetSrc === 'topo' ? OV.topoF : OV.pitF); if (!o || !o.x || !o.x.length) o = window.OV && (OV.pitF && OV.pitF.x && OV.pitF.x.length ? OV.pitF : OV.topoF);
    if (!o || !o.x || o.x.length < 3) return;
    var x0 = c.X0, x1 = c.X1, y0 = c.Y0, y1 = c.Y1, n = o.x.length, i;
    for (i = 0; i < n; i++) { if (o.x[i] === null) continue; var X = o.x[i] + offX, Y = o.y[i] + offY; if (X < x0) x0 = X; if (X > x1) x1 = X; if (Y < y0) y0 = Y; if (Y > y1) y1 = Y; }
    var w = Math.max(34, Math.min(52, c.fw * 0.2)), h = w * 0.74, th = 4, px = (x1 - x0) * 0.05, py = (y1 - y0) * 0.05; x0 -= px; x1 += px; y0 -= py; y1 += py;
    var ki = Math.min(w / (x1 - x0), (h - th) / (y1 - y0)), bx = c.fx + 14, by = c.fy + c.fh - 4 - h, mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
    var ix = function (X) { return bx + w / 2 + (X - mx) * ki; }, iy = function (Y) { return by + (h - th) / 2 + (Y - my) * ki; }, n0 = ops.length;
    ops.push({ t: 'rect', x: bx, y: by, w: w, h: h, fill: '#ffffff', stroke: '#233a7e', lw: 0.3 });
    ops.push({ t: 'rect', x: bx, y: by + h - th, w: w, h: th, fill: '#233a7e' });
    ops.push({ t: 'text', x: bx + 1.5, y: by + h - th + 1.2, s: 2.1, txt: 'Lokasi lembar   1 : ' + lyNice(1000 / ki, LYSC), col: '#ffffff', font: 'B' });
    ops.push({ t: 'clip', x: bx, y: by, w: w, h: h - th });
    var st = Math.max(1, Math.ceil(n / 6000)), cur = [], col = L.insetSrc === 'topo' ? '#9a7b5a' : '#5b6577', fl = function () { if (cur.length > 1) ops.push({ t: 'line', pts: cur, col: col, lw: 0.15 }); cur = []; }, cnt = 0;
    for (i = 0; i < n; i++) { if (o.x[i] === null) { fl(); cnt = 0; continue; } if (cnt++ % st && i + 1 < n && o.x[i + 1] !== null) continue; cur.push([ix(o.x[i] + offX), iy(o.y[i] + offY)]); } fl();
    var rw = Math.max(1.2, (c.X1 - c.X0) * ki), rh = Math.max(1.2, (c.Y1 - c.Y0) * ki), rx = ix((c.X0 + c.X1) / 2) - rw / 2, ry = iy((c.Y0 + c.Y1) / 2) - rh / 2;
    ops.push({ t: 'rect', x: rx, y: ry, w: rw, h: rh, fill: '#d93a2b', alpha: 0.2 }); ops.push({ t: 'rect', x: rx, y: ry, w: rw, h: rh, stroke: '#c22a1c', lw: 0.45 });
    ops.push({ t: 'unclip' });
    for (i = n0; i < ops.length; i++) ops[i].el = 'inset';
  };

  /* ---------- 6. tabel koordinat patok (halaman satu dig block) ---------- */
  var koord = function (ops, c, L) {
    if (c.grp || c.items.length !== 1) return; var r = c.items[0].r, B = lyBench(), rh = 2.6, cw = 39, avail = c.fw - c.tbw - 6, rows = Math.max(3, Math.floor((c.tbh - 9) / rh));
    var cols = Math.max(1, Math.min(Math.floor(avail / cw), Math.ceil(r.length / rows))), cap = cols * rows, w = cols * cw + 2, h = Math.min(rows, Math.ceil(r.length / cols)) * rh + 8, bx = c.fx + 2, by = c.fy + 2, n0 = ops.length;
    ops.push({ t: 'rect', x: bx, y: by, w: w, h: h, fill: '#ffffff', stroke: '#233a7e', lw: 0.3 });
    ops.push({ t: 'text', x: bx + 1.5, y: by + h - 3.2, s: 2.2, txt: 'Koordinat patok  (RL ' + lyFmt(B[0]) + ' - ' + lyFmt(B[1]) + ')', col: '#000000', font: 'B' });
    var per = Math.ceil(Math.min(r.length, cap) / cols);
    for (var q = 0; q < cols; q++) { var X = bx + 1.5 + q * cw; ops.push({ t: 'text', x: X, y: by + h - 6.4, s: 1.7, txt: 'No     Easting      Northing', col: '#555555', font: 'C' }); }
    r.forEach(function (p, i) {
      if (i >= cap) return; var q = Math.floor(i / per), k = i % per, X = bx + 1.5 + q * cw, Y = by + h - 6.4 - (k + 1) * rh, pad = function (s, n) { s = String(s); while (s.length < n) s = ' ' + s; return s; };
      ops.push({ t: 'text', x: X, y: Y, s: 1.7, txt: (i >= cap - 1 && r.length > cap) ? '... ' + (r.length - cap + 1) + ' titik lagi: lihat export STR' : pad(i + 1, 2) + pad(p[0].toFixed(2), 12) + pad(p[1].toFixed(2), 13), col: '#000000', font: 'C' });
    });
    for (var i = n0; i < ops.length; i++) ops[i].el = 'koord';
  };

  /* ---------- 7. label di dalam dig block (halaman gabungan) ---------- */
  var label = function (add, c, L) {
    if (!c.grp) return;
    c.items.forEach(function (o) {
      var b = lyBB(o.r), bw = (b[1] - b[0]) * c.k, bh = (b[3] - b[2]) * c.k, t = o.ton || {}, l1 = [(o.s && o.s.d) || '', o.dest || ''].filter(Boolean).join(' - '), l2 = t.t ? lyFmt(t.t) + ' t @ ' + (isFinite(t.grade) ? t.grade.toFixed(2) : '-') : '';
      var ln = [l1, l2].filter(Boolean); if (!ln.length) return; var mw = Math.max.apply(null, ln.map(function (s) { return wid(s, 1); }));
      var s = Math.min(3, bw * 0.82 / mw, (bh - 6) / (ln.length * 1.25)); if (!(s >= 1.3)) return;
      var lp = lyLabelPt(o.r), X = c.gx(lp[0]), Y = c.gy(lp[1]) - 2.9;
      ln.forEach(function (tx, i) { add.push({ t: 'text', x: X, y: Y - (i + 1) * s * 1.15, s: s, txt: tx, col: '#000000', font: i ? 'H' : 'B', anchor: 'm', halo: 1 }); });
    });
  };

  /* ---------- 8. catatan & panah bebas ---------- */
  var notes = function (add, c, L) {
    (L.notes || []).forEach(function (nt, i) {
      if (!nt || !nt.txt || nt.x < c.X0 || nt.x > c.X1 || nt.y < c.Y0 || nt.y > c.Y1) return;
      var X = c.gx(nt.x), Y = c.gy(nt.y), el = 'note:' + i;
      if (nt.arrow) {
        var ax = c.gx(nt.ax), ay = c.gy(nt.ay), d = Math.hypot(ax - X, ay - Y) || 1, ux = (ax - X) / d, uy = (ay - Y) / d, hl = 2.4, hw = 0.9;
        add.push({ t: 'line', pts: [[X, Y], [ax - ux * hl, ay - uy * hl]], col: '#b3261e', lw: 0.4, el: el });
        add.push({ t: 'poly', pts: [[ax, ay], [ax - ux * hl - uy * hw, ay - uy * hl + ux * hw], [ax - ux * hl + uy * hw, ay - uy * hl - ux * hw]], fill: '#b3261e', el: 'tip:' + i });
        if (L.drag) add.push({ t: 'circ', x: ax, y: ay, r: 1.6, fill: '#f08a4b', pv: 1, el: 'tip:' + i });
      }
      add.push({ t: 'text', x: X, y: Y + 1, s: 3, txt: nt.txt, col: '#b3261e', font: 'B', anchor: 'm', halo: 1, el: el });
    });
  };

  LX.enrich = function (pg) {
    var c = pg.ctx, L = lyU(); if (!c || L.lx === false) return pg; var ops = pg.ops, i;
    if (on(L, 'kopX')) kop(ops, c, L);
    grid(ops, c, L);
    var add = []; if (on(L, 'lblIn')) label(add, c, L); notes(add, c, L);
    if (add.length) { for (i = 0; i < ops.length; i++) if (ops[i].t === 'unclip') break; Array.prototype.splice.apply(ops, [i, 0].concat(add)); }
    if (on(L, 'tKoord')) koord(ops, c, L);
    if (on(L, 'inset')) inset(ops, c, L);
    var P = L.pos || {}; ops.forEach(function (p) { var q = p.el && P[p.el]; if (q) shift(p, q[0] * c.fw, q[1] * c.fh); });
    return pg;
  };
  var _page = lyPage;
  lyPage = function (items, opt) { var pg = _page(items, opt); try { LX.enrich(pg); } catch (e) { console.warn('LX', e); } return pg; };

  /* ---------- panel ---------- */
  LX.set = function (k, v) { lyU()[k] = v; LX.open = 1; lyPanel(); if (window.SA && SA.dirty) SA.dirty(); };
  LX.noteAdd = function () {
    var L = lyU(), it = [], cx = 0, cy = 0; try { it = lyItems(); } catch (e) { }
    if (!it.length) { alert('Belum ada dig block di flitch ini.'); return; }
    var b = lyBB(it[0].r); cx = (b[0] + b[1]) / 2; cy = b[3] + (b[3] - b[2]) * 0.15 + 2;
    L.notes.push({ txt: 'Catatan', x: cx, y: cy, ax: cx, ay: (b[2] + b[3]) / 2, arrow: true }); LX.set('notes', L.notes);
  };
  LX.noteSet = function (i, k, v) { var N = lyU().notes; if (N[i]) { N[i][k] = v; LX.set('notes', N); } };
  LX.noteDel = function (i) { var N = lyU().notes; N.splice(i, 1); LX.set('notes', N); };
  LX.posReset = function () { LX.set('pos', {}); };
  var _panel = lyPanel;
  lyPanel = function () {
    _panel(); var el = document.getElementById('lyBody'); if (!el) return; var L = lyU(), D = el.querySelectorAll('details.mini'); if (!D.length) return;
    var off = L.lx === false, dis = off ? ' disabled' : '', E = bxE;
    var chk = function (k, t) { return '<label class=sw><input type=checkbox data-lx="' + k + '" ' + (L[k] ? 'checked' : '') + dis + ' onchange="LX.set(\'' + k + '\',this.checked)">' + t + '</label>'; };
    var inp = function (k, lab, ph, w) { return '<div' + (w ? ' style="grid-column:span ' + w + '"' : '') + '><label>' + lab + '</label><input type=text data-lx="' + k + '" value="' + E(L[k] || '') + '" placeholder="' + E(ph || '') + '"' + dis + ' onchange="LX.set(\'' + k + '\',this.value)"></div>'; };
    var sel = function (k, lab, op) { return '<div><label>' + lab + '</label><select data-lx="' + k + '"' + dis + ' onchange="LX.set(\'' + k + '\',this.value)">' + op.map(function (o) { return '<option value="' + o[0] + '"' + (L[k] === o[0] ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select></div>'; };
    var h = '<details class=mini id=lxBox' + (LX.open ? ' open' : '') + ' ontoggle="LX.open=this.open?1:0"><summary>Pengayaan lembar (inset, kop, grid, label, catatan)</summary>' +
      '<label class=sw style="margin-top:6px;font-weight:600"><input type=checkbox data-lx="lx" ' + (off ? '' : 'checked') + ' onchange="LX.set(\'lx\',this.checked)">Pakai pengayaan lembar</label>' +
      '<div class=hint>Matikan sakelar ini bila ingin lembar seperti sebelumnya. Tiap bagian di bawah juga bisa dimatikan sendiri.</div>' +
      '<div class=sws style="margin-top:6px">' + chk('inset', 'Inset lokasi') + chk('kopX', 'Kop lengkap') + chk('lblIn', 'Label di dalam dig block') + chk('tKoord', 'Tabel koordinat patok') + chk('drag', 'Geser elemen di pratinjau') + '</div>' +
      '<div class=g2 style="margin-top:6px">' + sel('insetSrc', 'Isi inset lokasi', [['pit', 'Desain pit'], ['topo', 'Topografi']]) + sel('gridStyle', 'Gaya grid', [['line', 'Garis'], ['plus', 'Tanda +'], ['edge', 'Tepi saja']]) +
      inp('by', 'Dibuat') + inp('chk', 'Diperiksa') + inp('apr', 'Disetujui') + inp('rev', 'Revisi', '0') + inp('crs', 'Sistem koordinat', 'mis. UTM zona ...', 2) + inp('src', 'Sumber data', 'kosong = otomatis dari file yang dimuat', 2) + '</div>' +
      '<div style="margin-top:8px;font-size:11px;font-weight:600;color:var(--mu)">Catatan &amp; panah</div>' +
      (L.notes || []).map(function (n, i) { return '<div style="display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:5px;align-items:center;margin-top:4px"><input type=text data-lxn="' + i + '" value="' + E(n.txt || '') + '"' + dis + ' onchange="LX.noteSet(' + i + ',\'txt\',this.value)"><label class=sw style="margin:0"><input type=checkbox ' + (n.arrow ? 'checked' : '') + dis + ' onchange="LX.noteSet(' + i + ',\'arrow\',this.checked)">panah</label><button type=button title="Hapus catatan" style="height:26px;padding:0 8px"' + dis + ' onclick="LX.noteDel(' + i + ')">&times;</button></div>'; }).join('') +
      '<button type=button id=lxNoteAdd style="width:100%;margin-top:6px"' + dis + ' onclick="LX.noteAdd()">+ Catatan</button>' +
      '<div class=hint>Di <b>Pratinjau</b>: seret panah utara, skala batang, legenda, inset, tabel koordinat, catatan dan ujung panahnya. Klik dua kali = posisi bawaan. <a href="#" onclick="LX.posReset();return false">Kembalikan semua posisi</a></div></details>';
    D[D.length - 1].insertAdjacentHTML('afterend', h);
  };

  /* ---------- 4. geser elemen di pratinjau ---------- */
  var rebuild = function () { var pi = LY.pi; if (!lyBuild()) return; LY.pi = Math.min(pi, LY.pages.length - 1); lyShow(); if (window.SA && SA.dirty) SA.dirty(); };
  LX.move = function (el, dx, dy) { /* dx,dy mm lembar (Y ke atas) */
    var L = lyU(), pg = LY.pages[LY.pi], c = pg && pg.ctx; if (!c) return false; var m = /^(note|tip):(\d+)$/.exec(el);
    if (m) { var n = L.notes[+m[2]]; if (!n) return false; if (m[1] === 'note') { n.x += dx / c.k; n.y += dy / c.k; } else { n.ax += dx / c.k; n.ay += dy / c.k; } }
    else { var p = L.pos[el] || [0, 0]; L.pos[el] = [p[0] + dx / c.fw, p[1] + dy / c.fh]; }
    rebuild(); return true;
  };
  LX.home = function (el) { var L = lyU(); if (L.pos[el]) { delete L.pos[el]; rebuild(); } };
  var bind = function () {
    var d = document.getElementById('lyDlg'), svg = d && d.querySelector('.lyPg svg'), L = lyU(), pg = LY.pages[LY.pi]; if (!svg || !pg || !pg.ctx || L.lx === false || !L.drag) return;
    var bar = d.querySelector('.lyBar span'); if (bar && !bar.querySelector('.lxh')) bar.insertAdjacentHTML('beforeend', ' <span class=lxh style="flex:none">&middot; seret elemen untuk memindahkan, klik dua kali = posisi bawaan</span>');
    [].forEach.call(svg.querySelectorAll('[data-el]'), function (g) { g.style.cursor = 'move'; });
    var st = null, mm = function () { var r = svg.getBoundingClientRect(); return pg.W / r.width; };
    svg.addEventListener('pointerdown', function (e) { var g = e.target.closest && e.target.closest('[data-el]'); if (!g) return; e.preventDefault(); st = { el: g.getAttribute('data-el'), x: e.clientX, y: e.clientY, gs: [].slice.call(svg.querySelectorAll('[data-el="' + g.getAttribute('data-el') + '"]')), k: mm() }; try { svg.setPointerCapture(e.pointerId); } catch (x) { } });
    svg.addEventListener('pointermove', function (e) { if (!st) return; var dx = (e.clientX - st.x) * st.k, dy = (e.clientY - st.y) * st.k; st.gs.forEach(function (g) { g.setAttribute('transform', 'translate(' + dx.toFixed(2) + ' ' + dy.toFixed(2) + ')'); }); });
    svg.addEventListener('pointerup', function (e) { if (!st) return; var s = st, dx = (e.clientX - s.x) * s.k, dy = (e.clientY - s.y) * s.k; st = null; if (Math.hypot(dx, dy) < 0.8) { s.gs.forEach(function (g) { g.removeAttribute('transform'); }); return; } LX.move(s.el, dx, -dy); });
    svg.addEventListener('dblclick', function (e) { var g = e.target.closest && e.target.closest('[data-el]'); if (g) LX.home(g.getAttribute('data-el')); });
  };
  var _show = lyShow;
  lyShow = function () { _show(); try { bind(); } catch (e) { console.warn('LX', e); } };
})();
