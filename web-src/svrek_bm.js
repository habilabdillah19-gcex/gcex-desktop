/* ============ SOLID VEIN AKTUAL: REKONSILIASI DENGAN WIREFRAME MODEL -- GC-Ex Block Model 0.24.71 ============
   Pemilik 12 Nov 2026 memilih "Union + rekonsiliasi dengan wireframe model". Solid aktual periode (sesudah union)
   dibandingkan dengan wireframe model geologi (Import Wireframe Geologi, satu atau beberapa domain) dengan boolean
   (web-src/mfbool.js):
     ORE TERGALI  = aktual  ∩ model
     DILUSI       = aktual  − model            (yang tergali di luar model)
     ORE LOSS     = model ∩ zona − aktual      (model di area galian yang tidak ikut tergali)
   ZONA PENILAIAN membatasi ore loss supaya ore model yang memang belum ditambang tidak dianggap hilang: tiap flitch
   periode = gabungan poligon aktual flitch itu, diperlebar 'Lebar zona' (bawaan 3 m, sudut bulat), diekstrusi dari
   RL bawah s/d RL atas flitch. Lebar 0 = hanya di dalam poligon aktual.
   Volume = volume solid hasil boolean (eksak). Tonase solid = volume x SG Solid Vein. Kolom block model = blok UTUH yang
   titik pusatnya di dalam solid hasil (cara Surpac, sama dengan Report block model dalam Solid Vein), SG mengikuti
   Filter & SG (bxSGv), kadar tertimbang tonase. Hasil bisa ditampilkan di 3D / sayatan dan diekspor DTM + STR / CSV. */
