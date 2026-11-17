/* ================= GC-Ex (BM 0.24.103 / DH 0.24.106): KOTAK MELAYANG BISA DITUTUP + TEKS PENJELAS DIRINGKAS =================
   Pemilik 17 Nov 2026: "Beberapa panel atau bar yang muncul tidak bisa diminimizing atau dihide padahal sedang tidak digunakan
   (misal bar slicing di panel 3D) ... Harusnya bisa ditutup. Begitu pula bar yang lain."
   Setiap kotak di atas tampilan (bilah Sayatan, Ringkasan, kompas, skala) diberi tombol x kecil. Yang ditutup disimpan
   (localStorage 'gcex_tutup') dan tetap tertutup saat aplikasi dibuka lagi; tombol "Panel tersembunyi (n)" di bilah atas
   menampilkannya kembali. Bilah Sayatan tertutup hanya untuk sesi ini dan muncul lagi saat tombol Slicer dibuka
   (alat yang sama tersedia di menu Slicer). Legenda sudah punya tombol tutup sendiri. */
(function () {
  if (window.TUTUP) return;
  var DAFTAR = [
    { k: 'slab', sel: '#slabBar', nm: 'Bilah Sayatan', sesi: true },
    { k: 'ring', sel: '#statsCard', nm: 'Ringkasan' },
    { k: 'komp', sel: '#cpBox', nm: 'Kompas' },
    { k: 'skala', sel: '.gxSkala, .gxUkurB', nm: 'Skala & Ukur', btn: '.gxSkala' }
  ];
  var LS = 'gcex_tutup', sesi = {}, simpan = {};
  try { simpan = JSON.parse(localStorage.getItem(LS) || '{}') || {}; } catch (e) { simpan = {}; }
  var T = window.TUTUP = { daftar: DAFTAR };
  var tertutup = function (d) { return d.sesi ? !!sesi[d.k] : !!simpan[d.k]; };
  var tulis = function () { try { localStorage.setItem(LS, JSON.stringify(simpan)); } catch (e) { } };
  var css = document.createElement('style');
  css.textContent = '.gxTutup{display:none!important}.gxX{position:absolute;top:2px;right:2px;z-index:9;width:16px;height:16px;line-height:14px;padding:0;border:0;border-radius:3px;' +
    'background:transparent;color:var(--mu,#6b7785);font:600 13px Arial,sans-serif;cursor:pointer;opacity:.55}.gxX:hover{opacity:1;background:rgba(0,0,0,.08)}' +
    '#slabBar .gxX{position:static;margin-left:2px}#statsCard .gxX{top:6px;right:24px}#tutupBtn{display:none}#tutupBtn.ada{display:inline-flex}';
  document.head.appendChild(css);

  /* ---- teks penjelas (pemilik 17 Nov 2026: "terlalu banyak tulisan penjelas sehingga menjadi kumuh") ----
     Teks penjelas statis (.hint tanpa id) disembunyikan secara bawaan; tombol (i) di bilah atas menampilkannya lagi
     (tersimpan di localStorage 'gcex_hint'). Tetap tampil: pesan status / hasil (.hint ber-id, mis. info ortho, pesan galat),
     teks yang berisi tombol / isian / tautan, dan teks bergaya warna (peringatan). */
  var css2 = document.createElement('style');
  css2.textContent = 'body:not(.gxHintOn) .hint:not([id]):not([style*="color"]):not(:has(button,input,select,textarea,a,.warn,.err,.bad,.gxWarn)){display:none!important}' +
    '#hintBtn{min-width:28px;justify-content:center;font-weight:700}#hintBtn.on{background:var(--mj,#f0c047);color:var(--mjtx,#1d2b5e)}';
  document.head.appendChild(css2);
  var hintOn = false; try { hintOn = localStorage.getItem('gcex_hint') === '1'; } catch (e) { }
  T.penjelas = function (v) { hintOn = v == null ? !hintOn : !!v; try { localStorage.setItem('gcex_hint', hintOn ? '1' : '0'); } catch (e) { } T.terap(); };

  T.tutup = function (k) { var d = DAFTAR.filter(function (x) { return x.k === k; })[0]; if (!d) return; if (d.sesi) sesi[k] = 1; else { simpan[k] = 1; tulis(); } T.terap(); };
  T.buka = function (k) { if (k) { delete sesi[k]; delete simpan[k]; } else { sesi = {}; simpan = {}; } tulis(); T.terap(); };
  T.terap = function () {
    var n = 0;
    DAFTAR.forEach(function (d) {
      var t = tertutup(d); if (t) n++;
      document.querySelectorAll(d.sel).forEach(function (e) { e.classList.toggle('gxTutup', t); });
      document.querySelectorAll(d.btn || d.sel).forEach(function (e) {
        if (e.querySelector(':scope > .gxX')) return;
        var b = document.createElement('button'); b.type = 'button'; b.className = 'gxX'; b.innerHTML = '&times;';
        b.title = 'Tutup ' + d.nm + (d.sesi ? ' (muncul lagi saat tombol Slicer dibuka)' : ' (tampilkan lagi: tombol "Panel tersembunyi" di bilah atas)');
        b.onclick = function (ev) { ev.stopPropagation(); ev.preventDefault(); T.tutup(d.k); };
        if (getComputedStyle(e).position === 'static') e.style.position = 'relative';
        e.appendChild(b);
      });
    });
    document.body.classList.toggle('gxHintOn', hintOn);
    var hb = document.getElementById('hintBtn'), ref0 = document.getElementById('btnSecM');
    if (!hb && ref0 && ref0.parentNode) { hb = document.createElement('button'); hb.className = 'tb'; hb.id = 'hintBtn'; hb.type = 'button'; hb.innerHTML = '&#9432;'; hb.onclick = function () { T.penjelas(); }; ref0.parentNode.insertBefore(hb, ref0.nextSibling); }
    if (hb) { hb.classList.toggle('on', hintOn); hb.title = hintOn ? 'Sembunyikan teks penjelas di panel' : 'Tampilkan teks penjelas di panel'; }
    var tb = document.getElementById('tutupBtn');
    if (!tb) {
      var ref = document.getElementById('btnSecM'); if (!ref || !ref.parentNode) return;
      tb = document.createElement('button'); tb.className = 'tb'; tb.id = 'tutupBtn'; tb.type = 'button';
      tb.onclick = function () { T.buka(); };
      ref.parentNode.insertBefore(tb, (document.getElementById('hintBtn') || ref).nextSibling);
    }
    var nm = DAFTAR.filter(tertutup).map(function (d) { return d.nm; });
    tb.textContent = 'Panel tersembunyi (' + n + ')'; tb.title = 'Tampilkan lagi: ' + nm.join(', '); tb.classList.toggle('ada', n > 0); tb.style.display = n > 0 ? '' : 'none';
  };
  /* bilah Sayatan muncul lagi saat Slicer dibuka / tampilan 2D-3D diganti */
  document.addEventListener('click', function (e) { var t = e.target && e.target.closest ? e.target.closest('#btnSecM, #sb2d, #btn2D, #btn3D') : null; if (t && sesi.slab) { delete sesi.slab; setTimeout(T.terap, 0); } }, true);
  /* kotak dibuat ulang / ditambah oleh modul lain (skala tiap gambar ulang, bilah sayatan saat dibangun) */
  var jadwal = null, mo = new MutationObserver(function () { if (jadwal) return; jadwal = setTimeout(function () { jadwal = null; T.terap(); }, 120); });
  var mulai = function () { T.terap(); mo.observe(document.body, { childList: true, subtree: true }); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mulai); else setTimeout(mulai, 0);
})();
