/* ================= AS-MINED: ATAP (ROOF) dari pick-up survey =================
 *
 * MASALAH YANG DIPECAHKAN. Dalam satu flitch (mis. RL240–RL238,5), elevasi atap dan lantai
 * penggalian TIDAK pernah tepat di RL nominalnya. Lantai sudah ditangani `amfloor.js`: ia
 * diinterpolasi dari titik pick-up lantai. Atapnya belum — `amCalcM` memakai `B[0]`, yaitu RL
 * atas flitch nominal, ditulis mati.
 *
 * Akibatnya sistematis dan selalu BERLEBIH, jadi tidak saling menghapus antar flitch. Kalau atap
 * sebenarnya ada di 239,78 sementara nominalnya 240,00, setiap poligon kelebihan 0,22 m setebal
 * seluruh luasnya: pada poligon 2.000 m² itu 440 m³ ≈ 1.100 t ore yang tidak pernah digali.
 *
 * ATAP = pick-up dig block / poligon ore actual yang dipasang HARI SEBELUMNYA. Titik-titiknya
 * diimpor, lalu elevasinya diringkas menjadi satu elevasi RATA per poligon (atau diinterpolasi
 * sebagai permukaan, bila atapnya memang tidak rata).
 *
 * TITIK ATAP DAN TITIK LANTAI DISIMPAN TERPISAH (`amD().ptsR` vs `amD().pts`), bukan dipisahkan
 * dari elevasinya. Memisahkannya dari elevasi justru mustahil diandalkan: seluruh sebab modul ini
 * ada adalah karena elevasinya TIDAK pasti. Kalau keduanya tercampur dalam satu awan titik, atap
 * dan lantai akan diinterpolasi dari titik yang sama dan volumenya salah tanpa tanda apa pun.
 *
 * MEDIAN, bukan rata-rata, sebagai bawaan: satu titik salah tembak (di berm, atau dari flitch
 * sebelahnya) menggeser rata-rata, median tidak. Keduanya tetap DITAMPILKAN berdampingan, sebab
 * bila keduanya berbeda lebih dari beberapa sentimeter itu adalah TANDA bahwa awan titiknya
 * berisi outlier atau atapnya sebenarnya tidak rata — angka yang layak dilihat, bukan disembunyikan.
 */

/* ---------- pilihan ---------- */
function amRoofMode() {
  var R = amR();
  return (R.roof === 'flat' || R.roof === 'pickup' || R.roof === 'dtm') ? R.roof : 'flitch';
}

function amRoofPar(B) {
  var R = amR(), fh = B[0] - B[1];
  return {
    up: Math.max(0, amNumOr(R.rfUp, 2)),                      /* ke ATAS dari RL atas flitch */
    dn: Math.max(0, amNumOr(R.rfDn, +(0.6 * fh).toFixed(2))), /* ke BAWAH dari RL atas flitch */
    buf: Math.max(0, amNumOr(R.rfBuf, 2)),
    code: String(R.rfCode || '').trim(),
    stat: (R.rfStat === 'mean') ? 'mean' : 'med'
  };
}

/* ikut kunci cache supaya mengubah pilihan atap benar-benar menghitung ulang */
function amRoofKey() {
  var R = amR();
  var m = amRoofMode();
  if (m === 'flitch') return '';
  if (m === 'dtm') {
    var M = amRoofModel();
    return '|rf:dtm,' + String(R.rfModel || '') + ',' + (M ? M.nt : 0);
  }
  return '|rf:' + [m, R.rfUp, R.rfDn, R.rfBuf, R.rfCode, R.rfStat,
                   (amD().ptsR || []).length].join(',');
}

