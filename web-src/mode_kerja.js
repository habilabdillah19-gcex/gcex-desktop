/* mode_kerja.js — pindah mode Dig Block <-> As-Mined & tombol "Nol & simpan" (GC-Ex Block Model).
   Pemilik 27 Nov 2026: "kesulitan saat transisi panel dari As-Mined kembali lagi ke Dig Block" + "tombol ekstra di atas:
   meng-nol-kan display 3D dan otomatis menyimpan proyek, agar transisi mode lebih smooth".

   Bilah atas (sebelah tombol Proyek):
   [ Dig Block | As-Mined ]  — satu klik:
       * Project Tree: folder mode itu dibuka, folder mode lain dilipat, dan panel TERAKHIR yang dipakai di mode itu dibuka
         lagi (bawaan: Dig Block -> Otomatis, As-Mined -> Flitch, poligon, lantai & atap); pohon tidak perlu digulir.
       * Lapisan: poligon as-mined disembunyikan di mode Dig Block dan ditampilkan di mode As-Mined (pilihan pengguna di
         As-Mined diingat), supaya label poligon aktual tidak menumpuk di atas dig block.
       * Flitch aktif & sayatan tetap (dipakai bersama kedua mode).
   [ Nol & simpan ] — simpan proyek (SA.saveNow), lepaskan alat yang sedang aktif (Esc), kosongkan display 3D dan bebaskan
       memori grafis (Plotly.purge), arah kamera disimpan. Display tetap kosong sampai Anda memilih mode, mengklik panel di
       Project Tree, atau "Tampilkan lagi"; saat itu digambar ulang dari nol.
   Pintasan: Alt+1 Dig Block, Alt+2 As-Mined, Alt+0 Nol & simpan. */
