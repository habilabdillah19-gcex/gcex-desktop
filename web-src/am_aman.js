/* ================= AS-MINED: digitasi aman & hapus poligon dari Project Tree (BM 0.24.116, pemilik 27-11-2026) =================
   Kasus pemilik: "poligon as-mined yang saya digit malah menjadi poligon dig block" pada flitch yang belum punya dig block.
   Penyebab (direproduksi):
     1. Tombol "Digit poligon as-mined" membuka flitch lebih dulu (lyApply) bila flitch belum aktif. Pembuka flitch
        lalu memindah Project Tree ke "Buat Flitch Aktif" (fl.2d) = panel DIG BLOCK. Pengguna mendigit sambil
        melihat panel dig block, lengkap dengan tombol "Mulai" dig block.
     2. Menutup dengan Enter = "selesai sebagai string TERBUKA". Untuk as-mined string terbuka ditolak dan dibuang,
        tetapi pesannya tampil di panel As-Mined yang sedang tidak terlihat: poligonnya "hilang" tanpa kabar.
        Pengguna lalu mendigit ulang dengan tombol yang terlihat (Mulai di panel dig block) -> jadi dig block.
   Perbaikan:
     a. Digit as-mined tidak lagi memindah panel: Project Tree tetap di node As-Mined.
     b. Selama mendigit as-mined, Enter / "Selesai" menutup poligon (>= 3 titik), tidak membuangnya.
     c. Panel dig block yang terbuka saat mendigit as-mined menampilkan pita peringatan + tombol kembali / batal.
     d. Mulai digitasi dari mana pun SAAT panel As-Mined yang tampil = digitasi as-mined.
     e. Menu titik tiga di Project Tree: hapus poligon as-mined, hapus semua as-mined satu flitch, dan
        "Pindahkan ke As-Mined" pada dig block (memperbaiki data yang sudah telanjur menjadi dig block). */