/* ---------- titik atap untuk satu poligon ---------- */
function amRoofPts(o, B) {
  var D = amD(), P = D.ptsR || [], F = amRoofPar(B);
  /* Pita elevasi diukur dari RL ATAS flitch (bukan RL bawah seperti lantai): atap penggalian
     ada di sekitar RL atas. Batas bawahnya dijaga di atas RL bawah + 0,05 m supaya titik lantai
     yang salah masuk ke berkas atap tidak diam-diam dipakai sebagai atap. */
  var hi = B[0] + F.up, lo = Math.max(B[1] + 0.05, B[0] - F.dn);
  var b = o.b, buf = F.buf, rx = null, out = [];
  if (F.code) { try { rx = new RegExp(F.code, 'i'); } catch (e) { rx = null; } }
  for (var i = 0; i < P.length; i++) {
    var q = P[i];
    if (!isFinite(q.z) || q.z < lo || q.z > hi) continue;
    if (rx && !rx.test(q.c || '') && !rx.test(q.id || '')) continue;
    if (q.x < b[0] - buf || q.x > b[1] + buf || q.y < b[2] - buf || q.y > b[3] + buf) continue;
    if (!lyInS(o.r, q.x, q.y) && amDistPoly(o.r, q.x, q.y) > buf) continue;
    out.push(q);
  }
  return {pts: out, lo: lo, hi: hi};
}

/* ---------- fungsi atap z(x,y) satu poligon ----------
   mode 'flat'   : satu elevasi (median / rata-rata) untuk seluruh poligon
   mode 'pickup' : IDW pangkat 2, sama dengan lantai (dipakai bila atapnya memang tidak rata) */
function amRoofFn(o, B) {
  var mode = amRoofMode();
  if (mode === 'flitch') return {ok: false, n: 0, mode: mode, zmax: B[0], f: function () { return B[0]; }};
  if (mode === 'dtm') return amRoofFnDtm(o, B);
  var Q = amRoofPts(o, B), A = Q.pts, n = A.length, F = amRoofPar(B);
  if (n < 3) {
    /* Kurang dari 3 titik: jatuh ke RL atas NOMINAL, dan itu dilaporkan per poligon. Tanpa
       dilaporkan, tidak ada cara membedakan atap hasil survei dari atap asumsi. */
    return {ok: false, n: n, mode: mode, zmax: B[0], f: function () { return B[0]; }};
  }
  var z = A.map(function (q) { return q.z; }).sort(function (a, b2) { return a - b2; });
  var med = n % 2 ? z[(n - 1) / 2] : (z[n / 2 - 1] + z[n / 2]) / 2;
  var sum = 0; for (var i = 0; i < n; i++) sum += z[i];
  var mean = sum / n;
  var lo = Q.lo, hi = Q.hi;
  var out = {ok: true, n: n, mode: mode, med: med, mean: mean,
             zmin: z[0], zmax: z[n - 1], pakai: (F.stat === 'mean' ? mean : med)};
  if (mode === 'flat') {
    var zf = out.pakai;
    out.zmax = zf;
    out.f = function () { return zf; };
    return out;
  }
  /* permukaan: IDW pangkat 2, dijepit ke pita elevasi, sama dengan amFloorFn */
  var idw = function (L, x, y) {
    var sw = 0, sz = 0;
    for (var k = 0; k < L.length; k++) {
      var q = L[k], ddx = q.x - x, ddy = q.y - y, d2 = ddx * ddx + ddy * ddy;
      if (d2 < 1e-6) return q.z;
      var w = 1 / d2; sw += w; sz += w * q.z;
    }
    return sz / sw;
  };
  if (n <= 300) {
    out.f = function (x, y) { var v = idw(A, x, y); return v < lo ? lo : v > hi ? hi : v; };
  } else {
    var cs = 5, H = {}, key = function (i2, j2) { return i2 + '|' + j2; };
    A.forEach(function (q) {
      var k2 = key(Math.floor(q.x / cs), Math.floor(q.y / cs));
      (H[k2] = H[k2] || []).push(q);
    });
    out.f = function (x, y) {
      var ci = Math.floor(x / cs), cj = Math.floor(y / cs), L = [];
      for (var r = 0; r < 40 && L.length < 16; r++) {
        for (var i2 = ci - r; i2 <= ci + r; i2++) for (var j2 = cj - r; j2 <= cj + r; j2++) {
          if (Math.max(Math.abs(i2 - ci), Math.abs(j2 - cj)) !== r) continue;
          var c = H[key(i2, j2)]; if (c) L = L.concat(c);
        }
      }
      if (L.length > 16) {
        L.sort(function (a2, b2) {
          return (a2.x - x) * (a2.x - x) + (a2.y - y) * (a2.y - y)
               - (b2.x - x) * (b2.x - x) - (b2.y - y) * (b2.y - y);
        });
        L = L.slice(0, 16);
      }
      var v = idw(L, x, y); return v < lo ? lo : v > hi ? hi : v;
    };
  }
  return out;
}

