/* ================= DATABASE BOR: KAMPANYE & SET MERGE (gaya GEOVIA Surpac) =================
   Surpac menyambungkan beberapa database bor sekaligus (exploration_2024, infill_2023,
   grade_control_2025); SATU di antaranya ACTIVE, dan yang aktif itulah sumber pemodelan. GC-Ex
   menirukan alur itu TANPA memecah penyimpanan datanya.

   KEPUTUSAN RANCANGAN — satu dataset, label asal per hole:
     Seluruh fitur GC-Ex (3D, sayatan, Geostatistik, Geomodeller, Model Estimation, Reporting)
     membaca tabel global collars / surveys / assays / geoRows. Memecahnya menjadi beberapa
     penyimpanan terpisah berarti menyentuh semuanya, dengan risiko regresi besar dan tanpa manfaat
     tambahan. Jadi datanya tetap satu, dan setiap hole membawa LABEL kampanye asalnya; "database"
     di pohon proyek adalah PANDANGAN atas data itu, bukan salinan.

   DUA JENIS NODE DATABASE:
     - kampanye : berisi hole yang berlabel kampanye itu (eksplorasi_2024, gc_2025, …);
     - merge    : database BARU hasil penggabungan beberapa kampanye — Collar / Survey / Assay /
                  Geologi Merge. Anggotanya gabungan hole kampanye sumbernya, dihitung hidup, jadi
                  hole baru yang masuk ke kampanye sumber otomatis ikut.

   ALUR KERJANYA:
     1. Database utama adalah grade control. Kampanye eksplorasi / infill DITAMPILKAN berdampingan
        di jendela 3D untuk memvalidasi bor GC — centang tampil berdiri sendiri, tidak terikat mana
        yang aktif.
     2. Bila datanya bagus, gabungkan GC dengan eksplorasi / infill menjadi SET MERGE baru.
     3. Set merge itu bisa dijadikan AKTIF, dan sejak itu dialah sumber pemodelan & estimasi.
     4. Set merge bisa diekspor ke .xlsx empat sheet untuk pihak luar.

   ATURAN POKOK — pemodelan, estimasi dan statistik HANYA berlaku pada DATASET AKTIF:
     visHoles()  = daftar TAMPIL  (semua database yang dicentang) → dipakai penggambaran 3D/sayatan;
     visHolesK() = daftar AKTIF   (anggota dataset aktif saja)    → dipakai seluruh titik analisis.
     Bor yang hanya ditampilkan sebagai pembanding tidak pernah ikut komposit, variogram, flag
     otomatis, maupun estimasi.

   Atribut kategori VIRTUAL yang disediakan: "Kampanye" (label asal tiap hole, tetap utuh walau
   sudah masuk set merge) dan "Dataset aktif" (ikut / tidak ikut analisis). Keduanya diperlakukan
   seperti atribut geologi biasa oleh pewarnaan, filter, Geostatistik dan estimasi.

   Hole yang belum punya label — termasuk seluruh hole saat proyek lama dibuka pertama kali, dan
   hole baru hasil upsert — otomatis masuk ke KAMPANYE aktif (atau kampanye sumber pertama bila
   yang aktif adalah set merge).                                                                   */
