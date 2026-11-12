/* ================= REPORTING BM: PROPORSI VOLUME BLOK TERHADAP PERMUKAAN (cara GC-Ex) =================
   Dipakai GC-Ex Block Model dan GC-Ex Drill Hole (rpRun milik masing-masing aplikasi).

   Cara Surpac (BAWAAN, dipakai untuk audit): constraint topografi / desain pit / DTM diuji pada TITIK PUSAT blok,
   blok masuk 100% atau keluar 100%.
   Cara GC-Ex (pilihan): telapak blok dibagi n x n kolom kecil. Di tiap kolom dicari selang Z yang lolos SEMUA batas
   permukaan (di bawah topografi, di atas desain pit, di atas / di bawah tiap DTM tambahan), lalu dihitung panjang
   bagian kolom [dasar blok, atap blok] yang berada di selang itu. Proporsi blok = rata-rata panjang itu / tinggi blok.
   Kolom yang berada di luar jangkauan salah satu permukaan dihitung 0 (sama dengan cara Surpac: di luar DTM = tidak
   lolos). Di dalam satu kolom permukaan dianggap datar (nilai Z di pusat kolom), jadi galatnya mengecil dengan n.

   RPSF.make({tz, pz, sx:[{fn, side}], ox, oy, n}) -> function(xl, yl, z, sx, sy, sz) -> {f: 0..1, ext: bool}
     tz(xl,yl) / pz(xl,yl) : Z atap (topografi) / lantai (desain pit) di koordinat LOKAL, null = di luar jangkauan
     sx[j].fn(xw,yw)       : [z min, z maks] DTM di koordinat DUNIA (rpTinFn), side 'above' | 'below'
     ox, oy                : offset lokal -> dunia
     ext                   : true bila SEMUA kolom di luar jangkauan permukaan (dilaporkan sebagai "di luar DTM")  */
(function () {
  if (window.RPSF) return;
  window.RPSF = {
    make: function (S) {
      var n = Math.max(1, Math.min(10, (S.n | 0) || 4)), C = new Map(), sxl = S.sx || [];
      function selang(xl, yl) {
        var k = Math.round(xl * 20) + '|' + Math.round(yl * 20), r = C.get(k);
        if (r !== undefined) return r;
        var lo = -Infinity, hi = Infinity, ok = true;
        if (S.tz) { var t = S.tz(xl, yl); if (t == null || !isFinite(t)) ok = false; else hi = t; }
        if (ok && S.pz) { var p = S.pz(xl, yl); if (p == null || !isFinite(p)) ok = false; else lo = p; }
        for (var j = 0; ok && j < sxl.length; j++) {
          var q = sxl[j], r2 = q.fn(xl + S.ox, yl + S.oy);
          if (!r2) { ok = false; break; }
          if (q.side === 'above') lo = Math.max(lo, r2[0]); else hi = Math.min(hi, r2[1]);
        }
        r = ok ? [lo, hi] : null; C.set(k, r); return r;
      }
      return function (xl, yl, z, bx, by, bz) {
        var zb = z - bz / 2, zt = z + bz / 2, s = 0, luar = 0;
        for (var a = 0; a < n; a++) for (var b = 0; b < n; b++) {
          var r = selang(xl + ((a + 0.5) / n - 0.5) * bx, yl + ((b + 0.5) / n - 0.5) * by);
          if (!r) { luar++; continue; }
          var d = Math.min(r[1], zt) - Math.max(r[0], zb);
          if (d > 0) s += Math.min(d, bz);
        }
        var f = s / (n * n * bz);
        return { f: f > 0.9999 ? 1 : f < 1e-6 ? 0 : f, ext: luar === n * n };
      };
    }
  };
  /* pilihan di tab Constraint (sama di kedua aplikasi); rpSet global di keduanya */
  RPSF.ui = function (o) {
    var on = o.sfrac === true, n = +o.sfN || 4;
    var h = '<h4>Blok di batas permukaan</h4><div class="g3 f"><div style="grid-column:span 2"><select onchange="rpSet(\'sfrac\',this.value===\'1\')">' +
      '<option value=0' + (on ? '' : ' selected') + '>Cara Surpac &mdash; titik pusat blok (bawaan)</option>' +
      '<option value=1' + (on ? ' selected' : '') + '>Cara GC-Ex &mdash; proporsi volume blok</option></select></div><div>' +
      (on ? '<select title="Telapak blok dibagi n &times; n kolom" onchange="rpSet(\'sfN\',+this.value)">' + [2, 4, 6, 8].map(function (k) {
        return '<option value=' + k + (k === n ? ' selected' : '') + '>' + k + '&times;' + k + ' kolom</option>'; }).join('') + '</select>' : '') + '</div></div>';
    h += '<div class=hint style="margin-top:-4px">' + (on
      ? 'Blok yang terpotong topografi, desain pit atau batas DTM dihitung <b>sebagian</b>: telapaknya dibagi ' + n + '&times;' + n +
        ' kolom dan tonase ditimbang dengan bagian kolom yang lolos semua batas. <span class=warn>Angka ini tidak sama dengan report Surpac</span>; ' +
        'untuk audit / rekonsiliasi kembalikan ke cara Surpac. Bandingkan keduanya di tab <b>Metode tonase</b>.'
      : 'Blok dihitung <b>utuh</b> bila titik pusatnya lolos batas permukaan &mdash; sama dengan report Surpac (angka untuk audit). ' +
        'Blok di luar jangkauan topografi / pit / DTM tidak dilaporkan.') + '</div>';
    return h;
  };
})();