/* ---------- ringkasan titik atap, untuk panel ---------- */
function amRoofStat() {
  var D = amD(), P = D.ptsR || [], B = lyBench(), F = amRoofPar(B);
  var hi = B[0] + F.up, lo = Math.max(B[1] + 0.05, B[0] - F.dn);
  var z = [], luar = 0;
  P.forEach(function (q) {
    if (!isFinite(q.z)) { luar++; return; }
    if (q.z < lo || q.z > hi) { luar++; return; }
    z.push(q.z);
  });
  z.sort(function (a, b) { return a - b; });
  var n = z.length, sum = 0;
  for (var i = 0; i < n; i++) sum += z[i];
  return {n: P.length, nPita: n, luar: luar, lo: lo, hi: hi, B: B,
          med: n ? (n % 2 ? z[(n - 1) / 2] : (z[n / 2 - 1] + z[n / 2]) / 2) : NaN,
          mean: n ? sum / n : NaN, min: z[0], max: z[n - 1]};
}

/* ---------- impor / hapus ---------- */
function amRoofFile(files) { amPtsFile(files, 'ptsR'); }
function amRoofClear() { amPtsClear('ptsR'); }

/* ---------- kotak pilihan di panel as-mined ---------- */
function amRoofBox() {
  var R = amR(), B = lyBench(), F = amRoofPar(B), mode = amRoofMode();
  var D = amD(), has = (D.ptsR || []).length > 0, S = has ? amRoofStat() : null;
  var inp = function (k, lab, ph) {
    return '<div><label>' + amE(lab) + '</label><input value="' +
      amE(R[k] === undefined ? '' : R[k]) + '" placeholder="' + amE(ph || '') +
      '" onchange="amRSet(\'' + k + '\',this.value)"></div>';
  };
  var h = '<div class=amset id=amRoofBox><div class=amst><b>Atap (roof) penggalian</b>' +
    '<small>pick-up dig block hari sebelumnya</small></div>' +
    '<div class=g2><label style="grid-column:1/-1">Titik pick-up ATAP &mdash; pick-up dig block / ' +
    'poligon ore actual hari sebelumnya. Disimpan TERPISAH dari titik lantai.</label>' +
    '<div><input type=file multiple accept=".csv,.txt,.str,.dxf" onchange="amRoofFile(this.files)"></div>' +
    '<div><button onclick="amRoofClear()"' + (has ? '' : ' disabled') + '>Hapus titik atap</button></div></div>';
  if (S) {
    var beda = (isFinite(S.med) && isFinite(S.mean)) ? Math.abs(S.med - S.mean) : NaN;
    h += '<div class=hint>' + S.n.toLocaleString() + ' titik atap, <b>' + S.nPita.toLocaleString() +
      '</b> di dalam pita RL ' + S.lo.toFixed(2) + '&ndash;' + S.hi.toFixed(2) +
      (S.luar ? ' &middot; ' + S.luar.toLocaleString() + ' di luar pita / tanpa Z (tidak dipakai)' : '') +
      '</div>';
    if (S.nPita) {
      h += '<div class=hint>Median Z <b>' + S.med.toFixed(2) + '</b> &middot; rata-rata <b>' +
        S.mean.toFixed(2) + '</b> &middot; rentang ' + S.min.toFixed(2) + '&ndash;' + S.max.toFixed(2) +
        ' &middot; RL atas nominal ' + lyFmt(B[0]) +
        ' (selisih median ' + (S.med - B[0] >= 0 ? '+' : '') + (S.med - B[0]).toFixed(2) + ' m)';
      /* Median vs rata-rata yang berbeda jauh adalah TANDA, bukan hiasan. */
      if (isFinite(beda) && beda > 0.05) {
        h += ' &middot; <span class=warn>median dan rata-rata berbeda ' + beda.toFixed(2) +
          ' m: awan titik kemungkinan berisi outlier, atau atapnya tidak rata &mdash; ' +
          'pertimbangkan mode &ldquo;ikut permukaan&rdquo;</span>';
      }
      h += '</div>';
    }
  }
  /* Luas terjepit dari perhitungan terakhir. Teks di bawah menjanjikan angka ini dilaporkan;
     kalau tidak ditampilkan, janji itu palsu dan masalah survei tetap tersembunyi. */
  if (mode !== 'flitch' && window.AM && AM.jepit && AM.jepit.a > 0.01) {
    h += '<div class=hint><span class=warn>Perhitungan terakhir: ' + AM.jepit.a.toFixed(1) +
      ' m&sup2; luas yang atapnya berada di bawah / sama dengan lantai</span> &mdash; tebalnya ' +
      'dihitung NOL di situ. Itu underdig nyata, atau titik pick-up dari hari / flitch yang ' +
      'salah. Periksa sebelum angkanya dilaporkan.</div>';
  }
  h += '<div class=amcm><label>Batas atas volume as-mined</label>' +
    '<select onchange="amRSet(\'roof\',this.value)">' +
    '<option value=flitch' + (mode === 'flitch' ? ' selected' : '') + '>RL atas flitch (nominal, rumus lama)</option>' +
    '<option value=flat' + (mode === 'flat' ? ' selected' : '') + '>Atap rata dari pick-up (satu elevasi per poligon)</option>' +
    '<option value=pickup' + (mode === 'pickup' ? ' selected' : '') + '>Atap ikut permukaan pick-up (IDW, seperti lantai)</option>' +
    '<option value=dtm' + (mode === 'dtm' ? ' selected' : '') + '>Atap dari permukaan / DTM yang sudah dimuat (menu Model)</option>' +
    '</select>';
  if (mode === 'dtm') {
    var MM = (window.MD && MD.models) ? MD.models : [];
    if (!MM.length) {
      h += '<div class=hint><span class=warn>Belum ada permukaan yang dimuat.</span> Import ' +
        'Surpac <code>.dtm</code> (bersama <code>.str</code> pasangannya), Leapfrog <code>.msh</code>, ' +
        '<code>.obj</code> atau DXF mesh lewat menu <b>Model</b>, lalu pilih di sini.</div>';
    } else {
      h += '<div style="margin-top:4px"><label>Permukaan atap</label><select onchange="amRSet(\'rfModel\',this.value)">' +
        '<option value="">— pilih —</option>' +
        MM.map(function (m) {
          return '<option' + (String(R.rfModel || '') === m.name ? ' selected' : '') + '>' +
            amE(m.name) + '</option>';
        }).join('') + '</select>';
      var M = amRoofModel();
      if (M) {
        h += '<div class=hint>' + amE(M.name) + ': ' + M.nv.toLocaleString() + ' titik, ' +
          M.nt.toLocaleString() + ' segitiga.</div>';
      }
      h += '</div>';
    }
    /* Laporan dari perhitungan terakhir: dua hal yang kalau didiamkan menyesatkan. */
    if (window.AM && AM.luarAtap) {
      if (AM.luarAtap.a > 0.01) {
        h += '<div class=hint><span class=warn>' + AM.luarAtap.a.toFixed(1) + ' m&sup2; berada DI ' +
          'LUAR jangkauan permukaan</span> &mdash; di situ dipakai RL atas flitch nominal ' +
          lyFmt(B[0]) + ', yaitu atap ASUMSI. Periksa apakah permukaannya memang tidak menjangkau ' +
          'seluruh poligon.</div>';
      }
      if (AM.luarAtap.ganda > 0) {
        h += '<div class=hint><span class=warn>' + AM.luarAtap.ganda.toLocaleString() + ' titik ' +
          'mengenai lebih dari satu segitiga</span> &mdash; yang dipilih adalah perpotongan ' +
          'terdekat ke RL atas flitch. Itu tanda objek yang dipilih kemungkinan <b>solid tertutup</b>, ' +
          'bukan permukaan; volume as-mined bisa salah tanpa memunculkan galat.</div>';
      }
    }
  }
  if (mode === 'flitch') {
    h += '<div class=hint>Rumus lama: batas atas = RL atas flitch ' + lyFmt(B[0]) +
      ' apa adanya. Bila atap penggalian sebenarnya lebih rendah, volume as-mined <b>berlebih</b>, ' +
      'dan selalu berlebih &mdash; jadi ia menumpuk antar flitch, tidak saling menghapus.</div>';
  } else if (mode !== 'dtm') {
    h += '<div class=g3 style="margin-top:4px">' +
      inp('rfUp', 'Pita ke atas RL atas (m)', '2') +
      inp('rfDn', 'Pita ke bawah RL atas (m)', String(+(0.6 * (B[0] - B[1])).toFixed(2))) +
      inp('rfBuf', 'Buffer dari poligon (m)', '2') + '</div>' +
      '<div class=g2 style="margin-top:4px">' + inp('rfCode', 'Pola kode titik (kosong = semua)', 'ROOF|RF') +
      '<div><label>Ringkasan elevasi</label><select onchange="amRSet(\'rfStat\',this.value)">' +
      '<option value=med' + (F.stat === 'med' ? ' selected' : '') + '>Median (tahan outlier)</option>' +
      '<option value=mean' + (F.stat === 'mean' ? ' selected' : '') + '>Rata-rata</option>' +
      '</select></div></div>' +
      '<div class=hint>Atap tiap poligon dihitung dari titik atap di dalam / &le; ' + F.buf +
      ' m dari poligon, dengan Z antara RL ' + Math.max(B[1] + 0.05, B[0] - F.dn).toFixed(2) +
      ' dan ' + (B[0] + F.up).toFixed(2) + '. Poligon dengan &lt; 3 titik memakai RL atas ' +
      'flitch nominal, dan disebutkan di ringkasan per poligon. Bila lantai menembus atap di suatu ' +
      'tempat (underdig, atau titik dari hari yang salah), tebalnya dihitung nol dan luas yang ' +
      'terjepit itu <b>dilaporkan</b> &mdash; menjepitnya tanpa memberi tahu akan menyembunyikan ' +
      'masalah survei sebagai angka yang kelihatan wajar.</div>';
  }
  return h + '</div></div>';
}

