/* ================= DATA LATIHAN BAWAAN UNTUK TOMBOL DEMO =================
   Modul bersama GC-Ex Drill Hole dan GC-Ex Block Model.

   Masalahnya: tur Demo berjalan di atas data yang sedang terbuka. Kalau belum ada data, demo
   tidak bisa memperlihatkan apa pun; kalau datanya data proyek sungguhan, angka yang muncul
   tidak sama dengan angka di buku tutorial. Padahal tutorial sengaja memakai data simulasi
   dengan kondisi ideal, dan angkanya sudah dihitung serta dicetak di PDF-nya.

   Karena itu berkas data latihan yang dipakai tutorial dititipkan DI DALAM installer
   (extraResources -> resources/data-latihan) dan modul ini memuatnya dalam satu perintah:
   tombol "Muat data latihan & jalankan Demo" di menu Demo. Isinya dibaca lewat protokol
   gcexfile://latihan/<nama berkas> (desktop) atau folder data-latihan/ di sebelah index.html
   (versi HTML / pengujian), lalu disuapkan ke jalur import yang sama dengan yang dipakai
   pengguna -- SA.slotFile / SA.addSp / SA.bmPick / SA.go -- jadi tidak ada jalur baca kedua
   yang bisa berbeda hasilnya.

   Berkas yang dititipkan per aplikasi = yang dipakai bab-bab tutorial:
     Drill Hole : SIM_collar / survey / assay / geologi.csv, SIM_topo_xyz.csv, SIM_BM_GC.csv,
                  QV_Lensa2_Leapfrog.obj, SIM_pit_fase1/2.dxf, SIM_topo_akhir_juni/juli.dxf
     Block Model: SIM_BM_GC_kadar.csv, SIM_pit_fase1/2.dxf, SIM_topo_akhir_juni/juli.dxf      */
/* Modul ini dipasang di HALAMAN LUAR (shell), bukan di dalam sumber viewer (#vsrc): sumber viewer
   baru dieval sesudah import selesai, sehingga tombol di menu Demo belum ada saat data perlu dimuat.
   Tombolnya karena itu dua: satu di halaman import (selalu ada) dan satu di menu Demo (lewat
   window.DLAT, dipasang modul demox.js di dalam viewer).                                        */
