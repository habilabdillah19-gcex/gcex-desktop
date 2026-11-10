/* ================= GC-Ex (Block Model 0.24.60+ / Drillhole 0.24.63+): BAGIAN PANEL → JENDELA POP-UP =================
   Usulan pemilik (10 Nov 2026): panel di dalam panel yang harus di-scroll naik-turun diganti pop-up yang bisa
   disembunyikan bila tidak dipakai. Modul bersama kedua aplikasi (Drillhole lewat SHARED di build_dh.py); bagian yang
   host-nya tidak ada di aplikasi itu dilewati.

   Cara kerja: tiap bagian punya tombol "⧉ Pop-up" di judulnya. Saat menyala, isi bagian itu DIPINDAH (bukan disalin)
   ke jendela mengambang setiap kali panel digambar ulang (MutationObserver), sehingga semua tombol / isian tetap
   bekerja seperti di panel. Di panel tersisa satu baris "ditampilkan di jendela pop-up · kembalikan". Jendela bisa
   digeser, diubah ukurannya (pojok kanan bawah), diperkecil (–) dan ditutup (×); menutup = kembali ke panel. Pilihan
   diingat per komputer (localStorage). Gaya panel '#host …' disalin ke '.gxpb.h-host …' supaya isi tampil sama.

   Bagian (pemilik 10 Nov 2026):
     Block Model : Register poligon (bawaan pop-up), Register untuk database (bawaan), Layout & export As-Mined,
                   Solid Vein titik atap & poligon per flitch, daftar dig block per flitch (Running grade & tonnage),
                   hasil Reporting.
     Drillhole   : hasil Reporting; panel Geostatistik (statistik & variogram) bisa dilepas jadi jendela;
                   jendela "Data per lubang" (web-src-dh/holedata_dh.js) memakai POP.win. */
