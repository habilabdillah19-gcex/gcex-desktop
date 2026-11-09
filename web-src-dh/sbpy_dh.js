/* ================= PEMBANDING KECEPATAN sb_frac: JavaScript vs backend Python =================
   Perhitungan proporsi volume ore per blok (sb_frac) sudah ada dua kali: di dalam aplikasi ini
   (JavaScript, SB.frac) dan di backend Python (NumPy, /geostat/subblok). Keduanya sudah dibuktikan
   menghasilkan angka yang sama pada data latihan lewat uji paritas otomatis di repo.

   Modul ini TIDAK mengganti perhitungannya. Yang menulis atribut sb_frac tetap SB.frac versi
   JavaScript, apa pun hasil pembandingan ini. Tombol di bawah hanya:
     1. menjalankan versi JavaScript, dicatat waktunya,
     2. mengirim mesh solid & daftar blok yang SAMA ke backend Python, dicatat waktunya,
     3. melaporkan beda angka terbesar di antara keduanya dan selisih waktunya.

   Gunanya: kecepatan backend bergantung pada jumlah inti CPU komputer yang dipakai, jadi angka
   yang berarti hanya angka dari komputer Anda sendiri -- bukan dari komputer pengembang. Setelah
   terlihat seberapa besar bedanya, baru layak diputuskan apakah perhitungan ini dipindahkan
   sepenuhnya ke backend.

   Bila backend tidak aktif (mis. aplikasi dijalankan tanpa backend), tombolnya mengatakan begitu
   dan tidak terjadi apa-apa. */
