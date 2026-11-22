/* bmrot.js — block model terotasi (rotasi bearing / sumbu Z), BM 0.24.112.
   Pemilik 22 Nov 2026: "Bagaimana agar GC-Ex bisa memproses block model yang terotasi? Misalnya ketika import block
   model, ditentukan rotasi yang diterapkan." Jawaban pemilik: rotasi yang dipakai di site = bearing saja; contoh .mdl
   terotasi dari Surpac belum ada -> tahap ini lewat import CSV dengan isian rotasi.

   Konvensi (sama dengan Surpac): Bearing = azimuth sumbu X model, searah jarum jam dari utara; 90 = tidak diputar.
     sumbu X model di lapangan ex = (sin b, cos b); sumbu Y model ey = (-cos b, sin b).
   Penyimpanan: m.x / m.y SELALU koordinat lapangan (pusat blok), m.sx / m.sy tetap ukuran blok searah sumbu model,
   m.rot = {b, ex, ey, mode, px, py}. Semua perhitungan berbasis pusat blok (batas pit / topografi / domain, laporan,
   statistik, tonase = volume x SG) otomatis benar karena volume blok tidak berubah oleh rotasi.
   Yang dihitung ulang memperhitungkan rotasi: kubus 3D (bxTraces, dihitung di kerangka lokal lalu diputar), sayatan 2D
   (bxTraces2D: denah = persegi panjang miring), pemilihan blok dalam slab (bxSlabHit), jejak bukaan topografi (topopit_bm).
   Alat berbasis grid sumbu-lapangan (dig block otomatis, garis luar blok, snap sudut blok, komposit flitch, as-mined)
   BELUM mendukung model terotasi: dicegat di sini dengan pesan, bukan memberi angka yang salah. */
