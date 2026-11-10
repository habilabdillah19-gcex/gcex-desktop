/* ============ AS-MINED: penyesuaian sesudah diuji dengan data nyata (GC-Ex Block Model 0.24.54) ============
   Sumber: review 10-11-2026 dengan pick-up OB (atap), PROG (lantai) dan block model GC pit pemilik.
   1. Boundary dari CSV pick-up OB: titik berurutan = satu poligon tertutup. RL flitch, tanggal dan pit dibaca
      dari NAMA FILE (pola pemilik: ACT_SO261106OB_272-5_271_Z3.csv). Titiknya sekaligus jadi titik ATAP.
   2. Kelas kadar As-Mined mengikuti aturan block model (atribut kalkulasi IIF kolom material), bukan bawaan aplikasi.
   3. (di gcex_base.html, bxDefUI) kolom SG model dipakai otomatis.
   4. (lihat 1) tanggal / pit / flitch dari nama file.
   5. 3D hasil kerja: SOLID as-mined = poligon OB di antara permukaan atap dan lantai yang dipakai hitungan
      (bukan kubus sub-blok ukuran penuh, yang melebihkan volume di layar).
   6. Zoom ke poligon as-mined (3D: kamera; plan 2D: rentang sumbu).
   Material di luar poligon OB TIDAK dihitung (keputusan pemilik): dilusi hanya yang di dalam poligon OB.          */
