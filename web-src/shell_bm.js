/* ================= GC-Ex Block Model 0.24.78: shell ala Ore Works (tahap 1 + 2) =================
   Keputusan pemilik 14 Nov 2026 (mockup "Mockup adaptasi UI/UX Ore Works untuk GC-Ex Block Model"):
   - TIDAK ADA MENU KEMBAR: tombol tampilan DIPINDAH (bukan disalin) dari bilah atas ke toolbar (#bmTb).
   - Bilah atas: logo & huruf lama tetap (brand.js); hanya alat tampilan yang turun ke toolbar.
   - Toolbar baru: "Semua data" (zoom ke seluruh data, arah pandang tetap) + "Latar 3D" (Polos bawaan; Gradasi lembut /
     Gradasi navy hanya di area 3D -- tombol & panel tetap padat, skin_bm_solid.css).
   - Status bar navy: info lama tetap + koordinat kursor (E · N · RL) dan VE. Arah pandang & jumlah blok TIDAK diulang di
     status bar: sudah ada di kompas (#cpTxt), legenda dan badge Project Tree.
   - Jendela pop-up (popout.js) & kartu legenda (topopit_bm.js) berkepala navy + garis emas.
   - Tahap 2: kotak cari di Project Tree; kompas 3D (gcex_base.html cpDraw).
   - 0.24.79 (pemilik 14 Nov 2026, "Opsi A saja. Buatkan untuk Properti saja. Project remain in kiri saja, tapi bisa
     disembunyikan"): menu teks bilah atas DIHAPUS (kembar dengan Project Tree). Panel Properti (#side) bisa ditempel di
     kiri (bawah Project Tree, bawaan), di kanan (kolom #propR), atau dilepas jadi jendela (#propF); posisi diingat
     (gcex_bm_prop). Project Tree tetap di kiri dan bisa disembunyikan sendiri (Properti kiri tetap tampil). */
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
    '#top .brand,#top .dmWrap{flex:0 0 auto}#top #ttl{flex:1 1 0;min-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
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
    [].slice.call(top.children).forEach(function (c) { if (c.matches('.brand,.dmWrap,#ttl')) return; var p = pngBtn(tools); if (c.id === 'fsBtn' && p) tools.insertBefore(c, p.nextSibling); else tools.appendChild(c); });
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

  /* ================= 0.24.79: panel Properti tempel kiri / kanan / lepas; Project Tree bisa disembunyikan ================= */
  var dcss = document.createElement('style'); dcss.id = 'shellDockCss';
  dcss.textContent =
    '#ptPH .pdk{display:inline-flex;gap:2px;margin-left:auto;flex:none}#ptPH .pdk+.ptx,#ptPH .ptx{margin-left:2px}' +
    '#ptPH .pdk button{all:unset;box-sizing:border-box;width:22px;height:19px;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--bs-ln,#c6cfdb);border-bottom-color:var(--bs-lnbt,#9eabbc);border-radius:3px;background:var(--sf,#fff);color:var(--tx,#1c2733);cursor:pointer}' +
    '#ptPH .pdk button:hover{background:var(--bs-facehv,#eef2f8)}#ptPH .pdk button.on{background:var(--prs,#e6eefc);border-color:var(--pr,#233a7e);color:var(--pr,#233a7e)}#ptPH .pdk svg{width:14px!important;height:14px!important;flex:none}' +
    '#side #ptPH .pdk button,#ptPH .pdk button{width:24px!important;height:20px!important;min-width:0!important;min-height:0!important;padding:0!important;margin:0!important;font-size:12px!important;line-height:1!important;box-shadow:none!important}' +
    'body.pt-propout #ptWrap{flex:1 1 auto!important;height:auto!important}body.pt-propout #ptSplit{display:none!important}' +
    'body.pt-treehide #ptWrap,body.pt-treehide #ptSplit{display:none!important}' +
    '#propR{flex:0 0 auto;display:flex;flex-direction:row;min-height:0;background:var(--sf,#fff);border-left:1px solid var(--bd,#d5dbe3)}' +
    '#propR>#side,#propF>#side{flex:1 1 auto!important;width:auto!important;min-width:0;min-height:0;overflow-y:auto;border:0!important}' +
    '#propRg{flex:0 0 5px;cursor:col-resize;background:var(--bg,#f4f6f9)}#propRg:hover,body.pdrag #propRg{background:var(--pr,#233a7e)}' +
    '#propF{position:fixed;z-index:40;display:flex;flex-direction:column;min-width:260px;min-height:160px;background:var(--sf,#fff);border:1px solid var(--bs-pop,#9fb0c6);border-radius:4px;box-shadow:3px 3px 0 var(--bs-hard,#c9d3df);resize:both;overflow:hidden}' +
    '#propF.min{height:auto!important;min-height:0;resize:none}#propF.min>#side>*:not(#ptPH){display:none!important}' +
    '#propF #ptPH{position:static;margin:0!important;cursor:move;background:#233a7e!important;border-bottom:2px solid #b5893e!important;color:#fff}' +
    '#propF #ptPH .pp,#propF #ptPH b{color:#fff!important}#propF #ptPH .pi2{color:#fff}#propF #ptPH .ptx{color:#fff}' +
    '#propF #ptPH .pdk button{background:#2e4a8f;color:#fff;border-color:#46619f;border-bottom-color:#0d1a3d}#propF #ptPH .pdk button.on{background:#1b2f66;color:#fff;border-color:#f0c047}';
  document.head.appendChild(dcss);
  var IKD = {
    kiri: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="2" y="3" width="12" height="10"/><rect x="2" y="3" width="4" height="10" fill="currentColor"/></svg>',
    kanan: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="2" y="3" width="12" height="10"/><rect x="10" y="3" width="4" height="10" fill="currentColor"/></svg>',
    lepas: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="2" y="5" width="9" height="8"/><path d="M6 3h8v7"/></svg>',
    min: '<svg viewBox="0 0 16 16" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 8h8"/></svg>'
  };
  var D = { pos: null };
  function posV() { var v = LS('gcex_bm_prop'); return v === 'kanan' || v === 'lepas' ? v : 'kiri'; }
  function lebar() { var w = +LS('gcex_sideW'); return w > 0 ? w : 310; }
  function rsz() { try { if (window.uiResize) setTimeout(uiResize, 30); } catch (e) {} }
  function tombol() {
    var ph = $('ptPH'); if (!ph) return; var k = ph.querySelector('.pdk'), pos = D.pos || posV();
    if (!k) { k = document.createElement('span'); k.className = 'pdk';
      k.innerHTML = '<button type="button" data-p="kiri" title="Tempel Properti di kiri (bawah Project Tree)">' + IKD.kiri + '</button>' +
        '<button type="button" data-p="kanan" title="Tempel Properti di kanan">' + IKD.kanan + '</button>' +
        '<button type="button" data-p="lepas" title="Lepas Properti menjadi jendela">' + IKD.lepas + '</button>' +
        '<button type="button" data-p="min" title="Perkecil / perbesar jendela">' + IKD.min + '</button>';
      k.addEventListener('click', function (e) { var b = e.target.closest('button[data-p]'); if (!b) return; e.stopPropagation();
        if (b.dataset.p === 'min') { var f = $('propF'); if (f) f.classList.toggle('min'); return; } dock(b.dataset.p); });
      var x = ph.querySelector('.ptx'); if (x) ph.insertBefore(k, x); else ph.appendChild(k); }
    [].forEach.call(k.querySelectorAll('button[data-p]'), function (b) { var p = b.dataset.p; b.classList.toggle('on', p === pos); if (p === 'min') b.style.display = pos === 'lepas' ? '' : 'none'; });
  }
  function dock(pos) {
    var side = $('side'), col = $('ptCol'), body = $('body'), st = $('stage') || ($('plotDiv') && $('plotDiv').parentNode); if (!side || !col || !body) return;
    pos = pos === 'kanan' || pos === 'lepas' ? pos : 'kiri'; LS('gcex_bm_prop', pos); D.pos = pos;
    var R = $('propR'), F = $('propF');
    if (pos === 'kiri') { var sp = $('ptSplit'); if (side.parentNode !== col) col.appendChild(side); col.style.width = ''; if (sp && side.previousSibling !== sp) col.insertBefore(side, sp.nextSibling); }
    else { col.style.width = lebar() + 'px'; }
    if (pos === 'kanan') {
      if (!R) { R = document.createElement('div'); R.id = 'propR'; R.innerHTML = '<div id="propRg" title="Geser untuk mengubah lebar Properti"></div>'; body.appendChild(R);
        var g = R.firstChild; g.addEventListener('mousedown', function (e) { if (e.button !== 0) return; var x0 = e.clientX, w0 = R.getBoundingClientRect().width; document.body.classList.add('pdrag');
          var mv = function (ev) { var w = Math.max(240, Math.min(innerWidth * 0.55, w0 - (ev.clientX - x0))); R.style.width = w + 'px'; }, up = function () { document.removeEventListener('mousemove', mv); document.removeEventListener('mouseup', up); document.body.classList.remove('pdrag'); LS('gcex_bm_propW', String(R.getBoundingClientRect().width | 0)); rsz(); };
          document.addEventListener('mousemove', mv); document.addEventListener('mouseup', up); e.preventDefault(); }); }
      R.style.width = (+LS('gcex_bm_propW') || 320) + 'px'; R.style.display = ''; if (side.parentNode !== R) R.appendChild(side);
    } else if (R) R.style.display = 'none';
    if (pos === 'lepas') {
      if (!F) { F = document.createElement('div'); F.id = 'propF'; F.setAttribute('role', 'dialog'); F.setAttribute('aria-label', 'Properti'); document.body.appendChild(F);
        F.addEventListener('mousedown', function (e) { var h = e.target.closest('#ptPH'); if (!h || e.target.closest('button,select,input')) return; var r = F.getBoundingClientRect(), dx = e.clientX - r.left, dy = e.clientY - r.top;
          var mv = function (ev) { F.style.left = Math.max(0, Math.min(innerWidth - 80, ev.clientX - dx)) + 'px'; F.style.top = Math.max(0, Math.min(innerHeight - 30, ev.clientY - dy)) + 'px'; },
            up = function () { document.removeEventListener('mousemove', mv); document.removeEventListener('mouseup', up); simpanF(); };
          document.addEventListener('mousemove', mv); document.addEventListener('mouseup', up); e.preventDefault(); });
        try { new ResizeObserver(function () { clearTimeout(F._t); F._t = setTimeout(simpanF, 300); }).observe(F); } catch (e) {} }
      var g0 = {}; try { g0 = JSON.parse(LS('gcex_bm_propF') || '{}'); } catch (e) {}
      var sr = st ? st.getBoundingClientRect() : { left: 320, top: 80 };
      F.style.left = (g0.x != null ? g0.x : sr.left + 24) + 'px'; F.style.top = (g0.y != null ? g0.y : sr.top + 16) + 'px';
      F.style.width = (g0.w || 330) + 'px'; F.style.height = (g0.h || Math.round(innerHeight * 0.62)) + 'px'; F.style.display = 'flex'; if (side.parentNode !== F) F.appendChild(side);
    } else if (F) F.style.display = 'none';
    document.body.classList.toggle('pt-propout', pos !== 'kiri');
    pohon(!document.body.classList.contains('pt-treehide')); tombol(); rsz();
  }
  function simpanF() { var F = $('propF'); if (!F || F.style.display === 'none' || F.classList.contains('min')) return; var r = F.getBoundingClientRect(); LS('gcex_bm_propF', JSON.stringify({ x: r.left | 0, y: r.top | 0, w: r.width | 0, h: r.height | 0 })); }
  /* Project Tree tampil / sembunyi (sendiri). Properti di kiri tetap tampil di kolom kiri. */
  function pohon(v) {
    var col = $('ptCol'), side = $('side'), ob = $('ptOpen'); if (!col) return;
    if (side && side.classList.contains('hide')) side.classList.remove('hide');
    document.body.classList.toggle('pt-treehide', !v); LS('gcex_bm_tree', v ? '1' : '0');
    var pos = D.pos || posV(); col.classList.toggle('hide', !v && pos !== 'kiri'); col.style.display = (!v && pos !== 'kiri') ? 'none' : '';
    if (ob) ob.style.display = v ? 'none' : 'block'; rsz();
  }
  function dockUI() {
    var side = $('side'), col = $('ptCol'), ph = $('ptPH'); if (!side || !col || !ph) return;
    if (!D.pos) { D.pos = posV(); var h = $('ptHide'), ob = $('ptOpen');
      if (h) h.onclick = function () { pohon(false); }; if (ob) ob.onclick = function () { pohon(true); };
      new MutationObserver(function () { tombol(); }).observe(ph, { childList: true });
      /* geser tepi kolom kiri saat Properti tidak di kiri: lebar kolom Project Tree, bukan Properti */
      var gr = $('sideGrip'); if (gr) gr.addEventListener('mousedown', function (e) { if ((D.pos || 'kiri') === 'kiri' || e.button !== 0) return; e.stopImmediatePropagation(); e.preventDefault();
        var x0 = e.clientX, w0 = col.getBoundingClientRect().width, mv = function (ev) { var w = Math.max(220, Math.min(innerWidth * 0.5, w0 + ev.clientX - x0)); col.style.width = w + 'px'; },
          up = function () { document.removeEventListener('mousemove', mv); document.removeEventListener('mouseup', up); LS('gcex_sideW', String(col.getBoundingClientRect().width | 0)); rsz(); };
        document.addEventListener('mousemove', mv); document.addEventListener('mouseup', up); }, true);
      dock(D.pos); if (LS('gcex_bm_tree') === '0') pohon(false); }
    tombol();
  }
  function jalan() { try { toolbar(); } catch (e) {} try { status(); } catch (e) {} try { latar(false); } catch (e) {} try { pasang(); } catch (e) {} try { hover(); } catch (e) {} try { tick(); } catch (e) {} try { dockUI(); } catch (e) {} try { cariUI(); } catch (e) {} }
  window.SHELL = { semua: semua, latar: latar, cari: cari, dock: dock, pohon: pohon, jalan: jalan };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', jalan); else jalan();
  setTimeout(jalan, 1600); setTimeout(jalan, 5200); setInterval(jalan, 1000);
})();