(function () {
  'use strict';
  var RAD = Math.PI / 180;
  var normB = function (b) { b = ((+b % 360) + 360) % 360; return b; };
  var sumbu = function (b) { var r = b * RAD; return { ex: [Math.sin(r), Math.cos(r)], ey: [-Math.cos(r), Math.sin(r)] }; };
  var lokCache = new WeakMap();

  var BMR = window.BMR = {
    /* rot = {b: bearing (deg), mode: 'dunia' | 'lokal', px, py}; dipanggil SA.buildBM setelah koordinat terbaca */
    terapkan: function (m, rot) {
      if (!rot || !isFinite(+rot.b)) return m;
      var b = normB(rot.b); if (Math.abs(b - 90) < 1e-9) return m;           /* 90 = tidak diputar */
      var A = sumbu(b), n = m.n, i;
      var px = rot.px, py = rot.py;
      if (rot.mode === 'lokal') {
        /* koordinat file = koordinat lokal model; diputar terhadap titik putar (bawaan: sudut minimum model) */
        if (!(isFinite(px) && px !== null && px !== '') || !(isFinite(py) && py !== null && py !== '')) {
          var x0 = Infinity, y0 = Infinity;
          for (i = 0; i < n; i++) { var a = m.x[i] - m.sx[i] / 2, c = m.y[i] - m.sy[i] / 2; if (a < x0) x0 = a; if (c < y0) y0 = c; }
          px = x0; py = y0;
        }
        px = +px; py = +py;
        for (i = 0; i < n; i++) {
          var dx = m.x[i] - px, dy = m.y[i] - py;
          m.x[i] = px + dx * A.ex[0] + dy * A.ey[0];
          m.y[i] = py + dx * A.ex[1] + dy * A.ey[1];
        }
      }
      m.rot = { b: b, ex: A.ex, ey: A.ey, mode: rot.mode === 'lokal' ? 'lokal' : 'dunia', px: rot.mode === 'lokal' ? px : null, py: rot.mode === 'lokal' ? py : null };
      /* batas model (m.ext) dihitung SA.buildBM sesudah ini dari pusat blok yang sudah diputar */
      return m;
    },

    /* tampilan kerangka lokal (untuk menggambar kubus): x / y lokal terhadap P0 = (ext[0], ext[2]); ke(lx,ly) -> lapangan */
    lokal: function (m) {
      var R = m.rot; if (!R) return null;
      var c = lokCache.get(m); if (c) return c;
      var n = m.n, P0 = [m.ext[0], m.ext[2]], X = new Float64Array(n), Y = new Float64Array(n), e = [1e18, -1e18, 1e18, -1e18, m.ext[4], m.ext[5]];
      for (var i = 0; i < n; i++) {
        var dx = m.x[i] - P0[0], dy = m.y[i] - P0[1], lx = dx * R.ex[0] + dy * R.ex[1], ly = dx * R.ey[0] + dy * R.ey[1];
        X[i] = lx; Y[i] = ly; if (lx < e[0]) e[0] = lx; if (lx > e[1]) e[1] = lx; if (ly < e[2]) e[2] = ly; if (ly > e[3]) e[3] = ly;
      }
      var v = { n: n, x: X, y: Y, z: m.z, sx: m.sx, sy: m.sy, sz: m.sz, ext: e, s0: m.s0, num: m.num, cat: m.cat };
      c = { m: v, ke: function (lx, ly) { return [P0[0] + lx * R.ex[0] + ly * R.ey[0], P0[1] + lx * R.ex[1] + ly * R.ey[1]]; } };
      lokCache.set(m, c); return c;
    },

    /* setengah lebar blok di sumbu X / Y lapangan (untuk kotak pembatas) */
    hx: function (m, i) { var R = m.rot; return R ? (m.sx[i] * Math.abs(R.ex[0]) + m.sy[i] * Math.abs(R.ey[0])) / 2 : m.sx[i] / 2; },
    hy: function (m, i) { var R = m.rot; return R ? (m.sx[i] * Math.abs(R.ex[1]) + m.sy[i] * Math.abs(R.ey[1])) / 2 : m.sy[i] / 2; },

    teks: function (m) { var R = m && m.rot; if (!R) return ''; return 'Rotasi: bearing ' + (+R.b.toFixed(3)) + '° (sumbu X model)' + (R.mode === 'lokal' ? ', diputar dari koordinat lokal terhadap titik ' + R.px.toFixed(2) + ' / ' + R.py.toFixed(2) : ', koordinat file sudah koordinat lapangan'); },

    dlgHTML: function () {
      return '<div class=cmh>Rotasi model (opsional)</div><div class=cm>' +
        '<div><label>Bearing sumbu X model (seperti Surpac; 90 = tidak diputar)</label><input type=number step=any id=bxrb value=90></div>' +
        '<div><label>Koordinat X / Y di file adalah</label><select id=bxrm onchange="var e=document.getElementById(\'bxrpw\');if(e)e.style.display=this.value===\'lokal\'?\'\':\'none\'">' +
        '<option value=dunia>Koordinat lapangan (pusat blok sudah benar; hanya arah blok yang diputar)</option>' +
        '<option value=lokal>Koordinat lokal model (diputar ke lapangan terhadap titik putar)</option></select></div>' +
        '<div id=bxrpw style=display:none><label>Titik putar X / Y (koordinat lokal; kosong = sudut minimum model)</label>' +
        '<div style="display:flex;gap:6px"><input type=number step=any id=bxrpx placeholder=X><input type=number step=any id=bxrpy placeholder=Y></div></div></div>';
    },
    dlgGet: function () {
      var e = document.getElementById('bxrb'); if (!e || e.value === '') return null;
      var b = +e.value; if (!isFinite(b)) return null;
      if (Math.abs(normB(b) - 90) < 1e-9) return null;
      var g = function (id) { var v = document.getElementById(id); return v && v.value !== '' && isFinite(+v.value) ? +v.value : null; };
      return { b: b, mode: (document.getElementById('bxrm') || {}).value === 'lokal' ? 'lokal' : 'dunia', px: g('bxrpx'), py: g('bxrpy') };
    }
  };

  /* ---- alat berbasis grid sumbu-lapangan: belum mendukung model terotasi ---- */
  var PESAN = 'Block model ini terotasi. Fitur ini (dig block otomatis, garis luar blok, snap sudut blok, komposit / tonase flitch, as-mined) belum mendukung block model terotasi — hasilnya akan salah, jadi dihentikan. Tampilan 3D, sayatan, filter, statistik dan laporan grade × tonase tetap bisa dipakai.';
  var sudah = false;
  var beritahu = function (keras) { if (keras) { alert(PESAN); return; } if (sudah) return; sudah = true; try { if (window.msg) msg(PESAN, true); } catch (e) { } };
  var cegat = function (nm, keras, nilai) {
    var f = window[nm]; if (typeof f !== 'function') return;
    var g = function () { if (window.BX && BX.m && BX.m.rot) { beritahu(keras); return nilai; } return f.apply(this, arguments); };
    try { window[nm] = g; } catch (e) { }
  };
  [['amRun', true], ['dbAuto', true], ['bxOutline', true], ['lyTon', false, null], ['lyComp', false, null],
   ['dbCorners', false, null], ['bxCorners', false, null], ['dmBMPick', false]].forEach(function (a) { cegat(a[0], a[1], a[2]); });
})();