(function () {
  if (typeof BX === 'undefined' || typeof SB === 'undefined') return;
  var PY = { busy: false, msg: '' };
  window.SBPY = PY;

  function fmt(v, d) {
    return v == null || !isFinite(v) ? '-'
      : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 });
  }
  function sE(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; });
  }
  function pesan(h) {
    PY.msg = h;
    var d = document.getElementById('sbPyMsg');
    if (d) d.innerHTML = h;
  }

  /* solid domain, disusun sama seperti solids() di subblk_dh.js (yang bersifat lokal di modul itu) */
  function solidKirim() {
    var L = (window.gmTops ? gmTops() : (window.GM ? GM.doms : [])) || [], W = [];
    L.forEach(function (d) {
      var R = (typeof meGrpR === 'function') ? meGrpR(d) : null;
      if (!R || !R.mesh) return;
      if (window.mdLocal) mdLocal(R.mesh);
      var ms = R.mesh;
      W.push({
        name: d.name, bb: meBBox(ms),
        mesh: {
          x: Array.prototype.slice.call(ms._x), y: Array.prototype.slice.call(ms._y),
          z: Array.prototype.slice.call(ms._z), i: Array.prototype.slice.call(ms._i),
          j: Array.prototype.slice.call(ms._j), k: Array.prototype.slice.call(ms._k)
        }
      });
    });
    return W;
  }

  PY.ukur = async function () {
    if (PY.busy) return;
    var D = window.gcexDesktop;
    if (!D || !D.api) { pesan('<span class=warn>Pembandingan ini hanya tersedia di aplikasi desktop GC-Ex (butuh backend Python).</span>'); return; }
    var m = BX.m;
    if (!m) { pesan('<span class=warn>Belum ada block model aktif.</span>'); return; }
    var W;
    try { W = solidKirim(); } catch (e) { pesan('<span class=warn>' + sE(e.message || e) + '</span>'); return; }
    if (!W.length) { pesan('<span class=warn>Belum ada solid domain terbangun (Geological Modelling ). Proporsi volume memakai batas solid sebagai acuan.</span>'); return;  }

    PY.busy = true;
    var btn = document.getElementById('sbPyBtn');
    if (btn) btn.disabled = true;
    pesan('Menjalankan versi JavaScript&hellip;');
    try {
      /* 1. versi JavaScript -- ini juga yang menulis atribut sb_frac, seperti biasa */
      await new Promise(function (r) { setTimeout(r, 30); });
      var t0 = performance.now();
      var fr = SB.frac(10, true);
      var msJs = performance.now() - t0;
      var FJ = m.num['sb_frac'];
      if (!fr || !FJ) throw new Error('versi JavaScript tidak menghasilkan sb_frac');
      var FJsal = Array.prototype.slice.call(FJ);     /* disalin: backend tidak boleh menimpanya */

      /* 2. versi backend Python, dengan mesh & blok yang sama */
      pesan('Mengirim ' + fmt(m.n) + ' blok &amp; ' + fmt(W.reduce(function (a, s) { return a + s.mesh.i.length; }, 0)) + ' segitiga ke backend&hellip;');
      await new Promise(function (r) { setTimeout(r, 30); });
      var B = { x: [], y: [], z: [], sx: [], sy: [], sz: [] }, ox = window.offX || 0, oy = window.offY || 0, i;
      for (i = 0; i < m.n; i++) {
        B.x.push(m.x[i] - ox); B.y.push(m.y[i] - oy); B.z.push(m.z[i]);
        B.sx.push(m.sx[i]); B.sy.push(m.sy[i]); B.sz.push(m.sz[i]);
      }
      var t1 = performance.now();
      var r2 = await D.api('/geostat/subblok', { solids: W, blocks: B, mode: 'frac', nF: fr.N, workers: 'auto' });
      var msKirim = performance.now() - t1;                 /* termasuk kirim-terima data */
      var msPy = r2 && r2.ms ? r2.ms : NaN;                 /* hitung murni di Python */

      /* 3. bandingkan angkanya */
      var FP = r2.F || [], beda = 0, nBeda = 0;
      if (FP.length !== FJsal.length) throw new Error('jumlah blok dari backend tidak sama (' + FP.length + ' vs ' + FJsal.length + ')');
      for (i = 0; i < FP.length; i++) {
        var d2 = Math.abs(FP[i] - FJsal[i]);
        if (d2 > beda) beda = d2;
        if (d2 > 1e-6) nBeda++;
      }
      /* sb_frac disimpan Float32Array di aplikasi, jadi beda ~1e-7 adalah pembulatan penyimpanan,
         bukan selisih perhitungan. */
      var sama = nBeda === 0;
      var wk = r2.workers || 1;
      /* Yang ditunggu pemakai adalah waktu TOTAL: mengirim data ke backend lalu menghitung.
         Waktu hitung murni disebut terpisah supaya terlihat di mana ongkosnya berada --
         pada data sebesar ini, pengiriman data bisa sebesar perhitungannya sendiri. */
      var menang = msKirim < msJs;
      pesan(
        (sama ? '&#10003; <b>Angkanya sama</b>' : '<span class=warn>&#9888; Angkanya BERBEDA di ' + fmt(nBeda) + ' blok</span>') +
        ' &middot; beda terbesar ' + beda.toExponential(1) + ' (penyimpanan Float32 ~1e-7)' +
        '<br><b>Total yang ditunggu:</b> JavaScript <b>' + fmt(msJs) + ' ms</b> vs backend <b>' + fmt(msKirim) + ' ms</b> &middot; ' +
        (menang ? 'backend lebih cepat ' + fmt(msJs / Math.max(1, msKirim), 2) + '&times;'
                : '<span class=warn>JavaScript masih lebih cepat ' + fmt(msKirim / Math.max(1, msJs), 2) + '&times;</span>') +
        '<br><span class=hint>Rincian backend: menghitung ' + fmt(msPy) + ' ms di ' + wk + ' inti CPU, sisanya ' +
        fmt(Math.max(0, msKirim - msPy)) + ' ms untuk mengirim mesh &amp; blok. Kalau perhitungan ini kelak dipindah ' +
        'sepenuhnya, datanya perlu dikirim sekali lalu disimpan di backend &mdash; bukan dikirim ulang tiap kali. &middot; ' +
        fmt(fr.nPart) + ' blok di perbatasan, ' + fmt(fr.nFull) + ' utuh, ' + fmt(fr.nNol) + ' di luar. ' +
        'Atribut sb_frac yang tersimpan tetap hasil versi JavaScript.</span>'
      );
    } catch (e) {
      console.error(e);
      pesan('<span class=warn>Gagal: ' + sE(e.message || e) + '</span>');
    } finally {
      PY.busy = false;
      if (btn) btn.disabled = false;
    }
  };

  /* ---------- tombol di panel Block Model, di bawah tombol sb_frac ---------- */
  function addBtn() {
    var g = document.getElementById('sbFracBtn');
    if (!g || document.getElementById('sbPyBtn')) return;
    var w = document.createElement('div');
    w.style.marginTop = '4px';
    w.innerHTML = '<button id=sbPyBtn style="width:100%" onclick="SBPY.ukur()" title="Menjalankan kedua versi pada data yang sama lalu membandingkan angka dan waktunya">&#9201; Bandingkan sb_frac: JavaScript vs backend Python</button>' +
      '<div class=hint style="margin-top:3px">Perhitungan yang sama sudah ada di backend Python. Tombol ini menjalankan keduanya pada data yang sama lalu melaporkan beda angka dan beda waktunya <b>di komputer ini</b> &mdash; kecepatan backend bergantung jumlah inti CPU. Atribut <code>sb_frac</code> yang dipakai aplikasi tetap hasil versi JavaScript, jadi angka laporan tidak berubah.</div>' +
      '<div class=hint id=sbPyMsg style="margin-top:3px">' + (PY.msg || '') + '</div>';
    g.parentNode.insertBefore(w, g.nextSibling);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addBtn);
  else addBtn();
  setTimeout(addBtn, 500);
  setTimeout(addBtn, 1500);
})();