(function () {
  if (window.POP) return;
  /* ---------- jendela mengambang umum ---------- */
  var ZT = 60;
  function win(id, judul, isi) { var w = document.getElementById(id);
    if (!w) { w = document.createElement('div'); w.id = id; w.className = 'gxpop'; w.innerHTML = '<div class=gxph><b></b><span><button type=button data-m title="Perkecil / perbesar">&#8211;</button><button type=button data-x title="Tutup">&times;</button></span></div><div class=gxpb></div>'; document.body.appendChild(w);
      var h = w.firstChild, dr = null; w.addEventListener('mousedown', function () { w.style.zIndex = ++ZT; }, true);
      h.addEventListener('mousedown', function (e) { if (e.target.closest('button')) return; var r = w.getBoundingClientRect(); dr = [e.clientX - r.left, e.clientY - r.top]; e.preventDefault(); });
      window.addEventListener('mousemove', function (e) { if (!dr) return; w.style.left = Math.max(0, Math.min(innerWidth - 120, e.clientX - dr[0])) + 'px'; w.style.top = Math.max(0, Math.min(innerHeight - 40, e.clientY - dr[1])) + 'px'; });
      window.addEventListener('mouseup', function () { dr = null; });
      h.querySelector('[data-x]').onclick = function () { w.style.display = 'none'; }; h.querySelector('[data-m]').onclick = function () { w.classList.toggle('min'); }; }
    w.querySelector('.gxph b').textContent = judul; if (isi != null) w.querySelector('.gxpb').innerHTML = isi; w.style.display = 'flex'; if (isi != null) w.classList.remove('min'); w.style.zIndex = ++ZT; return w; }

  var ON = {}; try { ON = JSON.parse(localStorage.getItem('gcex_popout') || '{}') || {}; } catch (e) { ON = {}; }
  /* bawaan pop-up (pemilik 10-11-2026: "Flitch asmined banyak loh, mengapa tidak disajikan dalam bentuk pop up";
     "Setelah saya lihat layout nya, jadikan ini menu pop up") */
  ['am.reg', 'am.db'].forEach(function (k) { if (ON[k] === undefined) ON[k] = true; });
  var simpan = function () { try { localStorage.setItem('gcex_popout', JSON.stringify(ON)); } catch (e) {} };

  /* judul .amh (As-Mined): saudara sesudah judul sampai judul berikutnya */
  var amh = function (re) { return { hd: function (host) { var H = host.querySelectorAll('.amh'); for (var i = 0; i < H.length; i++) if (re.test(H[i].textContent.trim())) return H[i]; return null; }, grab: sampai('amh') }; };
  function sampai(cls) { return function (hd) { var out = [], n = hd.nextSibling; while (n && !(n.nodeType === 1 && n.classList && n.classList.contains(cls))) { out.push(n); n = n.nextSibling; } return out; }; }
  var svsec = function (k) { return { hd: function (host) { var s = host.querySelector('.svsec[data-sec="' + k + '"]'); return s ? s.querySelector('.svh') : null; }, grab: sampai('__tidakada__') }; };
  var ext = function (a, b) { for (var k in b) a[k] = b[k]; return a; };
  var DEF = [
    ext({ k: 'am.reg', host: 'amBody', t: 'Daftar poligon per flitch (Register poligon)' }, amh(/^Register poligon/)),
    ext({ k: 'am.db', host: 'amBody', t: 'Register untuk database · Report As-Mined', w: 'min(760px,calc(100vw - 440px))' }, amh(/^Register untuk database/)),
    ext({ k: 'am.ly', host: 'amBody', t: 'Layout & export As-Mined' }, amh(/^Layout/)),
    ext({ k: 'sv.pts', host: 'svBody', t: 'Solid Vein — titik atap (pick-up roof)' }, svsec('pts')),
    ext({ k: 'sv.poly', host: 'svBody', t: 'Solid Vein — poligon per flitch', w: 'min(700px,calc(100vw - 440px))' }, svsec('poly')),
    /* daftar dig block flitch aktif: judul "Σ Running grade & tonnage" sampai sub-judul .dbsub berikutnya */
    { k: 'db.list', host: 'dbBody', t: 'Daftar dig block (running grade & tonnage)', w: 'min(680px,calc(100vw - 440px))', css: ['#pBM .lyb'],
      hd: function (host) { var H = host.querySelectorAll('.dbsub'); for (var i = 0; i < H.length; i++) if (/Running grade/.test(H[i].textContent)) return H[i]; return null; }, grab: sampai('dbsub') },
    /* hasil Reporting (BM & DH): semua isi sesudah tab Atribut / Constraint / Hasil, hanya saat tab Hasil berisi hasil;
       saat pindah ke Constraint, jendela tetap memperlihatkan hasil terakhir */
    { k: 'rp.res', host: 'rpBody', t: 'Hasil Reporting Block Model', w: 'min(820px,calc(100vw - 440px))', css: ['#pRep'], btnIn: true,
      hd: function (host) { if (!(window.RP && RP.sec === '2' && RP.res)) return null; return host.querySelector('.rptabs'); }, grab: sampai('__tidakada__') }
  ];
  var sibuk = false;
  function wOf(d) { var id = 'gxpo_' + d.k.replace(/\W/g, '_'), w = document.getElementById(id);
    if (!w) { var i = DEF.indexOf(d); w = win(id, d.t, ''); w.style.left = (420 + 28 * i) + 'px'; w.style.top = (80 + 24 * i) + 'px'; w.style.width = d.w || 'min(620px,calc(100vw - 440px))'; w.style.display = 'none';
      w.querySelector('.gxpb').classList.add('h-' + d.host); salinCss(); w.querySelector('[data-x]').onclick = function () { POP.set(d.k, false); }; }
    return w; }
  /* ---------- gaya panel → jendela ---------- */
  var cssN = -1; function salinCss() { var map = {}; DEF.forEach(function (d) { map['#' + d.host] = d.host; (d.css || []).forEach(function (c) { map[c] = d.host; }); });
    var esc = function (k) { return k.replace(/[.#]/g, '\\$&').replace(/ /g, '\\s+'); }, keys = Object.keys(map).sort(function (a, b) { return b.length - a.length; }), RX = keys.map(function (k) { return [new RegExp(esc(k) + '(?![\\w-])', 'g'), '.gxpb.h-' + map[k]]; }), out = [], n = 0;
    try { [].forEach.call(document.styleSheets, function (sh) { var R; try { R = sh.cssRules; } catch (e) { return; } if (!R || (sh.ownerNode && sh.ownerNode.id === 'gxpoCss')) return;
        [].forEach.call(R, function (r) { var sel = r.selectorText; if (!sel) return; var ub = false; RX.forEach(function (q) { q[0].lastIndex = 0; if (q[0].test(sel)) { q[0].lastIndex = 0; sel = sel.replace(q[0], q[1]); ub = true; } }); if (ub) { n++; out.push(sel + '{' + r.style.cssText + '}'); } }); }); } catch (e) {}
    if (n === cssN) return; cssN = n; var el = document.getElementById('gxpoCss'); if (!el) { el = document.createElement('style'); el.id = 'gxpoCss'; document.head.appendChild(el); }
    el.textContent = out.join('\n') + '\n.gxpb .lylist{max-height:none!important}'; }
  function render(d) { try { ({ amBody: window.amPanel, svBody: window.SV && SV.panel, dbBody: window.dbPanel, rpBody: window.rpPanel }[d.host] || function () {})(); } catch (e) {} }
  function tampil(d, w, vis) { if (d._force || (vis && !d._vis)) { w.style.display = 'flex'; w.classList.remove('min'); w.style.zIndex = ++ZT; } d._force = 0; d._vis = vis; }
  function apply() { if (sibuk) return; amati(); sibuk = true;
    try { DEF.forEach(function (d) { var host = document.getElementById(d.host); if (!host) return; var hd = d.hd(host); if (!hd) { d._vis = false; return; }
        if (!hd.querySelector('.gxpob')) { var b = document.createElement('button'); b.type = 'button'; b.className = 'gxpob'; b.title = ON[d.k] ? 'Kembalikan ke panel' : 'Tampilkan bagian ini di jendela pop-up (bisa digeser, diperkecil, ditutup)'; b.innerHTML = ON[d.k] ? '&#8617; Panel' : '&#10697; Pop-up';
          b.onclick = function (e) { e.stopPropagation(); e.preventDefault(); POP.set(d.k, !ON[d.k]); }; hd.appendChild(b); }
        if (!ON[d.k]) return; var N = d.grab(hd); if (!N.length) return; var w = wOf(d), vis = hd.offsetParent !== null;
        if (N.some(function (n) { return n.nodeType === 1 && n.classList && n.classList.contains('gxpoph'); })) { tampil(d, w, vis); return; } /* sudah dipindah, panel belum digambar ulang */
        var body = w.querySelector('.gxpb'), st = body.scrollTop;
        var ph = document.createElement('div'); ph.className = 'gxpoph'; ph.innerHTML = '&#10697; Ditampilkan di jendela pop-up <b>' + d.t.replace(/</g, '&lt;') + '</b> &middot; <a href="#">tampilkan jendela</a> &middot; <a href="#" data-k>kembalikan ke panel</a>';
        ph.querySelector('a').onclick = function (e) { e.preventDefault(); w.style.display = 'flex'; w.classList.remove('min'); w.style.zIndex = ++ZT; }; ph.querySelector('[data-k]').onclick = function (e) { e.preventDefault(); POP.set(d.k, false); };
        hd.parentNode.insertBefore(ph, N[0]); body.innerHTML = ''; N.forEach(function (n) { body.appendChild(n); }); body.scrollTop = st;
        /* grafik Plotly di dalam isi yang dipindah perlu mengukur ulang lebarnya */
        setTimeout(function () { try { [].forEach.call(body.querySelectorAll('.js-plotly-plot'), function (g) { Plotly.Plots.resize(g); }); } catch (e) {} }, 60);
        tampil(d, w, vis); }); } catch (e) { console.error('popout', e); }
    sibuk = false; }
  var POP = window.POP = { def: DEF, apply: apply, win: win,
    set: function (k, v) { ON[k] = !!v; simpan(); var d = DEF.filter(function (q) { return q.k === k; })[0]; if (!d) return; var w = document.getElementById('gxpo_' + k.replace(/\W/g, '_'));
      if (!v && w) { w.style.display = 'none'; w.querySelector('.gxpb').innerHTML = ''; } d._force = !!v; render(d); setTimeout(apply, 0); },
    on: function (k) { return !!ON[k]; } };
  var T = null, kick = function () { if (sibuk) return; clearTimeout(T); T = setTimeout(apply, 0); };
  function amati() { DEF.forEach(function (d) { var e = document.getElementById(d.host); if (e && !e._gxpo) { e._gxpo = 1; new MutationObserver(kick).observe(e, { childList: true, attributes: true, attributeFilter: ['data-f', 'hidden', 'class', 'style'] }); } }); }
  amati(); setTimeout(function () { amati(); apply(); }, 0); setInterval(amati, 3000);
  /* pindah node di Project Tree sering hanya menyembunyikan / menampilkan bagian (tanpa menggambar ulang): periksa lagi sesudahnya */
  (function () { var tunggu = function () { if (!window.PT || !PT.select) return setTimeout(tunggu, 500); if (PT.select._gxpo) return; var _s = PT.select; PT.select = function () { var r = _s.apply(this, arguments); setTimeout(apply, 250); setTimeout(apply, 700); return r; }; PT.select._gxpo = 1; }; tunggu(); })();

  /* ---------- panel Geostatistik (statistik & variogram) dilepas jadi jendela ---------- */
  (function () { var gs = function () { var p = document.getElementById('gsPanel'); if (!p) return; var gh = p.querySelector('.gh'); if (!gh || gh.querySelector('.gxpob')) return;
      var b = document.createElement('button'); b.type = 'button'; b.className = 'gxpob'; var lepas = function (v) { p.classList.toggle('gxfloat', v); b.innerHTML = v ? '&#8617; Panel' : '&#10697; Pop-up'; b.title = v ? 'Kembalikan ke panel kanan' : 'Lepas panel Geostatistik menjadi jendela yang bisa digeser & diubah ukurannya';
          if (v && !p.style.left) { p.style.left = Math.max(40, innerWidth - 900) + 'px'; p.style.top = '70px'; } ON['gs.float'] = v; simpan();
          setTimeout(function () { try { if (window.uiResize) uiResize(); } catch (e) {} try { [].forEach.call(p.querySelectorAll('.js-plotly-plot'), function (g) { Plotly.Plots.resize(g); }); } catch (e) {} try { var gd = document.getElementById('plotDiv'); if (gd) Plotly.Plots.resize(gd); } catch (e) {} }, 80); };
      b.onclick = function (e) { e.stopPropagation(); lepas(!p.classList.contains('gxfloat')); }; var tg = gh.querySelector('span') || gh; tg.insertBefore(b, tg.firstChild);
      var dr = null; gh.addEventListener('mousedown', function (e) { if (!p.classList.contains('gxfloat') || e.target.closest('button,select,input')) return; var r = p.getBoundingClientRect(); dr = [e.clientX - r.left, e.clientY - r.top]; e.preventDefault(); });
      window.addEventListener('mousemove', function (e) { if (!dr) return; p.style.left = Math.max(0, Math.min(innerWidth - 160, e.clientX - dr[0])) + 'px'; p.style.top = Math.max(0, Math.min(innerHeight - 60, e.clientY - dr[1])) + 'px'; });
      window.addEventListener('mouseup', function () { if (dr) { dr = null; } });
      try { new ResizeObserver(function () { if (!p.classList.contains('gxfloat')) return; clearTimeout(p._rz); p._rz = setTimeout(function () { try { [].forEach.call(p.querySelectorAll('.js-plotly-plot'), function (g) { Plotly.Plots.resize(g); }); } catch (e) {} }, 120); }).observe(p); } catch (e) {}
      if (ON['gs.float']) lepas(true); };
    gs(); setTimeout(gs, 0); setTimeout(gs, 1500); })();

  var st = document.createElement('style'); st.textContent =
    '.gxpop{position:fixed;left:380px;top:70px;z-index:60;width:min(860px,calc(100vw - 400px));height:auto;max-height:calc(100vh - 90px);display:none;flex-direction:column;background:var(--sf,#fff);color:var(--tx);border:1px solid var(--bd);border-radius:8px;box-shadow:0 8px 28px rgba(0,0,0,.25);resize:both;overflow:hidden;min-width:300px;min-height:80px}' +
    '.gxpop .gxph{flex:0 0 auto;display:flex;justify-content:space-between;align-items:center;gap:8px;padding:6px 10px;background:var(--pr,#1c3d8f);color:#fff;border-radius:8px 8px 0 0;cursor:move;user-select:none}.gxpop .gxph button{background:none;border:0;color:#fff;font-size:16px;width:26px;height:24px;cursor:pointer}' +
    '.gxpop .gxpb{flex:1 1 auto;overflow:auto;padding:8px 10px}.gxpop.min .gxpb{display:none}.gxpop.min{width:320px!important;height:auto!important;resize:none}' +
    '.gxpop table.gxtb{border-collapse:collapse;width:100%;font-size:11.5px}.gxpop .gxtb th,.gxpop .gxtb td{border-bottom:1px solid var(--bd);padding:3px 5px;text-align:right;white-space:nowrap}.gxpop .gxtb th:first-child,.gxpop .gxtb td:first-child{text-align:left}.gxpop .gxtb th{position:sticky;top:0;background:var(--sf2,#eef1f6)}.gxpop .gxtb tr.tot td{font-weight:700;border-top:2px solid var(--bd)}.gxpop .gxtb tr.sub td{font-weight:600;background:var(--prs,#eef2fb)}.gxpop .gxtb tr.hl td{background:rgba(240,192,71,.25)}' +
    '.gxpob{float:right;height:20px;padding:0 7px;font-size:11px;font-weight:600;margin-left:6px;border-radius:10px}.rptabs .gxpob{float:none;flex:0 0 auto!important;align-self:center}.gxpoph{font-size:11.5px;color:var(--mu);border:1px dashed var(--bd);border-radius:6px;padding:4px 8px;margin:4px 0}.gxpop .gxpb .amh{margin-top:6px}' +
    '#gsPanel.gxfloat{position:fixed!important;z-index:59;width:820px;height:72vh;max-width:none;min-width:420px;min-height:260px;resize:both;overflow:hidden;border:1px solid var(--bd);border-radius:8px;box-shadow:0 8px 28px rgba(0,0,0,.25)}#gsPanel.gxfloat .gh{cursor:move}';
  document.head.appendChild(st);
})();
