/* ================= GC-Ex Drill Hole 0.24.65: PERBAIKAN DARI UJI DATA NYATA (Zona 3, 11-11-2026) =================
   Pemilik menguji pemodelan & estimasi vein dari nol dengan data GC nyata dan meminta seluruh temuan diperbaiki.
   Sebagian perbaikan ada langsung di sumbernya (gcex_dh_base.html, env_dh.js, aoi_dh.js, dom20_dh.js); modul ini
   menambah yang berupa fitur baru:
     #1  Export .mdl Surpac untuk block model yang TIDAK dibuka dari .mdl (kerangka AOI dari nol, CSV beraturan):
         header Version 4.0 disusun sendiri (origin = pojok blok terkecil, root = sel x 2^L), record octree.
     #16 Geostatistik: satu tombol "Sayatan di bidang domain" -- sayatan panjang di bidang vein (strike & dip solid),
         tebal mencakup semua kontak domain aktif, sehingga statistik / variogram memakai seluruh data domain.
     #17 Tampilan: label hole otomatis dimatikan bila > 150 lubang (bisa dinyalakan lagi), topografi yang baru diimpor
         langsung tampil, nama lengkap node Project Tree muncul sebagai tooltip.
     #18 Jendela "Status alur pemodelan": daftar langkah data -> domain -> string -> solid -> parameter -> block model ->
         estimasi -> reporting -> export, masing-masing dengan status & tombol buka.                                  */
