/* ================= DATABASE BOR PER KAMPANYE (gaya GEOVIA Surpac) =================
   Surpac menyambungkan beberapa database bor sekaligus (exploration_2024, infill_2023, gc_2025),
   satu di antaranya AKTIF, masing-masing berwarna sendiri di tampilan 3D. GC-Ex menirukan alur itu
   TANPA memecah penyimpanan datanya.

   KEPUTUSAN RANCANGAN — satu dataset, label asal per hole:
     Seluruh fitur GC-Ex (3D, sayatan, Geostatistik, Geomodeller, Model Estimation, Reporting)
     membaca tabel global collars / surveys / assays / geoRows. Memecahnya menjadi beberapa
     penyimpanan terpisah berarti menyentuh semuanya, dengan risiko regresi besar dan tanpa manfaat
     tambahan. Jadi datanya tetap satu, dan setiap hole membawa LABEL kampanye asalnya.
     Ini juga yang tersirat dari permintaan "kampanye sebagai atribut geologi virtual": begitu
     labelnya ada, pewarnaan, filter, Geostatistik dan estimasi langsung bisa dipisah per kampanye
     tanpa mengubah satu pun tabel yang sudah ada.

   Yang disediakan modul ini:
     - daftar kampanye berprioritas (urutan bisa digeser; yang lebih tinggi menang bila satu hole
       ada di dua kampanye), satu kampanye AKTIF sebagai tujuan import / upsert berikutnya;
     - TIGA KEADAAN per kampanye, bukan sekadar tampil / sembunyi:
         * set kerja  - dipakai pemodelan, Geostatistik, statistik dan estimasi;
         * referensi  - TAMPIL di 3D / sayatan sebagai pembanding visual, tetapi TIDAK ikut
                        populasi komposit, variogram, flag, maupun estimasi;
         * sembunyi   - tidak digambar sama sekali.
       Inilah inti alur kerjanya: saat kampanye grade control jadi set kerja, bor eksplorasi dan
       infill tetap terlihat sebagai bahan pertimbangan pemodelan tanpa ikut mencemari angkanya.
       Pemisahan ini nyata: visHoles() tetap daftar TAMPIL (dipakai penggambaran), sedangkan
       visHolesK() daftar SET KERJA, dan seluruh titik analisis dialihkan ke visHolesK();
     - atribut kategori VIRTUAL "Kampanye" (dan "Gabungan kampanye" bila ada grup gabungan),
       sehingga semua mesin yang sudah ada memperlakukannya seperti atribut geologi biasa;
     - gabungan kampanye (merge): kampanye terpilih dimasukkan ke SET KERJA sebagai satu grup
       bernama. Tiap hole TETAP memegang label kampanye aslinya (atribut "Kampanye"), ditambah
       penanda "Set kerja" - jadi data hasil merge bisa langsung dipakai pemodelan & estimasi,
       bisa diekspor, dan tetap bisa dipilah kembali per kampanye asalnya;
     - export set kerja ke .xlsx berisi empat sheet (Collar / Survey / Assay / Geologi);
     - node Database Bor di Project Tree dipecah per kampanye, lengkap dengan jumlah baris collar /
       survey / assay / geologi dan penanda AKTIF.

   Hole yang belum punya label — termasuk seluruh hole saat proyek lama dibuka pertama kali, dan
   hole baru hasil upsert — otomatis masuk ke kampanye AKTIF.                                      */