(function () {
  if (!window.SV || !window.MFB || window.SVK) return;
  var SVK = window.SVK = { R: {}, busy: false };
  var KEL = [['tg', 'Ore tergali', 'aktual ∩ model', '#2f9e44'], ['dil', 'Dilusi', 'aktual − model', '#1971c2'], ['loss', 'Ore loss', 'model ∩ zona − aktual', '#e03131']];
  var N = function (v, d) { return isFinite(v) ? (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }) : '-'; };
  var E = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  function O(p) { p.rek = p.rek || {}; if (!Array.isArray(p.rek.mods)) p.rek.mods = []; if (!(p.rek.buf >= 0)) p.rek.buf = 3; if (!p.rek.show) p.rek.show = { tg: true, dil: true, loss: true }; return p.rek; }
  function models() { return (window.MD && MD.models || []).filter(function (m) { return m.jenis !== 'surf' && !m.sv && m.v && m.t && m.nt; }); }
  function kunci(p, r) { var o = O(p); return [r.date, (r.uni || {}).vol, o.buf, o.mods.join('|')].join('#') + '#' + models().filter(function (m) { return o.mods.indexOf(m.name) >= 0; }).map(function (m) { return m.nv + ':' + m.nt; }).join(','); }
  function datar(V, tri) { var map = {}, v = [], t = []; tri.forEach(function (tr) { tr.forEach(function (ix) { if (map[ix] === undefined) { map[ix] = v.length / 3; v.push(V.x[ix] + offX, V.y[ix] + offY, V.z[ix]); } t.push(map[ix]); }); }); return { v: new Float64Array(v), t: new Uint32Array(t), nv: v.length / 3, nt: t.length / 3 }; }
  /* tubuh datar (dunia) -> {V lokal, tri} untuk SV.inSolid */
  function lokal(b) { var V = { x: new Float64Array(b.nv), y: new Float64Array(b.nv), z: new Float64Array(b.nv) }, tri = []; for (var i = 0; i < b.nv; i++) { V.x[i] = b.v[3 * i] - offX; V.y[i] = b.v[3 * i + 1] - offY; V.z[i] = b.v[3 * i + 2]; } for (i = 0; i < b.nt; i++) tri.push([b.t[3 * i], b.t[3 * i + 1], b.t[3 * i + 2]]); return { V: V, tri: tri }; }
  function gradeAttr() { var m = BX.m, U = BX.ui || {}; if (SV.rep && SV.rep.gr && m.num[SV.rep.gr]) return SV.rep.gr; var L = (window.elList ? elList(U.attr) : [U.attr]).filter(function (a) { return a && m.num[a]; }); return L[0] || Object.keys(m.num)[0]; }
  function blok(bodies) {
    var m = BX.m, U = BX.ui || {}; if (!m || !bodies.length) return null;
    var sgA = U.sgCol && m.num[U.sgCol] ? m.num[U.sgCol] : null, gr = gradeAttr(), G = gr ? m.num[gr] : null, S = bodies.map(function (b) { var l = lokal(b); return SV.inSolid(l.V, l.tri); });
    var o = { n: 0, v: 0, t: 0, gt: 0, w: 0, gr: gr };
    for (var i = 0; i < m.n; i++) { var x = m.x[i] - offX, y = m.y[i] - offY, z = m.z[i];
      for (var k = 0; k < S.length; k++) if (S[k].f(x, y, z)) { var v = m.sx[i] * m.sy[i] * m.sz[i], sg = window.bxSGv ? bxSGv(sgA ? sgA[i] : NaN) : (+U.sg || 2.6), t = v * sg; o.n++; o.v += v; o.t += t; if (G && isFinite(G[i])) { o.gt += G[i] * t; o.w += t; } break; } }
    o.g = o.w ? o.gt / o.w : NaN; return o;
  }

  SVK.hitung = function () {
    var p = SV.per(); if (!p) return; var o = O(p), r = SV.R(p);
    if (!r) { alert('Bangun solid periode ini dulu.'); return; }
    var M = models().filter(function (m) { return o.mods.indexOf(m.name) >= 0; });
    if (!M.length) { alert('Centang minimal satu wireframe model (Import Wireframe Geologi).'); return; }
    SVK.busy = true; SV.panel();
    MFB.load().then(function () {
      setTimeout(function () {
        var t0 = Date.now(), res = { key: kunci(p, r) };
        try {
          var A = r.IS.map(function (s) { return datar(r.V, s.tri); }), lapis = SV.levels(p).map(function (g) {
            return { top: g.top, bot: g.bot, polys: g.L.filter(function (v) { return v.on !== false && v.pts && v.pts.length >= 3; }).map(function (v) { return v.pts.map(function (q) { return [q[0] + offX, q[1] + offY]; }); }) }; });
          var B = M.map(function (m) { return { v: m.v, t: m.t, nv: m.nv, nt: m.nt, name: m.name }; });
          var X = MFB.ops(A, B, MFB.zona(lapis, +o.buf || 0));
          res.part = { tg: X.AnB, dil: X.AmB, loss: X.BmA }; res.volA = X.volA; res.volMZ = X.volB;
          var sg = +SV.P(p).sg || 0;
          KEL.forEach(function (k) { var q = res.part[k[0]]; q.t = q.vol * sg; q.bm = blok(q.bodies); });
          res.ms = Date.now() - t0; res.date = new Date().toISOString(); res.mods = M.map(function (m) { return m.name; }); res.buf = +o.buf || 0;
          SVK.R[p.id] = res;
          p.rekRes = { date: res.date, mods: res.mods, buf: res.buf, volA: res.volA, volMZ: res.volMZ, part: {} };
          KEL.forEach(function (k) { var q = res.part[k[0]]; p.rekRes.part[k[0]] = { vol: q.vol, t: q.t, n: q.bodies.length, bm: q.bm ? { n: q.bm.n, v: q.bm.v, t: q.bm.t, g: q.bm.g, gr: q.bm.gr } : null }; });
        } catch (e) { console.error(e); SVK.R[p.id] = { key: res.key, err: e.message }; }
        SVK.busy = false; SV.dirty(); SV.panel(); try { updatePlot(); } catch (e) {}
      }, 20);
    }, function () { SVK.busy = false; alert(MFB.err || 'Pustaka boolean gagal dimuat.'); SV.panel(); });
  };
  SVK.setMod = function (nm, v) { var p = SV.per(); if (!p) return; var o = O(p), i = o.mods.indexOf(nm); if (v && i < 0) o.mods.push(nm); if (!v && i >= 0) o.mods.splice(i, 1); SV.dirty(); SV.panel(); };
  SVK.set = function (k, v) { var p = SV.per(); if (!p) return; O(p)[k] = v; SV.dirty(); SV.panel(); };
  SVK.lihat = function (k, v) { var p = SV.per(); if (!p) return; O(p).show[k] = !!v; SV.dirty(); try { updatePlot(); } catch (e) {} };

  SV.rekHtml = function (p) {
    if (!p || !p.res) return '';
    var o = O(p), L = models(), res = SVK.R[p.id], r = null; try { r = SV.R(p); } catch (e) {}
    var baru = res && r && res.key === kunci(p, r), s = p.rekRes;
    var h = '<div class="svsec' + (SV.foc === 'rek' ? ' foc' : '') + '" data-sec="rek"><div class=svh>Rekonsiliasi dengan wireframe model</div>';
    if (!L.length) return h + '<div class=hint>Import wireframe model ore (menu <b>Import Wireframe Geologi</b>) untuk membandingkan solid aktual dengan model: ore tergali, dilusi dan ore loss.</div></div>';
    h += '<div class=hint>Wireframe model (domain ore yang dibandingkan):</div><div class=svfiles style="max-height:110px;overflow:auto">' + L.map(function (m) { return '<label><input type=checkbox ' + (o.mods.indexOf(m.name) >= 0 ? 'checked' : '') + ' onchange="SVK.setMod(' + E(JSON.stringify(m.name)) + ',this.checked)"> ' + E(m.name) + ' <small>' + N(m.nt) + ' segitiga</small></label>'; }).join('') + '</div>' +
      '<div class=g2 style="align-items:end"><div><label>Lebar zona penilaian ore loss (m)</label><input type=number min=0 step=0.5 value="' + o.buf + '" onchange="SVK.set(\'buf\',Math.max(0,+this.value||0))" title="Ore loss hanya dihitung di dalam poligon aktual tiap flitch diperlebar sejauh ini (sudut bulat), dari RL bawah sampai RL atas flitch. Ore model di luar zona dianggap belum ditambang, bukan hilang."></div>' +
      '<div><button class=btn-pri style="width:100%" onclick="SVK.hitung()" ' + (SVK.busy || !o.mods.length ? 'disabled' : '') + '>' + (SVK.busy ? 'Menghitung&hellip;' : 'Hitung rekonsiliasi') + '</button></div></div>';
    if (res && res.err) h += '<div class=hint><span class=warn>Gagal: ' + E(res.err) + '</span></div>';
    var X = baru && !res.err ? res.part : (s && s.part);
    if (X) {
      if (!baru) h += '<div class=hint><span class=warn>' + (res || s ? 'Hasil di bawah dihitung sebelum solid / pilihan berubah; tekan <b>Hitung rekonsiliasi</b> lagi.' : '') + '</span></div>';
      var gr = (X.tg.bm || X.dil.bm || X.loss.bm || {}).gr || '';
      h += '<table class=pltb style="margin-top:4px"><tr><th></th><th>Bagian</th><th>Volume m&sup3;</th><th>Ton (SG ' + N(+SV.P(p).sg || 0, 2) + ')</th><th>Blok BM: ton</th><th>' + E(gr || 'kadar') + '</th></tr>' + KEL.map(function (k) { var q = X[k[0]]; return '<tr><td>' + (baru ? '<input type=checkbox ' + (o.show[k[0]] !== false ? 'checked' : '') + ' onchange="SVK.lihat(\'' + k[0] + '\',this.checked)" title="Tampilkan di 3D / sayatan">' : '') + '</td><td><span style="color:' + k[3] + ';font-weight:700">' + k[1] + '</span><br><small>' + k[2] + '</small></td><td>' + N(q.vol, 1) + '</td><td>' + N(q.t, 0) + '</td><td>' + (q.bm ? N(q.bm.t, 0) : '-') + '</td><td>' + (q.bm ? N(q.bm.g, 3) : '-') + '</td></tr>'; }).join('') + '</table>';
      var tg = X.tg.vol, dil = X.dil.vol, loss = X.loss.vol, act = tg + dil, mz = tg + loss;
      h += '<div class=hint>Dilusi ' + N(act ? 100 * dil / act : NaN, 1) + '% dari volume aktual &middot; ore loss ' + N(mz ? 100 * loss / mz : NaN, 1) + '% dari model di zona penilaian (lebar ' + N((baru ? res.buf : s.buf), 1) + ' m)' + (baru ? ' &middot; ' + res.ms + ' ms' : '') + '. Kolom <b>Blok BM</b> = blok utuh bertitik pusat di dalam bagian itu (cara Surpac).</div>' +
        (baru ? '<div class=g3 style="margin-top:4px"><button onclick="SVK.ekspor(\'tg\')">DTM+STR tergali</button><button onclick="SVK.ekspor(\'dil\')">DTM+STR dilusi</button><button onclick="SVK.ekspor(\'loss\')">DTM+STR ore loss</button></div><button style="margin-top:4px;width:100%" onclick="SVK.csv()">CSV rekonsiliasi</button>' : '');
    }
    return h + '</div>';
  };

  /* ---------- 3D / sayatan ---------- */
  (function () { var _d = window.dgTraces; if (typeof _d !== 'function') return; window.dgTraces = function (T, o) { var r = _d.apply(this, arguments); try { tr(T, o); } catch (e) { console.error(e); } return r; }; })();
  function tr(T, o) {
    if (!SV.show || window.VIEW2D) return; var p = SV.per(); if (!p) return; var res = SVK.R[p.id], ok = res && !res.err && res.part; if (!ok) return;
    var r = null; try { r = SV.R(p); } catch (e) {} if (!r || res.key !== kunci(p, r)) return; var sh = O(p).show;
    KEL.forEach(function (k) { if (sh[k[0]] === false) return; res.part[k[0]].bodies.forEach(function (b, i) {
      var x = new Float64Array(b.nv), y = new Float64Array(b.nv), z = new Float64Array(b.nv); for (var q = 0; q < b.nv; q++) { x[q] = b.v[3 * q] - offX; y[q] = b.v[3 * q + 1] - offY; z[q] = b.v[3 * q + 2]; }
      var I = [], J = [], K = []; for (q = 0; q < b.nt; q++) { I.push(b.t[3 * q]); J.push(b.t[3 * q + 1]); K.push(b.t[3 * q + 2]); }
      T.push({ type: 'mesh3d', name: k[1] + ' ' + (p.name || '') + (res.part[k[0]].bodies.length > 1 ? ' #' + (i + 1) : ''), x: x, y: y, z: z, i: I, j: J, k: K, color: k[3], opacity: 0.6, flatshading: true, lighting: { ambient: 0.55, diffuse: 0.75, specular: 0.1, roughness: 0.8 }, hoverinfo: 'name', showlegend: i === 0 }); }); });
  }

  /* ---------- ekspor ---------- */
  SVK.ekspor = function (k) {
    var p = SV.per(), res = p && SVK.R[p.id]; if (!res || !res.part) return; var L = res.part[k].bodies; if (!L.length) { alert('Bagian ini kosong.'); return; }
    var nm = { tg: 'tergali', dil: 'dilusi', loss: 'oreloss' }[k], base = ('rek_' + (p.name || 'periode') + '_' + nm).toLowerCase().replace(/[^a-z0-9_-]+/g, '_'), d = new Date(), mo = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][d.getMonth()], hdr = base + ',' + ('0' + d.getDate()).slice(-2) + '-' + mo + '-' + String(d.getFullYear()).slice(-2) + ',,ssi_styles:styles.ssi', f3 = function (v) { return (+v).toFixed(3); };
    var S = [hdr, '0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000'], T = [hdr, '0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000', 'OBJECT, 1,'], np = 0, nt = 0;
    L.forEach(function (b, bi) { var o = np; for (var i = 0; i < b.nv; i++) S.push('1, ' + f3(b.v[3 * i + 1]) + ', ' + f3(b.v[3 * i]) + ', ' + f3(b.v[3 * i + 2]) + ','); np += b.nv;
      var EM = {}; for (i = 0; i < b.nt; i++) for (var e = 0; e < 3; e++) { var a = b.t[3 * i + e], c = b.t[3 * i + (e + 1) % 3], kk = a < c ? a + '_' + c : c + '_' + a; (EM[kk] = EM[kk] || []).push(i); }
      T.push('TRISOLATION, ' + (bi + 1) + ', neighbours=yes, validated=true, closed=true, solid=true,');
      for (i = 0; i < b.nt; i++) { var nb = []; for (e = 0; e < 3; e++) { a = b.t[3 * i + e]; c = b.t[3 * i + (e + 1) % 3]; kk = a < c ? a + '_' + c : c + '_' + a; var oo = (EM[kk] || []).filter(function (j) { return j !== i; })[0]; nb.push(oo === undefined ? 0 : nt + oo + 1); }
        T.push((nt + i + 1) + ', ' + (o + b.t[3 * i] + 1) + ', ' + (o + b.t[3 * i + 1] + 1) + ', ' + (o + b.t[3 * i + 2] + 1) + ', ' + nb.join(', ') + ','); } nt += b.nt; });
    S.push('0, 0.000, 0.000, 0.000,', '0, 0.000, 0.000, 0.000, END'); T.push('END');
    SVK._last = { dtm: T.join('\r\n') + '\r\n', str: S.join('\r\n') + '\r\n', base: base };
    gxSimpan(SVK._last.dtm, base + '.dtm').then(function (ok) { if (ok !== null) gxSimpan(SVK._last.str, base + '.str'); });
  };
  SVK.csv = function () {
    var p = SV.per(), res = p && SVK.R[p.id]; if (!res || !res.part) return; var sg = +SV.P(p).sg || 0, gr = '';
    KEL.forEach(function (k) { var q = res.part[k[0]]; if (q.bm && q.bm.gr) gr = q.bm.gr; });
    var o = ['Periode,Bagian,Definisi,Jumlah tubuh,Volume solid (m3),SG,Ton solid (t),Blok BM,Volume blok (m3),Ton blok (t),' + gr + ' (tertimbang ton),Wireframe model,Lebar zona (m)'];
    KEL.forEach(function (k) { var q = res.part[k[0]], b = q.bm || {}; o.push([p.name, k[1], k[2], q.bodies.length, q.vol.toFixed(3), sg, q.t.toFixed(1), b.n || 0, (b.v || 0).toFixed(1), (b.t || 0).toFixed(1), isFinite(b.g) ? b.g.toFixed(4) : '', res.mods.join(' + '), res.buf].map(function (v) { return '"' + String(v).replace(/"/g, '""') + '"'; }).join(',')); });
    gxSimpan(o.join('\r\n') + '\r\n', ('rekonsiliasi_' + (p.name || 'periode')).replace(/[^A-Za-z0-9_-]+/g, '_') + '.csv', 'text/csv');
  };
})();
