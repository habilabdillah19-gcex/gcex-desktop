/* ================= GC-Ex Block Model 0.24.58: As-Mined — KUNCI TANGGAL-SHIFT, REPORT PER TANGGAL, TAMPALAN =================
   Keputusan pemilik (10 Nov 2026):
   - Model as-mined dipakai untuk laporan produksi harian (tonase x kadar) pada hari poligon dibuat. Poligon & model hari
     yang sudah dilaporkan TIDAK boleh berubah ketika dua minggu kemudian flitch yang sama digali lagi di tempat lain.
   - Satuan kunci = TANGGAL-SHIFT (satu tombol untuk semua poligon hari & shift itu), bukan per poligon.
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
    '.gxpop table{border-collapse:collapse;width:100%;font-size:11.5px}.gxpop th,.gxpop td{border-bottom:1px solid var(--bd);padding:3px 5px;text-align:right;white-space:nowrap}.gxpop th:nth-child(-n+5),.gxpop td:nth-child(-n+5){text-align:left}.gxpop tr.tot td{font-weight:700;border-top:2px solid var(--bd)}.gxpop tr.sub td{font-weight:600;background:var(--prs,#eef2fb)}' +
    '.gxpop .rpt{display:flex;flex-wrap:wrap;gap:6px;align-items:end;margin-bottom:6px}.gxpop .rpt label{display:block;font-size:11px;color:var(--mu)}.gxpop .lk{color:#7048e8;font-weight:700}.gxpop .warn{color:var(--dn,#c92a2a)}'; document.head.appendChild(st); })();

  /* ---------- Report As-Mined per tanggal ---------- */
  AMK.f = AMK.f || { date: '', shift: '' };
  AMK.rows = function () { var f = AMK.f; return amAllInfo().filter(function (I) { var x = I.x; return x.on && String(x.date || '') === f.date && (!f.shift || String(x.shift || '') === f.shift); })
      .sort(function (a, b) { return String(a.x.shift).localeCompare(String(b.x.shift)) || b.x.top - a.x.top || String(a.code).localeCompare(String(b.code)); }); };
  function elsOf(R) { var o = []; R.forEach(function (I) { (I.elA || []).forEach(function (e) { if (o.indexOf(e) < 0) o.push(e); }); }); return o; }
  function agg(R, els) { var t = 0, b = 0, g = {}, w = {}; R.forEach(function (I) { if (!I.calc) return; t += I.ton || 0; b += I.bcm || 0; els.forEach(function (e) { var v = I.el && I.el[e]; if (isFinite(v)) { g[e] = (g[e] || 0) + v * I.ton; w[e] = (w[e] || 0) + I.ton; } }); }); var o = {}; els.forEach(function (e) { o[e] = w[e] ? g[e] / w[e] : NaN; }); return { t: t, b: b, g: o }; }
  AMK.tsv = function () { var R = AMK.rows(), els = elsOf(R), h = ['Tanggal', 'Shift', 'Kode', 'Flitch', 'Ore', 'Tujuan', 'BCM', 'Ton'].concat(els).concat(['Status']);
    return [h.join('\t')].concat(R.map(function (I) { var x = I.x; return [x.date, x.shift, I.code, lyNum(x.top) + '-' + lyNum(x.bot), I.ore, I.dest, I.calc ? I.bcm.toFixed(1) : '', I.calc ? I.ton.toFixed(1) : ''].concat(els.map(function (e) { var v = I.el && I.el[e]; return isFinite(v) ? (+v).toFixed(3) : ''; })).concat([I.lk ? 'TERKUNCI' : I.calc ? (I.lkBaru ? 'ditambah setelah dikunci' : 'belum dikunci') : 'BELUM DIHITUNG']).join('\t'); })).join('\r\n'); };
  AMK.copy = function () { var t = AMK.tsv(), ok = false; try { if (window.amCopyFb) ok = amCopyFb(t); } catch (e) {} var m = document.getElementById('amkMsg'); if (m) m.textContent = ok ? 'Tersalin — tempel (Ctrl+V) di Excel.' : 'Gagal menyalin.'; };
  AMK.csv = function () { var f = AMK.f, t = AMK.tsv().split('\r\n').map(function (l) { return l.split('\t').map(function (v) { return /[;"\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(';'); }).join('\r\n');
    dgDl('﻿' + t + '\r\n', 'Report_AsMined_' + (f.date || 'tanggal') + (f.shift ? '_' + f.shift : '') + '.csv', 'text/csv'); };
  AMK.set = function (k, v) { AMK.f[k] = v; AMK.render(); };
  AMK.tanggal = function () { var o = {}; amBndAll().forEach(function (x) { if (x.date) o[x.date] = 1; }); return Object.keys(o).sort().reverse(); };
  AMK.render = function () { var w = document.getElementById('amkPop'); if (!w || w.style.display === 'none') return; AMK.open(true); };
  AMK.open = function (diam) { if (!BX.m) { alert('Buka block model dulu.'); return; } var f = AMK.f, T = AMK.tanggal(); if (!f.date) f.date = T[0] || amToday();
    var R = AMK.rows(), els = elsOf(R), h = '<div class=rpt><div><label>Tanggal</label><input type=date value="' + E(f.date) + '" onchange="AMK.set(\'date\',this.value)"></div><div><label>Shift</label><select onchange="AMK.set(\'shift\',this.value)"><option value=""' + (f.shift ? '' : ' selected') + '>Semua (DS + NS)</option><option value=DS' + (f.shift === 'DS' ? ' selected' : '') + '>DS &middot; Siang</option><option value=NS' + (f.shift === 'NS' ? ' selected' : '') + '>NS &middot; Malam</option></select></div>' +
      (T.length ? '<div><label>Tanggal yang punya poligon</label><select onchange="if(this.value)AMK.set(\'date\',this.value)"><option value="">&mdash; pilih &mdash;</option>' + T.slice(0, 120).map(function (d) { return '<option value="' + d + '">' + E(amDateTxt(d)) + '</option>'; }).join('') + '</select></div>' : '') +
      '<div style="margin-left:auto;display:flex;gap:4px"><button onclick="AMK.copy()"' + (R.length ? '' : ' disabled') + '>Salin ke Excel</button><button onclick="AMK.csv()"' + (R.length ? '' : ' disabled') + '>CSV</button></div></div>';
    /* status kunci per shift */
    var sh = f.shift ? [f.shift] : ['DS', 'NS'];
    h += '<div class=rpt>' + sh.map(function (s) { var k = f.date + '|' + s, r = LK()[k], P = R.filter(function (I) { return I.x.shift === s; }); if (!P.length && !r) return '<span class=hint>' + s + ': tidak ada poligon</span>';
      return r ? '<span class=lk>&#128274; ' + s + ' terkunci ' + E(tLk(r)) + ' (' + r.n + ' poligon, ' + N(r.ton) + ' t)</span> <button onclick="AMK.unlock(\'' + f.date + '\',\'' + s + '\')">Buka kunci ' + s + '</button>' + (P.some(function (I) { return I.lkBaru; }) ? ' <button onclick="AMK.lock(\'' + f.date + '\',\'' + s + '\')" title="Ikut kunci poligon yang ditambahkan setelah dikunci">Kunci yang baru</button>' : '')
        : '<button class=btn-pri onclick="if(confirm(\'Kunci laporan ' + E(amDateTxt(f.date)) + ' shift ' + s + '?\\n\\nSemua poligon hari & shift ini dibekukan: tidak dihitung ulang, tidak bisa diedit / dihapus sampai kuncinya dibuka.\'))AMK.lock(\'' + f.date + '\',\'' + s + '\')">&#128274; Kunci ' + s + ' (' + P.length + ' poligon)</button>'; }).join(' ') + '</div>';
    if (!R.length) h += '<div class=hint>Tidak ada poligon as-mined bertanggal ' + E(amDateTxt(f.date)) + (f.shift ? ' shift ' + f.shift : '') + '. Tanggal & shift poligon diisi di panel As-Mined (Default poligon berikutnya / edit poligon).</div>';
    else { h += '<table><tr><th>Shift</th><th>Kode</th><th>Flitch</th><th>Ore</th><th>Tujuan</th><th>BCM</th><th>Ton</th>' + els.map(function (e) { return '<th>' + E(e) + '</th>'; }).join('') + '<th>Status</th></tr>';
      var baris = function (I) { var x = I.x; return '<tr><td>' + E(x.shift) + '</td><td>' + E(I.code) + '</td><td>' + E(lyNum(x.top) + '–' + lyNum(x.bot)) + '</td><td>' + E(I.ore) + '</td><td>' + E(I.dest) + '</td><td>' + (I.calc ? N(I.bcm, 1) : '-') + '</td><td>' + (I.calc ? N(I.ton, 1) : '-') + '</td>' + els.map(function (e) { var v = I.el && I.el[e]; return '<td>' + (I.calc && isFinite(v) ? N(v, 3) : '-') + '</td>'; }).join('') +
          '<td>' + (I.lk ? '<span class=lk>&#128274; terkunci</span>' : !I.calc ? '<span class=warn>belum dihitung</span>' : I.lkBaru ? '<span class=warn>ditambah setelah dikunci</span>' : 'belum dikunci') + (x.tampal ? ' <span class=warn title="Tampalan dengan poligon terkunci tidak dikurangkan">&#9888; tampal ' + E(x.tampal) + '</span>' : '') + '</td></tr>'; };
      var tot = function (lab, P, cls) { var a = agg(P, els); return '<tr class=' + cls + '><td colspan=5>' + lab + '</td><td>' + N(a.b, 1) + '</td><td>' + N(a.t, 1) + '</td>' + els.map(function (e) { return '<td>' + N(a.g[e], 3) + '</td>'; }).join('') + '<td></td></tr>'; };
      sh.forEach(function (s) { var P = R.filter(function (I) { return I.x.shift === s; }); if (!P.length) return; h += P.map(baris).join(''); if (sh.length > 1) h += tot('Subtotal ' + s, P, 'sub'); });
      h += tot('TOTAL ' + amDateTxt(f.date) + (f.shift ? ' ' + f.shift : ''), R, 'tot') + '</table>';
      if (R.some(function (I) { return !I.calc; })) h += '<div class="hint warn">Poligon "belum dihitung" tidak masuk total: buka flitch-nya di As-Mined lalu tekan Hitung.</div>'; }
    h += '<div class=hint id=amkMsg>Kadar = rata-rata tertimbang tonase. Poligon terkunci memakai angka beku saat dikunci; poligon lain memakai hasil Hitung terakhir.</div>';
    AMK.pop('amkPop', 'Report As-Mined per tanggal', h); };
})();
