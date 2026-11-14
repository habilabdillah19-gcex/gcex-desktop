/* ================= GC-Ex Block Model 0.24.78: shell ala Ore Works (tahap 1 + 2) =================
   Keputusan pemilik 14 Nov 2026 (mockup "Mockup adaptasi UI/UX Ore Works untuk GC-Ex Block Model"):
   - TIDAK ADA MENU KEMBAR: tombol tampilan DIPINDAH (bukan disalin) dari bilah atas ke toolbar (#bmTb).
   - Bilah atas: logo & huruf lama tetap (brand.js); hanya alat tampilan yang turun ke toolbar.
   - Toolbar baru: "Semua data" (zoom ke seluruh data, arah pandang tetap) + "Latar 3D" (Polos bawaan; Gradasi lembut /
     Gradasi navy hanya di area 3D -- tombol & panel tetap padat, skin_bm_solid.css).
   - Status bar navy: info lama tetap + koordinat kursor (E · N · RL) dan VE. Arah pandang & jumlah blok TIDAK diulang di
     status bar: sudah ada di kompas (#cpTxt), legenda dan badge Project Tree.
   - Jendela pop-up (popout.js) & kartu legenda (topopit_bm.js) berkepala navy + garis emas.
   - Tahap 2: menu teks di bilah atas = jalan pintas ke node Project Tree (navigasi saja, tidak menjalankan perintah);
     kotak cari di Project Tree; kompas 3D (gcex_base.html cpDraw). */