/* ---------- selisih volume terhitung vs volume blok penuh ----------
 * Ekspor .mdl / CSV menulis DX/DY/DZ ukuran sel PENUH, sedangkan sel di tepi poligon dan di atap /
 * lantai hanya terisi sebagian. Jadi siapa pun yang menghitung ulang volume dari dimensi blok --
 * di Surpac, misalnya, saat rekonsiliasi -- akan mendapat angka LEBIH BESAR daripada volume yang
 * dilaporkan GC-Ex. Selisih itu wajar dan ada penjelasannya, tetapi hanya kalau DITAMPILKAN.
 * Ditemukan orang lain saat rekonsiliasi, ia tampak seperti kesalahan.
 *
 * Mode atap MEMPERBESAR selisih ini: sebelumnya sel pecahan hanya di tepi poligon, sekarang atap
 * dan lantai juga menghasilkannya -- dan itu mengenai seluruh luas poligon, bukan cuma tepinya.
 */
function amVolTxt(s) {
  if (!s || !isFinite(s.volPenuh) || !isFinite(s.vol) || s.vol <= 0) return '';
  var d = s.volPenuh - s.vol, pc = d / s.vol * 100;
  if (!(d > 0.01)) return '';
  return '<div class=hint style="margin-bottom:4px">Volume terhitung <b>' +
    s.vol.toFixed(2) + ' m&sup3;</b> &middot; bila semua sel dihitung PENUH <b>' +
    s.volPenuh.toFixed(2) + ' m&sup3;</b> (+' + pc.toFixed(1) + '%). Selisihnya ada di sel ' +
    'pecahan: tepi poligon, atap dan lantai. Ekspor .mdl / CSV menulis blok berukuran penuh, ' +
    'jadi volume yang dihitung ulang dari dimensi blok akan sebesar angka kedua &mdash; ' +
    'kolom <code>FRAKSI</code> dan <code>VOLUME</code> di CSV memuat angka yang sebenarnya.</div>';
}

