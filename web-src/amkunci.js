/* ================= GC-Ex Block Model 0.24.58: As-Mined — KUNCI TANGGAL-SHIFT, REPORT PER TANGGAL, TAMPALAN =================
   Keputusan pemilik (10 Nov 2026):
   - Model as-mined dipakai untuk laporan produksi harian (tonase x kadar) pada hari poligon dibuat. Poligon & model hari
     yang sudah dilaporkan TIDAK boleh berubah ketika dua minggu kemudian flitch yang sama digali lagi di tempat lain.
   - Satuan kunci = TANGGAL-SHIFT (satu tombol untuk semua poligon hari & shift itu), bukan per poligon.
   - (koreksi pemilik, 10 Nov 21:28) Kunci terjadi OTOMATIS saat laporan harian keluar: Salin ke Excel, Register CSV
     (berkas benar-benar tersimpan) atau Kirim ke workbook berhasil -- bukan tombol tersendiri. Buka kunci tetap manual.
   - Laporan grade & tonnage as-mined diberi pilihan "Report As-Mined tanggal berapa".
   - Poligon baru yang bertampalan dengan poligon terkunci: peringatan + pilihan mengurangi area tampalan dari poligon baru.

   Cara kerja:
   - amD().lock['YYYY-MM-DD|DS'] = {t, ids:[...], n, ton}. Yang terkunci hanya poligon yang ADA saat dikunci (ids); poligon
     yang ditambahkan kemudian dengan tanggal-shift sama tidak ikut beku (ditandai "ditambah setelah dikunci").
   - Hitung (amRun) tetap menghitung semua poligon tercentang supaya sub-blok 3D / ekspor punya geometrinya, tetapi hasil
     poligon terkunci (x.st) DIKEMBALIKAN ke nilai beku, rekap flitch dikoreksi ke nilai beku, dan sub-blok poligon terkunci
     yang sudah ada di sesi ini dipertahankan. Selisih "bila dihitung ulang sekarang" dicatat (x._stNow, tidak disimpan).
   - Poligon terkunci tidak bisa diedit, dihapus, dimatikan, atau diganti tanggal/shift-nya sebelum kuncinya dibuka.
   - Panel report berupa jendela pop-up yang bisa digeser, diperkecil dan ditutup (usulan pemilik: panel di dalam panel
     yang harus di-scroll diganti pop-up). */
