/* digqt.js -- membaca string dig block yang dibuat PENAMPIL 3D Qt (`gcex_dig_qt.json`).
 *
 * MENGAPA ADA: penampil Qt sengaja TIDAK menulis ke `gcex_project.json`. Berkas itu dijaga
 * protokol yang cukup rumit (berkas kunci `gcex.lock`, nomor revisi `rev` untuk konflik antar
 * pemakai, cadangan ke `backup/` dan `backup/harian/`, hash isi); kalau penampil Qt menulis ke
 * situ dan satu bagian protokol terlewat, yang rusak adalah berkas proyek yang sedang dipakai
 * orang lain. Jadi Qt menulis ke berkas pendampingnya sendiri di folder proyek yang sama.
 *
 * Akibatnya alirannya semula SATU ARAH: string yang dibuat di aplikasi HTML terlihat di Qt,
 * tetapi string yang dibuat di Qt tidak terlihat di sini -- sehingga pemakai yang mendigit di Qt
 * lalu ingin mencetak peta oreblock, memakai aturan material HG/LG, atau as-mined akan menemui
 * daftar kosong, tanpa penjelasan. Modul ini menutup arah yang kedua.
 *
 * HAL YANG PALING MUDAH SALAH DI SINI: OFFSET. Titik digitasi tersimpan RELATIF terhadap
 * `offX`/`offY`, dan offset itu dihitung dari koordinat collar proyek. Berkas Qt mencatat offset
 * yang dipakainya saat menulis. Kalau data bor proyek berubah (collar baru di barat / selatan
 * yang menggeser minimum), offset aplikasi sekarang bisa BERBEDA dari yang tercatat di berkas.
 * Karena itu titiknya digeser sebesar selisih kedua offset, bukan dipakai apa adanya. Tanpa
 * penggeseran itu poligon pindah ribuan meter dan tidak ada galat apa pun yang muncul -- hanya
 * poligon kosong di tempat yang salah.
 *
 * MENAMBAH, BUKAN MENGGANTI. Daftar string yang sudah ada tidak pernah ditimpa: menimpa berarti
 * membuang pekerjaan yang mungkin belum tersimpan. String yang isinya sudah ada dilewati, dan
 * nomor yang sudah terpakai diganti nomor berikutnya supaya tidak ada dua string bernomor sama.
 */