/* ================= ATAP DARI PERMUKAAN (DTM / mesh) =================
 * Aplikasi sudah bisa membaca Surpac .dtm (berpasangan dengan .str), Leapfrog .msh, .obj dan
 * DXF mesh lewat menu Model; hasilnya ada di MD.models sebagai jaring segitiga. Jadi atap dari
 * DTM tidak perlu pembaca berkas kedua -- ia memakai model yang sudah dimuat.
 *
 * RUANG KOORDINAT: `m.v` memakai koordinat PENUH, ruang yang sama dengan poligon as-mined dan
 * block model (mdLocal() barulah mengurangi offX/offY, dan itu hanya untuk menggambar). Jadi
 * tidak ada penggeseran di sini -- dan itu diperiksa oleh uji, bukan diandaikan.
 *
 * SATU (x,y) BISA MENGENAI LEBIH DARI SATU SEGITIGA bila yang dipilih ternyata solid tertutup,
 * bukan permukaan. Yang diambil adalah perpotongan yang PALING DEKAT ke RL atas flitch, dan
 * jumlah kejadiannya dihitung lalu dilaporkan: memilih solid sebagai atap adalah kekeliruan
 * yang masuk akal, dan diam-diam mengambil salah satu sisinya akan memberi volume yang salah
 * tanpa tanda apa pun.
 */