(function () {
  var $ = function (i) { return document.getElementById(i); };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var amTampil = function () { var p = $('pAM'); return !!(p && !p.hidden && p.offsetParent); };
  var nodeAM = function (id) { return /^(am|reg)(\.|$)/.test(String(id || '')) && !/\.r$/.test(String(id || '')); };
  var viaDb = 0;

  function pasang() {
    if (!window.amDig || !window.dgFinish || !window.dgStart || !window.PT || !PT.select || !window.amBndAdd) return setTimeout(pasang, 400);
    if (window.AMA) return;

    /* a. tetap di panel As-Mined */
    var _ad = window.amDig;
    window.amDig = amDig = function () {
      var asal = nodeAM(PT.sel) ? PT.sel : 'am.3';
      try { if (PT.mau) PT.mau(asal); } catch (e) {}
      var r = _ad.apply(this, arguments);
      [80, 400, 900].forEach(function (t) { setTimeout(function () { try { if (AM.digOn && PT.sel !== asal) PT.select(asal); } catch (e) {} }, t); });
      return r;
    };

    /* d. digitasi yang dimulai saat panel As-Mined tampil = as-mined */
    var _db = window.dbDig;
    if (_db) window.dbDig = dbDig = function () { viaDb++; try { return _db.apply(this, arguments); } finally { viaDb--; } };
    var _st = window.dgStart;
    window.dgStart = dgStart = function () {
      if (!viaDb && !AM.digOn && amTampil()) { AM.digOn = true; if ($('dgDesc')) $('dgDesc').value = 'BOUNDARY'; }
      if (viaDb && AM.digOn) AM.digOn = false;
      var r = _st.apply(this, arguments); try { if (AM.digOn) amPanel(); } catch (e) {} return r;
    };

    /* b. Enter / Selesai menutup poligon as-mined; pesan "sudah ada" tidak lagi menyamar sebagai "harus tertutup" */
    var _f = window.dgFinish;
    window.dgFinish = dgFinish = function (closed) {
      var am = !!AM.digOn, n = (window.DG && DG.cur) ? DG.cur.length : 0, nb = amBndAll().length;
      if (am && !closed && n >= 3) closed = true;
      var r = _f.call(this, closed);
      if (am && closed && n >= 3 && amBndAll().length === nb && !AM.digOn) {
        AM.bmsg = '<span class=warn>Poligon yang sama persis sudah ada di flitch ini &mdash; tidak ditambahkan dua kali.</span>';
        try { amPanel(); } catch (e) {}
      }
      if (am && !AM.digOn) { try { if (!amTampil()) PT.select(nodeAM(PT.sel) ? PT.sel : 'am.3'); } catch (e) {} }
      return r;
    };

    /* c. pita peringatan di panel dig block */
    var _dp = window.dbPanel;
    if (_dp) window.dbPanel = dbPanel = function () {
      var r = _dp.apply(this, arguments);
      try {
        var b = $('dbBody'); if (!b) return r; var o = $('amaPita'); if (o) o.remove();
        if (window.AM && AM.digOn && window.DG && DG.on) {
          var d = document.createElement('div'); d.id = 'amaPita'; d.className = 'amdig';
          d.innerHTML = '<b>&#9679; Sedang mendigit poligon AS-MINED</b> &mdash; hasilnya masuk ke As-Mined, bukan dig block.' +
            '<div class=g2 style="margin-top:4px"><button class=btn-pri onclick="PT.select(\'am.3\')">Kembali ke panel As-Mined</button><button onclick="dgCancel()">Batal</button></div>';
          b.insertBefore(d, b.firstChild);
        }
      } catch (e) {}
      return r;
    };

    /* e. aksi menu titik tiga */
    var sesudah = function () { try { amAuto(); } catch (e) {} try { amPanel(); } catch (e) {} try { updatePlot(); } catch (e) {} try { amDirty(); } catch (e) {} try { PT.render(true); } catch (e) {} };
    window.AMA = {
      hapus: function (id, nama) {
        if (!confirm('Hapus poligon as-mined ' + (nama || id) + '?')) return;
        window.amBndDel(id); try { PT.render(true); } catch (e) {}
      },
      hapusBanyak: function (ids, label) {
        var L = amBndAll().filter(function (x) { return ids.indexOf(x.id) >= 0; });
        var kunci = L.filter(function (x) { return window.AMK && AMK.isLk && AMK.isLk(x); }), bebas = L.filter(function (x) { return kunci.indexOf(x) < 0; });
        if (!bebas.length) { alert(kunci.length ? 'Semua poligon ' + label + ' terkunci (sudah dilaporkan) — buka kuncinya dulu.' : 'Tidak ada poligon as-mined di ' + label + '.'); return; }
        if (!confirm('Hapus ' + bebas.length + ' poligon as-mined di ' + label + '?' + (kunci.length ? '\n' + kunci.length + ' poligon terkunci tidak ikut dihapus.' : ''))) return;
        var D = amD(), set = {}; bebas.forEach(function (x) { set[x.id] = 1; });
        D.bnd = D.bnd.filter(function (x) { return !set[x.id]; }); sesudah();
      },
      dariDb: function (q) {
        if (!q || !q.pts || q.pts.length < 3 || !q.closed) { alert('Hanya dig block tertutup yang bisa dipindahkan.'); return; }
        var B = q.db ? [q.db.top, q.db.bot] : lyBench();
        if (!confirm('Pindahkan dig block #' + q.no + ' (' + (q.d || '-') + ', RL ' + B[0] + ' – ' + B[1] + ') menjadi poligon AS-MINED?\n\nDig block-nya dihapus; bentuknya disalin ke As-Mined pada flitch yang sama.')) return;
        var ok = amBndAdd(q.pts.map(function (p) { return [p[0] + offX, p[1] + offY]; }), 'Dari dig block #' + q.no, { top: B[0], bot: B[1], src: 'dig block #' + q.no });
        if (!ok) { alert('Poligon yang sama persis sudah ada di As-Mined flitch ini. Dig block tidak diubah.'); return; }
        if (!q.id) q.id = dbId();
        dbDelIds([q.id], true); sesudah();
      }
    };
  }
  pasang();
})();