(function () {
  if (typeof window.amRun !== 'function' || typeof window.amBndAll !== 'function') return;
  var AMK = window.AMK = {};
  var E = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); };
  var N = function (v, d) { if (v == null || !isFinite(v)) return '-'; return (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); };
  function LK() { var D = amD(); if (!D.lock) D.lock = {}; return D.lock; }
  function kDS(x) { return String(x.date || '') + '|' + String(x.shift || ''); }
  AMK.key = kDS;
  AMK.isLk = function (x) { var r = x && LK()[kDS(x)]; return !!(r && r.ids && r.ids.indexOf(x.id) >= 0); };
  AMK.lkOf = function (x) { return x ? LK()[kDS(x)] || null : null; };
  function tLk(r) { try { return new Date(r.t).toLocaleString('id-ID'); } catch (e) { return r.t; } }
  function tolak(x, apa) { var r = AMK.lkOf(x), nm = x.name || ''; try { var I = amAllInfo().filter(function (q) { return q.x === x; })[0]; if (I && I.code) nm = I.code; } catch (e) {} alert('Poligon ' + nm + ' terkunci (tanggal ' + amDateTxt(x.date) + ' shift ' + (x.shift || '-') + ', dikunci ' + tLk(r) + ').\n' + apa + ' tidak bisa dilakukan sebelum kuncinya dibuka di "Report As-Mined per tanggal".'); }

  /* ---------- geometri: luas tampalan (sampel grid) & selisih A - B ---------- */
  function shoe(P) { var a = 0; for (var i = 0, n = P.length; i < n; i++) { var q = P[i], r = P[(i + 1) % n]; a += q[0] * r[1] - r[0] * q[1]; } return a / 2; }
  function inP(P, x, y) { var c = false; for (var i = 0, j = P.length - 1; i < P.length; j = i++) { var a = P[i], b = P[j]; if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; }
  function bb(P) { var b = [1e18, -1e18, 1e18, -1e18]; P.forEach(function (q) { if (q[0] < b[0]) b[0] = q[0]; if (q[0] > b[1]) b[1] = q[0]; if (q[1] < b[2]) b[2] = q[1]; if (q[1] > b[3]) b[3] = q[1]; }); return b; }
  /* luas A∩B dengan sampel titik tengah sel (sampai 160 x 160 sel di kotak irisan) */
  AMK.overlap = function (A, B) { var a = bb(A), b = bb(B), x0 = Math.max(a[0], b[0]), x1 = Math.min(a[1], b[1]), y0 = Math.max(a[2], b[2]), y1 = Math.min(a[3], b[3]); if (x1 <= x0 || y1 <= y0) return 0;
    var n = 160, dx = (x1 - x0) / n, dy = (y1 - y0) / n, k = 0; for (var i = 0; i < n; i++) for (var j = 0; j < n; j++) { var x = x0 + (i + 0.5) * dx, y = y0 + (j + 0.5) * dy; if (inP(A, x, y) && inP(B, x, y)) k++; } return k * dx * dy; };
  function dSeg(p, a, b) { var dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy, t = L > 0 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) : 0; return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy); }
  function cut(Pa, Pb) { var out = []; for (var i = 0, n = Pa.length; i < n; i++) { var a = Pa[i], b = Pa[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy, ts = [0, 1]; if (L2 < 1e-12) continue;
      for (var j = 0, m = Pb.length; j < m; j++) { var c = Pb[j], d = Pb[(j + 1) % m]; if (dSeg(c, a, b) <= 1e-6) ts.push(((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / L2);
        var ex = d[0] - c[0], ey = d[1] - c[1], den = dx * ey - dy * ex; if (Math.abs(den) > 1e-12) { var t = ((c[0] - a[0]) * ey - (c[1] - a[1]) * ex) / den, u = ((c[0] - a[0]) * dy - (c[1] - a[1]) * dx) / den; if (t > 1e-9 && t < 1 - 1e-9 && u > -1e-9 && u < 1 + 1e-9) ts.push(t); } }
      ts = ts.filter(function (t) { return t >= 0 && t <= 1; }).sort(function (x, y) { return x - y; }); for (var k = 1; k < ts.length; k++) { if (ts[k] - ts[k - 1] < 1e-9) continue; out.push([[a[0] + dx * ts[k - 1], a[1] + dy * ts[k - 1]], [a[0] + dx * ts[k], a[1] + dy * ts[k]]]); } } return out; }
  /* 1 dalam, 0 luar, 2 di sisi searah, -2 di sisi berlawanan */
  function loc(sg, Pq) { var mx = (sg[0][0] + sg[1][0]) / 2, my = (sg[0][1] + sg[1][1]) / 2, dx = sg[1][0] - sg[0][0], dy = sg[1][1] - sg[0][1]; for (var j = 0, m = Pq.length; j < m; j++) { var c = Pq[j], d = Pq[(j + 1) % m]; if (dSeg([mx, my], c, d) <= 1e-5) return (dx * (d[0] - c[0]) + dy * (d[1] - c[1])) >= 0 ? 2 : -2; } return inP(Pq, mx, my) ? 1 : 0; }
  /* A - B (keduanya poligon sederhana). Hasil: daftar loop (berlawanan jarum jam). null bila tidak bisa dirangkai atau
     B di dalam A (akan menjadi lubang; poligon as-mined tidak punya lubang). Diverifikasi dengan sampel luas. */
  AMK.diff = function (A0, B0) { var A = shoe(A0) < 0 ? A0.slice().reverse() : A0.slice(), B = shoe(B0) < 0 ? B0.slice().reverse() : B0.slice();
    var S = []; cut(A, B).forEach(function (sg) { var l = loc(sg, B); if (l === 0 || l === -2) S.push(sg); }); cut(B, A).forEach(function (sg) { if (loc(sg, A) === 1) S.push([sg[1], sg[0]]); });
    if (S.length < 3) return S.length ? null : [];
    var key = function (q) { return q[0].toFixed(4) + ',' + q[1].toFixed(4); }, out = {}; S.forEach(function (sg) { (out[key(sg[0])] = out[key(sg[0])] || []).push(sg); });
    var loops = [], guard = 0; S.forEach(function (st) { if (st._u) return; var lp = [], cur = st, k0 = key(st[0]); while (cur && !cur._u && guard++ < 200000) { cur._u = 1; lp.push(cur[0]); var kn = key(cur[1]); if (kn === k0) { loops.push(lp); break; } var O = (out[kn] || []).filter(function (x) { return !x._u; }); if (!O.length) break;
        if (O.length > 1) { var bx = cur[1][0] - cur[0][0], by = cur[1][1] - cur[0][1], best = null, ba = 9; O.forEach(function (x) { var cx = x[1][0] - x[0][0], cy = x[1][1] - x[0][1], an = Math.atan2(bx * cy - by * cx, bx * cx + by * cy); if (an < ba) { ba = an; best = x; } }); cur = best; } else cur = O[0]; } });
    loops = loops.filter(function (l) { return l.length >= 3 && shoe(l) > 1e-6; });
    /* verifikasi: luas loop = luas A - luas A∩B (toleransi 2 % + 0,5 m2) */
    var aA = Math.abs(shoe(A)), ov = AMK.overlap(A, B), sum = loops.reduce(function (s, l) { return s + shoe(l); }, 0);
    if (Math.abs(sum - (aA - ov)) > 0.02 * aA + 0.5) return null; return loops; };

  /* ---------- kunci / buka ---------- */
  function polysDS(date, shift) { return amBndAll().filter(function (x) { return String(x.date || '') === date && (!shift || String(x.shift || '') === shift); }); }
  AMK.lock = function (date, shift) { var sh = shift ? [shift] : ['DS', 'NS'], pesan = [], ok = 0;
    for (var i = 0; i < sh.length; i++) { var P = polysDS(date, sh[i]); if (!P.length) continue; var k = date + '|' + sh[i];
      var belum = P.filter(function (x) { return x.on && !x.st; }); if (belum.length) { pesan.push('Shift ' + sh[i] + ': ' + belum.length + ' poligon belum dihitung (' + belum.slice(0, 5).map(function (x) { return x.name; }).join(', ') + '). Buka flitch-nya dan tekan Hitung dulu.'); continue; }
      var On = P.filter(function (x) { return x.on; }), ton = 0; On.forEach(function (x) { var I = amInfo(x); ton += I.ton || 0; });
      var lama = LK()[k], ids = (lama && lama.ids || []).slice(); P.forEach(function (x) { if (ids.indexOf(x.id) < 0) ids.push(x.id); });
      LK()[k] = { t: new Date().toISOString(), ids: ids, n: On.length, ton: ton }; ok++; }
    if (pesan.length) alert(pesan.join('\n'));
    if (ok) { amDirty(); try { amPanel(); } catch (e) {} AMK.render(); try { if (window.PT) PT.render(true); } catch (e) {} } return ok; };
  /* KUNCI OTOMATIS saat laporan harian keluar (pemilik 10-11-2026: "suatu block atau polygon asmined baru terkunci setelah
     laporan dailynya dikirimkan ke Workbook atau sudah diexport ke Excel"). Yang dikunci = poligon yang BENAR-BENAR ikut
     keluar (baris register), dikelompokkan per tanggal-shift. Hanya dalam mode harian (tanggal dipilih); "Semua tanggal" tidak mengunci. */
  AMK.lockRows = function (rows, via) { if (!AMK.f.date || !AMK.harian() || !rows || !rows.length) return 0; var by = {}, n = 0; amAllInfo().forEach(function (I) { by[I.code] = I; });
    var G = {}; rows.forEach(function (r) { var I = by[r[0]]; if (!I || !I.calc) return; var k = kDS(I.x); (G[k] = G[k] || []).push(I); });
    Object.keys(G).forEach(function (k) { var L = G[k], lama = LK()[k], ids = (lama && lama.ids || []).slice(), ton = lama ? lama.ton || 0 : 0, baru = 0;
      L.forEach(function (I) { if (ids.indexOf(I.x.id) < 0) { ids.push(I.x.id); ton += I.ton || 0; baru++; } }); if (!baru) return;
      LK()[k] = { t: new Date().toISOString(), ids: ids, n: ids.length, ton: ton, via: via }; n += baru; });
    if (n) { amDirty(); var m = document.getElementById('amRegMsg'); setTimeout(function () { try { amPanel(); } catch (e) {} var m2 = document.getElementById('amRegMsg'); if (m2) m2.innerHTML = '&#128274; ' + n + ' poligon terkunci (' + via + ').'; }, 0); try { if (window.PT) PT.render(true); } catch (e) {} } return n; };
  AMK.unlock = function (date, shift) { var k = date + '|' + shift, r = LK()[k]; if (!r) return;
    if (!confirm('Buka kunci tanggal ' + amDateTxt(date) + ' shift ' + shift + '?\n\nPoligon hari itu akan bisa diedit dan DIHITUNG ULANG pada Hitung berikutnya, sehingga angka yang sudah dilaporkan dapat berubah.')) return;
    var D = amD(); D.lockLog = D.lockLog || []; D.lockLog.push({ k: k, kunci: r.t, buka: new Date().toISOString(), n: r.n, ton: r.ton }); delete LK()[k]; amDirty(); try { amPanel(); } catch (e) {} AMK.render(); };

  /* ---------- Hitung: poligon terkunci tetap beku ---------- */
  var _run = window.amRun; window.amRun = amRun = function () {
    var B = lyBench(), key = lyFmt(B[0]) + '_' + lyFmt(B[1]), prev = AM.res && AM.res[key], L = amBndCur().filter(function (x) { return x.on && AMK.isLk(x); });
    if (!L.length) return _run.apply(this, arguments);
    var st0 = {}; L.forEach(function (x) { st0[x.id] = x.st; });
    var r = _run.apply(this, arguments), nw = AM.res && AM.res[key];
    L.forEach(function (x) { if (x.st !== st0[x.id]) x._stNow = x.st; x.st = st0[x.id]; });
    if (nw && nw !== prev) { var s = nw.sum, num = function (v) { return isFinite(v) ? v : 0; };
      L.forEach(function (x) { var a = st0[x.id], b = x._stNow; if (!a || !b) return; var ta = num(a.t), tb = num(b.t);
        s.vol += num(a.v) - num(b.v); s.t += ta - tb; s.tu += num(a.tu) - num(b.tu); s.ne += num(a.ne) - num(b.ne); s.nf += (num(a.n) - num(a.ne)) - (num(b.n) - num(b.ne));
        s.gA += num(a.gA) * ta - num(b.gA) * tb; s.gO += num(a.gO) * ta - num(b.gO) * tb;
        if (s.el && s.elw) Object.keys(s.el).forEach(function (e) { var wa = num(a.elw && a.elw[e]), wb = num(b.elw && b.elw[e]), w = num(s.elw[e]), sum = num(s.el[e]) * w + num(a.el && a.el[e]) * wa - num(b.el && b.el[e]) * wb; w += wa - wb; s.elw[e] = w; s.el[e] = w > 0 ? sum / w : NaN; }); });
      if (s.el && s.elA && s.elA[0] && s.t > 0) s.el[s.elA[0]] = s.gA / s.t;
      /* sub-blok poligon terkunci dari hitungan sebelumnya di sesi ini dipertahankan (tampilan 3D / ekspor sel) */
      if (prev && prev.cells) { var ids = {}; L.forEach(function (x) { if (prev.cells.some(function (c) { return c.pid === x.id; })) ids[x.id] = 1; });
        if (Object.keys(ids).length) nw.cells = nw.cells.filter(function (c) { return !ids[c.pid]; }).concat(prev.cells.filter(function (c) { return ids[c.pid]; })); }
      var dT = L.reduce(function (t, x) { var a = st0[x.id], b = x._stNow; return t + (a && b ? num(b.t) - num(a.t) : 0); }, 0);
      AM.msg = (AM.msg || '') + '<div class=hint style="border-left:3px solid #7048e8;padding-left:6px">&#128274; <b>' + L.length + ' poligon terkunci</b> tidak dihitung ulang (angka beku dipakai di register, rekap & laporan).' + (Math.abs(dT) > 0.5 ? ' Bila dihitung ulang sekarang tonasenya berselisih ' + (dT > 0 ? '+' : '') + N(dT) + ' t.' : '') + '</div>';
      try { amPanel(); } catch (e) {} }
    /* label plan / register digambar ulang dengan angka beku (amRun menggambar saat x.st masih hasil hitung ulang) */
    try { updatePlot(); } catch (e) {}
    return r; };
  /* angka beku tidak pernah "kedaluwarsa" karena SG / metode berubah */
  var _inf = window.amInfo; window.amInfo = amInfo = function (x) { var I = _inf.apply(this, arguments); if (AMK.isLk(x)) { I.stale = false; I.lk = true; } else if (AMK.lkOf(x)) I.lkBaru = true; return I; };

  /* ---------- penjaga edit ---------- */
  var cari = function (id) { return amBndAll().filter(function (q) { return q.id === id; })[0]; };
  var jaga = function (nm, apa, kecuali) { var f = window[nm]; if (typeof f !== 'function') return; window[nm] = function (id) { var x = cari(id); if (x && AMK.isLk(x) && !(kecuali && kecuali.apply(this, arguments))) { tolak(x, apa); try { amPanel(); } catch (e) {} return; } return f.apply(this, arguments); }; };
  jaga('amBndDel', 'Menghapus poligon'); jaga('amBndOn', 'Mematikan / menyalakan poligon'); jaga('amEdShape', 'Mengedit bentuk poligon');
  /* atribut yang tidak memengaruhi angka (warna, cetak di layout) tetap boleh */
  jaga('amPSet', 'Mengubah atribut poligon', function (id, f) { return ['col', 'print', 'sid'].indexOf(f) >= 0; });
  try { amPSet = window.amPSet; amBndDel = window.amBndDel; amBndOn = window.amBndOn; if (window.amEdShape) amEdShape = window.amEdShape; } catch (e) {}

  /* ---------- poligon baru bertampalan dengan poligon terkunci ---------- */
  AMK.cekTampal = function (x) { if (!x || AMK.isLk(x)) return; var Lk = amBndAll().filter(function (q) { return q !== x && Math.abs(q.top - x.top) < 1e-6 && Math.abs(q.bot - x.bot) < 1e-6 && AMK.isLk(q); });
    var T = Lk.map(function (q) { return { q: q, a: AMK.overlap(x.pts, q.pts) }; }).filter(function (o) { return o.a > Math.max(0.5, 0.002 * Math.abs(shoe(x.pts))); }); if (!T.length) return;
    var tot = T.reduce(function (s, o) { return s + o.a; }, 0);
    var ya = confirm('Poligon baru ' + (x.name || '') + ' bertampalan ' + N(tot, 1) + ' m² dengan poligon TERKUNCI:\n' + T.map(function (o) { return ' • ' + o.q.name + ' (' + amDateTxt(o.q.date) + ' ' + (o.q.shift || '') + '): ' + N(o.a, 1) + ' m²'; }).join('\n') +
      '\n\nOK = kurangi area tampalan dari poligon baru (material itu sudah dilaporkan).\nBatal = biarkan (area tampalan akan terhitung dua kali).');
    if (!ya) { x.tampal = N(tot, 1) + ' m² dengan poligon terkunci'; amDirty(); return; }
    var Ps = [x.pts.map(function (q) { return [q[0], q[1]]; })]; for (var i = 0; i < T.length && Ps; i++) { var nx = []; for (var j = 0; j < Ps.length; j++) { var d = AMK.diff(Ps[j], T[i].q.pts); if (d === null) { Ps = null; break; } nx = nx.concat(d); } if (Ps) Ps = nx; }
    if (!Ps) { alert('Tampalan tidak bisa dikurangkan otomatis (bentuknya akan berlubang atau rumit). Poligon dibiarkan; perbaiki dengan edit titik.'); x.tampal = N(tot, 1) + ' m² dengan poligon terkunci'; amDirty(); return; }
    Ps = Ps.filter(function (l) { return shoe(l) > 0.5; }).sort(function (a, b) { return shoe(b) - shoe(a); });
    if (!Ps.length) { var D0 = amD(); D0.bnd = D0.bnd.filter(function (q) { return q !== x; }); alert('Poligon baru seluruhnya berada di dalam poligon terkunci, jadi tidak ditambahkan.'); amDirty(); return; }
    x.pts = Ps[0]; x.key = null; x.st = null; delete x.tampal;
    Ps.slice(1).forEach(function (l, i) { var c = JSON.parse(JSON.stringify(x)); c.id = (window.amBid ? amBid() : 'am' + Date.now() + i); c.pts = l; c.name = (x.name || 'P') + '_' + String.fromCharCode(98 + i); c.st = null; amD().bnd.push(c); });
    amDirty(); };
  var _add = window.amBndAdd; window.amBndAdd = amBndAdd = function () { var n0 = amBndAll().length, r = _add.apply(this, arguments); try { var A = amBndAll(); if (A.length > n0) A.slice(n0).forEach(function (x) { AMK.cekTampal(x); }); } catch (e) { console.error(e); } return r; };

  /* ---------- jendela pop-up (bisa digeser, diperkecil, ditutup) ---------- */
  AMK.pop = function (id, judul, isi) { var w = document.getElementById(id);
    if (!w) { w = document.createElement('div'); w.id = id; w.className = 'gxpop'; w.innerHTML = '<div class=gxph><b></b><span><button type=button data-m title="Perkecil / perbesar">&#8211;</button><button type=button data-x title="Tutup (data tidak hilang)">&times;</button></span></div><div class=gxpb></div>'; document.body.appendChild(w);
      var h = w.firstChild, dr = null; h.addEventListener('mousedown', function (e) { if (e.target.closest('button')) return; var r = w.getBoundingClientRect(); dr = [e.clientX - r.left, e.clientY - r.top]; e.preventDefault(); });
      window.addEventListener('mousemove', function (e) { if (!dr) return; w.style.left = Math.max(0, Math.min(innerWidth - 120, e.clientX - dr[0])) + 'px'; w.style.top = Math.max(0, Math.min(innerHeight - 40, e.clientY - dr[1])) + 'px'; });
      window.addEventListener('mouseup', function () { dr = null; });
      h.querySelector('[data-x]').onclick = function () { w.style.display = 'none'; }; h.querySelector('[data-m]').onclick = function () { w.classList.toggle('min'); }; }
    w.querySelector('.gxph b').textContent = judul; if (isi != null) w.querySelector('.gxpb').innerHTML = isi; w.style.display = 'flex'; return w; };
  (function () { var st = document.createElement('style'); st.textContent =
    '.gxpop{position:fixed;left:380px;top:70px;z-index:60;width:min(860px,calc(100vw - 400px));max-height:calc(100vh - 90px);display:none;flex-direction:column;background:var(--sf,#fff);color:var(--tx);border:1px solid var(--bd);border-radius:8px;box-shadow:0 8px 28px rgba(0,0,0,.25)}' +
    '.gxpop .gxph{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:6px 10px;background:var(--pr,#1c3d8f);color:#fff;border-radius:8px 8px 0 0;cursor:move;user-select:none}.gxpop .gxph button{background:none;border:0;color:#fff;font-size:16px;width:26px;height:24px;cursor:pointer}' +
    '.gxpop .gxpb{overflow:auto;padding:8px 10px}.gxpop.min .gxpb{display:none}.gxpop.min{width:320px}' +
    ''; document.head.appendChild(st); })();

  /* ---------- Report As-Mined per tanggal ---------- */
  AMK.f = AMK.f || { shift: '' };
  /* periode (pemilik 10-11-2026: "register weekly atau monthly"): harian / mingguan (Senin-Minggu) / bulanan / rentang.
     Diikat TANGGAL & shift poligon, bukan elevasi flitch: semua flitch ikut. Kunci otomatis hanya pada mode harian. */
  var iso = function (d) { var p = function (n) { return ('0' + n).slice(-2); }; return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()); };
  AMK.range = function () { var f = AMK.f, m = f.mode || 'hari'; if (!f.date) return null; var d = new Date(f.date + 'T00:00:00'); if (isNaN(d)) return null;
    if (m === 'minggu') { var w = (d.getDay() + 6) % 7, a = new Date(d); a.setDate(d.getDate() - w); var b = new Date(a); b.setDate(a.getDate() + 6); return [iso(a), iso(b)]; }
    if (m === 'bulan') { return [iso(new Date(d.getFullYear(), d.getMonth(), 1)), iso(new Date(d.getFullYear(), d.getMonth() + 1, 0))]; }
    if (m === 'rentang') { var e = f.date2 && f.date2 >= f.date ? f.date2 : f.date; return [f.date, e]; } return [f.date, f.date]; };
  AMK.harian = function () { return (AMK.f.mode || 'hari') === 'hari'; };
  AMK.rows = function () { var f = AMK.f, g = AMK.range(); if (!g) return []; return amAllInfo().filter(function (I) { var x = I.x, dt = String(x.date || ''); return x.on && dt >= g[0] && dt <= g[1] && (!f.shift || String(x.shift || '') === f.shift); })
      .sort(function (a, b) { return String(a.x.date).localeCompare(String(b.x.date)) || String(a.x.shift).localeCompare(String(b.x.shift)) || b.x.top - a.x.top || String(a.code).localeCompare(String(b.code)); }); };
  function elsOf(R) { var o = []; R.forEach(function (I) { (I.elA || []).forEach(function (e) { if (o.indexOf(e) < 0) o.push(e); }); }); return o; }
  function agg(R, els) { var t = 0, b = 0, g = {}, w = {}; R.forEach(function (I) { if (!I.calc) return; t += I.ton || 0; b += I.bcm || 0; els.forEach(function (e) { var v = I.el && I.el[e]; if (isFinite(v)) { g[e] = (g[e] || 0) + v * I.ton; w[e] = (w[e] || 0) + I.ton; } }); }); var o = {}; els.forEach(function (e) { o[e] = w[e] ? g[e] / w[e] : NaN; }); return { t: t, b: b, g: o }; }
  AMK.tsv = function () { var R = AMK.rows(), els = elsOf(R), h = ['Tanggal', 'Shift', 'Kode', 'Flitch', 'Ore', 'Tujuan', 'BCM', 'Ton'].concat(els).concat(['Status']);
    return [h.join('\t')].concat(R.map(function (I) { var x = I.x; return [x.date, x.shift, I.code, lyNum(x.top) + '-' + lyNum(x.bot), I.ore, I.dest, I.calc ? I.bcm.toFixed(1) : '', I.calc ? I.ton.toFixed(1) : ''].concat(els.map(function (e) { var v = I.el && I.el[e]; return isFinite(v) ? (+v).toFixed(3) : ''; })).concat([I.lk ? 'TERKUNCI' : I.calc ? (I.lkBaru ? 'ditambah setelah dikunci' : 'belum dikunci') : 'BELUM DIHITUNG']).join('\t'); })).join('\r\n'); };
  AMK.copy = function () { var t = AMK.tsv(), ok = false; try { if (window.amCopyFb) ok = amCopyFb(t); } catch (e) {} var m = document.getElementById('amkMsg'); if (m) m.textContent = ok ? 'Tersalin — tempel (Ctrl+V) di Excel.' : 'Gagal menyalin.'; };
  AMK.csv = function () { var f = AMK.f, t = AMK.tsv().split('\r\n').map(function (l) { return l.split('\t').map(function (v) { return /[;"\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(';'); }).join('\r\n');
    dgDl('﻿' + t + '\r\n', 'Report_AsMined_' + (f.date || 'tanggal') + (f.shift ? '_' + f.shift : '') + '.csv', 'text/csv'); };
  AMK.set = function (k, v) { AMK.f[k] = v; AMK.render(); };
  AMK.tanggal = function () { var o = {}; amBndAll().forEach(function (x) { if (x.date) o[x.date] = 1; }); return Object.keys(o).sort().reverse(); };
  /* Report As-Mined harian ada DI DALAM panel "Register untuk database" (pemilik 10-11-2026: "Tidak perlu pop up lah buat
     menu ini. Pakai saja panel Register untuk Database"). Tanggal + shift yang dipilih di sini juga menjadi cakupan
     Salin ke Excel / Register CSV / Kirim ke workbook di bawahnya (amRegRows dibungkus). Tanggal kosong = semua. */
  AMK.render = function () { try { amPanel(); } catch (e) {} };
  AMK.open = function () { if (!BX.m) { alert('Buka block model dulu.'); return; } try { if (window.PT && PT.select) PT.select('reg.db'); else { uiTab('AM'); amPanel(); } } catch (e) {} };
  AMK.keXl = function () { var e = document.getElementById('amXlWrap'); if (e) { e.scrollIntoView({ block: 'start', behavior: 'smooth' }); e.classList.add('amkhl'); setTimeout(function () { e.classList.remove('amkhl'); }, 2500); } };
  (function () {
    var _cp = window.amRegCopy; if (typeof _cp === 'function') window.amRegCopy = amRegCopy = function () { var rows = amRegRows(), r = _cp.apply(this, arguments); var m = document.getElementById('amRegMsg'); if (rows.length && !(m && /gagal/i.test(m.textContent))) AMK.lockRows(rows, 'disalin ke Excel'); return r; };
    var _csv = window.amRegCsv; if (typeof _csv === 'function') window.amRegCsv = amRegCsv = function () { var rows = amRegRows(); if (!rows.length) return _csv.apply(this, arguments);
      /* simpan berkas bisa dibatalkan di dialog Simpan: kunci hanya bila berkasnya benar-benar tersimpan */
      var _gs = window.gxSimpan, pakai = false; if (typeof _gs === 'function') { var w = function () { var p = _gs.apply(this, arguments); window.gxSimpan = _gs; try { gxSimpan = _gs; } catch (e) {} pakai = true; Promise.resolve(p).then(function (v) { if (v) AMK.lockRows(rows, 'diekspor ke CSV'); }); return p; }; window.gxSimpan = w; try { gxSimpan = w; } catch (e) {} }
      try { return _csv.apply(this, arguments); } finally { if (!pakai && typeof _gs === 'function') { window.gxSimpan = _gs; try { gxSimpan = _gs; } catch (e) {} } } };
    var _xs = window.amXlSend; if (typeof _xs === 'function') window.amXlSend = amXlSend = async function () { var rows = amRegRows(), r = await _xs.apply(this, arguments); if (AM.xl && AM.xl.res) AMK.lockRows(rows, 'dikirim ke workbook'); return r; };
  })();
  var _rr = window.amRegRows; if (typeof _rr === 'function') { window.amRegRows = amRegRows = function () { var f = AMK.f; if (!f.date) return _rr.apply(this, arguments);
      var keep = {}; AMK.rows().forEach(function (I) { keep[I.code] = 1; }); return _rr.apply(this, arguments).filter(function (r) { return keep[r[0]]; }); }; }
  AMK.inline = function () { var f = AMK.f, T = AMK.tanggal(); if (f.date === undefined || f._init !== 1) { f.date = T[0] || ''; f._init = 1; }
    var sh = f.shift ? [f.shift] : ['DS', 'NS'], R = f.date ? AMK.rows() : [], els = elsOf(R).slice(0, 3);
    var md = f.mode || 'hari', g = AMK.range(), lbl = { hari: 'Harian', minggu: 'Mingguan', bulan: 'Bulanan', rentang: 'Rentang tanggal' }[md], per = g ? (g[0] === g[1] ? amDateTxt(g[0]) : amDateTxt(g[0]) + ' s/d ' + amDateTxt(g[1])) : '';
    /* tata letak (pemilik 10-11-2026 "tombol menu tidak sejajar"): label pendek satu baris, isian sama tinggi */
    var h = '<div class=amset><div class=amst><b>&#128197; Report As-Mined ' + lbl.toLowerCase() + '</b></div>' +
      '<div class=amkf><div><label>Periode</label><select onchange="AMK.set(\'mode\',this.value)">' + [['hari', 'Harian'], ['minggu', 'Mingguan (Sen–Min)'], ['bulan', 'Bulanan'], ['rentang', 'Rentang tanggal']].map(function (o) { return '<option value=' + o[0] + (o[0] === md ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select></div>' +
      '<div><label>Shift</label><select onchange="AMK.set(\'shift\',this.value)"><option value=""' + (f.shift ? '' : ' selected') + '>DS + NS</option><option value=DS' + (f.shift === 'DS' ? ' selected' : '') + '>DS</option><option value=NS' + (f.shift === 'NS' ? ' selected' : '') + '>NS</option></select></div></div>' +
      '<div class=amkf style="margin-top:6px"><div><label>' + (md === 'rentang' ? 'Dari' : md === 'hari' ? 'Tanggal' : 'Tanggal di dalam periode') + '</label><input type=date value="' + E(f.date) + '" onchange="AMK.set(\'date\',this.value)"></div>' +
      (md === 'rentang' ? '<div><label>Sampai</label><input type=date value="' + E(f.date2 || f.date) + '" onchange="AMK.set(\'date2\',this.value)"></div>' : '<div><label>Tanggal berpoligon</label><select onchange="AMK.set(\'date\',this.value)"><option value=""' + (f.date ? '' : ' selected') + '>Semua (tanpa kunci)</option>' + T.slice(0, 120).map(function (d) { return '<option value="' + d + '"' + (d === f.date ? ' selected' : '') + '>' + E(amDateTxt(d)) + '</option>'; }).join('') + '</select></div>') + '</div>' +
      '<div class=hint style="margin-top:2px">' + (g ? 'Periode <b>' + E(per) + '</b>' + (f.shift ? ' shift ' + f.shift : '') + ' &middot; semua flitch &middot; = cakupan Salin / CSV / Kirim di bawah.' : '') + '</div>';
    if (!f.date) return h + '<div class=hint>Semua tanggal: salin / kirim memakai seluruh register (cara lama) dan <b>tidak mengunci</b>. Pilih tanggal untuk report: pada mode harian poligon terkunci otomatis saat laporannya keluar.</div></div>';
    if (!AMK.harian()) { var nb2 = R.filter(function (I) { return I.calc && !I.lk; }).length; h += '<div class=hint>' + (nb2 ? '<span class=warn>' + nb2 + ' poligon di periode ini belum dilaporkan harian (belum terkunci)</span> &mdash; ' : '&#128274; Semua poligon periode ini sudah terkunci. ') + 'Report mingguan / bulanan <b>tidak mengunci</b>; kunci terjadi pada report harian.</div>'; }
    else h += '<div class=amkst>' + sh.map(function (s) { var k = f.date + '|' + s, r = LK()[k], P = R.filter(function (I) { return I.x.shift === s; }); if (!P.length && !r) return '<span class=hint>' + s + ': tidak ada poligon</span>';
      var nb = P.filter(function (I) { return !I.lk && I.calc; }).length;
      return '<div>' + (r ? '<span class=lk>&#128274; ' + s + ' terkunci</span> <small>' + E(tLk(r)) + (r.via ? ' &middot; ' + E(r.via) : '') + '</small> <button onclick="AMK.unlock(\'' + f.date + '\',\'' + s + '\')">Buka kunci</button>' : '<span>' + s + ': belum dilaporkan</span>') +
        (nb ? '<div class=hint style="margin:0">' + nb + ' poligon ' + (r ? 'baru ' : '') + 'akan terkunci otomatis saat <b>Salin ke Excel</b>, <b>Register CSV</b> atau <b>Kirim ke workbook</b> di bawah.</div>' : '') + '</div>'; }).join('') + '</div>';
    if (!R.length) return h + '<div class=hint>Tidak ada poligon pada ' + E(per) + (f.shift ? ' shift ' + f.shift : '') + '.</div></div>';
    var sel = function (I) { return '<tr><td title="' + E(I.code) + '">' + (I.lk ? '&#128274; ' : '') + (AMK.harian() ? '' : E(amDateTxt(I.x.date)).replace(/-\d+$/, '') + ' ') + E(I.x.shift) + ' &middot; ' + E(String(I.x.blk || I.code).slice(0, 14)) + '</td><td>' + E(lyNum(I.x.top)) + '</td><td>' + (I.calc ? N(I.ton, 1) : '<span class=warn>belum dihitung</span>') + '</td>' + els.map(function (e) { var v = I.el && I.el[e]; return '<td>' + (I.calc && isFinite(v) ? N(v, 3) : '-') + '</td>'; }).join('') + '</tr>'; };
    var tot = function (lab, P, cls) { var a = agg(P, els); return '<tr class=' + cls + '><td>' + lab + '</td><td></td><td>' + N(a.t, 1) + '</td>' + els.map(function (e) { return '<td>' + N(a.g[e], 3) + '</td>'; }).join('') + '</tr>'; };
    h += '<div class=amktb><table class=pltb><tr><th>Shift &middot; block</th><th>RL</th><th>Ton</th>' + els.map(function (e) { return '<th>' + E(e) + '</th>'; }).join('') + '</tr>';
    if (AMK.harian()) sh.forEach(function (s) { var P = R.filter(function (I) { return I.x.shift === s; }); if (!P.length) return; h += P.map(sel).join(''); if (sh.length > 1) h += tot('Subtotal ' + s, P, 'sub'); });
    else { var D = []; R.forEach(function (I) { if (D.indexOf(I.x.date) < 0) D.push(I.x.date); }); D.forEach(function (d) { var P = R.filter(function (I) { return I.x.date === d; }); h += P.map(sel).join('') + tot('Subtotal ' + amDateTxt(d), P, 'sub'); }); }
    h += tot('TOTAL ' + per, R, 'tot') + '</table></div>';
    if (R.some(function (I) { return I.x.tampal; })) h += '<div class="hint warn">&#9888; Ada poligon yang tampalannya dengan poligon terkunci tidak dikurangkan.</div>';
    if (R.some(function (I) { return !I.calc; })) h += '<div class="hint warn">Poligon "belum dihitung" tidak masuk total &amp; register: buka flitch-nya lalu Hitung.</div>';
    var nLk = R.filter(function (I) { return I.lk; }).length;
    h += '<div class=hint>' + R.length + ' poligon (' + nLk + ' terkunci). Kadar tertimbang tonase. ' + '<a href="javascript:void(0)" onclick="AMK.keXl()">&darr; Kirim ke workbook</a> &middot; ' + 'Salin / CSV / Kirim di bawah hanya memakai baris tanggal ini.</div></div>';
    return h; };
  (function () { var st = document.createElement('style'); st.textContent = '#amBody .amkf{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:6px;align-items:end}#amBody .amkf label,#amBody .amkf1 label{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:2px}#amBody .amkf input,#amBody .amkf select,#amBody .amkf1 select{width:100%;height:30px;box-sizing:border-box;margin:0}#amBody .amkf1{margin-top:6px}#amBody .amkst{display:flex;flex-direction:column;gap:4px;margin:4px 0}#amBody .amkst .lk{color:#7048e8;font-weight:700}#amBody .amktb{overflow-x:auto;margin-top:4px}#amBody .amktb table{font-size:11px;width:100%}#amBody .amktb td,#amBody .amktb th{white-space:nowrap;padding:2px 4px;text-align:right}#amBody .amktb td:first-child,#amBody .amktb th:first-child{text-align:left}#amBody .amktb tr.sub td{background:var(--prs,#eef2fb);font-weight:600}#amBody .amktb tr.tot td{font-weight:700;border-top:2px solid var(--bd)}#amXlWrap.amkhl{outline:3px solid #7048e8;outline-offset:2px;border-radius:6px;transition:outline .3s}'; document.head.appendChild(st); })();
})();