(function () {
  if (window.DLAT) return;
  /* Aplikasi mana? Modul ini hidup di halaman luar, jadi fungsi viewer (meAN dsb.) BELUM ada saat
     dimuat: pakai tanda di halaman import -- hanya Drill Hole yang punya slot Collar / Survey / Assay. */
  function DHp() {
    try { if (document.querySelector('.slot[data-role=collar]') || document.getElementById('sfcollar')) return true; } catch (e) {}
    return typeof window.meAN === 'function';
  }
  var DB = ['SIM_collar.csv', 'SIM_survey.csv', 'SIM_assay.csv', 'SIM_geologi.csv'];
  var PERM = ['SIM_pit_fase1.dxf', 'SIM_pit_fase2.dxf', 'SIM_topo_akhir_juni.dxf', 'SIM_topo_akhir_juli.dxf'];
  function kandidat() {
    return DHp() ? DB.concat(['SIM_topo_xyz.csv', 'SIM_BM_GC_kadar.csv', 'QV_Lensa2_Leapfrog.obj'], PERM)
                 : ['SIM_BM_GC_kadar.csv'].concat(PERM);
  }
  var DLAT = window.DLAT = { files: [], dir: '', src: '', busy: false, msg: '', siap: false };
  Object.defineProperty(DLAT, 'dh', { get: DHp });
  var $ = function (i) { return document.getElementById(i); };
  var KUNCI = 'gcex_demo_latihan';            /* penanda: muat lagi sesudah halaman dimuat ulang */

  function url(nm) { return DLAT.src === 'desktop' ? 'gcexfile://latihan/' + nm : 'data-latihan/' + nm; }

  /* daftar berkas yang benar-benar ada */
  DLAT.cari = async function () {
    if (DLAT.siap) return DLAT.files;
    try {
      var KANDIDAT = kandidat();
      if (window.gcexDesktop && gcexDesktop.latihan) {
        var r = await gcexDesktop.latihan();
        DLAT.src = 'desktop'; DLAT.dir = (r && r.dir) || '';
        var ada = {}; ((r && r.files) || []).forEach(function (f) { ada[f] = 1; });
        DLAT.files = KANDIDAT.filter(function (f) { return ada[f]; });
      }
    } catch (e) { console.error(e); }
    if (!DLAT.files.length) {                 /* versi HTML / pengujian: folder di sebelah index.html */
      DLAT.src = 'web'; DLAT.dir = 'data-latihan/'; KANDIDAT = kandidat();
      var ok = [];
      for (var i = 0; i < KANDIDAT.length; i++) {
        /* HEAD: jangan mengunduh berkas 6 MB hanya untuk memeriksa keberadaannya */
        try {
          var res = await fetch(url(KANDIDAT[i]), { method: 'HEAD' });
          if (!res.ok) res = await fetch(url(KANDIDAT[i]), { method: 'GET', headers: { Range: 'bytes=0-1' } });
          if (res.ok || res.status === 206) ok.push(KANDIDAT[i]);
        } catch (e) {}
      }
      DLAT.files = ok;
      if (!ok.length) DLAT.src = '';
    }
    DLAT.siap = true;
    return DLAT.files;
  };
  DLAT.ada = function (nm) { return DLAT.files.indexOf(nm) >= 0; };
  DLAT.lengkap = function () { return DHp() ? DB.every(DLAT.ada) : DLAT.ada('SIM_BM_GC_kadar.csv'); };

  DLAT.berkas = async function (nm) {
    var res = await fetch(url(nm));
    if (!res.ok) throw new Error('Gagal membaca data latihan ' + nm + ' (HTTP ' + res.status + ')');
    var b = await res.blob();
    return new File([b], nm, { type: 'text/plain' });
  };

  function kabar(t) { DLAT.msg = t; var e = $('dlatMsg'); if (e) e.innerHTML = t; try { if (window.console) console.log('[data latihan]', String(t).replace(/<[^>]+>/g, '')); } catch (x) {} }

  /* ---------- muat seluruh data latihan lewat jalur import biasa ---------- */
  DLAT.muat = async function (lanjutDemo) {
    if (DLAT.busy) return false;
    await DLAT.cari();
    if (!DLAT.lengkap()) { alert('Data latihan tidak ada di folder instalasi. Ambil dari ZIP Data-Latihan pada Release, lalu import seperti biasa.'); return false; }
    /* sudah ada data terbuka: muat ulang halaman dulu supaya tidak bercampur */
    var sudah = DHp() ? (window.collars && collars.length) : (window.BX && BX.m);
    if (sudah) {
      if (!confirm('Muat data latihan simulasi?\n\nHalaman akan dimuat ulang. Pekerjaan yang belum tersimpan ke folder proyek akan hilang.')) return false;
      try { sessionStorage.setItem(KUNCI, lanjutDemo ? 'demo' : '1'); } catch (e) {}
      location.reload(); return true;
    }
    DLAT.busy = true;
    try {
      kabar('Membaca data latihan&hellip;');
      if (DHp()) {
        var peran = [['collar', 'SIM_collar.csv'], ['survey', 'SIM_survey.csv'], ['assay', 'SIM_assay.csv'], ['geo', 'SIM_geologi.csv']];
        for (var i = 0; i < peran.length; i++) {
          kabar('Membaca ' + peran[i][1] + '&hellip;');
          await SA.slotFile(peran[i][0], await DLAT.berkas(peran[i][1]));
        }
        var dn = $('dsName'); if (dn) dn.value = 'VeinA_Simulasi';
        if (DLAT.ada('SIM_topo_xyz.csv')) { kabar('Membaca topografi&hellip;'); await SA.addSp('topo', [await DLAT.berkas('SIM_topo_xyz.csv')]); }
        /* block model yang BERISI KADAR: demo bisa langsung memperlihatkan angka laporan tanpa harus
           menjalankan Model Estimation (yang memakan waktu menit). Untuk latihan estimasi sungguhan,
           pakai SIM_BM_GC.csv yang masih kosong dari ZIP Data-Latihan. */
        if (DLAT.ada('SIM_BM_GC_kadar.csv')) { kabar('Membaca block model&hellip;'); SA.bmPick(await DLAT.berkas('SIM_BM_GC_kadar.csv')); }
      } else {
        kabar('Membaca SIM_BM_GC_kadar.csv&hellip;');
        SA.bmPick(await DLAT.berkas('SIM_BM_GC_kadar.csv'));
        var dn2 = $('dsName'); if (dn2) dn2.value = 'Latihan_BM';
      }
      try { SA.preview(); } catch (e) {}
      try { if (SA.goState) SA.goState(); } catch (e) {}
      kabar('Membuka&hellip;');
      await SA.go();
      /* permukaan latihan (desain pit & survei topografi bulanan) dan wireframe Leapfrog.
         mdImport / spAdd ada di dalam sumber viewer, yang baru dieval sesudah SA.go(): tunggu dulu. */
      for (var w = 0; w < 80 && typeof window.mdImport !== 'function'; w++) await new Promise(function (r) { setTimeout(r, 150); });
      var perm = PERM.filter(DLAT.ada);
      if (DHp() && typeof window.spAdd === 'function') {
        /* Drill Hole: desain pit & survei topografi -> Data Spasial sebagai VERSI pit / topografi (bukan
           wireframe). spAdd menjadikan versi baru aktif dan menyalakan overlay; topografi aktif & centang
           overlay dikembalikan supaya angka tutorial (topografi SIM_topo_xyz) tidak bergeser. */
        var cb = function (id) { var e = $(id); return e ? e.checked : null; }, cbSet = function (id, v) { var e = $(id); if (e && v !== null) e.checked = v; };
        var ov0 = { p: cb('ovPit'), s: cb('ovTopoS'), l: cb('ovTopoL') }, t0 = null;
        try { t0 = spAct('topo'); } catch (e) {}
        for (var k = 0; k < perm.length; k++) {
          kabar('Membaca ' + perm[k] + '&hellip;');
          await window.spAdd(/pit/i.test(perm[k]) ? 'pit' : 'topo', { files: [await DLAT.berkas(perm[k])], value: '' });
        }
        try { if (t0 && spAct('topo') !== t0) spActivate('topo', t0.id); } catch (e) {}
        cbSet('ovPit', ov0.p); cbSet('ovTopoS', ov0.s); cbSet('ovTopoL', ov0.l);
        try { updatePlot(); } catch (e) {}
        perm = [];
      }
      if (perm.length && typeof window.mdImport === 'function') {
        /* Block Model: permukaan DTM di Data Referensi (Reporting > Pit & progres) */
        var F = [];
        for (var k2 = 0; k2 < perm.length; k2++) F.push(await DLAT.berkas(perm[k2]));
        kabar('Membaca ' + perm.length + ' permukaan latihan&hellip;');
        await window.mdImport({ files: F, value: '' }, 'surf');
      }
      /* wireframe Leapfrog (Drill Hole) -> node Import Wireframe Geologi, supaya langkah demo wireframe ada isinya */
      if (DHp() && DLAT.ada('QV_Lensa2_Leapfrog.obj') && typeof window.mdImport === 'function') {
        kabar('Membaca wireframe latihan&hellip;');
        await window.mdImport({ files: [await DLAT.berkas('QV_Lensa2_Leapfrog.obj')], value: '' }, 'geo');
      }
      kabar('&#10003; Data latihan siap.');
      DLAT.busy = false;
      if (lanjutDemo) setTimeout(function () { try { dmStart(); } catch (e) { console.error(e); } }, 900);
      return true;
    } catch (e) {
      console.error(e); DLAT.busy = false;
      alert('Gagal memuat data latihan: ' + (e.message || e));
      return false;
    }
  };

  /* sesudah location.reload(): lanjutkan sendiri */
  (function () {
    var tanda = '';
    try { tanda = sessionStorage.getItem(KUNCI) || ''; sessionStorage.removeItem(KUNCI); } catch (e) {}
    if (!tanda) return;
    var n = 0, t = setInterval(function () {
      if (++n > 120) { clearInterval(t); return; }
      if (!(window.SA && SA.go && $('btnGo'))) return;
      clearInterval(t);
      DLAT.muat(tanda === 'demo');
    }, 250);
  })();

  /* ---------- tombol di halaman import (selalu ada, sebelum viewer terbuka) ---------- */
  function pasangImport() {
    var f = document.querySelector('.impFoot');
    if (!f || $('dlatBtn')) return !!f;
    var b = document.createElement('button');
    b.id = 'dlatBtn'; b.className = 'ib'; b.style.display = 'none';
    b.innerHTML = '&#8681; Muat data latihan simulasi';
    b.title = 'Impor data simulasi yang dipakai buku tutorial (dititipkan di folder instalasi) lalu buka viewer. Angka yang muncul sama dengan tutorial PDF.';
    b.onclick = function () { DLAT.muat(false); };
    f.insertBefore(b, f.firstChild);
    var d = document.createElement('div'); d.id = 'dlatMsg'; d.className = 'hint'; d.style.cssText = 'flex:1;text-align:left';
    f.insertBefore(d, b);
    DLAT.cari().then(function (L) {
      if (!DLAT.lengkap()) { b.style.display = 'none'; return; }
      b.style.display = '';
      d.innerHTML = 'Data latihan simulasi tersedia di folder instalasi (' + L.length + ' berkas): angkanya sama dengan buku tutorial.';
    });
    return true;
  }
  var n0 = 0, t0 = setInterval(function () { if (pasangImport() || ++n0 > 60) clearInterval(t0); }, 250);
})();