(function () {
  var $ = function (i) { return document.getElementById(i); };
  var LS = function (k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var css = document.createElement('style'); css.id = 'shellBmCss';
  css.textContent =
    /* ---- toolbar ---- */
    '#bmTb{flex:0 0 auto;display:flex;align-items:center;min-height:36px;padding:0 10px;background:var(--bs-face,#f4f6f9);border-bottom:1px solid var(--bs-ln,#c6cfdb);z-index:4;overflow-x:auto;overflow-y:hidden}' +
    '#bmTb .tools{display:flex;align-items:center;gap:6px;flex-wrap:nowrap}#bmTb [hidden]{display:none!important}#bmTb select{width:auto!important;min-width:0!important}' +
    '#bmTb .tb,#bmTb .seg button,#bmTb select{height:26px;margin:0;display:inline-flex;align-items:center;gap:5px;padding:0 9px;font:inherit;font-size:12.5px;color:var(--tx,#1c2733);background:var(--sf,#fff);border:1px solid var(--bs-ln,#c6cfdb);border-bottom-color:var(--bs-lnbt,#9eabbc);border-radius:3px;box-shadow:none;cursor:pointer;white-space:nowrap}' +
    '#bmTb .tb:hover,#bmTb .seg button:hover{background:var(--bs-facehv,#eef2f8)}' +
    '#bmTb .tb.on,#bmTb .seg button.on{background:var(--prs,#e6eefc);border-color:var(--pr,#233a7e);color:var(--pr,#233a7e);box-shadow:inset 0 2px 0 rgba(0,0,0,.08)}' +
    '#bmTb .tb svg{width:15px;height:15px}' +
    '#bmTb .seg{display:inline-flex;border:0;border-radius:3px;overflow:hidden;background:none;box-shadow:none}' +
    '#bmTb .seg button{border-radius:0;border-right-width:0}#bmTb .seg button:first-child{border-radius:3px 0 0 3px}#bmTb .seg button:last-child{border-radius:0 3px 3px 0;border-right-width:1px}' +
    '#bmTb .tg{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--tx,#1c2733);cursor:pointer;white-space:nowrap}' +
    '#bmTb .tb.pri{background:#f0c047;border-color:#f0c047;border-bottom-color:#a77612;color:#1a2a5c;font-weight:700}' +
    '#bmTb .bmts{width:1px;height:22px;background:var(--bs-ln,#c6cfdb);margin:0 4px;flex:none}' +
    '#bmTb .bmtl{font-size:12px;color:var(--mu,#5b6b7c);white-space:nowrap}' +
    /* ---- bilah atas: menu teks (tahap 2) ---- */
    '#bmMenu{display:flex;align-items:center;gap:0;min-width:0;flex:0 1 auto;overflow:hidden}' +
    '#bmMenu>button{height:28px;margin:0;padding:0 9px;background:transparent;border:1px solid transparent;border-radius:3px;color:var(--toptx,#e9eef5);font:inherit;font-size:12.5px;cursor:pointer;white-space:nowrap;box-shadow:none}' +
    '#bmMenu>button:hover,#bmMenu>button.on{background:rgba(255,255,255,.13);border-color:rgba(255,255,255,.22)}' +
    '#bmMenuDd{position:fixed;z-index:60;min-width:220px;max-width:340px;max-height:70vh;overflow:auto;padding:4px;background:var(--sf,#fff);color:var(--tx,#1c2733);border:1px solid var(--bs-pop,#9fb0c6);border-radius:4px;box-shadow:3px 3px 0 var(--bs-hard,#c9d3df);font-size:12.5px;display:none}' +
    '#bmMenuDd button{display:flex;align-items:center;gap:6px;width:100%;margin:0;padding:5px 10px;background:none;border:0;border-radius:3px;color:inherit;font:inherit;text-align:left;cursor:pointer;box-shadow:none}' +
    '#bmMenuDd button:hover{background:var(--prs,#e6eefc);color:var(--pr,#233a7e)}#bmMenuDd button.k2{padding-left:24px;color:var(--mu,#5b6b7c)}#bmMenuDd .hd{font-weight:700}' +
    '#bmMenuDd hr{border:0;border-top:1px solid var(--bd,#d9dee5);margin:3px 0}' +
    '#top .brand,#top .dmWrap{flex:0 0 auto}#top #ttl{flex:1 1 0;min-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}#bmMenu>button.bmx{display:none}' +
    '#cpBox{right:18px!important}#cpTxt{position:absolute;right:0;top:102px;margin:0!important}' +
    /* ---- status bar navy ---- */
    '#status{background:#1b2333!important;color:#c9d2e3!important;border-top:2px solid #b5893e!important;gap:0!important;padding:0!important}' +
    '#status>span{display:flex;align-items:center;padding:0 11px;border-right:1px solid rgba(255,255,255,.12);white-space:nowrap;color:inherit}' +
    '#status>span.grow{border-right:0;padding:0}#status #secInfo,#status #sbXY{color:#e9eef5}#status #sbXY{font-variant-numeric:tabular-nums}' +
    '#status #wmark{border-right:0;color:#9aa5b8}#status #rtime{color:#9aa5b8}' +
    /* ---- jendela pop-up & legenda: kepala navy + garis emas ---- */
    '.gxpop{border-radius:4px!important}.gxpop .gxph{background:#233a7e!important;color:#fff!important;border-bottom:2px solid #b5893e!important;border-radius:3px 3px 0 0}' +
    '.gxpop .gxph b{color:#fff!important}.gxpop .gxph button{background:#2e4a8f!important;color:#fff!important;border:1px solid #46619f!important;border-bottom-color:#0d1a3d!important;border-radius:3px!important}' +
    '.tplg{border-radius:4px!important}.tplg-t{background:#233a7e;border-bottom:2px solid #b5893e!important;border-radius:3px 3px 0 0}.tplg-t b{color:#fff!important}' +
    '.tplg-t button{background:#2e4a8f!important;color:#fff!important;border:1px solid #46619f!important;border-bottom-color:#0d1a3d!important;border-radius:3px!important}' +
    /* ---- latar 3D ---- */
    '#stage.bglat-lembut{background:linear-gradient(#dfe6f0,#ffffff)!important}#stage.bglat-navy{background:linear-gradient(#1b2333,#3a4d74)!important}' +
    /* ---- cari di Project Tree (tahap 2) ---- */
    '#ptCari{display:flex;padding:4px 8px 6px}#ptCari input{flex:1;min-width:0;height:26px;box-sizing:border-box;padding:0 8px;font:inherit;font-size:12.5px;border:1px solid var(--bs-ln,#c6cfdb);border-bottom-color:var(--bs-lnbt,#9eabbc);border-radius:3px;background:var(--sf,#fff);color:var(--tx,#1c2733)}' +
    '#ptCari button{margin:0 0 0 4px;height:26px;padding:0 8px}#ptree .ptr.ptq-x{display:none!important}#ptree .ptr.ptq-hit .ptl{background:#fff2b8;border-radius:2px}' +
    'body.dark #ptree .ptr.ptq-hit .ptl{background:#5a4a14}';
  document.head.appendChild(css);

  /* ================= tahap 1: toolbar (pindah, bukan salin) ================= */
  function pngBtn(root) { return [].filter.call(root.querySelectorAll('button'), function (b) { return /PNG/.test(b.textContent); })[0]; }
  function eye() { var gd = $('plotDiv'); try { return gd._fullLayout.scene.camera.eye; } catch (e) { return null; } }
  function semua() {
    /* arah pandang dipertahankan, jarak & pusat kamera kembali ke bawaan -> seluruh data masuk layar */
    var e = eye() || { x: 1.5, y: -1.5, z: 1 }, n = Math.sqrt(e.x * e.x + e.y * e.y + e.z * e.z) || 1, k = Math.sqrt(1.5 * 1.5 * 2 + 1) / n;
    try { Plotly.relayout($('plotDiv'), { 'scene.camera.eye': { x: e.x * k, y: e.y * k, z: e.z * k }, 'scene.camera.center': { x: 0, y: 0, z: 0 } }); } catch (x) {}
  }
  function toolbar() {
    var top = $('top'), tools = top && (top.querySelector('.tools') || ($('bmTb') && $('bmTb').querySelector('.tools')));
    if (!top || !tools) return;
    var bar = $('bmTb'); if (!bar) { bar = document.createElement('div'); bar.id = 'bmTb'; bar.setAttribute('role', 'toolbar'); bar.setAttribute('aria-label', 'Alat tampilan'); top.parentNode.insertBefore(bar, top.nextSibling); }
    if (tools.parentNode !== bar) bar.appendChild(tools);
    /* tombol yang dipasang modul lain langsung ke bilah atas (mis. layar penuh, wm.js) ikut turun */
    [].slice.call(top.children).forEach(function (c) { if (c.matches('.brand,.dmWrap,#ttl,#bmMenu')) return; var p = pngBtn(tools); if (c.id === 'fsBtn' && p) tools.insertBefore(c, p.nextSibling); else tools.appendChild(c); });
    if (!$('tbAll')) {
      var seg = tools.querySelector('.seg'), b = document.createElement('button'); b.type = 'button'; b.className = 'tb'; b.id = 'tbAll';
      b.title = 'Zoom ke seluruh data (arah pandang tetap)';
      b.innerHTML = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 6V2h4M10 2h4v4M14 10v4h-4M6 14H2v-4"/></svg>Semua data';
      b.onclick = semua; if (seg && seg.nextSibling) tools.insertBefore(b, seg.nextSibling); else tools.appendChild(b);
    }
    if (!$('tbBg')) {
      var p = pngBtn(tools), w = document.createElement('span'); w.style.cssText = 'display:inline-flex;align-items:center;gap:5px';
      w.innerHTML = '<label class="bmtl" for="tbBg">Latar 3D</label><select id="tbBg" title="Latar area 3D saja (tombol & panel tetap padat)"><option value="polos">Polos</option><option value="lembut">Gradasi lembut</option><option value="navy">Gradasi navy</option></select>';
      if (p) tools.insertBefore(w, p); else tools.appendChild(w);
      var s = $('tbBg'); s.value = LS('gcex_bm_latar') || 'polos'; s.onchange = function () { LS('gcex_bm_latar', s.value); latar(true); };
    }
  }
  /* ================= latar 3D ================= */
  function latarV() { return LS('gcex_bm_latar') || 'polos'; }
  function latar(redraw) {
    var st = $('stage') || ($('plotDiv') && $('plotDiv').parentNode); if (!st) return; var v = latarV();
    st.classList.toggle('bglat-lembut', v === 'lembut'); st.classList.toggle('bglat-navy', v === 'navy');
    if (redraw && typeof updatePlot === 'function') try { updatePlot();
      /* label sumbu WebGL baru berganti warna pada gambar ulang berikutnya: picu satu relayout kamera yang sama */
      setTimeout(function () { try { var gd = $('plotDiv'), c = gd._fullLayout.scene.camera; Plotly.relayout(gd, { 'scene.camera': { eye: c.eye, up: c.up, center: c.center } }); } catch (e) {} }, 60); } catch (e) {}
  }
  function pasang() {
    if (!window.TP || !TP.pasca || TP.pasca._shell) return !!(window.TP && TP.pasca && TP.pasca._shell);
    var asli = TP.pasca, f = function (traces, layout) {
      var r = asli.apply(this, arguments), v = latarV();
      if (v !== 'polos' && layout) {
        layout.paper_bgcolor = 'rgba(0,0,0,0)'; layout.plot_bgcolor = 'rgba(0,0,0,0)'; layout.scene = layout.scene || {}; layout.scene.bgcolor = 'rgba(0,0,0,0)';
        if (v === 'navy') {
          layout.font = Object.assign({}, layout.font || {}, { color: '#dbe3ec' });
          ['xaxis', 'yaxis', 'zaxis'].forEach(function (a) { var o = layout.scene[a] = Object.assign({}, layout.scene[a] || {}); o.color = '#c9d2e3'; o.gridcolor = '#4a5d86'; o.tickfont = Object.assign({}, o.tickfont || {}, { color: '#c9d2e3' }); if (o.title != null) { var tt = typeof o.title === 'string' ? { text: o.title } : Object.assign({}, o.title); tt.font = Object.assign({}, tt.font || {}, { color: '#dbe3ec' }); o.title = tt; } o.zerolinecolor = '#6a7da6'; o.linecolor = '#6a7da6'; if (o.backgroundcolor) o.backgroundcolor = 'rgba(0,0,0,0)'; });
        }
      }
      return r;
    };
    f._shell = 1; TP.pasca = f; return true;
  }
  /* ================= status bar ================= */
  function status() {
    var s = $('status'); if (!s || $('sbXY')) return;
    var sec = $('secInfo'), mk = function (id, t) { var e = document.createElement('span'); e.id = id; e.textContent = t || ''; return e; };
    var xy = mk('sbXY', 'E — · N — · RL —'), ve = mk('sbVE');
    xy.title = 'Koordinat titik di bawah kursor (block model / permukaan / lubang)';
    if (sec) { s.insertBefore(xy, sec); s.insertBefore(ve, sec); } else { s.appendChild(xy); s.appendChild(ve); }
  }
  var fmt = function (v, d) { return isFinite(v) ? Number(v).toLocaleString('id-ID', { minimumFractionDigits: d, maximumFractionDigits: d }) : '—'; };
  function hover() {
    var gd = $('plotDiv'); if (!gd || !gd.on || gd._shellHover) return; gd._shellHover = 1;
    gd.on('plotly_hover', function (e) {
      var p = e && e.points && e.points[0], el = $('sbXY'); if (!p || !el || p.x == null || p.y == null) return;
      var ox = window.offX || 0, oy = window.offY || 0;
      el.textContent = 'E ' + fmt(+p.x + ox, 1) + ' · N ' + fmt(+p.y + oy, 1) + ' · RL ' + (p.z != null ? fmt(+p.z, 1) : '—');
    });
  }
  function tick() {
    var ve = $('sbVE'), z = $('zex');
    if (ve) { var v = z ? +z.value : 1; ve.textContent = 'VE ' + String(+(isFinite(v) && v > 0 ? v : 1).toFixed(1)).replace('.', ',') + '×'; }
  }

  /* ================= tahap 2: menu teks = jalan pintas ke node Project Tree ================= */
  var dd = null, ddFor = null;
  var SINGKAT = { sp: 'Data Spasial', bm: 'Block Model', ref: 'Referensi', wf: 'Wireframe', fl: 'Flitch', dig: 'Dig Block', rep: 'Laporan', out: 'Layout', am: 'As-Mined', reg: 'Register', sv: 'Solid Vein', set: 'Pengaturan' };
  var pendek = function (n) { return SINGKAT[n.id] || String(n.t || '').replace(/\s*\(.*\)\s*$/, '').replace(/^Import\s+/i, '').trim(); };
  function topNodes() { var P = window.PT; if (!P || !P.nodes) return []; return P.nodes.filter(function (n) { return n && !n.addRow && !/^(pj|proj)/.test(n.id) && !/^Proyek/i.test(n.t); }); }
  function ddClose() { if (dd) dd.style.display = 'none'; ddFor = null; [].forEach.call(document.querySelectorAll('#bmMenu>button.on'), function (b) { b.classList.remove('on'); }); }
  function pilih(id) {
    var P = window.PT; if (!P) return; ddClose();
    var par = {}; (function w(L, p) { (L || []).forEach(function (n) { par[n.id] = p; if (n.kids) w(n.kids, n.id); }); })(P.nodes, null);
    for (var q = par[id]; q; q = par[q]) P.open[q] = 1;
    try { var side = $('side'); if (side && side.classList.contains('hide') && window.uiSide) uiSide(); } catch (e) {}
    try { P.render(true); } catch (e) {} P.select(id);
    setTimeout(function () { var r = document.querySelector('#ptree .ptr[data-id="' + (window.CSS && CSS.escape ? CSS.escape(id) : id) + '"]'); if (r && r.scrollIntoView) r.scrollIntoView({ block: 'nearest' }); }, 60);
  }
  function buka(btn, n) {
    if (ddFor === n.id) { ddClose(); return; } ddClose();
    if (!dd) { dd = document.createElement('div'); dd.id = 'bmMenuDd'; dd.setAttribute('role', 'menu'); document.body.appendChild(dd);
      dd.addEventListener('click', function (e) { var b = e.target.closest('button[data-id]'); if (b) pilih(b.dataset.id); });
      document.addEventListener('mousedown', function (e) { if (dd.style.display !== 'none' && !e.target.closest('#bmMenuDd,#bmMenu')) ddClose(); });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape') ddClose(); }); }
    var h = '<button type="button" role="menuitem" class="hd" data-id="' + esc(n.id) + '">' + esc(n.t) + '</button>', ks = (n.kids || []).filter(function (k) { return !k.addRow && !k.info; });
    if (ks.length) h += '<hr>';
    ks.forEach(function (k) { h += '<button type="button" role="menuitem" data-id="' + esc(k.id) + '">' + esc(k.t) + '</button>';
      (k.kids || []).filter(function (c) { return !c.addRow && !c.info; }).slice(0, 12).forEach(function (c) { h += '<button type="button" role="menuitem" class="k2" data-id="' + esc(c.id) + '">' + esc(c.t) + '</button>'; }); });
    dd.innerHTML = h; var r = btn.getBoundingClientRect(); dd.style.display = 'block'; dd.style.left = Math.max(4, Math.min(r.left, innerWidth - dd.offsetWidth - 6)) + 'px'; dd.style.top = (r.bottom + 2) + 'px';
    ddFor = n.id; btn.classList.add('on');
  }
  var menuSig = '';
  function menu() {
    var top = $('top'), ttl = $('ttl'); if (!top || !window.PT || !PT.nodes || !PT.nodes.length) return;
    var m = $('bmMenu'); if (!m) { m = document.createElement('nav'); m.id = 'bmMenu'; m.setAttribute('aria-label', 'Menu (jalan pintas Project Tree)'); if (ttl) top.insertBefore(m, ttl); else top.appendChild(m); }
    var L = topNodes(), sig = L.map(function (n) { return n.id + ':' + n.t; }).join('|'); if (sig === menuSig) return; menuSig = sig;
    m.innerHTML = L.map(function (n, i) { return '<button type="button" data-i="' + i + '" title="' + esc(n.t) + ' (Project Tree)">' + esc(pendek(n)) + '</button>'; }).join('') +
      '<button type="button" id="bmMore" title="Menu lainnya">Lainnya &#9662;</button>';
    m.onclick = function (e) { var b = e.target.closest('button'); if (!b) return; if (b.id === 'bmMore') { lainnya(b); return; } var n = topNodes()[+b.dataset.i]; if (n) buka(b, n); };
    muat();
  }
  /* menu yang tidak muat di bilah atas masuk "Lainnya" (logo & judul tidak terdesak) */
  function muat() {
    var m = $('bmMenu'); if (!m) return; var B = [].slice.call(m.querySelectorAll('button[data-i]')), more = $('bmMore');
    B.forEach(function (b) { b.classList.remove('bmx'); }); more.style.display = 'none';
    if (m.scrollWidth <= m.clientWidth + 1) return; more.style.display = '';
    for (var i = B.length - 1; i >= 0 && m.scrollWidth > m.clientWidth + 1; i--) B[i].classList.add('bmx');
  }
  function lainnya(btn) {
    if (!document.querySelector('#bmMenu>button.bmx')) return;
    var L = topNodes(), h = ''; [].forEach.call(document.querySelectorAll('#bmMenu>button.bmx'), function (b) { var n = L[+b.dataset.i]; if (n) h += '<button type="button" role="menuitem" class="hd" data-id="' + esc(n.id) + '">' + esc(n.t) + '</button>'; });
    if (ddFor === '__more') { ddClose(); return; } buka(btn, { id: '__more', t: '', kids: [] }); dd.innerHTML = h; ddFor = '__more';
  }
  window.addEventListener('resize', function () { try { muat(); } catch (e) {} });
  /* ================= tahap 2: cari di Project Tree ================= */
  var Q = { q: '', open0: null };
  function cariUI() {
    var w = $('ptWrap'), tr = $('ptree'); if (!w || !tr || $('ptCari')) return;
    var d = document.createElement('div'); d.id = 'ptCari';
    d.innerHTML = '<input id="ptQ" type="search" placeholder="Cari di Project Tree…" aria-label="Cari di Project Tree"><button type="button" id="ptQx" title="Hapus pencarian" style="display:none">&times;</button>';
    w.insertBefore(d, tr);
    var inp = $('ptQ'), x = $('ptQx');
    inp.addEventListener('input', function () { cari(inp.value); x.style.display = inp.value ? '' : 'none'; });
    inp.addEventListener('keydown', function (e) { if (e.key === 'Escape') { inp.value = ''; cari(''); x.style.display = 'none'; } });
    x.onclick = function () { inp.value = ''; cari(''); x.style.display = 'none'; inp.focus(); };
    new MutationObserver(function () { if (Q.q) saring(); }).observe(tr, { childList: true });
  }
  function cari(q) {
    var P = window.PT; if (!P) return; q = String(q || '').trim().toLowerCase();
    if (q && !Q.q) Q.open0 = JSON.parse(JSON.stringify(P.open || {}));
    Q.q = q;
    if (!q) { if (Q.open0) { P.open = Q.open0; Q.open0 = null; } try { P.render(true); } catch (e) {} return; }
    var par = {}, hit = {}, keep = {};
    (function w(L, p) { (L || []).forEach(function (n) { par[n.id] = p; if (!n.addRow && String(n.t || '').toLowerCase().indexOf(q) >= 0) hit[n.id] = 1; if (n.kids) w(n.kids, n.id); }); })(P.nodes, null);
    Object.keys(hit).forEach(function (id) { keep[id] = 1; for (var a = par[id]; a; a = par[a]) { keep[a] = 1; P.open[a] = 1; } });
    Q.hit = hit; Q.keep = keep; try { P.render(true); } catch (e) {} saring();
  }
  function saring() {
    var tr = $('ptree'); if (!tr) return;
    [].forEach.call(tr.querySelectorAll('.ptr'), function (r) { var id = r.getAttribute('data-id'); r.classList.toggle('ptq-x', !Q.keep[id]); r.classList.toggle('ptq-hit', !!Q.hit[id]); });
  }

  function jalan() { try { toolbar(); } catch (e) {} try { status(); } catch (e) {} try { latar(false); } catch (e) {} try { pasang(); } catch (e) {} try { hover(); } catch (e) {} try { tick(); } catch (e) {} try { menu(); muat(); } catch (e) {} try { cariUI(); } catch (e) {} }
  window.SHELL = { semua: semua, latar: latar, pilih: pilih, cari: cari, jalan: jalan };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', jalan); else jalan();
  setTimeout(jalan, 1600); setTimeout(jalan, 5200); setInterval(jalan, 1000);
})();