(function () {
  var BERKAS = 'gcex_dig_qt.json';

  /* Pelolos karakter sendiri. `esc()` aplikasi TIDAK terjangkau dari lingkup modul ini (sama
     seperti `encTA`), dan memakainya membuat dgQtImport melempar galat SETELAH string tergabung
     -- pemakai melihat galat padahal pekerjaannya sudah masuk. Pelolosan tidak boleh dibuang
     begitu saja: keterangan string dan waktu simpan datang dari BERKAS, yaitu masukan luar. */
  function E(v) {
    return String(v === undefined || v === null ? '' : v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /* Ambil dan baca berkas Qt. Kembalikan {err} atau {dg, meta, offX, offY}. */
  async function baca() {
    if (typeof FP === 'undefined' || !FP.dir) return {err: 'Belum ada folder proyek yang terhubung.'};
    var t = null;
    try { t = await FP.readText(FP.dir, BERKAS); } catch (e) { t = null; }
    if (!t) return {err: 'Tidak ada ' + BERKAS + ' di folder proyek ini (penampil Qt belum pernah menyimpan string di sini).'};
    var U;
    try { U = FP.unpack(t); } catch (e) {
      /* Berkasnya TIDAK disentuh: pemakai mungkin masih bisa menyelamatkan isinya sendiri. */
      return {err: BERKAS + ' tidak bisa dibaca (' + (e && e.message || e) + '). Berkasnya dibiarkan apa adanya, tidak ditimpa.'};
    }
    var B = U.body || {};
    if (!B.dg || !B.dg.length) return {err: BERKAS + ' ada, tetapi belum memuat string.'};
    return {dg: B.dg, meta: U.meta || {}, offX: +B.offX || 0, offY: +B.offY || 0};
  }

  /* Gabungkan ke DG.S. Kembalikan ringkasan untuk ditampilkan. */
  function gabung(R) {
    var dx = R.offX - (typeof offX === 'number' ? offX : 0);
    var dy = R.offY - (typeof offY === 'number' ? offY : 0);
    var pakai = {}, nomor = {}, maks = 0;
    DG.S.forEach(function (s) {
      nomor[s.no] = 1;
      if (+s.no > maks) maks = +s.no;
      pakai[JSON.stringify(s.pts)] = 1;
    });
    var tambah = 0, lewat = 0, warna = DG.pal || ['#e8590c'];
    R.dg.forEach(function (d, k) {
      if (!d || !d.pts || d.pts.length < 2) { lewat++; return; }
      var pts = d.pts.map(function (p) { return [p[0] + dx, p[1] + dy, p[2]]; });
      if (pakai[JSON.stringify(pts)]) { lewat++; return; }
      var no = parseInt(d.no) || (maks + 1);
      if (nomor[no]) { maks += 1; no = maks; } else if (no > maks) { maks = no; }
      nomor[no] = 1;
      pakai[JSON.stringify(pts)] = 1;
      DG.S.push({no: no, d: String(d.d || ''), closed: !!d.closed, pts: pts,
                 pl: {m: 'H', pos: pts[0][2]},
                 col: d.col || warna[(DG.S.length) % warna.length],
                 vis: d.vis !== false, dariQt: true});
      tambah++;
    });
    return {tambah: tambah, lewat: lewat, dx: dx, dy: dy, total: R.dg.length};
  }

  window.dgQtImport = async function () {
    var R = await baca();
    if (R.err) { if (window.msg) msg(E(R.err), true); return; }
    var G = gabung(R);
    if (!G.tambah) {
      if (window.msg) msg('Semua ' + G.total + ' string dari penampil Qt sudah ada di daftar.');
      return;
    }
    try { dgSave(); } catch (e) { }
    try { dgList(); } catch (e) { }
    try { updatePlot(); } catch (e) { }
    try { if (window.dbPanel) dbPanel(); } catch (e) { }
    try { if (window.lyPanel) lyPanel(); } catch (e) { }
    var h = '<b>' + G.tambah + '</b> string dari penampil 3D Qt ditambahkan (dari ' + G.total +
      ' di berkas' + (G.lewat ? ', ' + G.lewat + ' dilewati karena sudah ada / terlalu pendek' : '') + ').';
    /* Penggeseran offset WAJIB dikatakan: kalau tidak, pemakai tidak punya cara mengetahui
       bahwa koordinatnya disesuaikan, dan tidak bisa menilai apakah itu wajar. */
    if (G.dx || G.dy) {
      h += ' Koordinat digeser ' + G.dx.toFixed(0) + ' / ' + G.dy.toFixed(0) +
        ' m karena offset proyek berbeda dari saat berkas Qt ditulis (biasanya karena ada collar baru).';
    }
    if (R.meta && R.meta.savedAt) h += ' Berkas Qt disimpan ' + E(R.meta.savedAt) + '.';
    if (window.msg) msg(h);
  };

  /* Tombol di panel Dig block. Dipasang setiap dbPanel() menggambar ulang panelnya. */
  if (typeof dbPanel === 'function') {
    var _pn = dbPanel;
    dbPanel = function () {
      var r = _pn.apply(this, arguments);
      try {
        var el = document.getElementById('dbRun');
        if (el && !document.getElementById('dgQtBtn')) {
          var d = document.createElement('div');
          d.style.marginTop = '6px';
          d.innerHTML = '<button id="dgQtBtn" onclick="dgQtImport()" ' +
            'title="Baca string dig block yang dibuat penampil 3D Qt (gcex_dig_qt.json di folder proyek). Menambah, tidak mengganti.">' +
            '&#8681; Ambil string dari penampil 3D Qt</button>';
          el.parentNode.insertBefore(d, el.nextSibling);
        }
      } catch (e) { }
      return r;
    };
  }
})();