(function () {
  if (typeof CAT === 'undefined' || typeof window.visHoles !== 'function') return;

  var PAL = ['#2c5282', '#c0522d', '#1b7f4b', '#7c3aed', '#c98a16', '#0f766e', '#be185d', '#57534e'];
  var KP = { L: [], g: [], act: '', of: {}, mg: [], ver: 0, _ci: -1, _gi: -1, _si: -1 };
  window.KP = KP;

  function kE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function uid() { return 'k' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5); }
  function byId(id) { for (var i = 0; i < KP.L.length; i++) if (KP.L[i].id === id) return KP.L[i]; return null; }
  function grpOf(id) { for (var i = 0; i < KP.g.length; i++) if (KP.g[i].ids.indexOf(id) >= 0) return KP.g[i]; return null; }
  window.kpById = byId;

  /* nama bawaan kampanye pertama: dari nama dataset proyek bila ada */
  function namaAwal() {
    try {
      var n = (window.SA && SA.D && SA.D.name) || (document.getElementById('dsName') || {}).value || '';
      n = String(n || '').trim();
      if (n) return n.slice(0, 40);
    } catch (e) {}
    return 'import_awal';
  }

  /* keadaan kampanye: 'kerja' (ikut analisis), 'ref' (tampil saja), 'off' (sembunyi) */
  function st(k) {
    if (!k) return 'off';
    if (k.st) return k.st;
    return k.vis === false ? 'off' : 'kerja';          /* proyek lama: vis true/false */
  }
  window.kpSt = st;

  function baru(nama) {
    var k = { id: uid(), name: nama || ('kampanye_' + (KP.L.length + 1)), col: PAL[KP.L.length % PAL.length], st: 'kerja' };
    KP.L.push(k);
    if (!KP.act) KP.act = k.id;
    return k;
  }
  window.kpBaru = baru;

  /* ---------- sinkron: hole tanpa label masuk ke kampanye aktif ---------- */
  function sync() {
    var C = window.collars || [];
    if (!KP.L.length && C.length) { baru(namaAwal()); }
    if (!KP.L.length) return false;
    if (!byId(KP.act)) KP.act = KP.L[0].id;
    var n = 0;
    for (var i = 0; i < C.length; i++) {
      var h = C[i][0];
      if (!KP.of[h] || !byId(KP.of[h])) { KP.of[h] = KP.act; n++; }
    }
    if (n) KP.ver++;
    catSync();
    return n > 0;
  }
  window.kpSync = sync;

  function kpOf(hole) { return KP.of[hole] || ''; }
  window.kpOf = kpOf;

  /* ---------- jumlah baris per kampanye ---------- */
  var _cnt = null, _cntVer = -1;
  function cnt() {
    var key = KP.ver + '|' + (window.collars || []).length + '|' + (window.assays || []).length + '|' + (window.geoRows || []).length + '|' + (window.surveys || []).length;
    if (_cnt && _cntVer === key) return _cnt;
    var o = {};
    KP.L.forEach(function (k) { o[k.id] = { c: 0, s: 0, a: 0, g: 0, h: {} }; });
    (window.collars || []).forEach(function (r) { var k = o[kpOf(r[0])]; if (k) { k.c++; k.h[r[0]] = 1; } });
    (window.surveys || []).forEach(function (r) { var k = o[kpOf(r[0])]; if (k) k.s++; });
    (window.assays || []).forEach(function (r) { var k = o[kpOf(r[0])]; if (k) k.a++; });
    (window.geoRows || []).forEach(function (r) { var k = o[kpOf(r[0])]; if (k) k.g++; });
    _cnt = o; _cntVer = key;
    return o;
  }
  window.kpCnt = cnt;

  /* ---------- atribut kategori virtual ---------- */
  function idxOf(id) { for (var i = 0; i < KP.L.length; i++) if (KP.L[i].id === id) return i; return -1; }
  function gIdxOf(id) { var g = grpOf(id); if (!g) return -1; for (var i = 0; i < KP.g.length; i++) if (KP.g[i].id === g.id) return i; return -1; }

  function catSync() {
    /* "Kampanye": satu kode per kampanye, urut sesuai prioritas */
    if (KP._ci < 0) { KP._ci = CAT.length; CAT.push({ name: 'Kampanye', src: 'kp', k: 0, d: [] }); }
    var C = CAT[KP._ci];
    C.d = KP.L.map(function (k) { return k.name; });
    /* warna kampanye dipakai sebagai warna kategori, supaya pewarnaan trajectory memakai warna yang sama */
    try {
      var s = GSTY['Kampanye'] || (GSTY['Kampanye'] = {});
      KP.L.forEach(function (k, i) { s[i] = Object.assign({}, s[i] || {}, { c: k.col, p: (s[i] && s[i].p) || '' }); });
    } catch (e) {}
    /* "Gabungan kampanye": hanya ada bila sudah dibuat grup gabungan */
    if (KP.g.length) {
      if (KP._gi < 0) { KP._gi = CAT.length; CAT.push({ name: 'Gabungan kampanye', src: 'kpg', k: 0, d: [] }); }
      CAT[KP._gi].d = KP.g.map(function (g) { return g.name; });
      try {
        var s2 = GSTY['Gabungan kampanye'] || (GSTY['Gabungan kampanye'] = {});
        KP.g.forEach(function (g, i) { s2[i] = Object.assign({}, s2[i] || {}, { c: g.col, p: (s2[i] && s2[i].p) || '' }); });
      } catch (e) {}
    } else if (KP._gi >= 0) { CAT[KP._gi].d = []; }
    /* "Set kerja": penanda apakah hole ikut analisis atau sekadar referensi.
       Dipakai bersama atribut "Kampanye" (label asli) sesuai permintaan: label asli + penanda. */
    if (KP._si < 0) { KP._si = CAT.length; CAT.push({ name: 'Set kerja', src: 'kps', k: 0, d: [] }); }
    CAT[KP._si].d = ['set kerja', 'referensi'];
    try {
      var s3 = GSTY['Set kerja'] || (GSTY['Set kerja'] = {});
      s3[0] = Object.assign({}, s3[0] || {}, { c: '#1b7f4b' });
      s3[1] = Object.assign({}, s3[1] || {}, { c: '#8a93a0' });
    } catch (e) {}
  }
  function sCode(id) { var k = byId(kpOf(id)); return !k ? -1 : (st(k) === 'kerja' ? 0 : 1); }

  /* interval: satu kampanye berlaku untuk SELURUH panjang hole */
  if (typeof window.geoIntervals === 'function') {
    var _gi = window.geoIntervals;
    window.geoIntervals = function (ci, id) {
      if (ci === KP._ci || (KP._gi >= 0 && ci === KP._gi) || ci === KP._si) {
        var h = (window.holeData || {})[id];
        if (!h || !(h.maxD > 0)) return [];
        var code = ci === KP._ci ? idxOf(kpOf(id)) : (ci === KP._si ? sCode(id) : gIdxOf(kpOf(id)));
        return code < 0 ? [] : [[0, h.maxD, code]];
      }
      return _gi.apply(this, arguments);
    };
  }
  /* kategori per interval assay (dipakai filter domain & statistik) */
  if (typeof window.catAssay === 'function') {
    var _ca = window.catAssay;
    window.catAssay = function (ci, id, a) {
      if (ci === KP._ci) return idxOf(kpOf(id));
      if (ci === KP._si) return sCode(id);
      if (KP._gi >= 0 && ci === KP._gi) return gIdxOf(kpOf(id));
      return _ca.apply(this, arguments);
    };
  }

  /* ---------- tampil / sembunyi per kampanye: menyaring visHoles ---------- */
  var _vh = window.visHoles;
  /* daftar TAMPIL: dipakai penggambaran 3D / sayatan. Hanya kampanye 'off' yang dibuang. */
  window.visHoles = function () {
    var v = _vh.apply(this, arguments);
    if (!KP.L.length) return v;
    var off = {};
    KP.L.forEach(function (k) { if (st(k) === 'off') off[k.id] = 1; });
    if (!Object.keys(off).length) return v;
    return v.filter(function (id) { return !off[kpOf(id)]; });
  };
  /* satu hole ikut analisis? */
  window.kpKerja = function (id) {
    if (!KP.L.length) return true;
    var k = byId(kpOf(id));
    return !k || st(k) === 'kerja';
  };
  /* daftar SET KERJA: dipakai Geostatistik, statistik, flag otomatis, komposit dan estimasi.
     Kampanye 'ref' sengaja dibuang di sini supaya bor referensi tidak ikut mencemari angkanya. */
  window.visHolesK = function () {
    return window.visHoles.apply(this, arguments).filter(window.kpKerja);
  };
  /* estimasi & waste berjalan dari GM.flags / holeData, bukan visHoles: saring di sana juga */
  if (typeof window.meRuns === 'function') {
    var _mr = window.meRuns;
    window.meRuns = function () {
      var R = _mr.apply(this, arguments);
      if (!KP.L.length) return R;
      Object.keys(R).forEach(function (id) { if (!window.kpKerja(id)) delete R[id]; });
      return R;
    };
  }

  /* ---------- tindakan ---------- */
  function ubah(diam) {
    KP.ver++; _cntVer = -1; catSync();
    if (window.SA && SA.dirty) SA.dirty();
    if (!diam) {
      try { if (window.updatePlot) updatePlot(); } catch (e) {}
      try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
      try { if (window.geoLegend) geoLegend(); } catch (e) {}
    }
  }
  window.kpUbah = ubah;

  window.kpAktif = function (id) { var k = byId(id); if (k) { KP.act = id; k.st = 'kerja'; ubah(); } };
  window.kpSet = function (id, v) {
    var k = byId(id); if (!k) return;
    if (v !== 'kerja' && id === KP.act) { alert('Kampanye AKTIF selalu ikut set kerja.\n\nJadikan kampanye lain aktif dulu bila ingin yang ini jadi referensi.'); return; }
    k.st = v; delete k.vis; ubah();
  };
  window.kpVis = function (id, on) { window.kpSet(id, on ? 'kerja' : 'off'); };
  window.kpGVis = function (id, on) {
    for (var i = 0; i < KP.g.length; i++) if (KP.g[i].id === id) {
      KP.g[i].vis = !!on;
      KP.g[i].ids.forEach(function (x) { var k = byId(x); if (k && (on || x !== KP.act)) k.st = on ? 'kerja' : 'ref'; });
      ubah(); return;
    }
  };
  window.kpWarna = function (id, c) {
    var k = byId(id); if (k) { k.col = c; ubah(); return; }
    for (var i = 0; i < KP.g.length; i++) if (KP.g[i].id === id) { KP.g[i].col = c; ubah(); return; }
  };
  window.kpGeser = function (id, d) {
    var i = idxOf(id), j = i + d;
    if (i < 0 || j < 0 || j >= KP.L.length) return;
    var t = KP.L[i]; KP.L[i] = KP.L[j]; KP.L[j] = t;
    ubah();
  };
  window.kpRename = function (id) {
    var k = byId(id) || KP.g.filter(function (g) { return g.id === id; })[0];
    if (!k) return;
    var n = prompt('Nama kampanye:', k.name);
    if (n == null) return;
    n = String(n).trim().slice(0, 40);
    if (!n) return;
    k.name = n; ubah();
  };
  window.kpTambah = function () {
    var n = prompt('Nama kampanye baru (mis. infill_2025):', 'kampanye_' + (KP.L.length + 1));
    if (n == null) return;
    n = String(n).trim().slice(0, 40);
    if (!n) return;
    var k = baru(n); KP.act = k.id;
    ubah();
    alert('Kampanye "' + n + '" dibuat dan dijadikan AKTIF.\n\nImport / upsert berikutnya masuk ke kampanye ini.');
  };
  window.kpHapus = function (id) {
    var k = byId(id); if (!k) return;
    if (KP.L.length < 2) { alert('Kampanye terakhir tidak bisa dihapus.'); return; }
    var c = cnt()[id] || { c: 0 };
    var sisa = KP.L.filter(function (x) { return x.id !== id; })[0];
    if (!confirm('Hapus kampanye "' + k.name + '" dari daftar?\n\n' + c.c + ' hole di dalamnya dipindahkan ke "' + sisa.name + '".\nData bornya TIDAK dihapus.')) return;
    Object.keys(KP.of).forEach(function (h) { if (KP.of[h] === id) KP.of[h] = sisa.id; });
    KP.L = KP.L.filter(function (x) { return x.id !== id; });
    KP.g.forEach(function (g) { g.ids = g.ids.filter(function (x) { return x !== id; }); });
    KP.g = KP.g.filter(function (g) { return g.ids.length > 1; });
    if (KP.act === id) KP.act = sisa.id;
    ubah();
  };
  /* pindahkan hole tertentu ke kampanye lain (mis. salah label saat import) */
  window.kpPindah = function (id) {
    var k = byId(id); if (!k) return;
    var r = prompt('HoleID yang dipindahkan ke kampanye "' + k.name + '" (pisahkan dengan koma / spasi).\nKosongkan untuk membatalkan:', '');
    if (!r) return;
    var ids = String(r).split(/[\s,;]+/).filter(Boolean), ada = {}, n = 0;
    (window.collars || []).forEach(function (c) { ada[String(c[0]).toUpperCase()] = c[0]; });
    ids.forEach(function (h) { var real = ada[String(h).toUpperCase()]; if (real) { KP.of[real] = id; n++; } });
    ubah();
    alert(n + ' hole dipindahkan ke "' + k.name + '"' + (n < ids.length ? '; ' + (ids.length - n) + ' HoleID tidak ditemukan.' : '.'));
  };

  /* ---------- gabungan kampanye (merge) ---------- */
  window.kpGabung = function () {
    if (KP.L.length < 2) { alert('Perlu minimal dua kampanye untuk digabungkan.'); return; }
    var daftar = KP.L.map(function (k, i) { return (i + 1) + '. ' + k.name; }).join('\n');
    var r = prompt('Gabungkan kampanye mana saja? Tulis nomornya, pisahkan dengan koma.\n\n' + daftar + '\n\nContoh: 1,3', '');
    if (!r) return;
    var pick = String(r).split(/[\s,;]+/).map(function (x) { return parseInt(x, 10) - 1; })
      .filter(function (i) { return i >= 0 && i < KP.L.length; });
    pick = pick.filter(function (v, i) { return pick.indexOf(v) === i; });
    if (pick.length < 2) { alert('Pilih minimal dua kampanye.'); return; }
    var nm = prompt('Nama gabungan:', pick.map(function (i) { return KP.L[i].name; }).join('+').slice(0, 40));
    if (nm == null) return;
    nm = String(nm).trim().slice(0, 40) || 'gabungan';
    var ids = pick.map(function (i) { return KP.L[i].id; });
    KP.g.push({ id: uid(), name: nm, col: PAL[(KP.g.length + 3) % PAL.length], vis: true, ids: ids });
    /* merge = masukkan ke SET KERJA: sejak ini data gabungan dipakai pemodelan & estimasi */
    var nRef = 0;
    ids.forEach(function (x) { var k = byId(x); if (k && st(k) !== 'kerja') { k.st = 'kerja'; delete k.vis; nRef++; } });
    KP.mg.push({ id: uid(), name: nm, ids: ids.slice(), when: new Date().toISOString().slice(0, 16).replace('T', ' ') });
    ubah();
    var n = 0, C2 = cnt();
    ids.forEach(function (x) { n += (C2[x] || { c: 0 }).c; });
    alert('Gabungan "' + nm + '" dibuat: ' + n + ' hole kini masuk SET KERJA' + (nRef ? ' (' + nRef + ' kampanye dinaikkan dari referensi)' : '') + '.\n\n' +
          'Data gabungan ini dipakai pemodelan, Geostatistik dan estimasi, dan bisa diekspor lewat "Export set kerja (.xlsx)".\n' +
          'Tiap hole TETAP memegang kampanye aslinya (atribut "Kampanye") ditambah penanda "Set kerja", jadi masih bisa dipilah kembali.');
  };
  window.kpGHapus = function (id) {
    var g = KP.g.filter(function (x) { return x.id === id; })[0]; if (!g) return;
    if (!confirm('Hapus gabungan "' + g.name + '"?\n\nKampanye di dalamnya tidak terpengaruh.')) return;
    KP.g = KP.g.filter(function (x) { return x.id !== id; });
    ubah();
  };

  /* ================= EXPORT SET KERJA KE .xlsx =================
     Penulis .xlsx sendiri: zip dengan entri STORED (tanpa kompresi) + SpreadsheetML inline string.
     Entri stored dipilih supaya tidak bergantung pada CompressionStream dan hasilnya mudah diperiksa;
     file jadi lebih besar, tetapi tetap .xlsx sah yang bisa dibuka Excel dan Surpac.               */
  var CT = (function () {
    var t = new Uint32Array(256);
    for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1); t[n] = c >>> 0; }
    return t;
  })();
  function crc32(u) { var c = 0xFFFFFFFF; for (var i = 0; i < u.length; i++) c = CT[(c ^ u[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  function enc(s) { return new TextEncoder().encode(s); }
  function xq(v) { return String(v == null ? '' : v).replace(/[&<>]/g, function (c) { return c === '&' ? '&amp;' : c === '<' ? '&lt;' : '&gt;'; }).replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, ''); }
  function colName(i) { var s = ''; i++; while (i > 0) { var m = (i - 1) % 26; s = String.fromCharCode(65 + m) + s; i = (i - m - 1) / 26; } return s; }

  function sheetXml(rows) {
    var out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
      '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'];
    for (var r = 0; r < rows.length; r++) {
      var R = rows[r], cells = [];
      for (var c = 0; c < R.length; c++) {
        var v = R[c], ref = colName(c) + (r + 1);
        if (v === null || v === undefined || v === '') continue;
        if (typeof v === 'number' && isFinite(v)) cells.push('<c r="' + ref + '"><v>' + v + '</v></c>');
        else cells.push('<c r="' + ref + '" t="inlineStr"><is><t xml:space="preserve">' + xq(v) + '</t></is></c>');
      }
      out.push('<row r="' + (r + 1) + '">' + cells.join('') + '</row>');
    }
    out.push('</sheetData></worksheet>');
    return out.join('');
  }

  function zipStored(files) {
    /* files: [{name, data:Uint8Array}] -> Uint8Array (zip, metode 0 / stored) */
    var parts = [], cd = [], off = 0, i;
    var u16 = function (v) { return [v & 255, (v >> 8) & 255]; };
    var u32 = function (v) { return [v & 255, (v >>> 8) & 255, (v >>> 16) & 255, (v >>> 24) & 255]; };
    for (i = 0; i < files.length; i++) {
      var f = files[i], nm = enc(f.name), crc = crc32(f.data), n = f.data.length;
      var lh = [].concat([0x50, 0x4b, 0x03, 0x04], u16(20), u16(0), u16(0), u16(0), u16(0),
                         u32(crc), u32(n), u32(n), u16(nm.length), u16(0));
      parts.push(new Uint8Array(lh), nm, f.data);
      cd.push({ nm: nm, crc: crc, n: n, off: off });
      off += lh.length + nm.length + n;
    }
    var cdb = [], cstart = off;
    for (i = 0; i < cd.length; i++) {
      var e = cd[i];
      cdb = cdb.concat([0x50, 0x4b, 0x01, 0x02], u16(20), u16(20), u16(0), u16(0), u16(0), u16(0),
                       u32(e.crc), u32(e.n), u32(e.n), u16(e.nm.length), u16(0), u16(0), u16(0), u16(0), u32(0), u32(e.off));
      cdb = cdb.concat(Array.prototype.slice.call(e.nm));
    }
    var eocd = [].concat([0x50, 0x4b, 0x05, 0x06], u16(0), u16(0), u16(cd.length), u16(cd.length),
                         u32(cdb.length), u32(cstart), u16(0));
    parts.push(new Uint8Array(cdb), new Uint8Array(eocd));
    var tot = 0;
    parts.forEach(function (p2) { tot += p2.length; });
    var out = new Uint8Array(tot), q = 0;
    parts.forEach(function (p2) { out.set(p2, q); q += p2.length; });
    return out;
  }

  function xlsx(sheets) {
    /* sheets: [{name, rows}] */
    var F = [], rels = [], wsx = [], ov = [];
    sheets.forEach(function (sh, i) {
      F.push({ name: 'xl/worksheets/sheet' + (i + 1) + '.xml', data: enc(sheetXml(sh.rows)) });
      rels.push('<Relationship Id="rId' + (i + 1) + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet' + (i + 1) + '.xml"/>');
      wsx.push('<sheet name="' + xq(sh.name) + '" sheetId="' + (i + 1) + '" r:id="rId' + (i + 1) + '"/>');
      ov.push('<Override PartName="/xl/worksheets/sheet' + (i + 1) + '.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>');
    });
    F.unshift({ name: '[Content_Types].xml', data: enc('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
      '<Default Extension="xml" ContentType="application/xml"/>' +
      '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' +
      ov.join('') + '</Types>') });
    F.push({ name: '_rels/.rels', data: enc('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
      '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>') });
    F.push({ name: 'xl/workbook.xml', data: enc('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ' +
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + wsx.join('') + '</sheets></workbook>') });
    F.push({ name: 'xl/_rels/workbook.xml.rels', data: enc('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + rels.join('') + '</Relationships>') });
    return zipStored(F);
  }
  window.kpXlsx = xlsx;

  /* tabel set kerja: collar / survey / assay / geologi, hanya hole yang ikut analisis */
  window.kpTabel = function () {
    var ok = {}, nH = 0;
    (window.collars || []).forEach(function (c) { if (window.kpKerja(c[0])) { ok[c[0]] = 1; nH++; } });
    var nm = function (id) { var k = byId(kpOf(id)); return k ? k.name : ''; };
    var col = [['HoleID', 'East', 'North', 'RL', 'Depth', 'Kampanye']];
    (window.collars || []).forEach(function (c) { if (ok[c[0]]) col.push([c[0], c[1], c[2], c[3], c[4], nm(c[0])]); });
    var sv = [['HoleID', 'Depth', 'Dip', 'Azimuth']];
    (window.surveys || []).forEach(function (r) { if (ok[r[0]]) sv.push([r[0], r[1], r[2], r[3]]); });
    var E = window.elements || [], AC = (window.asCat || []).map(function (c) { return c.n; });
    var as = [['HoleID', 'From', 'To', 'SampleID'].concat(E, AC, ['Kampanye'])];
    (window.assays || []).forEach(function (r) {
      if (!ok[r[0]]) return;
      var row = [r[0], r[1], r[2], r[3]];
      E.forEach(function (_, i) { row.push(r[4] && r[4][i] != null ? r[4][i] : ''); });
      AC.forEach(function (_, i) {
        var c = (window.asCat || [])[i], code = r[5] && r[5][i];
        row.push(c && code != null && code >= 0 && c.d ? c.d[code] : '');
      });
      row.push(nm(r[0]));
      as.push(row);
    });
    var GC = (window.geoCat || []).map(function (c) { return c.n; });
    var ge = [['HoleID', 'From', 'To'].concat(GC, ['Kampanye'])];
    (window.geoRows || []).forEach(function (r) {
      if (!ok[r[0]]) return;
      var row = [r[0], r[1], r[2]];
      GC.forEach(function (_, i) {
        var c = (window.geoCat || [])[i], code = r[3] && r[3][i];
        row.push(c && code != null && code >= 0 && c.d ? c.d[code] : '');
      });
      row.push(nm(r[0]));
      ge.push(row);
    });
    return { nH: nH, sheets: [{ name: 'Collar', rows: col }, { name: 'Survey', rows: sv },
                              { name: 'Assay', rows: as }, { name: 'Geologi', rows: ge }] };
  };

  window.kpExport = function () {
    try {
      sync();
      var T = window.kpTabel();
      if (!T.nH) { alert('Set kerja kosong: tidak ada kampanye berstatus "set kerja".'); return; }
      var u = xlsx(T.sheets);
      var kerja = KP.L.filter(function (k) { return st(k) === 'kerja'; }).map(function (k) { return k.name; });
      var nama = 'GCEx_setkerja_' + kerja.join('+').replace(/[^A-Za-z0-9_+-]+/g, '_').slice(0, 60) + '.xlsx';
      var b = new Blob([u], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      var a2 = document.createElement('a');
      a2.href = URL.createObjectURL(b); a2.download = nama; document.body.appendChild(a2); a2.click();
      setTimeout(function () { URL.revokeObjectURL(a2.href); a2.remove(); }, 2000);
      alert('Export set kerja: ' + T.nH + ' hole dari kampanye ' + kerja.join(', ') + '.\n\n' +
            T.sheets.map(function (s2) { return s2.name + ' ' + (s2.rows.length - 1) + ' baris'; }).join(' · ') +
            '\n\nKolom "Kampanye" ikut ditulis di tiap sheet supaya asal tiap hole tetap terlacak.');
    } catch (e) { console.error(e); alert('Export gagal: ' + (e.message || e)); }
  };

  /* ---------- node Project Tree ---------- */
  window.kpTree = function () {
    sync();
    if (!KP.L.length) return [];
    var N = function (n) { try { return (+n).toLocaleString('id-ID'); } catch (e) { return String(n); } };
    var C = cnt(), out = [];
    var tabel = function (kid, t, ic, n) { return { id: kid, t: t, ic: ic, b: n ? N(n) : '', dim: !n }; };
    KP.L.forEach(function (k, i) {
      var c = C[k.id] || { c: 0, s: 0, a: 0, g: 0 }, aktif = KP.act === k.id, S = st(k);
      var lbl = { kerja: 'set kerja', ref: 'referensi', off: 'sembunyi' }[S];
      out.push({
        id: 'db.kp.' + k.id, t: k.name, ic: 'folder', fold: 1, tab: 'Data',
        b: (aktif ? 'AKTIF &middot; ' : '') + lbl + ' &middot; ' + N(c.c) + ' hole',
        mark: aktif ? 'aktif' : '', dim: S !== 'kerja',
        chk: S !== 'off', onChk: function (v) { kpSet(k.id, v ? (aktif ? 'kerja' : 'ref') : 'off'); },
        hint: (S === 'kerja' ? 'Ikut pemodelan, Geostatistik & estimasi'
             : S === 'ref' ? 'Hanya tampil sebagai referensi — tidak ikut analisis' : 'Disembunyikan') +
             ' · prioritas ' + (i + 1) + ' dari ' + KP.L.length + (aktif ? ' · tujuan import / upsert berikutnya' : ''),
        menu: function () {
          return [
            { t: aktif ? '✓ Kampanye aktif' : 'Jadikan kampanye aktif', dis: aktif, fn: function () { kpAktif(k.id); } },
            { sep: 1 },
            { h: 'Peran kampanye' },
            { t: 'Set kerja — ikut pemodelan & estimasi', on: S === 'kerja', fn: function () { kpSet(k.id, 'kerja'); } },
            { t: 'Referensi — tampil saja, tidak ikut analisis', on: S === 'ref', dis: aktif, fn: function () { kpSet(k.id, 'ref'); } },
            { t: 'Sembunyikan', on: S === 'off', dis: aktif, fn: function () { kpSet(k.id, 'off'); } },
            { sep: 1 },
            { t: 'Naikkan prioritas', dis: i === 0, fn: function () { kpGeser(k.id, -1); } },
            { t: 'Turunkan prioritas', dis: i === KP.L.length - 1, fn: function () { kpGeser(k.id, 1); } },
            { sep: 1 },
            { t: 'Ganti nama…', fn: function () { kpRename(k.id); } },
            { t: 'Pindahkan hole ke sini…', fn: function () { kpPindah(k.id); } },
            { sep: 1 },
            { t: 'Kampanye baru…', fn: function () { kpTambah(); } },
            { t: 'Gabungkan ke set kerja… (merge)', fn: function () { kpGabung(); } },
            { t: 'Export set kerja (.xlsx)…', fn: function () { kpExport(); } },
            { sep: 1 },
            { t: 'Hapus kampanye ini…', danger: 1, dis: KP.L.length < 2, fn: function () { kpHapus(k.id); } }
          ];
        },
        kids: [tabel('db.kp.' + k.id + '.c', 'Collar', 'collar', c.c),
               tabel('db.kp.' + k.id + '.s', 'Survey', 'table', c.s),
               tabel('db.kp.' + k.id + '.a', 'Assay', 'table', c.a),
               tabel('db.kp.' + k.id + '.g', 'Geologi', 'geo', c.g)]
      });
    });
    KP.g.forEach(function (g) {
      var n = 0;
      g.ids.forEach(function (i) { n += (C[i] || { c: 0 }).c; });
      out.push({
        id: 'db.kpg.' + g.id, t: g.name, ic: 'folder', fold: 1, tab: 'Data',
        b: 'gabungan &middot; ' + N(n) + ' hole', dim: g.vis === false,
        chk: g.vis !== false, onChk: function (v) { kpGVis(g.id, v); },
        hint: 'Gabungan ' + g.ids.length + ' kampanye di set kerja; tiap hole tetap memegang kampanye aslinya',
        menu: function () {
          return [{ t: 'Ganti nama…', fn: function () { kpRename(g.id); } },
                  { t: 'Export set kerja (.xlsx)…', fn: function () { kpExport(); } },
                  { sep: 1 },
                  { t: 'Hapus gabungan…', danger: 1, fn: function () { kpGHapus(g.id); } }];
        },
        kids: g.ids.map(function (i) {
          var k = byId(i), c = C[i] || { c: 0 };
          return { id: 'db.kpg.' + g.id + '.' + i, t: k ? k.name : '(hilang)', ic: 'hole', b: N(c.c) + ' hole', dim: !k };
        })
      });
    });
    return out;
  };

  /* ---------- simpan / muat bersama proyek ---------- */
  if (window.SA && typeof SA.collectWork === 'function') {
    var _c = SA.collectWork;
    SA.collectWork = function () {
      var w = _c.apply(this, arguments);
      try { w.kp = { L: KP.L, g: KP.g, act: KP.act, of: KP.of, mg: KP.mg }; } catch (e) { console.error(e); }
      return w;
    };
    var _a = SA.applyWork;
    SA.applyWork = function (W) {
      try {
        var o = W && W.kp;
        KP.L = (o && o.L) || []; KP.g = (o && o.g) || []; KP.act = (o && o.act) || ''; KP.of = (o && o.of) || {}; KP.mg = (o && o.mg) || [];
        KP.ver++; _cntVer = -1;
      } catch (e) { console.error(e); }
      var r = _a.apply(this, arguments);
      try { sync(); ubah(true); } catch (e) { console.error(e); }
      return r;
    };
  }

  setTimeout(function () { try { sync(); } catch (e) {} }, 400);
})();