(function () {
  if (window.AMN || typeof amBndAdd !== 'function') return;
  var $ = function (i) { return document.getElementById(i); }, AMN = window.AMN = {};
  /* ---------- nama file -> flitch, tanggal, pit ---------- */
  AMN.nama = function (nm) { var b = String(nm || '').replace(/\.[^.]+$/, ''), o = { top: NaN, bot: NaN, date: '', pit: '' }, re = /(?:^|_)(\d{1,4}(?:-\d{1,2})?)_(\d{1,4}(?:-\d{1,2})?)(?=_|$)/g, m, end = -1;
    while ((m = re.exec(b))) { var a = parseFloat(m[1].replace('-', '.')), c = parseFloat(m[2].replace('-', '.')), t = Math.max(a, c), bo = Math.min(a, c); if (t - bo > 0 && t - bo <= 12) { o.top = t; o.bot = bo; end = m.index + m[0].length; } re.lastIndex = m.index + 1; }
    /* tanggal: enam angka yymmdd pertama yang sah (sesudah huruf), mis. SO261106 / PROG261107; angka ke-7 (salah ketik) diabaikan */
    var d = /[A-Za-z](\d{2})(\d{2})(\d{2})\d?(?=[A-Za-z_]|$)/.exec(b); if (d && +d[2] >= 1 && +d[2] <= 12 && +d[3] >= 1 && +d[3] <= 31) o.date = '20' + d[1] + '-' + d[2] + '-' + d[3];
    /* pit: potongan terakhir sesudah flitch, atau potongan terakhir nama bila pendek (Z3, Z4, PIT2) */
    var tail = end >= 0 ? b.slice(end).replace(/^_/, '') : (b.indexOf('_') >= 0 ? b.split('_').pop() : ''); if (/^[A-Za-z][A-Za-z0-9]{0,7}$/.test(tail)) o.pit = tail.toUpperCase(); return o; };
  /* ---------- CSV pick-up (tanpa / dengan judul): ID,X,Y,Z,kode ---------- */
  function csvPts(txt) { var L = String(txt).replace(/^﻿/, '').split(/\r?\n/).filter(function (l) { return l.trim() !== ''; }); if (!L.length) return []; var dl = ',', bn = -1; [',', ';', '\t'].forEach(function (c) { var n = L[0].split(c).length; if (n > bn) { bn = n; dl = c; } });
    var R = L.map(function (l) { return l.split(dl).map(function (v) { return v.trim().replace(/^"|"$/g, ''); }); }), num = function (v) { var x = parseFloat(String(v).replace(',', '.')); return isFinite(x) ? x : NaN; };
    if (R[0].some(function (v) { return v !== '' && !isFinite(num(v)); })) R = R.slice(1); var nc = 0; R.forEach(function (r) { if (r.length > nc) nc = r.length; });
    var med = function (c) { var v = []; R.slice(0, 200).forEach(function (r) { var t = num(r[c]); if (isFinite(t)) v.push(Math.abs(t)); }); if (!v.length) return NaN; v.sort(function (a, b) { return a - b; }); return v[v.length >> 1]; }, j = -1; for (var c = 0; c + 1 < nc; c++) if (med(c) >= 1000 && med(c + 1) >= 1000) { j = c; break; } if (j < 0) j = nc >= 4 ? 1 : 0;
    var out = []; R.forEach(function (r) { var x = num(r[j]), y = num(r[j + 1]), z = num(r[j + 2]); if (isFinite(x) && isFinite(y)) out.push([x, y, z, j > 0 ? String(r[j - 1] || '') : '', String(r[j + 3] || '')]); }); return out; }
  AMN.csvPts = csvPts;
  function memotong(P) { var n = P.length, X = function (a, b, c, d) { var r = [b[0] - a[0], b[1] - a[1]], s = [d[0] - c[0], d[1] - c[1]], den = r[0] * s[1] - r[1] * s[0]; if (Math.abs(den) < 1e-12) return false; var q = [c[0] - a[0], c[1] - a[1]], t = (q[0] * s[1] - q[1] * s[0]) / den, u = (q[0] * r[1] - q[1] * r[0]) / den; return t > 1e-9 && t < 1 - 1e-9 && u > 1e-9 && u < 1 - 1e-9; };
    for (var i = 0; i < n; i++) for (var k = i + 2; k < n; k++) { if (i === 0 && k === n - 1) continue; if (X(P[i], P[(i + 1) % n], P[k], P[(k + 1) % n])) return true; } return false; }
  /* ---------- 1 & 4. import boundary: CSV ditangani di sini, STR / DXF tetap oleh pembaca lama ---------- */
  (function () { var _f = window.amBndFile; window.amBndFile = function (files) { var L = Array.prototype.slice.call(files || []), C = L.filter(function (f) { return /\.(csv|txt)$/i.test(f.name); }), S = L.filter(function (f) { return !/\.(csv|txt)$/i.test(f.name); });
      if (!C.length) return _f.apply(this, arguments);
      (async function () { var info = [], R = amR(), D = amD();
        for (var i = 0; i < C.length; i++) { var f = C[i]; try { var Q = csvPts(await f.text()), P = [], last = null; Q.forEach(function (q) { if (!last || Math.hypot(q[0] - last[0], q[1] - last[1]) > 0.02) { P.push(q); last = q; } }); if (P.length > 3 && Math.hypot(P[0][0] - P[P.length - 1][0], P[0][1] - P[P.length - 1][1]) < 0.02) P.pop();
            if (P.length < 3) { info.push('<span class=warn>' + amE(f.name) + ': kurang dari 3 titik</span>'); continue; }
            var N = AMN.nama(f.name), opt = { top: N.top, bot: N.bot, date: N.date, pit: N.pit, src: f.name }, nm = f.name.replace(/\.[^.]+$/, '');
            if (!isFinite(N.top)) { var B0 = lyBench(); opt.top = NaN; opt.bot = NaN; }
            var ok = amBndAdd(P.map(function (q) { return [q[0], q[1], q[2]]; }), nm, opt); if (!ok) { info.push('<span class=warn>' + amE(f.name) + ': poligon yang sama sudah ada di flitch itu</span>'); continue; }
            if (N.pit && !R.pit) R.pit = N.pit;
            /* titik OB = titik ATAP galian: disimpan juga ke titik atap (file bernama sama diganti) */
            D.ptsR = (D.ptsR || []).filter(function (q) { return q.f !== f.name; }); Q.forEach(function (q) { if (isFinite(q[2])) D.ptsR.push({ x: q[0], y: q[1], z: q[2], id: q[3], c: q[4], f: f.name }); });
            var Bx = AM.lastFl || lyBench(), cross = memotong(P);
            info.push(amE(f.name) + ': 1 poligon ' + P.length + ' titik &rarr; flitch RL ' + lyFmt(Bx[0]) + '&ndash;' + lyFmt(Bx[1]) + (isFinite(N.top) ? ' (dari nama file)' : ' <span class=warn>(nama file tanpa RL: memakai flitch aktif)</span>') + (N.date ? ' &middot; tanggal ' + N.date : '') + (N.pit ? ' &middot; pit ' + amE(N.pit) : '') + ' &middot; titiknya juga jadi titik atap' +
              (cross ? '<br><span class=warn>Urutan titik membuat poligon memotong dirinya sendiri: file ini mungkin berisi lebih dari satu dig block. Periksa di plan, perbaiki dengan Edit bentuk atau digit ulang.</span>' : ''));
          } catch (e) { info.push('<span class=warn>' + amE(f.name) + ': ' + amE(e.message) + '</span>'); } }
        AM.bmsg = info.join('<br>'); amPanel(); updatePlot(); amDirty(); if (S.length) _f.call(window, S); })(); }; })();
  /* ---------- 2. kelas kadar dari block model ---------- */
  AMN.kelasModel = function () { var m = BX.m; if (!m) return null; var U = amU(), ga = U.attr, ex = (m.mdl && m.mdl.expr) || {}, best = null;
    Object.keys(ex).forEach(function (nm) { var e = ex[nm], v = String(ga).replace(/[^A-Za-z0-9_]/g, ''); if (!new RegExp('\\b' + v + '\\b', 'i').test(e)) return;
      var re = new RegExp('\\b' + v + '\\s*>=\\s*([0-9.]+)\\s*(?:AND\\s+' + v + '\\s*<\\s*([0-9.]+)\\s*)?,\\s*"([^"]+)"', 'ig'), mm, L = []; while ((mm = re.exec(e))) L.push({ m: mm[3].toUpperCase(), lo: +mm[1], hi: mm[2] === undefined ? '' : +mm[2] });
      if (L.length >= 2 && (!best || L.length > best.L.length)) best = { L: L, src: 'aturan kolom ' + nm + ' di block model' }; });
    if (!best) { /* tanpa rumus: batas dari data -- kadar terendah tiap kategori kolom material */ var cn = Object.keys(m.cat).filter(function (n) { return /mat|class|kelas|ore/i.test(n); })[0], G = m.num[ga]; if (cn && G) { var C = m.cat[cn], lo = {}, st = Math.max(1, Math.floor(m.n / 200000)); for (var i = 0; i < m.n; i += st) { var k = C.dict[C.codes[i]], g = G[i]; if (k == null || !isFinite(g)) continue; if (lo[k] === undefined || g < lo[k]) lo[k] = g; }
        var L2 = Object.keys(lo).map(function (k) { return { m: String(k).toUpperCase(), lo: +lo[k].toFixed(2) }; }).filter(function (q) { return q.lo > 0; }).sort(function (a, b) { return a.lo - b.lo; }); L2.forEach(function (q, i) { q.hi = i + 1 < L2.length ? L2[i + 1].lo : ''; }); if (L2.length >= 2) best = { L: L2, src: 'kadar terendah tiap kategori kolom ' + cn + ' (perkiraan dari data)' }; } }
    return best; };
  var WARNA = { MO: ['#ffd43b', 13], LG: ['#4caf50', 14], HG: ['#ff1a1a', 17], SG: ['#c2185b', 18], VHG: ['#c2185b', 18] };
  AMN.pakaiKelas = function (diam) { var K = AMN.kelasModel(), R = amR(); if (!K) { if (!diam) alert('Block model ini tidak membawa aturan kelas (atribut kalkulasi IIF) maupun kolom material yang bisa dibaca.'); return false; }
    var lama = {}; (R.cls || []).forEach(function (q) { lama[q.m] = q; }); var n0 = 19;
    R.cls = K.L.filter(function (q) { return !/^(WASTE|WS|BLANK)$/i.test(q.m); }).map(function (q) { var w = WARNA[q.m] || (lama[q.m] ? [lama[q.m].c, lama[q.m].n] : ['#7048e8', n0++]); return { m: q.m, lo: q.lo, hi: q.hi, n: lama[q.m] ? lama[q.m].n : w[1], c: lama[q.m] ? lama[q.m].c : w[0] }; });
    /* tujuan: kelas baru di atas HG (mis. SG) ikut aturan HG bila belum punya aturan sendiri */
    R.cls.forEach(function (q) { if (!(R.dst || []).some(function (d) { return new RegExp('^' + String(d.o).replace(/\*/g, '.*') + '$', 'i').test(q.m + 'OX') || new RegExp('^' + String(d.o).replace(/\*/g, '.*') + '$', 'i').test(q.m + 'SF'); })) { var hg = (R.dst || []).filter(function (d) { return /^HG/i.test(d.o); })[0]; if (hg) R.dst.unshift({ o: q.m + '*', d: hg.d, l: hg.l, j: hg.j }); } });
    R.clsSrc = K.src; R.clsCek = 2; try { amBndAll().forEach(function (x) { x.ore = ''; }); } catch (e) {} if (!diam) { amPanel(); updatePlot(); } amDirty(); return true; };
  /* otomatis sekali per proyek: hanya bila kelas masih PERSIS bawaan aplikasi (belum pernah diubah pemakai) */
  (function () { var _r = window.amR, DEF = JSON.stringify([{ m: 'MO', lo: 0.3, hi: 0.5 }, { m: 'LG', lo: 0.5, hi: 1 }, { m: 'HG', lo: 1, hi: '' }]); window.amR = amR = function () { var R = _r.apply(this, arguments); try { if (!R.clsCek && BX.m) { R.clsCek = 1; if (JSON.stringify((R.cls || []).map(function (q) { return { m: q.m, lo: q.lo, hi: q.hi }; })) === DEF) AMN.pakaiKelas(true); } } catch (e) { console.error(e); } return R; }; })();
  /* ---------- 5. solid as-mined 3D ---------- */
  function dalam(P, x, y) { var c = false; for (var i = 0, j = P.length - 1; i < P.length; j = i++) { if (((P[i][1] > y) !== (P[j][1] > y)) && (x < (P[j][0] - P[i][0]) * (y - P[i][1]) / (P[j][1] - P[i][1]) + P[i][0])) c = !c; } return c; }
  AMN.solid = function (I) { var x = I.x, B = [+x.top, +x.bot], P = x.pts, o = { id: x.id, r: P, b: lyBB(P), area: lyArea(P), name: x.name }, R = amR(), rf = null, fl = null;
    /* fungsi atap / lantai dihitung dengan setelan flitch poligon itu sendiri */ var L = lyU(), sv = { fh: L.fh, top: L.top, bot: L.bot }; try { L.fh = +(B[0] - B[1]).toFixed(4); L.top = B[0]; L.bot = B[1]; rf = window.amRoofFn ? amRoofFn(o, B) : null; fl = (R.floor === 'pickup' && window.amFloorFn) ? amFloorFn(o, B) : null; } catch (e) {} finally { L.fh = sv.fh; L.top = sv.top; L.bot = sv.bot; }
    var zr = function (a, b) { var v = rf && rf.f ? rf.f(a, b) : B[0]; return isFinite(v) ? v : B[0]; }, zf = function (a, b, r) { var v = fl && fl.f ? fl.f(a, b) : B[1]; if (!isFinite(v)) v = B[1]; return v > r ? r : v; };
    var st = Math.max(0.35, Math.min(2, Math.sqrt(o.area) / 14)), ring = [], n = P.length, i; for (i = 0; i < n; i++) { var a = P[i], b = P[(i + 1) % n], d = Math.hypot(b[0] - a[0], b[1] - a[1]), k = Math.max(1, Math.ceil(d / st)); for (var q = 0; q < k; q++) ring.push([a[0] + (b[0] - a[0]) * q / k, a[1] + (b[1] - a[1]) * q / k]); }
    var pts = ring.slice(), bb = o.b; for (var gx = bb[0] + st / 2; gx < bb[1]; gx += st) for (var gy = bb[2] + st / 2; gy < bb[3]; gy += st) if (dalam(P, gx, gy)) { var dek = false; for (i = 0; i < ring.length && !dek; i += 2) dek = Math.hypot(ring[i][0] - gx, ring[i][1] - gy) < st * 0.45; if (!dek) pts.push([gx, gy]); }
    if (!window.Delaunator || pts.length < 3) return null; var T; try { T = Delaunator.from(pts).triangles; } catch (e) { return null; }
    var X = [], Y = [], Z = [], Ii = [], Jj = [], Kk = [], m = pts.length; pts.forEach(function (p) { var r = zr(p[0], p[1]); X.push(p[0] - offX); Y.push(p[1] - offY); Z.push(r); }); pts.forEach(function (p, k) { X.push(p[0] - offX); Y.push(p[1] - offY); Z.push(zf(p[0], p[1], Z[k])); });
    for (i = 0; i < T.length; i += 3) { var a2 = T[i], b2 = T[i + 1], c2 = T[i + 2]; if (!dalam(P, (pts[a2][0] + pts[b2][0] + pts[c2][0]) / 3, (pts[a2][1] + pts[b2][1] + pts[c2][1]) / 3)) continue; Ii.push(a2); Jj.push(b2); Kk.push(c2); Ii.push(m + a2); Jj.push(m + c2); Kk.push(m + b2); }
    var nr = ring.length; for (i = 0; i < nr; i++) { var j2 = (i + 1) % nr; Ii.push(i, j2); Jj.push(m + i, m + i); Kk.push(j2, m + j2); }
    var zs = Z.slice(0, m), zl = Z.slice(m), mean = function (A) { var t = 0; A.forEach(function (v) { t += v; }); return t / A.length; };
    return { x: X, y: Y, z: Z, i: Ii, j: Jj, k: Kk, atap: mean(zs), lantai: mean(zl), rf: !!(rf && rf.ok), fl: !!(fl && fl.ok) }; };
  if (window.AM3) { AM3.sol = true; AM3.sb = false; }
  (function () { var _t = window.am3Traces; if (typeof _t !== 'function') return; window.am3Traces = am3Traces = function (T) { var r = _t.apply(this, arguments); try { if (!AM3.sol) return r; var n = 0; amAllInfo().forEach(function (I) { var x = I.x; if (!x.on || !I.calc) return; var S = AMN.solid(I); if (!S) return; n++;
          T.push({ type: 'mesh3d', x: S.x, y: S.y, z: S.z, i: S.i, j: S.j, k: S.k, color: I.col || '#2b8a3e', opacity: 0.82, flatshading: true, lighting: { ambient: 0.6, diffuse: 0.7, specular: 0.1, roughness: 0.8 }, name: 'Solid as-mined ' + I.code + ' · ' + lyFmt(I.ton.toFixed(0)) + ' t @ ' + amF(I.gA, 2) + ' · atap ' + S.atap.toFixed(2) + ' lantai ' + S.lantai.toFixed(2), hoverinfo: 'name', showlegend: false, showscale: false }); });
        /* satu baris legenda untuk semua solid (dulu satu baris per poligon memenuhi layar); rinciannya di hover */ if (n) T.push({ type: 'scatter3d', mode: 'markers', x: [null], y: [null], z: [null], marker: { size: 9, color: '#2b8a3e', symbol: 'square' }, name: 'Solid as-mined (' + n + ' poligon, warna = kelas)', showlegend: true }); } catch (e) { console.error(e); } return r; }; })();
  /* ---------- 6. zoom ke poligon as-mined ---------- */
  AMN.zoom = function (semua) { var b = [1e18, -1e18, 1e18, -1e18, 1e18, -1e18], B = lyBench(), n = 0; amBndAll().forEach(function (x) { if (!x.on) return; if (!semua && !(Math.abs(x.top - B[0]) < 1e-6 && Math.abs(x.bot - B[1]) < 1e-6)) return; n++; x.pts.forEach(function (q) { var X = q[0] - offX, Y = q[1] - offY; if (X < b[0]) b[0] = X; if (X > b[1]) b[1] = X; if (Y < b[2]) b[2] = Y; if (Y > b[3]) b[3] = Y; }); if (x.bot - 0.5 < b[4]) b[4] = x.bot - 0.5; if (x.top + 0.5 > b[5]) b[5] = x.top + 0.5; });
    if (!n) { if (!semua) return AMN.zoom(true); alert('Belum ada poligon as-mined.'); return; }
    var go = function (k) { var gd = $('plotDiv'), L = gd && gd._fullLayout; if (!L) { if (k < 20) setTimeout(function () { go(k + 1); }, 150); return; }
      if (window.VIEW2D) { if (!L.xaxis || !L.xaxis.range) { if (k < 20) setTimeout(function () { go(k + 1); }, 150); return; } var mx = Math.max(5, (b[1] - b[0]) * 0.35), my = Math.max(5, (b[3] - b[2]) * 0.35), w = L.xaxis._length || 800, h = L.yaxis._length || 600, cx = (b[0] + b[1]) / 2 + offX, cy = (b[2] + b[3]) / 2 + offY, hx = (b[1] - b[0]) / 2 + mx, hy = (b[3] - b[2]) / 2 + my, sc = Math.max(hx / w, hy / h); try { Plotly.relayout(gd, { 'xaxis.range': [cx - sc * w, cx + sc * w], 'yaxis.range': [cy - sc * h, cy + sc * h] }); } catch (e) {} return; }
      var s3 = L.scene; if (!s3 || !s3.xaxis || !s3.xaxis.range) { if (k < 20) setTimeout(function () { go(k + 1); }, 150); return; } var ar = s3.aspectratio || { x: 1, y: 1, z: 1 }, f = function (ax, v, a) { var r = ax.range; return ((v - (r[0] + r[1]) / 2) / ((r[1] - r[0]) || 1)) * a; };
      var c = { x: f(s3.xaxis, (b[0] + b[1]) / 2, ar.x), y: f(s3.yaxis, (b[2] + b[3]) / 2, ar.y), z: f(s3.zaxis, (b[4] + b[5]) / 2, ar.z) }, sx = Math.abs(f(s3.xaxis, b[1], ar.x) - f(s3.xaxis, b[0], ar.x)), sy = Math.abs(f(s3.yaxis, b[3], ar.y) - f(s3.yaxis, b[2], ar.y)), sz = Math.abs(f(s3.zaxis, b[5], ar.z) - f(s3.zaxis, b[4], ar.z)), d = Math.max(0.02, Math.sqrt(sx * sx + sy * sy + sz * sz)) * 1.5;
      try { Plotly.relayout(gd, { 'scene.camera': { center: c, eye: { x: c.x + d * 0.62, y: c.y - d * 0.62, z: c.z + d * 0.5 }, up: { x: 0, y: 0, z: 1 } } }); } catch (e) {} };
    setTimeout(function () { go(0); }, 150); };
  (function () { var _g = window.am3Toggle; if (typeof _g === 'function') window.am3Toggle = am3Toggle = function () { var r = _g.apply(this, arguments); try { if (AM3.on) setTimeout(function () { AMN.zoom(true); }, 900); } catch (e) {} return r; }; })();
  /* ---------- 7. titik ATAP tampil & jadi sasaran snap saat mendigit (BM 0.24.56) ----------
     Laporan pemilik 10-11-2026: "sistem meminta mendigit poligon roof, tetapi titik roof tidak ada di jendela; yang tampak
     hanya titik floor". Plan as-mined hanya menggambar titik lantai (amD().pts); titik atap (amD().ptsR) tidak pernah
     digambar dan tidak bisa di-snap. Titik atap milik flitch = titik dari file yang RL flitch-nya (nama file) sama dengan
     flitch ini; file tanpa RL di namanya -> titik ber-Z antara RL bawah dan RL atas + toleransi tampil. */
  var flF = {}; function flFile(nm) { if (!(nm in flF)) { var o = AMN.nama(nm); flF[nm] = isFinite(o.top) ? o : null; } return flF[nm]; }
  AMN.roofNear = function (B) { B = B || lyBench(); var D = amD(), P = D.ptsR || [], t = (window.amPTol ? amPTol() : 3);
    if (D.pAll) return P.slice(); return P.filter(function (q) { var f = q.f && flFile(q.f); if (f) return Math.abs(f.top - B[0]) < 1e-3 && Math.abs(f.bot - B[1]) < 1e-3; return isFinite(q.z) && q.z >= B[1] && q.z <= B[0] + t; }); };
  (function () { var _t = window.amTraces2D; if (typeof _t !== 'function') return; window.amTraces2D = amTraces2D = function () { var out = _t.apply(this, arguments); try { var D = amD(), B = lyBench(), P = AMN.roofNear(B); if (!P.length) return out;
        var x = [], y = [], t = [], h = []; P.forEach(function (q) { x.push(q.x); y.push(q.y); t.push(D.plab ? (q.id || '') + (isFinite(q.z) ? ' ' + q.z.toFixed(2) : '') : ''); h.push('<b>ATAP</b> ' + (q.id ? amE(q.id) + ' ' : '') + (q.f ? '<br>' + amE(q.f) : '') + '<br>Z ' + (isFinite(q.z) ? q.z.toFixed(2) + ' &middot; &Delta; RL atas ' + (q.z - B[0] >= 0 ? '+' : '') + (q.z - B[0]).toFixed(2) + ' m' : '-')); });
        out.push({ type: 'scatter', mode: D.plab ? 'markers+text' : 'markers', x: x, y: y, text: t, hovertext: h, hoverinfo: 'text', textposition: 'bottom right', textfont: { size: 9, color: '#7048e8' }, marker: { symbol: 'x-thin-open', size: 11, color: '#7048e8', line: { width: 2.2, color: '#7048e8' } }, name: 'Pick-up ATAP (' + P.length + ')', showlegend: true }); } catch (e) { console.error(e); } return out; }; })();
  (function () { var _h = window.dgSnapHook; window.dgSnapHook = function (A, px, py) { if (AM.digOn && amD().snap !== false) { var best = 12, res = null; AMN.roofNear().forEach(function (q) { var p = dgPx(A, q.x, q.y), d = Math.hypot(p[0] - px, p[1] - py); if (d < best) { best = d; res = [q.x, q.y]; } }); if (res) return res; } return _h ? _h(A, px, py) : null; }; })();
  /* titik atap untuk hitungan: titik file ber-flitch sama ikut dipakai walau Z-nya di luar pita atap (atap nyata naik-turun) */
  (function () { var _r = window.amRoofPts; if (typeof _r !== 'function') return; window.amRoofPts = amRoofPts = function (o, B) { var r = _r.apply(this, arguments); try { var F = amRoofPar(B), seen = {}; r.pts.forEach(function (q) { seen[q.x + ',' + q.y + ',' + q.z] = 1; });
        (amD().ptsR || []).forEach(function (q) { var f = q.f && flFile(q.f); if (!f || Math.abs(f.top - B[0]) > 1e-3 || !isFinite(q.z) || seen[q.x + ',' + q.y + ',' + q.z]) return; var b = o.b, buf = F.buf; if (q.x < b[0] - buf || q.x > b[1] + buf || q.y < b[2] - buf || q.y > b[3] + buf) return; if (!lyInS(o.r, q.x, q.y) && amDistPoly(o.r, q.x, q.y) > buf) return; r.pts.push(q); }); } catch (e) { console.error(e); } return r; }; })();

  /* 8. tombol tampil / sembunyikan lapisan titik LANTAI & ATAP (pemilik 10-11-2026: "biar mudah melakukan digitasi").
     Hanya tampilan + snap: titik yang disembunyikan tidak digambar dan tidak ditempeli kursor saat mendigit, tetapi TETAP
     dipakai hitungan permukaan atap / lantai. Dipasang paling luar (setelah semua skrip, termasuk amfloor.js). */
  AMN.vis = function (k) { var D = amD(); D[k] = D[k] === false ? true : false; try { amPanel(); } catch (e) { } updatePlot(); };
  AMN.isRoofTr = function (t) { return /^Pick-up ATAP/.test(String(t && t.name || '')); };
  AMN.isFloorTr = function (t) { var n = String(t && t.name || ''); return /^Pick-up /.test(n) && !AMN.isRoofTr(t); };
  setTimeout(function () {
    var _t = window.amTraces2D; if (typeof _t === 'function' && !_t._vis) { window.amTraces2D = amTraces2D = function () { var out = _t.apply(this, arguments); try { var D = amD(); if (D.vF === false || D.vR === false) out = out.filter(function (t) { return !(D.vF === false && AMN.isFloorTr(t)) && !(D.vR === false && AMN.isRoofTr(t)); }); } catch (e) { console.error(e); } return out; }; amTraces2D._vis = 1; }
    var _h = window.dgSnapHook; if (typeof _h === 'function' && !_h._vis) { window.dgSnapHook = function (A, px, py) { var D = amD(); if (!AM.digOn || D.snap === false || (D.vF !== false && D.vR !== false)) return _h(A, px, py);
        var best = 12, res = null, P = [].concat(D.vF === false ? [] : amPtsNear(), D.vR === false ? [] : AMN.roofNear()); P.forEach(function (q) { var p = dgPx(A, q.x, q.y), d = Math.hypot(p[0] - px, p[1] - py); if (d < best) { best = d; res = [q.x, q.y]; } }); if (res) return res;
        /* kait lain (sudut blok, dll.) tetap jalan; kait titik as-mined dilewati supaya titik tersembunyi tidak ditempeli */
        AM.digOn = false; try { return _h(A, px, py); } finally { AM.digOn = true; } }; window.dgSnapHook._vis = 1; }
  }, 0);

  /* ---------- panel: tombol & keterangan ---------- */
  (function () { var _b = window.am3Box; if (typeof _b === 'function') window.am3Box = am3Box = function () { var h = _b.apply(this, arguments);
      var add = '<div class=am3ly><label class=sw title="Poligon OB di antara permukaan atap dan lantai yang dipakai hitungan: bentuk yang benar-benar dihitung"><input type=checkbox ' + (AM3.sol ? 'checked' : '') + ' onchange="AM3.sol=this.checked;updatePlot()">Solid as-mined (atap &ndash; lantai, dipotong poligon)</label></div>' +
        '<div class=g2 style="margin-top:4px"><button onclick="AMN.zoom(false)" title="Dekatkan tampilan ke poligon as-mined flitch aktif (3D: kamera; plan 2D: rentang sumbu)">&#8982; Zoom ke poligon flitch ini</button><button onclick="AMN.zoom(true)">&#8982; Zoom semua poligon</button></div>' +
        '<div class=hint>Kotak <b>Sub-blok model as-mined</b> menggambar sub-blok <b>ukuran penuh</b> (lebih besar dari volume yang dihitung); yang sesuai hitungan adalah <b>Solid as-mined</b>. Material di luar poligon OB tidak dihitung.</div>';
      return h.replace(/<\/div>\s*$/, add + '</div>'); }; })();
  (function () { var _p = window.amPanel; if (typeof _p !== 'function') return; window.amPanel = amPanel = function () { var r = _p.apply(this, arguments); try { var el = $('amBody'); if (!el || !BX.m) return r; var R = amR(), U = BX.ui, t = el.querySelector('.amcls,table.amct') || null;
        var box = document.createElement('div'); box.className = 'hint amnbox'; box.setAttribute('data-amn', '1');
        box.innerHTML = '<b>Kelas kadar:</b> ' + (R.cls || []).map(function (q) { return amE(q.m) + ' ' + q.lo + (q.hi === '' ? '+' : '&ndash;' + q.hi); }).join(' &middot; ') + (R.clsSrc ? ' <small>(dari ' + amE(R.clsSrc) + ')</small>' : ' <small>(bawaan aplikasi / diubah manual)</small>') + ' <button onclick="AMN.pakaiKelas()" title="Samakan batas kelas As-Mined dengan aturan kelas di block model">Ambil dari block model</button>' +
          '<br><b>SG tonase:</b> ' + (U.sgCol ? 'kolom <code>' + amE(U.sgCol) + '</code> block model' + (U.sgAuto === U.sgCol ? ' (dipilih otomatis)' : '') : 'tetap ' + U.sg + (Object.keys(BX.m.num).some(function (n) { return /^(sg|dens|bd)/i.test(n); }) ? ' <span class=warn>&mdash; model punya kolom SG; pilih di Block Model &rsaquo; Filter &amp; SG</span>' : ''));
        var sec = el.querySelector('.uisec[data-k="1"]') || el.querySelector('.uisec') || el; sec.appendChild(box); } catch (e) { console.error(e); } return r; }; })();
  (function () { var st = document.createElement('style'); st.textContent = '#amBody .amnbox{margin-top:8px;padding:6px 8px;border:1px solid var(--bd);border-left:4px solid var(--ac);border-radius:6px;line-height:1.5}#amBody .amnbox button{font-size:11px;min-height:20px;padding:0 6px}#amBody .amvis{display:flex;gap:6px;align-items:center;margin:6px 0 2px;flex-wrap:wrap}#amBody .amvis span{font-size:11.5px;color:var(--mu)}#amBody .amvis button{height:24px;padding:0 9px;font-size:11.5px;border-radius:12px}#amBody .amvis button.on{background:var(--mj,#f0c047);border-color:var(--mjln,#d6a12b);color:var(--mjtx,#1d2b5e);font-weight:700}'; document.head.appendChild(st); })();
})();
