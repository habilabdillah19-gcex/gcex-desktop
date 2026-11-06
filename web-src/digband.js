/* digband.js -- dig block: angka KEDUA metode tonase selalu ditampilkan berdampingan.
 *
 * MENGAPA: bawaan dig block adalah metode presisi GC-Ex, sedangkan perangkat lunak yang diakui
 * di tambang adalah Surpac. Perbedaan keduanya di dig block bersifat GEOMETRIS (blok dipotong di
 * garis poligon vs blok utuh bila titik tengahnya di dalam), jadi ia tetap ada walaupun block
 * model tidak punya atribut proporsi `sb_frac` -- berbeda dengan Reporting BM, yang tanpa
 * `sb_frac` memang memberi angka identik. Pada uji paritas, selisihnya 0,1% sampai 17,9%
 * tergantung posisi garis poligon terhadap grid blok, dan kadarnya pun bergeser.
 *
 * Selisih sebesar itu menentukan apakah angka dig block bisa dipertanggungjawabkan terhadap
 * Surpac. Karena itu angka pembandingnya TIDAK boleh bersembunyi di balik satu pilihan di menu:
 * keduanya ditampilkan, selalu, di tempat angkanya dibaca. Keputusan pemilik: bawaan TIDAK
 * diubah (supaya tidak ada angka lama yang berubah diam-diam), yang diubah hanya bahwa angka
 * pembandingnya selalu terlihat.
 *
 * CARANYA: metode lain dihitung dengan MEMBALIK `lyU().calcM` sesaat lalu memanggil `lyTon()`
 * yang sama, bukan dengan memanggil `lyTonS()` langsung. Itu jalur yang persis sama dengan yang
 * didapat pemakai saat mengganti pilihan metode sendiri -- jadi tidak mungkin ada jalur ketiga
 * yang perilakunya menyimpang dari keduanya.
 */
(function () {
  if (typeof lyTon !== 'function' || typeof lyU !== 'function') return;

  /* hasil metode LAIN untuk poligon yang sama. null bila tidak bisa dihitung. */
  function lain(P, zs, excl) {
    if (!window.BX || !BX.m || !P || P.length < 3) return null;
    var L = lyU(), simpan = L.calcM;
    var ke = (lyCalcM() === 'surpac') ? 'clip' : 'surpac';
    var r = null;
    try {
      L.calcM = ke;
      if (window.LY) LY.ix = null;          /* cache indeks flitch ikut metode, wajib dibuang */
      r = lyTon(P, zs, excl || []);
      if (r) r.m2 = ke;
    } catch (e) {
      r = null;
    } finally {
      L.calcM = simpan;
      if (window.LY) LY.ix = null;
    }
    return r;
  }
  window.dbLain = lain;

  function nm(k) { return k === 'surpac' ? 'Surpac' : 'presisi'; }
  function f(v) { return (window.lyFmt ? lyFmt(v) : (+v).toFixed(2)); }

  /* teks pembanding: "· Surpac 16.900,00 t @ 0,26 (+10,6%)" */
  function bandingTxt(t, P, zs, excl) {
    if (!t) return '';
    var o = lain(P, zs, excl);
    if (!o) return '';
    var d = o.t ? (t.t - o.t) / o.t * 100 : NaN;
    var s = ' &middot; <span class=dbband>' + nm(o.m2) + ' <b>' + f(o.t) + ' t</b>';
    if (isFinite(o.grade)) s += ' @ ' + o.grade.toFixed(2);
    if (isFinite(d)) s += ' (' + (d >= 0 ? '+' : '') + d.toFixed(1) + '%)';
    return s + '</span>';
  }

  /* ---- 1. angka langsung saat mendigit ---- */
  if (typeof dbRunTxt === 'function') {
    var _rt = dbRunTxt;
    dbRunTxt = function (r) {
      var s = _rt.apply(this, arguments);
      if (!r || !r.t) return s;
      /* poligon yang sedang didigit: titik yang sama dengan dipakai dbRunCalc */
      var P = null;
      try {
        var A = (typeof dgAx === 'function') ? dgAx() : null;
        P = (window.DG && DG.c2) ? DG.c2.slice() : null;
        if (P && A && DG.hov) P.push([A.x.p2d(DG.hov[0] - A.x._offset), A.y.p2d(DG.hov[1] - A.y._offset)]);
      } catch (e) { P = null; }
      if (!P || P.length < 3) return s;
      return s + bandingTxt(r.t, P, (typeof lyZs === 'function') ? lyZs() : undefined, []);
    };
  }

  /* ---- 2. daftar dig block yang sudah tersimpan ---- */
  if (typeof lyItems === 'function') {
    var _it = lyItems;
    lyItems = function () {
      var out = _it.apply(this, arguments);
      if (!out || !out.length) return out;
      var zs = (typeof lyZs === 'function') ? lyZs() : undefined;
      out.forEach(function (o) {
        if (!o || !o.ton) return;
        try {
          var ex = [];                      /* lubang sudah ikut di o.ton; dihitung ulang sama */
          o.ton2 = lain(o.r, zs, ex);
          if (o.ton2 && o.ton2.t) o.ton2.beda = (o.ton.t - o.ton2.t) / o.ton2.t * 100;
        } catch (e) { o.ton2 = null; }
      });
      return out;
    };
  }

  /* ---- 3. keterangan tetap di panel dig block ---- */
  var GAYA = '.dbband{color:#7ee0ff}.dbbandnb{color:#8b97a8;font-size:11px;line-height:1.35;margin-top:4px}';
  function gaya() {
    if (document.getElementById('dbbandCss')) return;
    var st = document.createElement('style');
    st.id = 'dbbandCss';
    st.textContent = GAYA;
    document.head.appendChild(st);
  }
  if (typeof dbPanel === 'function') {
    var _pn = dbPanel;
    dbPanel = function () {
      var r = _pn.apply(this, arguments);
      gaya();
      try {
        var el = document.getElementById('dbRun');
        if (el && !document.getElementById('dbbandNb')) {
          var d = document.createElement('div');
          d.id = 'dbbandNb';
          d.className = 'dbbandnb';
          d.innerHTML = 'Angka <b>' + (lyCalcM() === 'surpac' ? 'Surpac' : 'presisi GC-Ex') +
            '</b> dipakai, angka metode lain ditampilkan di sebelahnya sebagai pembanding. ' +
            'Selisihnya GEOMETRIS (blok dipotong di garis vs blok utuh), jadi tetap ada walau ' +
            'block model tanpa <code>sb_frac</code>. Bila angka akan dibandingkan dengan Surpac, ' +
            'pakai angka Surpac &mdash; dan ingat <b>waste pengisi hanya ditambahkan pada metode ' +
            'presisi</b>.';
          el.parentNode.insertBefore(d, el.nextSibling);
        }
      } catch (e) { }
      return r;
    };
  }
})();