(function () {
  if (typeof CAT === 'undefined' || typeof window.visHoles !== 'function') return;

  var PAL = ['#2c5282', '#c0522d', '#1b7f4b', '#7c3aed', '#c98a16', '#0f766e', '#be185d', '#57534e'];
  /* L = daftar database: {id,name,col,show,kind:'kp'|'mg',ids:[sumber] bila merge} */
  var KP = { L: [], act: '', of: {}, ver: 0, _ci: -1, _si: -1 };
  window.KP = KP;

  function kE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function uid() { return 'k' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5); }
  function byId(id) { for (var i = 0; i < KP.L.length; i++) if (KP.L[i].id === id) return KP.L[i]; return null; }
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

  function isMg(k) { return !!(k && k.kind === 'mg'); }
  function show(k) { return !k ? false : (k.show !== undefined ? !!k.show : (k.st ? k.st !== 'off' : k.vis !== false)); }
  window.kpShowOf = show;

  /* anggota sebuah database: himpunan HoleID. Kampanye = hole berlabel itu; merge = gabungan
     anggota kampanye sumbernya (dihitung hidup, bukan salinan). */
  function anggota(id, seen) {
    var k = byId(id), out = {};
    if (!k) return out;
    if (!isMg(k)) {
      (window.collars || []).forEach(function (c) { if (kpOf(c[0]) === id) out[c[0]] = 1; });
      return out;
    }
    seen = seen || {};
    if (seen[id]) return out;
    seen[id] = 1;
    (k.ids || []).forEach(function (x) { var m = anggota(x, seen); Object.keys(m).forEach(function (h) { out[h] = 1; }); });
    return out;
  }
  window.kpAnggota = anggota;

  /* kampanye tempat import / upsert berikutnya mendarat: database aktif bila kampanye,
     kalau yang aktif set merge maka kampanye sumber pertamanya */
  function kpTujuan() {
    var k = byId(KP.act);
    if (k && !isMg(k)) return k.id;
    if (k && isMg(k)) { for (var i = 0; i < (k.ids || []).length; i++) { var q = byId(k.ids[i]); if (q && !isMg(q)) return q.id; } }
    for (var j = 0; j < KP.L.length; j++) if (!isMg(KP.L[j])) return KP.L[j].id;
    return '';
  }
  window.kpTujuan = kpTujuan;

  function baru(nama) {
    var k = { id: uid(), name: nama || ('kampanye_' + (KP.L.length + 1)), col: PAL[KP.L.length % PAL.length], show: true, kind: 'kp' };
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
    var tj = kpTujuan() || KP.L[0].id, n = 0;
    for (var i = 0; i < C.length; i++) {
      var h = C[i][0], q = KP.of[h] && byId(KP.of[h]);
      if (!q || isMg(q)) { KP.of[h] = tj; n++; }
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
    var o = {}, M = {};
    KP.L.forEach(function (k) { o[k.id] = { c: 0, s: 0, a: 0, g: 0 }; M[k.id] = anggota(k.id); });
    var tally = function (arr, f) { (arr || []).forEach(function (r) { KP.L.forEach(function (k) { if (M[k.id][r[0]]) o[k.id][f]++; }); }); };
    tally(window.collars, 'c'); tally(window.surveys, 's'); tally(window.assays, 'a'); tally(window.geoRows, 'g');
    _cnt = o; _cntVer = key;
    return o;
  }
  window.kpCnt = cnt;

  /* ---------- atribut kategori virtual ---------- */
  function idxOf(id) { for (var i = 0; i < KP.L.length; i++) if (KP.L[i].id === id) return i; return -1; }

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
    /* "Dataset aktif": penanda apakah hole ikut analisis. Dipakai bersama "Kampanye" (label asal). */
    if (KP._si < 0) { KP._si = CAT.length; CAT.push({ name: 'Dataset aktif', src: 'kps', k: 0, d: [] }); }
    CAT[KP._si].d = ['ikut dataset aktif', 'hanya tampil'];
    try {
      var s3 = GSTY['Dataset aktif'] || (GSTY['Dataset aktif'] = {});
      s3[0] = Object.assign({}, s3[0] || {}, { c: '#1b7f4b' });
      s3[1] = Object.assign({}, s3[1] || {}, { c: '#8a93a0' });
    } catch (e) {}
  }
  var _aktM = null, _aktV = -1;
  function aktifSet() {
    if (_aktM && _aktV === KP.ver + '|' + (window.collars || []).length) return _aktM;
    _aktM = anggota(KP.act); _aktV = KP.ver + '|' + (window.collars || []).length;
    return _aktM;
  }
  function sCode(id) { return aktifSet()[id] ? 0 : 1; }

  /* interval: satu kampanye berlaku untuk SELURUH panjang hole */
  if (typeof window.geoIntervals === 'function') {
    var _gi = window.geoIntervals;
    window.geoIntervals = function (ci, id) {
      if (ci === KP._ci || ci === KP._si) {
        var h = (window.holeData || {})[id];
        if (!h || !(h.maxD > 0)) return [];
        var code = ci === KP._ci ? idxOf(kpOf(id)) : sCode(id);
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
      return _ca.apply(this, arguments);
    };
  }

  /* ---------- tampil / sembunyi per kampanye: menyaring visHoles ---------- */
  var _vh = window.visHoles;
  /* daftar TAMPIL: dipakai penggambaran 3D / sayatan. Hanya kampanye 'off' yang dibuang. */
  window.visHoles = function () {
    var v = _vh.apply(this, arguments);
    if (!KP.L.length) return v;
    var on = {};
    KP.L.forEach(function (k) { if (show(k) && !isMg(k)) { var m = anggota(k.id); Object.keys(m).forEach(function (h) { on[h] = 1; }); } });
    KP.L.forEach(function (k) { if (show(k) && isMg(k)) { var m2 = anggota(k.id); Object.keys(m2).forEach(function (h) { on[h] = 1; }); } });
    return v.filter(function (id) { return on[id]; });
  };
  /* satu hole ikut analisis? -> hanya bila anggota DATASET AKTIF */
  window.kpKerja = function (id) {
    if (!KP.L.length) return true;
    return !!aktifSet()[id];
  };
  /* daftar DATASET AKTIF: dipakai Geostatistik, statistik, flag otomatis, komposit dan estimasi.
     Database yang sekadar ditampilkan sebagai pembanding sengaja dibuang di sini. */
  window.visHolesK = function () {
    var v = window.visHoles.apply(this, arguments), A = aktifSet();
    var out = v.filter(function (id) { return A[id]; });
    /* dataset aktif yang kebetulan tidak dicentang tampil tetap dipakai analisis */
    if (!out.length && Object.keys(A).length) {
      out = (window.collars || []).map(function (c) { return c[0]; }).filter(function (id) { return A[id]; });
    }
    return out;
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
    KP.ver++; _cntVer = -1; _aktV = -1; catSync();
    if (window.SA && SA.dirty) SA.dirty();
    if (!diam) {
      try { if (window.updatePlot) updatePlot(); } catch (e) {}
      try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
      try { if (window.geoLegend) geoLegend(); } catch (e) {}
    }
  }
  window.kpUbah = ubah;

  window.kpAktif = function (id) { var k = byId(id); if (k) { KP.act = id; k.show = true; _aktV = -1; ubah(); } };
  window.kpVis = function (id, on) { var k = byId(id); if (k) { k.show = !!on; delete k.st; delete k.vis; ubah(); } };
  window.kpWarna = function (id, c) { var k = byId(id); if (k) { k.col = c; ubah(); } };
  window.kpGeser = function (id, d) {
    var i = idxOf(id), j = i + d;
    if (i < 0 || j < 0 || j >= KP.L.length) return;
    var t = KP.L[i]; KP.L[i] = KP.L[j]; KP.L[j] = t;
    ubah();
  };
  window.kpRename = function (id) {
    var k = byId(id);
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
    if (KP.L.filter(function (x) { return !isMg(x); }).length < 2) { alert('Kampanye terakhir tidak bisa dihapus.'); return; }
    var c = cnt()[id] || { c: 0 };
    var sisa = KP.L.filter(function (x) { return x.id !== id && !isMg(x); })[0];
    if (!sisa) { alert('Tidak ada kampanye lain sebagai tujuan pemindahan.'); return; }
    if (!confirm('Hapus kampanye "' + k.name + '" dari daftar?\n\n' + c.c + ' hole di dalamnya dipindahkan ke "' + sisa.name + '".\nData bornya TIDAK dihapus.')) return;
    Object.keys(KP.of).forEach(function (h) { if (KP.of[h] === id) KP.of[h] = sisa.id; });
    KP.L = KP.L.filter(function (x) { return x.id !== id; });
    KP.L.forEach(function (x) { if (isMg(x)) x.ids = (x.ids || []).filter(function (q) { return q !== id; }); });
    KP.L = KP.L.filter(function (x) { return !isMg(x) || (x.ids || []).length > 1; });
    if (!byId(KP.act)) KP.act = sisa.id;
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

  /* ---------- merge: membuat DATABASE BARU dari beberapa kampanye ---------- */
  window.kpGabung = function () {
    sync();
    var src = KP.L.filter(function (k) { return !isMg(k); });
    if (src.length < 2) { alert('Perlu minimal dua kampanye untuk digabungkan.'); return; }
    var daftar = src.map(function (k, i) { return (i + 1) + '. ' + k.name; }).join('\n');
    var r = prompt('Set database MERGE baru dari kampanye mana saja?\nTulis nomornya, pisahkan dengan koma.\n\n' + daftar + '\n\nContoh: 1,3', '');
    if (!r) return;
    var pick = String(r).split(/[\s,;]+/).map(function (x) { return parseInt(x, 10) - 1; })
      .filter(function (i) { return i >= 0 && i < src.length; });
    pick = pick.filter(function (v, i) { return pick.indexOf(v) === i; });
    if (pick.length < 2) { alert('Pilih minimal dua kampanye.'); return; }
    var nm = prompt('Nama set merge:', pick.map(function (i) { return src[i].name; }).join('+').slice(0, 40));
    if (nm == null) return;
    nm = String(nm).trim().slice(0, 40) || 'merge';
    var k = { id: uid(), name: nm, col: PAL[(KP.L.length + 3) % PAL.length], show: true, kind: 'mg',
              ids: pick.map(function (i) { return src[i].id; }), when: new Date().toISOString().slice(0, 16).replace('T', ' ') };
    KP.L.push(k);
    ubah();
    var n = Object.keys(anggota(k.id)).length;
    if (confirm('Set merge "' + nm + '" dibuat: ' + n + ' hole dari ' + k.ids.length + ' kampanye.\n\n' +
                'Isinya Collar / Survey / Assay / Geologi gabungan, dan tiap hole TETAP memegang label kampanye aslinya.\n\n' +
                'Jadikan set merge ini sebagai DATASET AKTIF sekarang?\n(Pemodelan, estimasi dan statistik hanya berlaku pada dataset aktif.)')) {
      window.kpAktif(k.id);
    }
  };
  window.kpGHapus = function (id) {
    var k = byId(id); if (!k || !isMg(k)) return;
    if (!confirm('Hapus set merge "' + k.name + '"?\n\nKampanye sumbernya tidak terpengaruh; tidak ada data bor yang dihapus.')) return;
    KP.L = KP.L.filter(function (x) { return x.id !== id; });
    KP.L.forEach(function (x) { if (isMg(x)) x.ids = (x.ids || []).filter(function (q) { return q !== id; }); });
    if (KP.act === id) KP.act = (KP.L.filter(function (x) { return !isMg(x); })[0] || KP.L[0] || {}).id || '';
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
  window.kpTabel = function (dbId) {
    var A = dbId ? anggota(dbId) : aktifSet(), ok = {}, nH = 0;
    (window.collars || []).forEach(function (c) { if (A[c[0]]) { ok[c[0]] = 1; nH++; } });
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

  window.kpExport = function (dbId) {
    try {
      sync();
      var db = byId(dbId) || byId(KP.act);
      if (!db) { alert('Belum ada database bor.'); return; }
      var T = window.kpTabel(db.id);
      if (!T.nH) { alert('Database "' + db.name + '" tidak berisi hole.'); return; }
      var u = xlsx(T.sheets);
      var nama = 'GCEx_' + db.name.replace(/[^A-Za-z0-9_+-]+/g, '_').slice(0, 60) + '.xlsx';
      var b = new Blob([u], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      var a2 = document.createElement('a');
      a2.href = URL.createObjectURL(b); a2.download = nama; document.body.appendChild(a2); a2.click();
      setTimeout(function () { URL.revokeObjectURL(a2.href); a2.remove(); }, 2000);
      alert('Export "' + db.name + '": ' + T.nH + ' hole.\n\n' +
            T.sheets.map(function (s2) { return s2.name + ' ' + (s2.rows.length - 1) + ' baris'; }).join(' · ') +
            '\n\nKolom "Kampanye" ikut ditulis di tiap sheet supaya asal tiap hole tetap terlacak.');
    } catch (e) { console.error(e); alert('Export gagal: ' + (e.message || e)); }
  };

  /* ---------- node Project Tree ---------- */
  /* Peran sebuah database diturunkan dari status aktif + centang tampil:
       AKTIF                      -> "set kerja" : tampil DAN satu-satunya sumber analisis
       dicentang, bukan aktif     -> "referensi" : tampil sebagai pembanding, tidak ikut analisis
       tidak dicentang            -> "sembunyi"  : tidak digambar                                 */
  function peran(k) { return KP.act === k.id ? 'set kerja' : (show(k) ? 'referensi' : 'sembunyi'); }
  window.kpPeran = peran;

  window.kpTree = function () {
    sync();
    if (!KP.L.length) return [];
    var N = function (n) { try { return (+n).toLocaleString('id-ID'); } catch (e) { return String(n); } };
    var C = cnt(), out = [];
    var tabel = function (kid, t, ic, n, mg) {
      return { id: kid, t: t + (mg ? ' Merge' : ''), ic: ic, b: n ? N(n) : '', dim: !n };
    };
    KP.L.forEach(function (k, i) {
      var c = C[k.id] || { c: 0, s: 0, a: 0, g: 0 }, aktif = KP.act === k.id, mg = isMg(k), pr = peran(k);
      var sumber = mg ? (k.ids || []).map(function (x) { var q = byId(x); return q ? q.name : '?'; }) : [];
      out.push({
        id: 'db.kp.' + k.id, t: k.name, ic: mg ? 'db' : 'folder', fold: 1, tab: 'Data',
        b: (aktif ? 'AKTIF &middot; ' : '') + pr + ' &middot; ' + N(c.c) + ' hole',
        mark: aktif ? 'aktif' : '', dim: !aktif,
        chk: show(k), onChk: function (v) { kpVis(k.id, v); },
        hint: (mg ? 'Set merge dari ' + sumber.join(' + ') + ' \u00b7 ' : '') +
              (aktif ? 'DATASET AKTIF — satu-satunya sumber pemodelan, estimasi dan statistik'
                     : show(k) ? 'Referensi — tampil sebagai pembanding, tidak ikut analisis' : 'Disembunyikan'),
        menu: function () {
          var L = [
            { t: aktif ? '\u2713 Dataset aktif (sumber pemodelan & estimasi)' : 'Jadikan dataset aktif', dis: aktif, fn: function () { kpAktif(k.id); } },
            { t: show(k) ? 'Sembunyikan dari tampilan' : 'Tampilkan sebagai referensi', dis: aktif && show(k), fn: function () { kpVis(k.id, !show(k)); } },
            { sep: 1 },
            { t: 'Ganti nama…', fn: function () { kpRename(k.id); } },
            { t: 'Export database ini (.xlsx)…', fn: function () { kpExport(k.id); } }
          ];
          if (!mg) L = L.concat([
            { sep: 1 },
            { t: 'Naikkan prioritas', dis: i === 0, fn: function () { kpGeser(k.id, -1); } },
            { t: 'Turunkan prioritas', dis: i === KP.L.length - 1, fn: function () { kpGeser(k.id, 1); } },
            { t: 'Pindahkan hole ke sini…', fn: function () { kpPindah(k.id); } }
          ]);
          L = L.concat([
            { sep: 1 },
            { t: 'Kampanye baru…', fn: function () { kpTambah(); } },
            { t: 'Buat set merge… (gabungkan kampanye)', fn: function () { kpGabung(); } },
            { sep: 1 },
            mg ? { t: 'Hapus set merge ini…', danger: 1, fn: function () { kpGHapus(k.id); } }
               : { t: 'Hapus kampanye ini…', danger: 1, fn: function () { kpHapus(k.id); } }
          ]);
          return L;
        },
        kids: [tabel('db.kp.' + k.id + '.c', 'Collar', 'collar', c.c, mg),
               tabel('db.kp.' + k.id + '.s', 'Survey', 'table', c.s, mg),
               tabel('db.kp.' + k.id + '.a', 'Assay', 'table', c.a, mg),
               tabel('db.kp.' + k.id + '.g', 'Geologi', 'geo', c.g, mg)]
          .concat(mg ? [{ id: 'db.kp.' + k.id + '.src', t: 'Sumber: ' + sumber.join(' + '), ic: 'attr', dim: 1 }] : [])
      });
    });
    return out;
  };

  /* ---------- simpan / muat bersama proyek ---------- */
  if (window.SA && typeof SA.collectWork === 'function') {
    var _c = SA.collectWork;
    SA.collectWork = function () {
      var w = _c.apply(this, arguments);
      try { w.kp = { L: KP.L, act: KP.act, of: KP.of }; } catch (e) { console.error(e); }
      return w;
    };
    var _a = SA.applyWork;
    SA.applyWork = function (W) {
      try {
        var o = W && W.kp;
        KP.L = (o && o.L) || []; KP.act = (o && o.act) || ''; KP.of = (o && o.of) || {};
        /* proyek lama (0.24.25/26): grup gabungan & keadaan tiga nilai -> set merge & centang tampil */
        ((o && o.g) || []).forEach(function (g) { KP.L.push({ id: g.id, name: g.name, col: g.col, show: g.vis !== false, kind: 'mg', ids: g.ids || [] }); });
        KP.L.forEach(function (k) { if (k.show === undefined) { k.show = k.st ? k.st !== 'off' : k.vis !== false; } if (!k.kind) k.kind = 'kp'; });
        KP.ver++; _cntVer = -1;
      } catch (e) { console.error(e); }
      var r = _a.apply(this, arguments);
      try { sync(); ubah(true); } catch (e) { console.error(e); }
      return r;
    };
  }

  setTimeout(function () { try { sync(); } catch (e) {} }, 400);
})();