(function () {
  'use strict';
  var MODE = {
    dig: { label: 'Dig Block', folder: 'dig', awal: 'dig.auto', pre: /^dig(\.|$)/, lain: ['am', 'reg'] },
    am: { label: 'As-Mined', folder: 'am', awal: 'am.3', pre: /^(am|reg)(\.|$)/, lain: ['dig'] }
  };
  var KUNCI = 'gcex_bm_mode';
  var ingat = {}; try { ingat = JSON.parse(localStorage.getItem(KUNCI) || '{}') || {}; } catch (e) { }
  var simpanIngat = function () { try { localStorage.setItem(KUNCI, JSON.stringify(ingat)); } catch (e) { } };
  var NOL = false, kamera = null;
  var plotEl = function () { return document.getElementById('plotDiv'); };

  var modeDari = function (id) { if (!id) return null; if (MODE.dig.pre.test(id)) return 'dig'; if (MODE.am.pre.test(id)) return 'am'; return null; };
  var nodeAda = function (id) { try { return !!(window.PT && PT.find && PT.find(id)); } catch (e) { return false; } };

  /* ---------------- tampil lagi / nol ---------------- */
  function tampilLagi() {
    if (!NOL) return;
    NOL = false; var ov = document.getElementById('gxNolOv'); if (ov) ov.remove();
    try { updatePlot(); } catch (e) { console.error(e); }
    tandai();
  }
  function nolDanSimpan() {
    /* 1. lepaskan alat aktif (digitasi, ukur, edit) dengan Esc */
    try { document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); } catch (e) { }
    try { if (window.UKUR && UKUR.aktif && UKUR.mati) UKUR.mati(); } catch (e) { }
    /* 2. simpan proyek */
    var sv = null; try { if (window.SA && SA.saveNow) sv = SA.saveNow(); } catch (e) { console.error(e); }
    /* 3. kosongkan display & bebaskan memori grafis; arah kamera disimpan */
    var el = plotEl();
    try {
      if (el && el.layout) { kamera = el.layout.scene && el.layout.scene.camera ? JSON.parse(JSON.stringify(el.layout.scene.camera)) : null; }
      if (el && window.Plotly) {
        var L = el.layout ? JSON.parse(JSON.stringify(el.layout)) : {};
        Plotly.purge(el);
        Plotly.newPlot(el, [], L, { displaylogo: false, responsive: true });
      }
    } catch (e) { console.error(e); }
    NOL = true; overlay();
    Promise.resolve(sv).then(function () { var t = document.getElementById('gxNolTxt'); if (t) t.innerHTML = '&#10003; Proyek tersimpan &middot; display 3D dikosongkan'; }).catch(function () { var t = document.getElementById('gxNolTxt'); if (t) t.innerHTML = '&#9888; Gagal menyimpan proyek &mdash; coba Proyek &rarr; Simpan sekarang'; });
    tandai();
  }
  function overlay() {
    var el = plotEl(); if (!el) return; var host = el.parentElement || el; var lama = document.getElementById('gxNolOv'); if (lama) lama.remove();
    var o = document.createElement('div'); o.id = 'gxNolOv';
    o.style.cssText = 'position:absolute;left:50%;top:42%;transform:translate(-50%,-50%);z-index:30;background:rgba(255,255,255,.96);border:1px solid #D3CDC1;border-radius:10px;padding:14px 18px;box-shadow:0 6px 24px rgba(0,0,0,.12);font:13px Inter,Segoe UI,sans-serif;color:#1F2430;text-align:center;max-width:420px';
    o.innerHTML = '<div id=gxNolTxt style="font-weight:600;margin-bottom:6px">Menyimpan proyek&hellip;</div>' +
      '<div style="color:#5C6672;margin-bottom:10px">Pilih mode di bilah atas, klik panel di Project Tree, atau tampilkan lagi.</div>' +
      '<div style="display:flex;gap:8px;justify-content:center"><button type=button data-m=dig class=tb>Dig Block</button><button type=button data-m=am class=tb>As-Mined</button>' +
      '<button type=button id=gxNolLagi class="tb pri">Tampilkan lagi</button></div>';
    if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
    host.appendChild(o);
    o.querySelector('#gxNolLagi').onclick = tampilLagi;
    o.querySelectorAll('[data-m]').forEach(function (b) { b.onclick = function () { keMode(b.getAttribute('data-m')); }; });
  }
  /* selama dikosongkan, gambar ulang ditahan (proyek tetap bisa diubah dari panel) */
  if (typeof window.updatePlot === 'function') {
    var _up = window.updatePlot;
    window.updatePlot = updatePlot = function () {
      if (NOL) return;
      var r = _up.apply(this, arguments);
      if (kamera) { var c = kamera; kamera = null; try { var el = plotEl(); if (el && el.layout && el.layout.scene) Plotly.relayout(el, { 'scene.camera': c }); } catch (e) { } }
      return r;
    };
  }

  /* ---------------- pindah mode ---------------- */
  function keMode(k) {
    var M = MODE[k]; if (!M || !window.PT) return;
    var cur = PT.sel, mc = modeDari(cur); if (mc && mc !== k) { ingat[mc] = cur; simpanIngat(); }
    /* lapisan poligon as-mined */
    try {
      if (window.AM) {
        if (k === 'dig') { if (AM.show) { ingat.amShow = true; simpanIngat(); } AM.show = false; }
        else { AM.show = ingat.amShow !== false; }
      }
    } catch (e) { }
    /* pohon: buka folder mode ini, lipat folder mode lain */
    try { PT.open[M.folder] = 1; M.lain.forEach(function (f) { delete PT.open[f]; }); } catch (e) { }
    var tgt = ingat[k] && nodeAda(ingat[k]) ? ingat[k] : M.awal;
    if (!nodeAda(tgt)) tgt = M.folder;
    var wasNol = NOL; NOL = false; var ov = document.getElementById('gxNolOv'); if (ov) ov.remove();
    try { PT.select(tgt); } catch (e) { console.error(e); }
    try { if (window.amPanel) amPanel(); } catch (e) { }
    try { updatePlot(); } catch (e) { console.error(e); }
    void wasNol; tandai(k);
  }

  /* ---------------- tombol di bilah atas ---------------- */
  function tandai(paksa) {
    var w = document.getElementById('gxMode'); if (!w) return;
    var m = paksa || modeDari(window.PT && PT.sel);
    w.querySelectorAll('[data-mode]').forEach(function (b) { var on = b.getAttribute('data-mode') === m; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on ? 'true' : 'false'); });
    var n = document.getElementById('gxNol'); if (n) n.classList.toggle('on', NOL);
  }
  function pasangUI() {
    if (document.getElementById('gxMode')) return true;
    var pj = document.getElementById('pjWrap'); if (!pj) return false;
    var st = document.createElement('style'); st.id = 'gxModeCss';
    st.textContent = '#gxMode{display:inline-flex;align-items:center;gap:6px;margin-left:8px}' +
      '#gxMode .seg{display:inline-flex;border:1px solid rgba(255,255,255,.28);border-radius:6px;overflow:hidden}' +
      '#gxMode .seg button{border:0;border-radius:0;margin:0;background:transparent;color:inherit;padding:4px 10px;font:inherit;font-size:12px;cursor:pointer;opacity:.85}' +
      '#gxMode .seg button+button{border-left:1px solid rgba(255,255,255,.28)}' +
      '#gxMode .seg button.on{background:rgba(255,255,255,.18);opacity:1;font-weight:600;box-shadow:inset 0 -2px 0 currentColor}' +
      '#gxMode #gxNol{font-size:12px;padding:4px 10px}#gxMode #gxNol.on{outline:2px solid rgba(255,255,255,.5)}';
    document.head.appendChild(st);
    var w = document.createElement('div'); w.id = 'gxMode'; w.className = 'dmWrap';
    w.innerHTML = '<span class=seg role=group aria-label="Mode kerja"><button type=button data-mode=dig title="Mode Dig Block (Alt+1): buka panel dig block terakhir, sembunyikan poligon as-mined">Dig Block</button>' +
      '<button type=button data-mode=am title="Mode As-Mined (Alt+2): buka panel as-mined terakhir, tampilkan poligon as-mined">As-Mined</button></span>' +
      '<button type=button id=gxNol class=tb title="Simpan proyek lalu kosongkan display 3D dan bebaskan memori grafis (Alt+0). Display tampil lagi saat memilih mode / panel.">&#10227; Nol &amp; simpan</button>';
    pj.parentNode.insertBefore(w, pj.nextSibling);
    w.querySelectorAll('[data-mode]').forEach(function (b) { b.onclick = function () { keMode(b.getAttribute('data-mode')); }; });
    w.querySelector('#gxNol').onclick = nolDanSimpan;
    tandai(); return true;
  }
  var coba = 0; (function tunggu() { if (!pasangUI() && coba++ < 200) setTimeout(tunggu, 150); })();

  /* klik panel di Project Tree: catat panel terakhir per mode, dan tampilkan lagi bila sedang dikosongkan */
  document.addEventListener('click', function (e) {
    var r = e.target && e.target.closest && e.target.closest('#ptree .ptr[data-id]'); if (!r) return;
    var id = r.getAttribute('data-id'), m = modeDari(id);
    if (m && id !== MODE[m].folder) { ingat[m] = id; simpanIngat(); }
    if (NOL) setTimeout(tampilLagi, 60);
    setTimeout(tandai, 120);
  }, true);
  document.addEventListener('keydown', function (e) {
    if (!e.altKey || e.ctrlKey || e.metaKey) return;
    var t = e.target; if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    if (e.key === '1') { e.preventDefault(); keMode('dig'); } else if (e.key === '2') { e.preventDefault(); keMode('am'); } else if (e.key === '0') { e.preventDefault(); nolDanSimpan(); }
  });
  window.MODEKERJA = { ke: keMode, nol: nolDanSimpan, tampil: tampilLagi, aktif: function () { return NOL; } };
})();
