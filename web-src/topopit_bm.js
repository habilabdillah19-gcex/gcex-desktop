/* ================= GC-Ex Block Model 0.24.73 — TOPO × PIT, BATAS PERMUKAAN BLOK, BUKA ATAP, LEGENDA =================
   Permintaan pemilik 13 Nov 2026: "menampilkan Topografi yang sudah terpotong (patch) dengan Desain Pit, kemudian di
   dalamnya Block Model pulau As-Mined, Block Model asli (difilter), atau Solid Vein di Display 3D" + legenda seperti
   contoh (kartu bersekat: judul bagian, kotak warna, tombol kecilkan / tutup). Keputusan diskusi: TIDAK ada filter kadar
   baru (filter & kelas tetap di menu Block Model yang sudah ada), tampilan blok tetap seperti sebelumnya.

   A. PERMUKAAN GABUNGAN TOPO × PIT (Project Tree › Data Referensi › Permukaan, menu "+ Tambah data referensi")
      Di setiap titik dipakai permukaan yang LEBIH RENDAH antara topografi dan desain pit (seperti menggabungkan dua DTM
      Surpac, ambil yang lebih rendah). Sumber = topografi & desain pit Data Spasial (OV.topoF / OV.pitF) — SAMA dengan
      yang dipakai Reporting, tampilan dan hitungan selalu sejalan. Segitiga TIN topografi dan pit ditumpang-susun
      (overlay) tepat: tiap potongan memakai bidang yang lebih rendah, garis potong (daylight) lurus di tiap potongan. Interpolasi Z memakai TIN yang sama dengan tampilan/hitungan (tinz.js).
      Hasil = satu model permukaan (MD.models, jenis 'surf'): ikut tersimpan di proyek, bisa dipilih di Reporting
      (Permukaan DTM), diwarnai dua nada (warna topo & warna pit Overlay) dengan hillshade, dan diekspor DTM + STR.
   B. BATAS PERMUKAAN (menu Block Model, di bawah "Tampilkan bila (cut-off)")
      Semua blok | Di bawah topo × pit (sisa in-situ) | Di antara topo & pit (yang akan ditambang). Titik pusat blok
      (cara Surpac, sama dengan Reporting); di luar cakupan topografi blok tidak lolos. Bekerja bersama filter & kelas yang
      ada; tabel ringkasan kelas ikut. As-Mined / Solid Vein memakai filter yang sama.
   C. BUKA ATAP (panel Overlay) + transparansi desain pit sendiri
      Segitiga permukaan (topo, pit, permukaan DTM termasuk gabungan) yang berada DI ATAS blok yang sedang ditampilkan
      (titik berat segitiga lebih tinggi dari atap blok di kolom itu) disembunyikan (jarak tepi bisa diatur); lantai pit di
      bawah blok tetap tampil, sehingga isi di bawah permukaan terlihat. Hanya tampilan.
   D. LEGENDA (kartu di pojok kanan bawah grafik 3D): Block model (kelas tampil), Permukaan, Wireframe & solid,
      Lapisan lain. Tombol − (kecilkan) / × (tutup, buka lagi lewat tombol "Legenda"). Legenda bawaan Plotly dimatikan
      selama kartu ini aktif. */