function amRoofModel() {
  var R = amR(), nm = String(R.rfModel || '');
  if (!nm || !window.MD || !MD.models) return null;
  for (var i = 0; i < MD.models.length; i++) if (MD.models[i].name === nm) return MD.models[i];
  return null;
}

/* indeks 2D segitiga: ember per sel grid, dibangun sekali per model (disimpan di modelnya) */
function amRoofIndex(m) {
  if (m._rfIx && m._rfIxVer === m.nt) return m._rfIx;
  var nt = m.nt, V = m.v, T = m.t;
  var x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity, i;
  for (i = 0; i < m.nv; i++) {
    var vx = V[i * 3], vy = V[i * 3 + 1];
    if (vx < x0) x0 = vx; if (vx > x1) x1 = vx;
    if (vy < y0) y0 = vy; if (vy > y1) y1 = vy;
  }
  /* sel dipilih supaya rata-rata beberapa segitiga per sel; batasi agar tidak boros memori */
  var n = Math.max(1, Math.min(400, Math.round(Math.sqrt(nt / 2))));
  var cw = Math.max(1e-6, (x1 - x0) / n), ch = Math.max(1e-6, (y1 - y0) / n);
  var H = {};
  for (var t = 0; t < nt; t++) {
    var a = T[t * 3], b = T[t * 3 + 1], c = T[t * 3 + 2];
    var ax = V[a * 3], ay = V[a * 3 + 1], bx = V[b * 3], by = V[b * 3 + 1],
        cx = V[c * 3], cy = V[c * 3 + 1];
    var i0 = Math.floor((Math.min(ax, bx, cx) - x0) / cw), i1 = Math.floor((Math.max(ax, bx, cx) - x0) / cw);
    var j0 = Math.floor((Math.min(ay, by, cy) - y0) / ch), j1 = Math.floor((Math.max(ay, by, cy) - y0) / ch);
    for (var ii = i0; ii <= i1; ii++) for (var jj = j0; jj <= j1; jj++) {
      var k = ii + '|' + jj;
      (H[k] = H[k] || []).push(t);
    }
  }
  m._rfIx = {H: H, x0: x0, y0: y0, x1: x1, y1: y1, cw: cw, ch: ch};
  m._rfIxVer = nt;
  return m._rfIx;
}