(function () {
  if (window.NY) return;
  var NY = window.NY = {};
  function $(i) { return document.getElementById(i); }
  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function N(v, d) { return (v == null || !isFinite(v)) ? '-' : (+v).toLocaleString('id-ID', { maximumFractionDigits: d == null ? 0 : d, minimumFractionDigits: d || 0 }); }

  /* ======================= #1 header .mdl sintetis ======================= */
  NY.mdlSynth = function (m) {
    var n = m.n, mn = [Infinity, Infinity, Infinity], lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity], i, k;
    for (i = 0; i < n; i++) {
      var s = [m.sx[i], m.sy[i], m.sz[i]], c = [m.x[i], m.y[i], m.z[i]];
      if (!(s[0] > 0)) continue;
      for (k = 0; k < 3; k++) { if (s[k] < mn[k]) mn[k] = s[k]; if (c[k] - s[k] / 2 < lo[k]) lo[k] = c[k] - s[k] / 2; if (c[k] + s[k] / 2 > hi[k]) hi[k] = c[k] + s[k] / 2; }
    }
    if (!isFinite(mn[0])) return { err: 'Block model kosong.' };
    var cfg = (m.src && m.src.cfg) || (m.aoi && m.aoi.cfg) || null, O = lo.slice();
    /* origin grid AOI (mis. origin .mdl acuan) dipakai bila blok memang sejajar dengannya */
    if (cfg && cfg.snap && (cfg.ox || cfg.oy || cfg.oz)) {
      var og = [+cfg.ox || 0, +cfg.oy || 0, +cfg.oz || 0], okO = true;
      for (k = 0; k < 3; k++) { var q = (lo[k] - og[k]) / mn[k]; if (q < -1e-6 || Math.abs(q - Math.round(q)) > 1e-6) okO = false; }
      if (okO) O = og;
    }
    var lvl = function (O2) { var L2 = 0; for (var q = 0; q < 3; q++) L2 = Math.max(L2, Math.ceil(Math.log2(Math.max(1, (hi[q] - O2[q]) / mn[q]) - 1e-9))); return L2; };
    var L = lvl(O); if (L > 19) { O = lo.slice(); L = lvl(O); }   /* kode octree .mdl: maks 19 tingkat (3 + 6 + 10 digit) */
    if (L > 19) return { err: 'Extent terlalu besar untuk octree .mdl (' + L + ' tingkat, maks 19).' };
    var RT = [mn[0] * Math.pow(2, L), mn[1] * Math.pow(2, L), mn[2] * Math.pow(2, L)], bad = 0;
    for (i = 0; i < n; i++) {
      var lx = Math.log2(RT[0] / m.sx[i]), ly = Math.log2(RT[1] / m.sy[i]), lz = Math.log2(RT[2] / m.sz[i]);
      if (Math.abs(lx - Math.round(lx)) > 1e-6 || Math.abs(lx - ly) > 1e-6 || Math.abs(lx - lz) > 1e-6) { bad++; continue; }
      var ix = (m.x[i] - m.sx[i] / 2 - O[0]) / m.sx[i], iy = (m.y[i] - m.sy[i] / 2 - O[1]) / m.sy[i], iz = (m.z[i] - m.sz[i] / 2 - O[2]) / m.sz[i];
      if (Math.abs(ix - Math.round(ix)) > 1e-4 || Math.abs(iy - Math.round(iy)) > 1e-4 || Math.abs(iz - Math.round(iz)) > 1e-4) bad++;
    }
    if (bad) return { err: bad.toLocaleString('id-ID') + ' blok tidak jatuh di kisi octree (ukuran bukan 2^k kali sel terkecil atau posisi tidak sejajar). Export .mdl dibatalkan; pakai export CSV.' };
    /* atribut: numerik = real 3 desimal (nilai kosong -99), kategori = karakter */
    var ST = [];
    Object.keys(m.num).forEach(function (a) { if (a === 'AOI_BLOK') return; ST.push({ name: a.toLowerCase().replace(/[^a-z0-9_]/g, '_').slice(0, 30), src: a, type: 2, dec: 3, def: -99 }); });
    Object.keys(m.cat).forEach(function (a) { ST.push({ name: a.toLowerCase().replace(/[^a-z0-9_]/g, '_').slice(0, 30), src: a, type: 3, def: '' }); });
    var seen = {}; ST = ST.filter(function (a) { if (seen[a.name]) return false; seen[a.name] = 1; return true; });
    var te = new TextEncoder(), name = String(m.name || 'gcex_bm').replace(/\.mdl$/i, '').replace(/[^A-Za-z0-9_.-]+/g, '_') + '.mdl';
    var head = te.encode('### Block Model ###\nVersion 4.0\n'), nmB = te.encode(name), defs = ST.map(function (a) { return bxMdlAttrDef(a, te); });
    var tot = head.length + 1 + nmB.length + 2 + 12 + 72 + 8; defs.forEach(function (d) { tot += d.length; }); tot += 4;
    var H = new Uint8Array(tot), dv = new DataView(H.buffer), p = 0;
    H.set(head, p); p += head.length; H[p++] = 0; var nmA = p; H.set(nmB, p); p += nmB.length; var nmEnd = p; H[p++] = 0; H[p++] = 0;
    dv.setInt32(p, 1); dv.setInt32(p + 4, L); dv.setInt32(p + 8, L); p += 12;
    [O[0], O[1], O[2], RT[0], RT[1], RT[2], hi[0] - O[0], hi[1] - O[1], hi[2] - O[2]].forEach(function (v) { dv.setFloat64(p, v); p += 8; });
    dv.setInt32(p, 0); var pNa = p + 4; dv.setInt32(p + 4, ST.length); p += 8;
    defs.forEach(function (d) { H.set(d, p); p += d.length; }); var pAE = p; dv.setInt32(p, 0); p += 4;
    /* model bayangan: nama atribut .mdl -> larik GC-Ex */
    var num = {}, cat = {};
    ST.forEach(function (a) { if (a.type === 3) cat[a.name] = m.cat[a.src]; else num[a.name] = m.num[a.src]; });
    var mm = { n: n, x: m.x, y: m.y, z: m.z, sx: m.sx, sy: m.sy, sz: m.sz, num: num, cat: cat, name: m.name,
      mdl: { synth: true, origin: O, root: RT, extent: [hi[0] - O[0], hi[1] - O[1], hi[2] - O[2]], hraw: H, nmA: nmA, nmB: nmEnd, pNa: pNa, pAE: pAE,
             st: ST.map(function (a) { return { name: a.name, type: a.type, def: a.def, dec: a.dec }; }), tail: null, file: name, add: [] } };
    return { mm: mm, name: name, L: L, origin: O, root: RT, st: ST };
  };
  NY.mdlExport = function () {
    var m = window.BX && BX.m; if (!m) { alert('Belum ada block model GC.'); return; }
    var S = NY.mdlSynth(m); if (S.err) { alert(S.err); return; }
    var nm = (S.name.replace(/\.mdl$/i, '') + '_gcex_' + gxDate()).replace(/[^A-Za-z0-9_.-]+/g, '_') + '.mdl', R = bxMdlBytes(S.mm, nm);
    gxDl(new Blob(R.parts, { type: 'application/octet-stream' }), nm);
    var el = $('bxMdlMsg');
    if (el) el.innerHTML = '&#10003; ' + E(nm) + ': ' + m.n.toLocaleString('id-ID') + ' blok, header .mdl disusun baru (origin ' + S.origin.map(function (v) { return N(v, 2); }).join(' / ') +
      ', sel ' + S.mm.sx[0] + ' m, ' + S.L + ' tingkat octree), atribut: ' + S.st.map(function (a) { return a.name; }).join(', ') + '. Nilai kosong ditulis -99.';
    NY.lastMdl = { name: nm, n: m.n, st: S.st.map(function (a) { return a.name; }), origin: S.origin, root: S.root };
    return R;
  };
  if (typeof window.bxMdlExport === 'function') {
    var _ex = bxMdlExport;
    window.bxMdlExport = bxMdlExport = function () {
      var m = window.BX && BX.m;
      if (m && !(m.mdl && m.mdl.hraw)) return NY.mdlExport();
      return _ex.apply(this, arguments);
    };
  }

  /* ======================= #16 sayatan di bidang domain (Geostatistik) ======================= */
  NY.planeSec = function () {
    var d = window.GM && gmDom(GM.act); if (!d) { alert('Pilih domain aktif dulu (Geological Modelling).'); return; }
    var top = d.env ? gmDom(d.env) : (gmIsKid(d) ? gmDom(d.par) : d), S = typeof arStrike === 'function' ? arStrike(top) : null;
    if (!S) { alert('Domain ' + top.name + ' belum punya cukup kontak (minimal 2 lubang ber-flag).'); return; }
    var R = (typeof meGrpR === 'function' ? meGrpR(top) : null) || IM.R[top.id], dip = R && R.st && isFinite(R.st.dip) ? R.st.dip : 90;
    var C = gmContacts(top.id).L.map(function (c) { return { x: (c.hw.x + c.fw.x) / 2, y: (c.hw.y + c.fw.y) / 2, z: (c.hw.z + c.fw.z) / 2 }; });
    var r = S.az * Math.PI / 180, ux = Math.sin(r), uy = Math.cos(r), L2 = 0, best = null;
    C.forEach(function (p) { L2 = Math.max(L2, Math.abs((p.x - S.c[0]) * ux + (p.y - S.c[1]) * uy)); });
    L2 = Math.max(50, L2 * 1.2 + 20);
    var zc = 0; C.forEach(function (p) { zc += p.z; }); zc /= Math.max(1, C.length);
    [1, -1].forEach(function (sg) {
      $('sMode').value = 'P';
      $('p1e').value = (S.c[0] - sg * ux * L2 + offX).toFixed(2); $('p1n').value = (S.c[1] - sg * uy * L2 + offY).toFixed(2);
      $('p2e').value = (S.c[0] + sg * ux * L2 + offX).toFixed(2); $('p2n').value = (S.c[1] + sg * uy * L2 + offY).toFixed(2);
      $('dipS').value = Math.round(dip); if ($('dipN')) $('dipN').value = Math.round(dip);
      var ls = $('limSeg'); if (ls) ls.checked = false;
      try { modeChanged(); } catch (e) {}
      /* tebal = sebaran kontak tegak lurus bidang (posisi 0 di pusat kontak) */
      $('pos').value = 0; $('thick').value = 400;
      var K = secK().K, g = K[0], dd = C.map(function (p) { return sd(g.n, g.c, p); }), mid = dd.reduce(function (a, b) { return a + b; }, 0) / Math.max(1, dd.length);
      var spread = 0; dd.forEach(function (v) { spread = Math.max(spread, Math.abs(v - mid)); });
      var th = Math.min(200, Math.max(10, 2 * spread + 6));
      if (!best || th < best.th) best = { sg: sg, th: th, pos: Math.round(mid * 10) / 10 };
    });
    $('p1e').value = (S.c[0] - best.sg * ux * L2 + offX).toFixed(2); $('p1n').value = (S.c[1] - best.sg * uy * L2 + offY).toFixed(2);
    $('p2e').value = (S.c[0] + best.sg * ux * L2 + offX).toFixed(2); $('p2n').value = (S.c[1] + best.sg * uy * L2 + offY).toFixed(2);
    try { modeChanged(); } catch (e) {}
    $('pos').value = best.pos; $('thick').value = Math.round(best.th);
    NY.lastPlane = { az: S.az, dip: dip, thick: Math.round(best.th), pos: best.pos, n: C.length, dom: top.name };
    GS.domOnly = true;
    try { if (!GS.open) gsToggle(); else gsRun(); } catch (e) { console.error(e); }
    try { updatePlot(); } catch (e) {}
    return NY.lastPlane;
  };
  function gsBtn() {
    var b = $('gsDomBar'); if (!b || b.querySelector('.nyPlane')) return;
    var bt = document.createElement('button'); bt.type = 'button'; bt.className = 'nyPlane';
    bt.title = 'Sayatan panjang di bidang vein domain aktif (strike & dip solid), tebal mencakup semua kontak -- statistik & variogram memakai seluruh data domain';
    bt.innerHTML = '&#9638; Sayatan di bidang domain'; bt.onclick = function () { NY.planeSec(); };
    b.appendChild(bt);
  }
  /* #15: bilah domain disegarkan setiap panel Geostatistik tampil (tanpa membungkus gsToggle) */
  (function () { var p = $('gsPanel'); if (!p) return; var was = false;
    new MutationObserver(function () { var on = p.style.display === 'block'; if (on && !was) { try { gsBar(); } catch (e) {} } was = on; }).observe(p, { attributes: true, attributeFilter: ['style'] }); })();
  if (typeof window.gsBar === 'function') { var _gb = gsBar; window.gsBar = gsBar = function () { var r = _gb.apply(this, arguments); try { gsBtn(); } catch (e) {} return r; }; }

  /* ======================= #17 tampilan ======================= */
  /* sekali per dataset (kunci localStorage): sesudah itu pilihan pengguna dihormati */
  (function cek(t) {
    if (!(window.collars && collars.length && $('showLabel'))) { if ((t || 0) < 120) setTimeout(function () { cek((t || 0) + 1); }, 500); return; }
    var key = 'gcex_ny_auto_' + String(window.ZONE || '').slice(0, 60), done = null; try { done = localStorage.getItem(key); } catch (e) {}
    if (done) return;
    try {
      if (collars.length > 150 && $('showLabel').checked) { $('showLabel').checked = false; NY.lblOff = collars.length; }
      if (typeof imTopoOk === 'function' && imTopoOk() && $('ovTopoS') && $('ovTopoL') && !$('ovTopoS').checked && !$('ovTopoL').checked) { $('ovTopoL').checked = true; NY.topoOn = true; }
      if (NY.lblOff || NY.topoOn) { updatePlot(); try { localStorage.setItem(key, '1'); } catch (e) {}
        if (NY.lblOff && typeof gxToast === 'function') gxToast('Label hole dimatikan otomatis (' + collars.length + ' lubang saling tumpuk). Nyalakan lagi di Layer.'); }
    } catch (e) { console.error(e); }
  })();
  /* tooltip nama lengkap di Project Tree (nama dataset panjang terpotong "Zo...") */
  function ptTitles() {
    var t = $('ptree'); if (!t) return;
    t.querySelectorAll('.ptr').forEach(function (r) { var l = r.querySelector('.ptl'); if (!l) return; var nm = l.textContent, tt = r.getAttribute('title') || '';
      if (tt.indexOf(nm) !== 0) r.setAttribute('title', nm + (tt && tt !== nm ? ' — ' + tt : '')); });
  }
  (function () { var t = $('ptree'); if (!t) { setTimeout(arguments.callee, 500); return; } new MutationObserver(function () { ptTitles(); }).observe(t, { childList: true, subtree: true }); ptTitles(); })();

  /* ======================= #18 status alur pemodelan ======================= */
  NY.steps = function () {
    var L = [], add = function (t, st, info, go) { L.push({ t: t, st: st, info: info, go: go }); };
    var nc = window.collars ? collars.length : 0, topo = typeof imTopoOk === 'function' && imTopoOk();
    add('Database bor', nc ? 'ok' : 'todo', nc ? N(nc) + ' lubang, ' + N(window.assays ? assays.length : 0) + ' interval assay' : 'impor collar / survey / assay / geologi', "uiTab('Data')");
    add('Topografi', topo ? 'ok' : 'opt', topo ? 'aktif (dipakai potong solid & Reporting)' : 'opsional, untuk area tertambang & laporan in-situ', "uiTab('Data')");
    var D = window.GM ? GM.doms : [], V = D.filter(function (d) { return !d.env; }), S = typeof gmStats === 'function' ? gmStats() : {};
    var flagged = V.filter(function (d) { return S[d.id] && S[d.id].n > 0; });
    add('Domain & flag', !V.length ? 'todo' : flagged.length === V.length ? 'ok' : 'part', V.length ? V.map(function (d) { var s = S[d.id] || { h: {}, l: 0 }; return E(d.name) + (d.par ? ' (cabang)' : '') + ': ' + Object.keys(s.h).length + ' lubang, ' + N(s.l, 1) + ' m'; }).join('<br>') : 'buat domain vein lalu flag interval', "uiTab('GM')");
    var withStr = D.filter(function (d) { return GM.str.some(function (s) { return s.dom === d.id; }); });
    add('String kontrol HW / FW', !D.length ? 'todo' : withStr.length === D.length ? 'ok' : withStr.length ? 'part' : 'todo', D.map(function (d) { return E(d.name) + ': ' + GM.str.filter(function (s) { return s.dom === d.id; }).length + ' string'; }).join('<br>') || '-', "uiTab('GM')");
    var sol = D.map(function (d) { var R = IM.R[d.id]; return { d: d, R: R && R.mesh ? R : null, err: R && R.err }; }), nOk = sol.filter(function (o) { return o.R; }).length, warn = '';
    var si = sol.map(function (o) { if (!o.R) return E(o.d.name) + ': ' + (o.err ? '<span class=warn>gagal: ' + E(o.err) + '</span>' : 'belum dibangun'); var s = o.R.st;
      if ((s.far15 || 0) > 0.25) warn = ' ';
      return E(o.d.name) + ': ' + N(s.vol) + ' m&sup3;, flag di dalam ' + s.nin + '/' + s.nfl + (s.nab ? ' (+' + s.nab + ' tertambang)' : '') + ((s.far15 || 0) > 0.25 ? ' <span class=warn>&middot; ' + N(s.far15 * 100) + '% volume &gt; 15 m dari bor</span>' : ''); }).join('<br>');
    add('Solid (RBF)', !D.length ? 'todo' : nOk === D.length ? (warn ? 'part' : 'ok') : nOk ? 'part' : 'todo', si || '-', "uiTab('GM')");
    var tops = D.filter(function (d) { return !(typeof gmIsKid === 'function' && gmIsKid(d)); }), par = tops.filter(function (d) { return typeof meParOf === 'function' && meParOf(d); });
    add('Parameter estimasi (Geostatistik)', !tops.length ? 'todo' : par.length === tops.length ? 'ok' : par.length ? 'part' : 'todo', tops.map(function (d) { var P = typeof meParOf === 'function' ? meParOf(d) : null; return E(d.name) + ': ' + (P ? 'komposit ' + (P.L || '-') + ' m, top-cut ' + (P.tc || '-') + ', nugget ' + N(P.m.c0, 2) : 'belum disimpan'); }).join('<br>') || '-', "try{gxDomAct(GM.act,'gs')}catch(e){}");
    var m = window.BX && BX.m;
    add('Block model', m ? 'ok' : 'todo', m ? E(m.name) + ' &middot; ' + N(m.n) + ' blok &middot; ' + E(m.sizes || '') : 'impor .mdl / CSV atau buat kerangka AOI', "uiTab('BM')");
    var st = window.ME && ME.store, runs = st && st.runs || [], lastBy = {};
    runs.forEach(function (r) { lastBy[r.dom] = r; });
    var est = tops.filter(function (d) { return lastBy[d.name]; });
    add('Model Estimation', !tops.length || !m ? 'todo' : est.length === tops.length ? 'ok' : est.length ? 'part' : 'todo', tops.map(function (d) { var r = lastBy[d.name]; return E(d.name) + ': ' + (r ? 'run #' + r.id + ' (' + E(r.date) + '), ' + N(r.nEst) + ' blok' + (r.nFail ? ', <span class=warn>' + N(r.nFail) + ' tanpa sampel cukup</span>' : '') : 'belum'); }).join('<br>') || '-', "uiTab('ME')");
    var rp = window.RP && RP.res;
    add('Reporting', rp ? 'ok' : 'todo', rp ? N(rp.nb) + ' blok terlapor (' + E(rp.lab || '') + ')' : 'tonase & kadar per cut-off', "try{uiTab('RP')}catch(e){}");
    add('Export ke Surpac (.mdl)', NY.lastMdl ? 'ok' : 'opt', NY.lastMdl ? E(NY.lastMdl.name) : 'panel Block Model &rarr; Export block model GC (.mdl Surpac)', "uiTab('BM')");
    var ix = L.findIndex(function (s) { return s.st === 'todo' || s.st === 'part'; }); if (ix >= 0) L[ix].next = true;
    return L;
  };
  NY.statusHtml = function () {
    var ic = { ok: '&#10003;', part: '&#9680;', todo: '&#9675;', opt: '&ndash;' }, col = { ok: 'var(--ok,#2b8a3e)', part: '#e8590c', todo: 'var(--mu)', opt: 'var(--mu)' };
    return '<div class=nyst>' + NY.steps().map(function (s, i) {
      return '<div class="nyr' + (s.next ? ' nx' : '') + '"><span class=nyi style="color:' + col[s.st] + '">' + ic[s.st] + '</span><div><b>' + (i + 1) + '. ' + s.t + '</b>' + (s.next ? ' <small class=nyn>langkah berikutnya</small>' : '') +
        '<div class=nyd>' + s.info + '</div></div><button type=button onclick="' + s.go + '">Buka</button></div>';
    }).join('') + '<div class=hint>&#10003; selesai &middot; &#9680; sebagian / perlu dicek &middot; &#9675; belum &middot; &ndash; opsional. Jendela ini diperbarui otomatis.</div></div>';
  };
  NY.status = function () { if (!window.POP) return; POP.win('nyStatusWin', 'Status alur pemodelan', NY.statusHtml()); NY.statusOn = true; };
  setInterval(function () { var w = $('nyStatusWin'); if (w && w.style.display !== 'none' && !w.classList.contains('min')) { var b = w.querySelector('.gxpb'); if (b) b.innerHTML = NY.statusHtml(); } }, 2500);
  function addLaunch(host, id) {
    var b = $(host); if (!b || $(id)) return;
    var bt = document.createElement('button'); bt.type = 'button'; bt.id = id; bt.className = 'nyLaunch'; bt.innerHTML = '&#9745; Status alur pemodelan';
    bt.title = 'Langkah data &rarr; domain &rarr; string &rarr; solid &rarr; parameter &rarr; block model &rarr; estimasi &rarr; reporting &rarr; export, dengan statusnya';
    bt.onclick = function () { NY.status(); }; b.insertBefore(bt, b.firstChild);
  }
  ['gmPanel', 'mePanel'].forEach(function (f) {
    if (typeof window[f] !== 'function') return; var _o = window[f];
    window[f] = function () { var r = _o.apply(this, arguments); try { addLaunch(f === 'gmPanel' ? 'gmBody' : 'meBody', f === 'gmPanel' ? 'nyStGm' : 'nyStMe'); } catch (e) {} return r; };
  });
  var st = document.createElement('style');
  st.textContent = '.nyLaunch{width:100%;margin:0 0 8px}.gsDomBar .nyPlane{margin-left:6px;font-size:11px;padding:1px 8px}' +
    '.nyst{min-width:380px;max-width:560px;font-size:12px}.nyr{display:grid;grid-template-columns:18px 1fr auto;gap:6px;align-items:start;padding:6px 4px;border-bottom:1px solid var(--bd)}' +
    '.nyr.nx{background:var(--sf2)}.nyi{font-size:14px;line-height:16px}.nyd{color:var(--mu);font-size:11px;margin-top:2px}.nyn{color:#e8590c}.nyr button{font-size:11px;padding:1px 8px}';
  document.head.appendChild(st);
  try { gmPanel(); } catch (e) {} try { mePanel(); } catch (e) {}
})();
