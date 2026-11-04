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
     - centang tampil / sembunyi dan warna per kampanye (menyaring visHoles, jadi berlaku di 3D,
       sayatan 2D, statistik, Geostatistik dan komposit sekaligus);
     - atribut kategori VIRTUAL "Kampanye" (dan "Gabungan kampanye" bila ada grup gabungan),
       sehingga semua mesin yang sudah ada memperlakukannya seperti atribut geologi biasa;
     - gabungan kampanye (merge): beberapa kampanye disatukan sebagai satu grup bernama, tetapi
       tiap hole TETAP memegang label kampanye aslinya sehingga masih bisa difilter satu per satu;
     - node Database Bor di Project Tree dipecah per kampanye, lengkap dengan jumlah baris collar /
       survey / assay / geologi dan penanda AKTIF.

   Hole yang belum punya label — termasuk seluruh hole saat proyek lama dibuka pertama kali, dan
   hole baru hasil upsert — otomatis masuk ke kampanye AKTIF.                                      */
(function () {
  if (typeof CAT === 'undefined' || typeof window.visHoles !== 'function') return;

  var PAL = ['#2c5282', '#c0522d', '#1b7f4b', '#7c3aed', '#c98a16', '#0f766e', '#be185d', '#57534e'];
  var KP = { L: [], g: [], act: '', of: {}, ver: 0, _ci: -1, _gi: -1 };
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

  function baru(nama) {
    var k = { id: uid(), name: nama || ('kampanye_' + (KP.L.length + 1)), col: PAL[KP.L.length % PAL.length], vis: true };
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
  }

  /* interval: satu kampanye berlaku untuk SELURUH panjang hole */
  if (typeof window.geoIntervals === 'function') {
    var _gi = window.geoIntervals;
    window.geoIntervals = function (ci, id) {
      if (ci === KP._ci || (KP._gi >= 0 && ci === KP._gi)) {
        var h = (window.holeData || {})[id];
        if (!h || !(h.maxD > 0)) return [];
        var code = ci === KP._ci ? idxOf(kpOf(id)) : gIdxOf(kpOf(id));
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
      if (KP._gi >= 0 && ci === KP._gi) return gIdxOf(kpOf(id));
      return _ca.apply(this, arguments);
    };
  }

  /* ---------- tampil / sembunyi per kampanye: menyaring visHoles ---------- */
  var _vh = window.visHoles;
  window.visHoles = function () {
    var v = _vh.apply(this, arguments);
    if (!KP.L.length) return v;
    var off = {};
    KP.L.forEach(function (k) { if (k.vis === false) off[k.id] = 1; });
    KP.g.forEach(function (g) { if (g.vis === false) g.ids.forEach(function (i) { off[i] = 1; }); });
    if (!Object.keys(off).length) return v;
    return v.filter(function (id) { return !off[kpOf(id)]; });
  };

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

  window.kpAktif = function (id) { if (byId(id)) { KP.act = id; ubah(); } };
  window.kpVis = function (id, on) { var k = byId(id); if (k) { k.vis = !!on; ubah(); } };
  window.kpGVis = function (id, on) { for (var i = 0; i < KP.g.length; i++) if (KP.g[i].id === id) { KP.g[i].vis = !!on; ubah(); return; } };
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
    KP.g.push({ id: uid(), name: nm, col: PAL[(KP.g.length + 3) % PAL.length], vis: true, ids: pick.map(function (i) { return KP.L[i].id; }) });
    ubah();
    alert('Gabungan "' + nm + '" dibuat.\n\nTiap hole TETAP memegang kampanye aslinya, jadi Anda masih bisa memfilter per kampanye. ' +
          'Gabungan ini muncul sebagai atribut kategori "Gabungan kampanye" untuk pewarnaan, filter, Geostatistik dan estimasi.');
  };
  window.kpGHapus = function (id) {
    var g = KP.g.filter(function (x) { return x.id === id; })[0]; if (!g) return;
    if (!confirm('Hapus gabungan "' + g.name + '"?\n\nKampanye di dalamnya tidak terpengaruh.')) return;
    KP.g = KP.g.filter(function (x) { return x.id !== id; });
    ubah();
  };

  /* ---------- node Project Tree ---------- */
  window.kpTree = function () {
    sync();
    if (!KP.L.length) return [];
    var N = function (n) { try { return (+n).toLocaleString('id-ID'); } catch (e) { return String(n); } };
    var C = cnt(), out = [];
    var tabel = function (kid, t, ic, n) { return { id: kid, t: t, ic: ic, b: n ? N(n) : '', dim: !n }; };
    KP.L.forEach(function (k, i) {
      var c = C[k.id] || { c: 0, s: 0, a: 0, g: 0 }, aktif = KP.act === k.id;
      out.push({
        id: 'db.kp.' + k.id, t: k.name, ic: 'folder', fold: 1, tab: 'Data',
        b: (aktif ? 'AKTIF &middot; ' : '') + N(c.c) + ' hole',
        mark: aktif ? 'aktif' : '', dim: k.vis === false,
        chk: k.vis !== false, onChk: function (v) { kpVis(k.id, v); },
        hint: 'Prioritas ' + (i + 1) + ' dari ' + KP.L.length + (aktif ? ' — tujuan import / upsert berikutnya' : ''),
        menu: function () {
          return [
            { t: aktif ? '✓ Kampanye aktif' : 'Jadikan kampanye aktif', dis: aktif, fn: function () { kpAktif(k.id); } },
            { sep: 1 },
            { t: 'Naikkan prioritas', dis: i === 0, fn: function () { kpGeser(k.id, -1); } },
            { t: 'Turunkan prioritas', dis: i === KP.L.length - 1, fn: function () { kpGeser(k.id, 1); } },
            { sep: 1 },
            { t: 'Ganti nama…', fn: function () { kpRename(k.id); } },
            { t: 'Pindahkan hole ke sini…', fn: function () { kpPindah(k.id); } },
            { sep: 1 },
            { t: 'Kampanye baru…', fn: function () { kpTambah(); } },
            { t: 'Gabungkan kampanye…', fn: function () { kpGabung(); } },
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
        hint: 'Gabungan ' + g.ids.length + ' kampanye; tiap hole tetap memegang kampanye aslinya',
        menu: function () {
          return [{ t: 'Ganti nama…', fn: function () { kpRename(g.id); } },
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
      try { w.kp = { L: KP.L, g: KP.g, act: KP.act, of: KP.of }; } catch (e) { console.error(e); }
      return w;
    };
    var _a = SA.applyWork;
    SA.applyWork = function (W) {
      try {
        var o = W && W.kp;
        KP.L = (o && o.L) || []; KP.g = (o && o.g) || []; KP.act = (o && o.act) || ''; KP.of = (o && o.of) || {};
        KP.ver++; _cntVer = -1;
      } catch (e) { console.error(e); }
      var r = _a.apply(this, arguments);
      try { sync(); ubah(true); } catch (e) { console.error(e); }
      return r;
    };
  }

  setTimeout(function () { try { sync(); } catch (e) {} }, 400);
})();