/* z permukaan di (x,y). zAcuan = RL yang dipakai memilih bila ada beberapa perpotongan.
   Kembalikan NaN bila (x,y) di luar permukaan. `cnt` (opsional) menghitung kejadian ganda. */
function amRoofZ(m, X, ix, x, y, zAcuan, cnt) {
  if (x < ix.x0 || x > ix.x1 || y < ix.y0 || y > ix.y1) return NaN;
  var L = ix.H[Math.floor((x - ix.x0) / ix.cw) + '|' + Math.floor((y - ix.y0) / ix.ch)];
  if (!L) return NaN;
  var V = m.v, T = m.t, best = NaN, bestD = Infinity, nHit = 0;
  for (var q = 0; q < L.length; q++) {
    var t = L[q], a = T[t * 3], b = T[t * 3 + 1], c = T[t * 3 + 2];
    var ax = V[a * 3], ay = V[a * 3 + 1], az = V[a * 3 + 2];
    var bx = V[b * 3], by = V[b * 3 + 1], bz = V[b * 3 + 2];
    var cx = V[c * 3], cy = V[c * 3 + 1], cz = V[c * 3 + 2];
    var d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy);
    if (Math.abs(d) < 1e-12) continue;                 /* segitiga tegak / degenerat dari atas */
    var w1 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / d;
    var w2 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / d;
    var w3 = 1 - w1 - w2;
    if (w1 < -1e-9 || w2 < -1e-9 || w3 < -1e-9) continue;
    var z = w1 * az + w2 * bz + w3 * cz;
    nHit++;
    var dd = Math.abs(z - zAcuan);
    if (dd < bestD) { bestD = dd; best = z; }
  }
  if (cnt && nHit > 1) cnt.ganda++;
  return best;
}


/* atap dari permukaan: f(x,y) mengembalikan NaN di luar permukaan, dan am2.js yang memutuskan
   apa yang terjadi di situ (jatuh ke RL nominal, dan luasnya DICATAT) -- sebab hanya di sana
   luas sel yang sebenarnya diketahui. */
function amRoofFnDtm(o, B) {
  var m = amRoofModel();
  if (!m) return {ok: false, n: 0, mode: 'dtm', zmax: B[0], f: function () { return B[0]; },
                  err: 'model permukaan belum dipilih'};
  var ix = amRoofIndex(m), b = o.b, V = m.v, T = m.t;
  /* batas atas pencarian blok: z tertinggi segitiga yang menyentuh kotak pembatas poligon */
  var zmax = -Infinity, i0 = Math.floor((b[0] - ix.x0) / ix.cw), i1 = Math.floor((b[1] - ix.x0) / ix.cw);
  var j0 = Math.floor((b[2] - ix.y0) / ix.ch), j1 = Math.floor((b[3] - ix.y0) / ix.ch), seen = {};
  for (var ii = i0; ii <= i1; ii++) for (var jj = j0; jj <= j1; jj++) {
    var L = ix.H[ii + '|' + jj];
    if (!L) continue;
    for (var q = 0; q < L.length; q++) {
      var t = L[q];
      if (seen[t]) continue;
      seen[t] = 1;
      for (var k = 0; k < 3; k++) {
        var z = V[T[t * 3 + k] * 3 + 2];
        if (z > zmax) zmax = z;
      }
    }
  }
  if (!isFinite(zmax)) zmax = B[0];
  var cnt = {ganda: 0};
  return {ok: true, n: m.nt, mode: 'dtm', nama: m.name, zmax: Math.max(zmax, B[0]), cnt: cnt,
          f: function (x, y) { return amRoofZ(m, null, ix, x, y, B[0], cnt); }};
}