(function () {
  if (window.TP || typeof MD === 'undefined') return;
  var TP = window.TP = { NAMA: 'Topo × Pit (gabungan)', eps: 1e-3, faktor: 8 };
  var E = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var ada = function (o) { return o && o.x && o.x.length > 2; };
  /* SUMBER (bisa dipilih di kotak Topo × Pit): 'ov:topo' / 'ov:pit' = Data Spasial (sama dengan Reporting), atau
     'md:<nama>' = permukaan DTM di Data Referensi (mis. desain pit .dtm Surpac — segitiganya dipakai apa adanya, tidak
     ditriangulasi ulang, sehingga garis jenjang desain tetap). */
  TP.cfg = { t: '', p: '' };
  var mdSurf = function (nm) { for (var i = 0; i < MD.models.length; i++) { var m = MD.models[i]; if (m.jenis === 'surf' && !m.gab && m.name === nm) return m; } return null; };
  TP.daftar = function () { var L = []; if (window.OV && ada(OV.topoF)) L.push(['ov:topo', 'Data Spasial: topografi']); if (window.OV && ada(OV.pitF)) L.push(['ov:pit', 'Data Spasial: desain pit']);
    MD.models.forEach(function (m) { if (m.jenis === 'surf' && !m.gab && m.nt) L.push(['md:' + m.name, (m.survei ? 'Survei: ' : 'Permukaan DTM: ') + m.name]); }); return L; };
  var adaKey = function (k) { return TP.daftar().some(function (x) { return x[0] === k; }); };
  TP.kunci = function (peran) { var m = TP.model(), k = TP.cfg[peran] || (m && m.gab && m.gab.src && m.gab.src[peran]) || '';
    if (k && adaKey(k)) return k; var L = TP.daftar(), re = peran === 't' ? /topo|asbuilt|as-built|survey|survei/i : /pit|desain|design/i;
    if (adaKey(peran === 't' ? 'ov:topo' : 'ov:pit')) return peran === 't' ? 'ov:topo' : 'ov:pit';
    for (var i = 0; i < L.length; i++) if (/^md:/.test(L[i][0]) && re.test(L[i][0])) return L[i][0]; return ''; };
  TP.srcT = function () { return TP.kunci('t') ? TP.kunci('t') : null; };
  TP.srcP = function () { return TP.kunci('p') ? TP.kunci('p') : null; };
  var nama = function (k) { return !k ? '-' : k === 'ov:topo' ? 'topografi Data Spasial' : k === 'ov:pit' ? 'desain pit Data Spasial' : k.slice(3); };
  /* tanda sumber: jumlah titik + beberapa koordinat (data baru = tanda baru) */
  var sigO = function (o) { if (!o) return ''; var n = o.x.length, s = n + ''; [0, n >> 2, n >> 1, n - 1].forEach(function (i) { s += ':' + o.x[i] + ',' + o.y[i] + ',' + o.z[i]; }); return s; };
  TP.sig = function (k) { if (!k) return ''; if (k === 'ov:topo') return k + sigO(window.OV && OV.topoF); if (k === 'ov:pit') return k + sigO(window.OV && OV.pitF);
    var m = mdSurf(k.slice(3)); return m ? k + ':' + m.nv + ':' + m.nt + ':' + m.v[0] + ':' + m.v[m.v.length - 1] : ''; };
  /* TIN sumber: {x,y,z,i,j,k,n} koordinat lokal */
  TP.tin = function (k) { if (k === 'ov:topo') return TIN.build(TIN.rapat ? TIN.rapat(OV.topoF, 2) : OV.topoF);   /* 0.24.77: topografi string dirapatkan seperti pit & Reporting (rpSurf) */ if (k === 'ov:pit') return TIN.build(TIN.rapat ? TIN.rapat(OV.pitF, 2) : OV.pitF); var m = k && mdSurf(k.slice(3)); if (!m) return null; mdLocal(m);
    return { x: m._x, y: m._y, z: m._z, i: m._i, j: m._j, k: m._k, n: m.nv }; };
  TP.model = function () { for (var i = 0; i < MD.models.length; i++) if (MD.models[i].gab) return MD.models[i]; return null; };
  TP.usang = function (m) { m = m || TP.model(); if (!m || !m.gab) return false; var s = m.gab.src || { t: 'ov:topo', p: 'ov:pit' }; return m.gab.t !== TP.sig(s.t) || m.gab.p !== TP.sig(s.p); };
  /* Z permukaan di (x,y) lokal: null = di luar cakupan. Data Spasial: TIN tinz.js (sama dengan Reporting); DTM: segitiganya
     sendiri (bila bertumpuk di proyeksi, ambil yang terendah). */
  var zf = function (k) {
    if (k === 'ov:topo' || k === 'ov:pit') { var o0 = k === 'ov:topo' ? OV.topoF : OV.pitF, o = o0 && window.TIN && TIN.rapat ? TIN.rapat(o0, 2) : o0, t = o && window.TINZ && TINZ.of ? TINZ.of(o, o !== o0 && o.x.length > o0.x.length) : null; return t ? function (x, y) { var v = t.f(x, y); return v != null && isFinite(v) ? v : null; } : function () { return null; }; }
    var ms = k && /^md:/.test(k) ? mdSurf(k.slice(3)) : null; if (ms && ms.pts && ms.pts.x && ms.pts.x.length && window.TINZ && TINZ.of) { var tz = TINZ.of(ms.pts); if (tz) return function (x, y) { var v = tz.f(x, y); return v != null && isFinite(v) ? v : null; }; }
    var tin = k ? TP.tin(k) : null; if (!tin) return function () { return null; }; var L = segi(tin), q = indeks(L);
    return function (x, y) { var C = q([x, x, y, y]), p = [x, y], best = null; for (var r = 0; r < C.length; r++) { var t = L[C[r]]; if (!t.z) continue; var H = t.H; if (H[0](p) <= 1e-9 && H[1](p) <= 1e-9 && H[2](p) <= 1e-9) { var z = t.z(p); if (best === null || z < best) best = z; } } return best; }; };

  TP.zf = function (k) { return zf(k); };
  /* ---------- A. bangun permukaan gabungan ---------- */
  /* Tumpang-susun (overlay) dua TIN, tepat: setiap segitiga topografi dipotong dengan segitiga pit yang menindihnya
     (poligon cembung). Di setiap potongan kedua permukaan berupa bidang datar, jadi garis potong d = z_topo − z_pit = 0
     lurus dan dihitung tepat; bagian yang lebih rendah dipakai. Bagian segitiga topo yang tidak ditindih pit = topo saja,
     bagian segitiga pit tanpa topo = pit saja. Tidak ada triangulasi ulang, sehingga jenjang (crest / toe) pit dan lekuk
     topografi tidak terpotong (versi awal memakai Delaunay ulang: menyimpang sampai 10 m di jenjang pit data nyata Zona 2). */
  var luas = function (P) { var s = 0; for (var i = 0, n = P.length; i < n; i++) { var j = (i + 1) % n; s += P[i][0] * P[j][1] - P[j][0] * P[i][1]; } return s / 2; };
  var potongHP = function (P, f) { var o = [], n = P.length; if (!n) return o; for (var i = 0; i < n; i++) { var c = P[i], p = P[(i + n - 1) % n], dc = f(c), dp = f(p);
      if (dc <= 0) { if (dp > 0) { var t = dp / (dp - dc); o.push([p[0] + (c[0] - p[0]) * t, p[1] + (c[1] - p[1]) * t]); } o.push(c); } else if (dp <= 0) { var t2 = dp / (dp - dc); o.push([p[0] + (c[0] - p[0]) * t2, p[1] + (c[1] - p[1]) * t2]); } } return o; };
  var sisi = function (Q) { var H = []; for (var e = 0; e < 3; e++) (function (a, b) { H.push(function (q) { return -((b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])); }); })(Q[e], Q[(e + 1) % 3]); return H; };
  var irisan = function (A, H) { for (var e = 0; e < 3 && A.length; e++) A = potongHP(A, H[e]); return A; };
  var kurang = function (A, H, out) { for (var e = 0; e < 3 && A.length > 2; e++) { var luar = potongHP(A, function (q) { return -H[e](q); }); if (luar.length > 2 && Math.abs(luas(luar)) > 1e-9) out.push(luar); A = potongHP(A, H[e]); } };
  var bidang = function (x, y, z, a, b, c) { var ux = x[b] - x[a], uy = y[b] - y[a], uz = z[b] - z[a], vx = x[c] - x[a], vy = y[c] - y[a], vz = z[c] - z[a], nz = ux * vy - uy * vx; if (Math.abs(nz) < 1e-12) return null;
    var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz; return function (q) { return z[a] - (nx * (q[0] - x[a]) + ny * (q[1] - y[a])) / nz; }; };
  var segi = function (tin) { var n = tin.i.length, L = new Array(n); for (var q = 0; q < n; q++) { var a = tin.i[q], b = tin.j[q], c = tin.k[q], Q = [[tin.x[a], tin.y[a]], [tin.x[b], tin.y[b]], [tin.x[c], tin.y[c]]];
      if (luas(Q) < 0) { Q.reverse(); } if (Math.abs(luas(Q)) < 1e-9) { L[q] = null; continue; } L[q] = { Q: Q, H: sisi(Q), z: bidang(tin.x, tin.y, tin.z, a, b, c), b: [Math.min(Q[0][0], Q[1][0], Q[2][0]), Math.max(Q[0][0], Q[1][0], Q[2][0]), Math.min(Q[0][1], Q[1][1], Q[2][1]), Math.max(Q[0][1], Q[1][1], Q[2][1])] }; } return L; };
  var indeks = function (L) { var x0 = 1e18, x1 = -1e18, y0 = 1e18, y1 = -1e18, s = 0, k = 0; L.forEach(function (t) { if (!t) return; x0 = Math.min(x0, t.b[0]); x1 = Math.max(x1, t.b[1]); y0 = Math.min(y0, t.b[2]); y1 = Math.max(y1, t.b[3]); s += (t.b[1] - t.b[0]) + (t.b[3] - t.b[2]); k++; });
    if (!k) return function () { return []; }; var cs = Math.max(0.5, s / k / 2), gx, gy; while (true) { gx = Math.floor((x1 - x0) / cs) + 1; gy = Math.floor((y1 - y0) / cs) + 1; if (gx * gy <= 4e6) break; cs *= 1.5; }
    var G = new Map(); L.forEach(function (t, q) { if (!t) return; for (var u = Math.floor((t.b[0] - x0) / cs); u <= Math.floor((t.b[1] - x0) / cs); u++) for (var w = Math.floor((t.b[2] - y0) / cs); w <= Math.floor((t.b[3] - y0) / cs); w++) { var key = w * gx + u, a = G.get(key); if (a) a.push(q); else G.set(key, [q]); } });
    var cap = new Uint32Array(L.length), cap0 = 0;
    return function (b) { cap0++; var o = []; if (b[1] < x0 || b[0] > x1 || b[3] < y0 || b[2] > y1) return o; for (var u = Math.max(0, Math.floor((b[0] - x0) / cs)); u <= Math.min(gx - 1, Math.floor((b[1] - x0) / cs)); u++) for (var w = Math.max(0, Math.floor((b[2] - y0) / cs)); w <= Math.min(gy - 1, Math.floor((b[3] - y0) / cs)); w++) { var a = G.get(w * gx + u); if (!a) continue;
        for (var r = 0; r < a.length; r++) { var q = a[r], t = L[q]; if (cap[q] === cap0) continue; cap[q] = cap0; if (t.b[1] < b[0] || t.b[0] > b[1] || t.b[3] < b[2] || t.b[2] > b[3]) continue; o.push(q); } } return o; };
  };
  TP.bangun = function (kT, kP) {
    var tT = TP.tin(kT), tP = TP.tin(kP); if (!tT || !tP) throw new Error('topografi / desain pit belum bisa ditriangulasi');
    var LT = segi(tT), LP = segi(tP), qT = indeks(LT), qP = indeks(LP), eps = TP.eps;
    var X = [], Y = [], Z = [], M = new Map(), TR = [], SRC = [], nC = 0;
    /* titik disatukan bila X, Y DAN Z sama (mm): topo & pit bisa bertemu di XY yang sama dengan Z berbeda (tepi DTM) */
    var titik = function (x, y, z) { var k = Math.round(x * 1000) + ':' + Math.round(y * 1000) + ':' + Math.round(z * 1000), j = M.get(k); if (j !== undefined) return j; M.set(k, X.length); X.push(x); Y.push(y); Z.push(z); return X.length - 1; };
    var simpan = function (Pg, zf, s) { if (Pg.length < 3 || Math.abs(luas(Pg)) < 1e-6) return; var id = Pg.map(function (q) { return titik(q[0], q[1], zf(q)); });
      for (var r = 1; r + 1 < id.length; r++) { if (id[0] === id[r] || id[r] === id[r + 1] || id[0] === id[r + 1]) continue; TR.push(id[0], id[r], id[r + 1]); SRC.push(s); } };
    var q, r;
    /* 1. segitiga topografi */
    for (q = 0; q < LT.length; q++) { var t = LT[q]; if (!t || !t.z) continue; var C = qP(t.b), sisa = [t.Q];
      for (r = 0; r < C.length; r++) { var p = LP[C[r]]; if (!p.z) continue; var baru = [];
        for (var s = 0; s < sisa.length; s++) { var A = sisa[s], I = irisan(A, p.H); if (I.length > 2 && Math.abs(luas(I)) > 1e-9) {
            var zt = t.z, zp = p.z, d = function (q2) { return zt(q2) - zp(q2); }, bawahT = potongHP(I, d), bawahP = potongHP(I, function (q2) { return -d(q2); });
            if (bawahT.length > 2 && bawahP.length > 2 && Math.abs(luas(bawahT)) > 1e-6 && Math.abs(luas(bawahP)) > 1e-6) nC++;
            simpan(bawahT, zt, 0); simpan(bawahP, zp, 1); kurang(A, p.H, baru); } else baru.push(A); }
        sisa = baru; if (!sisa.length) break; }
      for (r = 0; r < sisa.length; r++) simpan(sisa[r], t.z, 0); }
    /* 2. bagian segitiga pit yang tidak ditindih topografi (desain di luar cakupan survei) */
    for (q = 0; q < LP.length; q++) { var pp = LP[q]; if (!pp || !pp.z) continue; var C2 = qT(pp.b), sisa2 = [pp.Q];
      for (r = 0; r < C2.length && sisa2.length; r++) { var tt = LT[C2[r]]; if (!tt) continue; var baru2 = []; for (var s2 = 0; s2 < sisa2.length; s2++) kurang(sisa2[s2], tt.H, baru2); sisa2 = baru2; }
      for (r = 0; r < sisa2.length; r++) simpan(sisa2[r], pp.z, 1); }
    var n = X.length; if (n < 3 || !TR.length) throw new Error('permukaan gabungan kosong');
    var v = new Float64Array(3 * n); for (var i = 0; i < n; i++) { v[3 * i] = X[i] + offX; v[3 * i + 1] = Y[i] + offY; v[3 * i + 2] = Z[i]; }
    return { v: v, t: Uint32Array.from(TR), nv: n, nt: TR.length / 3, fsrc: Uint8Array.from(SRC), nC: nC };
  };
  TP.gabung = function () {
    var T = TP.srcT(), P = TP.srcP(), el = E('tpMsg');
    var tulis = function (h) { if (el) el.innerHTML = h; };
    if (!T || !P || T === P) { var w = T && T === P ? 'Topografi dan desain pit tidak boleh permukaan yang sama.' : 'Perlu topografi DAN desain pit (Data Spasial, atau permukaan DTM di Data Referensi). Belum ada: ' + [!T ? 'topografi' : '', !P ? 'desain pit' : ''].filter(Boolean).join(' & ') + '.'; tulis('<span class=warn>' + w + '</span>'); if (!el) alert(w); return null; }
    tulis('Menghitung ' + esc(TP.NAMA) + '&hellip;');
    var t0 = performance.now(), R;
    try { R = TP.bangun(T, P); } catch (e) { console.error(e); tulis('<span class=warn>Gagal: ' + esc(e.message) + '</span>'); return null; }
    var old = TP.model(), m = old || { name: TP.NAMA, jenis: 'surf', col: (E('ovTopoCol') || {}).value || '#a7b58a', op: 1, vis: true };
    m.v = R.v; m.t = R.t; m.nv = R.nv; m.nt = R.nt; m.fsrc = R.fsrc; m.jenis = 'surf'; m.vis = true;
    ['_x', '_y', '_z', '_i', '_j', '_k', '_hsF', '_hsK', '_tpK', '_tpF'].forEach(function (k) { delete m[k]; });
    m.gab = { t: TP.sig(T), p: TP.sig(P), src: { t: T, p: P }, at: new Date().toISOString(), nC: R.nC, ms: Math.round(performance.now() - t0) };
    if (!old) MD.models.push(m);
    /* topo & pit Overlay dimatikan supaya tidak bertumpuk dengan permukaan gabungan (bisa dinyalakan lagi) */
    if (T === 'ov:topo') { var c1 = E('ovTopoS'); if (c1) c1.checked = false; } if (P === 'ov:pit') { var c2 = E('ovPit'); if (c2) c2.checked = false; }
    [T, P].forEach(function (k) { var s2 = /^md:/.test(k) && mdSurf(k.slice(3)); if (s2) s2.vis = false; });
    tulis('&#10003; ' + esc(TP.NAMA) + ': ' + R.nv.toLocaleString('id-ID') + ' titik, ' + R.nt.toLocaleString('id-ID') + ' segitiga, ' + R.nC.toLocaleString('id-ID') + ' titik garis potong (' + m.gab.ms + ' ms). Sumber: ' + esc(nama(T)) + ' &times; ' + esc(nama(P)) + ' (tampilan sumbernya dimatikan; nyalakan lagi bila perlu).');
    BX && (BX._tpM = null); mdBump(); try { if (window.PT) PT.render(true); } catch (e) { } TP.box();
    return m;
  };
  /* ekspor DTM + STR (OBJECT / TRISOLATION) seperti ekspor Solid Vein */
  TP.ekspor = function (m) {
    m = m || TP.model(); if (!m) { alert('Belum ada permukaan gabungan.'); return; }
    var nm = String(m.name).replace(/[^A-Za-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '') || 'TopoPit', d = new Date(), tg = ('0' + d.getDate()).slice(-2) + '-' + ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][d.getMonth()] + '-' + String(d.getFullYear()).slice(-2);
    var S = [nm + ',' + tg + ',,ssi_styles:styles.ssi', '0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000'];
    for (var i = 0; i < m.nv; i++) S.push('1, ' + m.v[3 * i + 1].toFixed(3) + ', ' + m.v[3 * i].toFixed(3) + ', ' + m.v[3 * i + 2].toFixed(3) + ',');
    S.push('0, 0.000, 0.000, 0.000,', '0, 0.000, 0.000, 0.000, END');
    var D = [nm + '.str,', '0, 0.000, 0.000, 0.000, END', 'OBJECT, 1,', 'TRISOLATION, 1, neighbours=no, validated=true, closed=no'];
    for (var q = 0; q < m.nt; q++) D.push((q + 1) + ', ' + (m.t[3 * q] + 1) + ', ' + (m.t[3 * q + 1] + 1) + ', ' + (m.t[3 * q + 2] + 1) + ', 0, 0, 0,');
    D.push('END');
    var sv = window.gxSimpan || function (t, n) { var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([t], { type: 'text/plain' })); a.download = n; document.body.appendChild(a); a.click(); a.remove(); return Promise.resolve(true); };
    return Promise.resolve(sv(S.join('\r\n') + '\r\n', nm + '.str')).then(function () { return sv(D.join('\r\n') + '\r\n', nm + '.dtm'); });
  };
  /* ---------- 0.24.75 (pemilik 13 Nov 2026): NODE di Data Spasial ----------
     Data Spasial: Topografi, Desain pit, Topo × Pit (gabungan) [centang tampil, menu ⋯], Orthofoto, + Import topografi…,
     + Import desain pit…. Panel properti node Topo × Pit = kotak #tpBox (section #pTP). Data Referensi tetap untuk DTM
     tambahan (fase pit, survei bulan lalu); semuanya bisa dipilih sebagai sumber. */
  TP.vis = function (v) { var m = TP.model(); if (!m) return; m.vis = !!v; mdBump(); try { PT.render(true); } catch (e) { } };
  TP.op = function (v) { var m = TP.model(); if (!m) return; m.op = +v; mdBump(); };
  TP.hapus = function () { var m = TP.model(); if (!m || !confirm('Hapus permukaan ' + m.name + '? (bisa digabungkan lagi kapan saja)')) return; MD.models.splice(MD.models.indexOf(m), 1); mdBump(); try { PT.render(true); } catch (e) { } TP.box(); };
  TP.spKids = function (K, amb) {
    var m = TP.model(), L = (K || []).slice(), i = -1;
    var tp = { id: 'sp.tp', t: 'Topo × Pit (gabungan)', ic: 'pit', tab: 'TP', dim: !m, chk: m ? !!m.vis : undefined, onChk: function (v) { TP.vis(v); },
      b: m ? (TP.usang(m) ? 'usang' : m.nt.toLocaleString('id-ID') + ' segitiga') : '', hint: 'Topografi dipotong desain pit: permukaan yang lebih rendah di setiap titik (garis potong tepat)',
      go: function () { TP.box(); },
      menu: function () { var mm = TP.model(), g = !!(mm && mm.gab.garis !== false); return [{ t: mm ? 'Hitung ulang dari topografi & desain pit' : 'Gabungkan topografi × desain pit', fn: function () { TP.gabung(); } },
        { t: 'Ekspor DTM + STR', dis: !mm, fn: function () { TP.ekspor(); } }, { t: 'Garis kontur topografi & jenjang pit', on: g, dis: !mm, fn: function () { TP.setGaris(!g); } },
        { sep: 1 }, { t: 'Hapus permukaan gabungan', danger: 1, dis: !mm, fn: function () { TP.hapus(); } }]; } };
    for (var q = 0; q < L.length; q++) if (L[q] && L[q].id === 'sp.pit') i = q;
    L.splice(i >= 0 ? i + 1 : L.length, 0, tp);
    if (typeof amb === 'function') L.push({ id: 'sp.+topo', t: '+ Import topografi…', ic: 'add', addRow: { fn: amb('topo', 'tambah') }, hint: 'Topografi (STR / DXF / XYZ)' },
      { id: 'sp.+pit', t: '+ Import desain pit…', ic: 'add', addRow: { fn: amb('pit', 'tambah') }, hint: 'Desain pit (STR / DXF / XYZ)' });
    return L;
  };
  (function () { var side = E('side'); if (side && !E('pTP')) { var sec = document.createElement('section'); sec.id = 'pTP'; sec.hidden = true; sec.innerHTML = '<h3>Topo &times; Pit (gabungan)</h3><div id=tpBox></div>'; side.insertBefore(sec, E('pOverlay') || null); }
    var _u = window.uiTab; if (typeof _u === 'function') window.uiTab = function (n) { var sec2 = E('pTP');
      if (n === 'TP') { _u.call(this, 'Overlay'); var ov = E('pOverlay'); if (ov) ov.hidden = true; if (sec2) sec2.hidden = false; TP.box(); return; }
      var r = _u.apply(this, arguments); if (sec2) sec2.hidden = true; return r; }; })();
  /* Reporting › Pit & progres: "Pilih file topografi" -> node Data Referensi (bertanda survei) BESERTA titik aslinya, tersimpan di
     proyek; hitungan Reporting tetap memakai titik itu (rppit.js). Sebaliknya Reporting bisa memilih topografi Data Spasial /
     Data Referensi yang sudah ada. */
  if (window.RPX) RPX.keRef = function (nama, q) {
    if (!window.MD || !window.TIN) return null; var tin = TIN.build(q); var pts = { x: Float64Array.from(q.x), y: Float64Array.from(q.y), z: Float64Array.from(q.z) };
    var m = { name: nama, jenis: 'surf', survei: true, pts: pts, col: '#b08d57', op: 0.55, vis: false, v: new Float64Array(0), t: new Uint32Array(0), nv: 0, nt: 0 };
    if (tin) { var v = new Float64Array(3 * tin.n); for (var i = 0; i < tin.n; i++) { v[3 * i] = tin.x[i] + offX; v[3 * i + 1] = tin.y[i] + offY; v[3 * i + 2] = tin.z[i]; } var t = new Uint32Array(3 * tin.i.length);
      for (var k = 0; k < tin.i.length; k++) { t[3 * k] = tin.i[k]; t[3 * k + 1] = tin.j[k]; t[3 * k + 2] = tin.k[k]; } m.v = v; m.t = t; m.nv = tin.n; m.nt = tin.i.length; }
    var old = MD.models.filter(function (w) { return w.survei && w.name === nama; })[0]; if (old) MD.models.splice(MD.models.indexOf(old), 1, m); else MD.models.push(m);
    mdBump(true); try { PT.render(true); } catch (e) { } return 'wf:' + MD.models.indexOf(m);
  };

  /* kotak di panel properti node Topo × Pit */
  TP.box = function () {
    var b = E('tpBox'); if (!b) return; var m = TP.model(), T = TP.srcT(), P = TP.srcP(), L = TP.daftar();
    var sel = function (peran, k) { return '<select onchange="TP.cfg.' + peran + '=this.value;TP.box()">' + (k ? '' : '<option value="">(belum ada)</option>') + L.map(function (x) { return '<option value="' + esc(x[0]) + '"' + (x[0] === k ? ' selected' : '') + '>' + esc(x[1]) + '</option>'; }).join('') + '</select>'; };
    b.innerHTML = '<div class=g2 style="margin:4px 0"><div><label>Topografi</label>' + sel('t', T) + '</div><div><label>Desain pit</label>' + sel('p', P) + '</div></div><div class="g2 f" style="margin:4px 0 6px"><button class=btn-pri onclick="TP.gabung()"' + (T && P ? '' : ' disabled') + '>' + (m ? '&#8635; Hitung ulang' : '&#9650; Gabungkan') + ' topografi × desain pit</button>' +
      (m ? '<button onclick="TP.ekspor()">&#8681; Ekspor DTM + STR</button>' : '<span></span>') + '</div>' +
      (m ? '<label class=sw><input type=checkbox' + (m.vis ? ' checked' : '') + ' onchange="TP.vis(this.checked)">Tampilkan permukaan gabungan</label><label class=sw><input type=checkbox' + (m.gab.garis !== false ? ' checked' : '') + ' onchange="TP.setGaris(this.checked)">Garis kontur topografi &amp; jenjang pit</label><div class=f><label>Opasitas</label><input type=range min=0.1 max=1 step=0.05 value=' + m.op + ' onchange="TP.op(+this.value)"></div>' : '') +
      '<div class=hint>Permukaan yang lebih rendah antara topografi dan desain pit; garis potong dihitung tepat. Bawaan Data Spasial (sama dengan Reporting); permukaan DTM / survei di Data Referensi juga bisa dipilih.' +
      (!T || !P ? ' <b>Belum ada ' + [!T ? 'topografi' : '', !P ? 'desain pit' : ''].filter(Boolean).join(' & ') + '.</b>' : '') +
      (m && TP.usang(m) ? ' <span class=warn>Topografi / desain pit sudah berganti: klik Hitung ulang.</span>' : '') + '</div><div id=tpMsg class=hint></div>';
  };
  if (typeof mdList === 'function') { var _ml = mdList; window.mdList = mdList = function () { var r = _ml.apply(this, arguments); try { TP.box(); } catch (e) { } return r; }; }

  /* palet gradasi (Pit Studio): topo hijau-krem, pit biru muda (atas) ke biru (bawah) */
  TP.SKT = [[0, '#9eb385'], [0.33, '#b8c794'], [0.67, '#d6d1a8'], [1, '#ede8d6']];
  TP.SKP = [[0, '#738cc7'], [1, '#ccd9ed']];
  /* GARIS KONTUR TOPO & JENJANG PIT di atas permukaan gabungan (cara Pit Studio: string asli digambar, dipotong di bagian
     yang tidak tampil): segmen topo tampil bila topo yang lebih rendah di titik tengahnya, segmen pit bila pit yang lebih
     rendah; diangkat 8 cm supaya tidak tenggelam. Hanya untuk sumber Data Spasial (permukaan DTM tidak punya string).
     Cache per model (WeakMap, tidak ikut tersimpan di proyek). */
  var GWM = typeof WeakMap !== 'undefined' ? new WeakMap() : null;
  TP.garis = function (m) {
    if (!GWM || !m.gab || !m.gab.src) return null; var c = GWM.get(m); if (c && c.k === m.gab.at) return c.g;
    var s = m.gab.src, fT = zf(s.t), fP = zf(s.p), out = [];
    var berString = function (o) { for (var i = 0; i < o.x.length; i++) if (o.x[i] === null || o.x[i] === undefined) return true; return false; };
    var potongStr = function (o, sendiri, lain, nm, col, w, op, rapat) { if (!o || !o.x || !o.x.length || !berString(o)) return; /* awan titik XYZ: tidak ada garis */ if (rapat && TIN.rapat) o = TIN.rapat(o, 2); var X = [], Y = [], Z = [], buka = false;
      for (var i = 1; i < o.x.length; i++) { var x0 = o.x[i - 1], x1 = o.x[i]; if (x0 === null || x1 === null || x0 === undefined || x1 === undefined) { if (buka) { X.push(null); Y.push(null); Z.push(null); buka = false; } continue; }
        var y0 = o.y[i - 1], y1 = o.y[i], z0 = o.z[i - 1], z1 = o.z[i], mx = (x0 + x1) / 2, my = (y0 + y1) / 2, mz = (z0 + z1) / 2, zo = lain(mx, my), ok = zo === null || (sendiri === 'topo' ? mz <= zo + 0.05 : mz < zo - 0.05);
        if (!ok) { if (buka) { X.push(null); Y.push(null); Z.push(null); buka = false; } continue; }
        if (!buka) { X.push(x0); Y.push(y0); Z.push(z0 + 0.08); buka = true; } X.push(x1); Y.push(y1); Z.push(z1 + 0.08); }
      out.push({ nm: nm, x: X, y: Y, z: Z, c: col, w: w, op: op }); };
    if (s.t === 'ov:topo') potongStr(OV.topoF, 'topo', fP, 'Kontur topografi', '#5a4630', 1.5, 0.55, false);
    if (s.p === 'ov:pit') potongStr(OV.pitF, 'pit', fT, 'Garis jenjang pit', '#1b2a4e', 2, 0.75, true);
    GWM.set(m, { k: m.gab.at, g: out }); return out;
  };
  TP.setGaris = function (v) { var m = TP.model(); if (!m) return; m.gab.garis = !!v; mdBump(); };

  /* warna dua nada untuk permukaan gabungan + tanda lapisan untuk legenda / buka atap */
  if (typeof mdTraces === 'function') {
    var _mt = mdTraces;
    window.mdTraces = mdTraces = function (T, o) {
      var n0 = T.length, r = _mt.apply(this, arguments), byName = {};
      MD.models.forEach(function (m) { if (m.vis) byName[m.name] = m; });
      for (var q = n0; q < T.length; q++) { var t = T[q], m = byName[t.name]; if (!m) continue; t._tpMd = m; if (t.type !== 'mesh3d') continue;
        if (m.jenis === 'surf') t._tpSurf = 1;
        if (m.gab && m.fsrc && m.fsrc.length === m.nt) {
          var hm = window.TIN ? TIN.shadeMode() : 'plotly', ct = (E('ovTopoCol') || {}).value || '#a7b58a', cp = (E('ovPitCol') || {}).value || '#8ea4c8', gr = ((E('ovWarna') || {}).value === 'grad'), k = hm + '|' + ct + '|' + cp + '|' + gr + '|' + m.nt;
          if (m._tpK !== k) { var tin = { x: m._x, y: m._y, z: m._z, i: m._i, j: m._j, k: m._k }, F;
            if (hm !== 'plotly' && TIN.hillshade) { var a = {}, b = {}; TIN.hillshade(a, tin, { color: ct, grad: gr, colorscale: TP.SKT }, hm); TIN.hillshade(b, tin, { color: cp, grad: gr, colorscale: TP.SKP }, hm); F = new Array(m.nt); for (var s = 0; s < m.nt; s++) F[s] = m.fsrc[s] ? b.facecolor[s] : a.facecolor[s]; }
            else { F = new Array(m.nt); for (var s2 = 0; s2 < m.nt; s2++) F[s2] = m.fsrc[s2] ? cp : ct; }
            m._tpF = F; m._tpK = k; }
          t.facecolor = m._tpF; delete t.color; if (hm !== 'plotly') t.lighting = { ambient: 1, diffuse: 0, specular: 0, roughness: 1, fresnel: 0 };
          if (m.gab.garis !== false && !VIEW2D) { var G2 = TP.garis(m); if (G2) G2.forEach(function (g) { if (g.x.length) T.push({ type: 'scatter3d', mode: 'lines', name: g.nm, x: g.x, y: g.y, z: g.z, line: { color: g.c, width: g.w }, opacity: g.op, hoverinfo: 'skip', showlegend: false, _tpGaris: 1 }); }); } } }
      return r; };
  }
  if (typeof bxTraces === 'function') { var _bt = bxTraces; window.bxTraces = bxTraces = function (T) { var n0 = T.length, r = _bt.apply(this, arguments); for (var q = n0; q < T.length; q++) T[q]._tpBx = 1; return r; }; }

  /* ---------- B. batas permukaan blok ---------- */
  TP.MODE = { '': 'Semua blok', bawah: 'Di bawah topo × pit (sisa in-situ)', pit: 'Di antara topo & pit (yang akan ditambang)' };
  /* bit 1 = titik pusat di bawah permukaan gabungan (di dalam cakupan topografi); bit 2 = di atas / tepat di pit dan di bawah topografi */
  TP.mask = function () {
    var m = window.BX && BX.m; if (!m) return null; var T = TP.srcT(), P = TP.srcP(); if (P === T) P = null; var k = BX.ver + '|' + TP.sig(T) + '|' + TP.sig(P);
    if (BX._tpM && BX._tpM.k === k) return BX._tpM.a;
    var fT = zf(T), fP = zf(P), a = new Uint8Array(m.n);
    if (T) for (var i = 0; i < m.n; i++) { var x = m.x[i] - offX, y = m.y[i] - offY, z = m.z[i], t = fT(x, y); if (t == null) continue; var p = P ? fP(x, y) : null;
      /* batas sama dengan Reporting (rpbm.js): di atas topografi = keluar, tepat di permukaan ikut; di bawah pit = sisa */
      if (z <= t && (p == null || z < p)) a[i] |= 1; if (p != null && z <= t && z >= p) a[i] |= 2; }
    BX._tpM = { k: k, a: a }; return a;
  };
  if (typeof bxPass === 'function') { var _bp = bxPass; window.bxPass = bxPass = function (i) { var md = BX.ui && BX.ui.tpB; if (md) { var a = TP.mask(); if (a && a.length === BX.m.n && !(a[i] & (md === 'pit' ? 2 : 1))) return false; } return _bp(i); }; }
  if (typeof bxSel === 'function') { var _bs = bxSel; window.bxSel = bxSel = function (o) { var md = BX.ui && BX.ui.tpB || '', k = md ? md + '|' + (BX._tpM ? BX._tpM.k : TP.sig(TP.srcT()) + TP.sig(TP.srcP())) : ''; if (BX._tpk !== k) { BX._tpk = k; BX.sc = {}; } return _bs(o); }; }
  TP.uiRow = function () {
    var U = BX.ui || {}, T = TP.srcT(), P = TP.srcP(), md = U.tpB || '';
    return '<div class=lab style="margin-top:6px">Batas permukaan</div><select id=bxTpB onchange="bxSet(&#39;tpB&#39;,this.value)"' + (T ? '' : ' disabled title="Belum ada topografi di Data Spasial"') + '>' +
      Object.keys(TP.MODE).map(function (k) { return '<option value="' + k + '"' + (k === md ? ' selected' : '') + (k === 'pit' && !P ? ' disabled' : '') + '>' + TP.MODE[k] + '</option>'; }).join('') + '</select>' +
      '<div class=hint>Titik pusat blok (cara Surpac, sama dengan Reporting) terhadap ' + esc(nama(T)) + ' &times; ' + esc(nama(P)) + ' (pilihan sumber di Data Spasial &rsaquo; Topo &times; Pit). Bekerja bersama cut-off &amp; kelas di atas' + (T ? '' : '; <b>belum ada topografi</b>') + '.</div>';
  };

  /* ---------- C. buka atap ---------- */
  TP.jejak = function () {
    if (!E('ovBuka') || !E('ovBuka').checked || VIEW2D || !window.BX || !BX.m || !E('bxShow') || !E('bxShow').checked || !BX.sc || !BX.sc.v || !BX.sc.v.idx.length) return null;
    var m = BX.m, I = BX.sc.v.idx, buf = Math.max(0, +((E('ovBukaM') || {}).value) || 0), k = BX.sc.key + '|' + buf;
    if (TP._jj && TP._jj.k === k) return TP._jj;
    var x0 = 1e18, x1 = -1e18, y0 = 1e18, y1 = -1e18, cs = 1e9, q;
    for (q = 0; q < I.length; q++) { var i = I[q], x = m.x[i] - offX, y = m.y[i] - offY, hx = m.sx[i] / 2, hy = m.sy[i] / 2; if (x - hx < x0) x0 = x - hx; if (x + hx > x1) x1 = x + hx; if (y - hy < y0) y0 = y - hy; if (y + hy > y1) y1 = y + hy; if (q < 2000) cs = Math.min(cs, m.sx[i], m.sy[i]); }
    cs = Math.max(0.25, cs / 2); x0 -= buf; y0 -= buf; x1 += buf; y1 += buf;
    while ((x1 - x0) / cs * (y1 - y0) / cs > 2e7) cs *= 1.5;
    var gx = Math.ceil((x1 - x0) / cs) + 1, gy = Math.ceil((y1 - y0) / cs) + 1, G = new Float32Array(gx * gy).fill(-Infinity);
    for (q = 0; q < I.length; q++) { var j = I[q], cx = m.x[j] - offX, cy = m.y[j] - offY, a0 = Math.floor((cx - m.sx[j] / 2 - buf - x0) / cs), a1 = Math.floor((cx + m.sx[j] / 2 + buf - x0) / cs), b0 = Math.floor((cy - m.sy[j] / 2 - buf - y0) / cs), b1 = Math.floor((cy + m.sy[j] / 2 + buf - y0) / cs);
      var zt = m.z[j] + m.sz[j] / 2; /* atap blok: permukaan di ATAS ini yang dibuka, lantai pit di bawah blok tetap */
      for (var u = Math.max(0, a0); u <= Math.min(gx - 1, a1); u++) for (var w = Math.max(0, b0); w <= Math.min(gy - 1, b1); w++) if (zt > G[w * gx + u]) G[w * gx + u] = zt; }
    TP._jj = { k: k, x0: x0, y0: y0, cs: cs, gx: gx, gy: gy, G: G }; return TP._jj;
  };
  var potong = function (t, J) {
    var c = t._tpCut; if (c && c.k === J.k && c.n === t.i.length) return c.t;
    var I = t.i, Jx = t.j, K = t.k, X = t.x, Y = t.y, Zs = t.z, ni = [], nj = [], nk = [], fc = t.facecolor ? [] : null;
    for (var q = 0; q < I.length; q++) { var a = I[q], b = Jx[q], d = K[q], u = Math.floor(((X[a] + X[b] + X[d]) / 3 - J.x0) / J.cs), w = Math.floor(((Y[a] + Y[b] + Y[d]) / 3 - J.y0) / J.cs);
      if (u >= 0 && w >= 0 && u < J.gx && w < J.gy) { var g = J.G[w * J.gx + u]; if (g > -Infinity && (Zs[a] + Zs[b] + Zs[d]) / 3 > g - 0.01) continue; } ni.push(a); nj.push(b); nk.push(d); if (fc) fc.push(t.facecolor[q]); }
    var o = Object.assign({}, t, { i: ni, j: nj, k: nk }); if (fc) o.facecolor = fc; delete o._tpCut;
    t._tpCut = { k: J.k, n: I.length, t: o }; return o;
  };

  /* ---------- D. legenda ---------- */
  var LS = function () { try { return JSON.parse(localStorage.getItem('gcex_tp_leg') || '{}'); } catch (e) { return {}; } };
  TP.leg = Object.assign({ on: true, min: false }, LS());
  TP.legSet = function (k, v) { TP.leg[k] = v; try { localStorage.setItem('gcex_tp_leg', JSON.stringify(TP.leg)); } catch (e) { } updatePlot(); };
  var warna = function (t) { var c = (t.line && typeof t.line.color === 'string' && t.line.color) || (t.marker && typeof t.marker.color === 'string' && t.marker.color) || (typeof t.color === 'string' && t.color) || (t.fillcolor) || ''; return c; };
  var bentuk = function (t) { return t.type === 'mesh3d' ? 'kotak' : (t.mode && t.mode.indexOf('lines') >= 0 && !(t.mode.indexOf('markers') >= 0)) ? 'garis' : 'titik'; };
  TP.legHtml = function (traces) {
    var S = [], it = function (c, lab, sh) { return '<div class=tplg-i><span class="tplg-s ' + (sh || 'kotak') + '" style="background:' + esc(c || '#9aa5b1') + '"></span><span>' + lab + '</span></div>'; };
    /* block model: kelas yang sedang tampil */
    if (window.BX && BX.m && E('bxShow') && E('bxShow').checked && !VIEW2D && BX.sc && BX.sc.v && typeof bxClassInfo === 'function') {
      var U = BX.ui, ks = {}; BX.sc.v.cl.forEach(function (k) { ks[k] = (ks[k] || 0) + 1; });
      var h = Object.keys(ks).map(Number).sort(function (a, b) { return a - b; }).map(function (k) { var ci = bxClassInfo(k); return it(ci.col, esc(ci.lab) + ' <small>' + ks[k].toLocaleString('id-ID') + '</small>'); }).join('');
      var sub = [U.fAttr && U.fVal !== '' ? esc(U.fAttr) + ' ' + (U.fOp === 'lt' ? '&lt;' : '≥') + ' ' + esc(U.fVal) : '', U.tpB ? esc(TP.MODE[U.tpB]) : ''].filter(Boolean).join(' · ');
      if (h) S.push('<div class=tplg-h>Block model · ' + esc(U.attr) + '</div>' + (sub ? '<div class=tplg-n>' + sub + '</div>' : '') + h);
    }
    var srf = [], wf = [], lain = [], seen = {};
    if (!VIEW2D && E('ovTopoS') && E('ovTopoS').checked && window.OV && ada(OV.topoF)) srf.push(it((E('ovTopoCol') || {}).value, 'Topografi'));
    if (!VIEW2D && E('ovPit') && E('ovPit').checked && window.OV && ada(OV.pitF)) srf.push(it((E('ovPitCol') || {}).value, 'Desain pit', (E('ovPitMode') || {}).value === 'line' ? 'garis' : 'kotak'));
    traces.forEach(function (t) {
      if (t._tpGaris) { if (!seen['g:' + t.name]) { seen['g:' + t.name] = 1; srf.push(it(t.line.color, esc(t.name), 'garis')); } return; }
      if (t._tpBx || t.showlegend === false || !t.name || /^_/.test(t.name)) return;
      var m = t._tpMd, key = (m ? 'md:' : '') + t.name; if (seen[key]) return; seen[key] = 1;
      if (m && m.gab) { srf.push(it((E('ovTopoCol') || {}).value, 'Topografi <small>(gabungan)</small>'), it((E('ovPitCol') || {}).value, 'Desain pit <small>(gabungan)</small>')); return; }
      if (m && m.jenis === 'surf') { srf.push(it(m.col, esc(t.name))); return; }
      if (m) { wf.push(it(m.col, esc(t.name), t.type === 'mesh3d' ? 'kotak' : 'garis')); return; }
      if (lain.length < 14) lain.push(it(warna(t), esc(t.name), bentuk(t)));
    });
    if (srf.length) S.push('<div class=tplg-h>Permukaan</div>' + srf.join(''));
    if (wf.length) S.push('<div class=tplg-h>Wireframe &amp; solid</div>' + wf.join(''));
    if (lain.length) S.push('<div class=tplg-h>Lapisan lain</div>' + lain.join(''));
    return S.join('');
  };
  TP.legRender = function (traces) {
    var pd = E('plotDiv'); if (!pd || !pd.parentElement) return; var host = pd.parentElement; if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
    var box = E('tpLeg'); if (!box) { box = document.createElement('div'); box.id = 'tpLeg'; host.appendChild(box); }
    var body = TP.leg.on ? TP.legHtml(traces) : '';
    if (!TP.leg.on || !body) { box.className = 'tplg tplg-pill'; box.innerHTML = TP.leg.on ? '' : '<button onclick="TP.legSet(&#39;on&#39;,true)" title="Tampilkan legenda">&#9776; Legenda</button>'; box.style.display = TP.leg.on ? 'none' : ''; return; }
    box.style.display = ''; box.className = 'tplg' + (TP.leg.min ? ' tplg-min' : '');
    box.innerHTML = '<div class=tplg-t><b>Legenda</b><span><button onclick="TP.legSet(&#39;min&#39;,' + (!TP.leg.min) + ')" title="' + (TP.leg.min ? 'Buka' : 'Kecilkan') + '">' + (TP.leg.min ? '+' : '&minus;') + '</button><button onclick="TP.legSet(&#39;on&#39;,false)" title="Tutup">&times;</button></span></div>' + (TP.leg.min ? '' : '<div class=tplg-b>' + body + '</div>');
  };
  var css = document.createElement('style');
  css.textContent = '.tplg{position:absolute;right:12px;bottom:12px;z-index:5;min-width:190px;max-width:270px;max-height:58%;display:flex;flex-direction:column;background:var(--sf,#fff);color:var(--tx,#1c2733);border:1px solid var(--bd,#d9dee5);border-radius:10px;box-shadow:0 4px 14px rgba(16,24,40,.16);font:12px "Segoe UI",Roboto,Arial,sans-serif}' +
    '.tplg-t{display:flex;align-items:center;justify-content:space-between;padding:7px 10px;border-bottom:1px solid var(--bd,#d9dee5)}.tplg-t b{font-size:13px;color:var(--pr,#1f3a5f)}' +
    '.tplg-t button,.tplg-pill button{border:1px solid var(--bd,#d9dee5);background:var(--sf2,#f5f7fa);color:var(--tx,#1c2733);border-radius:6px;width:22px;height:22px;margin-left:4px;padding:0;line-height:18px;cursor:pointer}' +
    '.tplg-pill{min-width:0;background:transparent;border:0;box-shadow:none}.tplg-pill button{width:auto;height:auto;padding:5px 10px;font-weight:600;box-shadow:0 2px 8px rgba(16,24,40,.15)}' +
    '.tplg-min .tplg-t{border-bottom:0}.tplg-b{overflow:auto;padding:4px 10px 8px}.tplg-h{font-weight:700;color:var(--pr,#1f3a5f);margin:8px 0 3px}.tplg-n{color:var(--mu,#5b6b7c);font-size:11px;margin:-2px 0 3px}' +
    '.tplg-i{display:flex;align-items:center;gap:7px;margin:2px 0;line-height:16px}.tplg-i small{color:var(--mu,#5b6b7c)}.tplg-s{flex:0 0 auto;width:16px;height:11px;border-radius:2px;border:1px solid rgba(0,0,0,.18)}' +
    '.tplg-s.garis{height:3px;border:0;border-radius:2px}.tplg-s.titik{width:10px;height:10px;border-radius:50%;margin:0 3px}';
  document.head.appendChild(css);

  /* ---------- pasca: dipanggil updatePlot tepat sebelum Plotly.react ---------- */
  TP.pasca = function (traces, layout) {
    var J = TP.jejak();
    if (J) for (var q = 0; q < traces.length; q++) { var t = traces[q]; if (t.type === 'mesh3d' && t.i && t.i.length && (t._tpSurf || t.uid === 'ovTopoS' || t.uid === 'ovPitS')) traces[q] = potong(t, J);
      else if (t._tpGaris) { var X = [], Y = [], Z = []; for (var i = 0; i < t.x.length; i++) { var x = t.x[i]; if (x === null) { X.push(null); Y.push(null); Z.push(null); continue; } var u = Math.floor((x - J.x0) / J.cs), w = Math.floor((t.y[i] - J.y0) / J.cs), g = (u >= 0 && w >= 0 && u < J.gx && w < J.gy) ? J.G[w * J.gx + u] : -Infinity;
          if (g > -Infinity && t.z[i] > g - 0.01) { if (X.length && X[X.length - 1] !== null) { X.push(null); Y.push(null); Z.push(null); } continue; } X.push(x); Y.push(t.y[i]); Z.push(t.z[i]); }
        traces[q] = Object.assign({}, t, { x: X, y: Y, z: Z }); } }
    if (!VIEW2D && TP.leg.on && layout) layout.showlegend = false;
    try { if (!VIEW2D) TP.legRender(traces); else { var b = E('tpLeg'); if (b) b.style.display = 'none'; } } catch (e) { console.warn('[TP legenda]', e); }
    /* tanda internal dibuang sebelum Plotly (objek model besar tidak ikut dibandingkan / disalin) */
    traces.forEach(function (t) { delete t._tpMd; delete t._tpSurf; delete t._tpBx; delete t._tpGaris; });
  };

  /* ---------- Demo: satu langkah sebelum Penutup (data latihan: topografi Data Spasial x SIM_pit_fase1) ---------- */
  (function () { var _s = window.dmSteps; if (typeof _s !== 'function') return; window.dmSteps = dmSteps = function () { var S = _s.apply(this, arguments) || []; if (S.length < 3) return S;
      if (!TP.srcT() || !TP.srcP() || !window.BX || !BX.m) return S;
      var st = { s: 'Model & Overlay', t: 'Topografi terpotong desain pit', dur: 10, el: '#tpBox',
        d: 'Topo × Pit (gabungan): topografi dipotong desain pit menjadi satu permukaan (hijau topo, biru pit). Block model difilter cut-off seperti biasa, lalu Batas permukaan "Di antara topo & pit" menampilkan blok yang akan ditambang di dalam pit; legenda di pojok kanan bawah.',
        run: function (A) { var U = BX.ui, sv = { fA: U.fAttr, fO: U.fOp, fV: U.fVal, tp: U.tpB || '' };
          A(0, function () { try { if (window.PT && PT.mau) PT.mau('sp.tp'); uiTab('TP'); } catch (e) { } TP.box(); });
          A(1.5, function () { if (!TP.model()) TP.gabung(); });
          A(3.5, function () { var bs = E('bxShow'); if (bs) bs.checked = true; U.fAttr = U.attr; U.fOp = 'ge'; if (U.fVal === '' || U.fVal == null) U.fVal = String((bxCls(U.attr)[3] || bxCls(U.attr)[1] || {}).lo || ''); bxSet('tpB', 'pit'); });
          A(5, function () { try { setCam(0.42, -0.5, 0.38); } catch (e) { } });
          A(9.5, function () { U.fAttr = sv.fA; U.fOp = sv.fO; U.fVal = sv.fV; bxSet('tpB', sv.tp); }); } };
      var k = S.length - 1; while (k > 0 && S[k].s !== 'Penutup') k--; if (k <= 0) k = S.length; S.splice(k, 0, st); return S; }; })();

  /* transparansi desain pit sendiri: nilai lama = opasitas topo + 0,25 */
  TP.opPit = function (op) { var e = E('ovPitOp'); return e ? +e.value : Math.min(1, op + 0.25); };
})();
