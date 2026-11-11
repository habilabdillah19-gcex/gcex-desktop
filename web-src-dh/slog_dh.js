/* ============ PARAMETER ESTIMASI DARI LOG SURPAC (GC-Ex Drillhole 0.24.79) ============
   Pemilik 12 Nov 2026 (geolog pengganti, jalur Lanjutkan): parameter estimasi pendahulu ada di log Surpac.
   Dulu tidak ada tempat memasukkan orientasi Surpac (ZXY LRL: bearing, plunge, dip) — Model Estimation hanya
   menerima parameter dari Geostatistik. Modul ini membaca log Surpac (BM FILL OK), menampilkan semua run,
   dan menyalin run pilihan ke domain:
     frm20101  variogram  : co, c1..c5, a1..a5, azimuth/plunge/dip, semi_ratio, minor_ratio (sferis)
     frm20080  pencarian  : majordist, semimajfact, minorfact, minsamples, maxsamples, max_samp_per_id
     frm20040  sumber     : location (compositeXX.str -> unsur), constrain (N = soft, Y = hard)
   Orientasi Surpac ZXY LRL: bearing = putar sumbu Z (kiri, searah jarum jam dari utara), plunge = putar sumbu X'
   (kanan), dip = putar sumbu Y' (kiri) — lihat SLOG.vek. Hanya jalur Lanjutkan dengan
   acuan parameter (atau proyek tanpa jalur); di jalur Mulai dari nol tombolnya tidak tampil.             */
(function () {
  if (window.SLOG || typeof window.meParHtml !== 'function') return;
  var SLOG = window.SLOG = { runs: [], file: '', pil: -1, dom: {}, nd: [1, 1, 1] };
  var $ = function (id) { return document.getElementById(id); };
  var E = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var N = function (v, k) { v = +v; return isFinite(v) ? v.toLocaleString('id-ID', { maximumFractionDigits: k == null ? 2 : k }) : '-'; };
  var boleh = function () { return !(window.JLR && JLR.mode) || JLR.tebak || (JLR.boleh && JLR.boleh('par')); };
  SLOG.boleh = boleh;

  /* ---------- 1. baca log ---------- */
  SLOG.parse = function (txt) {
    var L = String(txt || '').split(/\r?\n/), runs = [], ts = '', cur = null, frm = null, m;
    function tutup() { if (cur) runs.push(cur); cur = null; frm = null; }
    for (var i = 0; i < L.length; i++) {
      var s = L[i].trim();
      if ((m = s.match(/^\S{1,2}\s+(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\s*$/))) { ts = m[1]; continue; }
      if ((m = s.match(/^\S{1,2}\s+(BM [A-Z][A-Z ]*[A-Z])\s*$/))) {
        tutup();
        var cmd = m[1];
        if (/^BM FILL (OK|ORDINARY KRIGING|INVERSE DISTANCE|NEAREST NEIGHBOUR)/.test(cmd)) cur = { cmd: cmd, ts: ts, f: {}, con: [], baris: i + 1 };
        continue;
      }
      if (!cur) continue;
      if ((m = s.match(/^(frm\d+)\s*=/))) { frm = m[1]; if (!cur.f[frm]) cur.f[frm] = {}; continue; }
      if (frm && (m = s.match(/^(\w+)\s*=\s*"(.*)"\s*$/))) { if (!(m[1] in cur.f[frm])) cur.f[frm][m[1]] = m[2]; continue; }
      if ((m = s.match(/^\{\s*"[^"]*"\s+"(INSIDE|OUTSIDE)"\s+"CONSTRAINT"\s+"([^"]+)"/))) cur.con.push(m[1] + ' ' + m[2]);
    }
    tutup();
    return runs.map(function (r, k) { var o = ringkas(r); o.i = k; return o; });
  };
  function g(o, k, d) { var v = o && o[k]; return v === undefined || v === '' ? d : v; }
  function ringkas(r) {
    var f = r.f, sr = f.frm20040 || {}, se = f.frm20080 || {}, vg = f.frm20101 || {}, at = (f.frm20030 || {}).attname || '';
    var loc = g(sr, 'location', ''), file = loc.split(/[\\/]/).pop(), kode = (file.match(/^composite([a-z0-9_]+)\.str$/i) || [])[1] || '';
    var S = [];
    for (var k = 1; k <= 5; k++) {
      var c = +g(vg, 'c' + k, 0), a = +g(vg, 'a' + k, 0);
      if (c > 0 && a > 0) S.push({ c: c, a: a, sr: +g(vg, 'semi_ratio' + k, 1) || 1, mr: +g(vg, 'minor_ratio' + k, 1) || 1,
        b: +g(vg, 'azimuth' + k, 0), p: +g(vg, 'plunge' + k, 0), d: +g(vg, 'dip' + k, 0) });
    }
    var ok = /^BM FILL (OK|ORDINARY KRIGING)/.test(r.cmd) && S.length > 0;
    return { cmd: r.cmd, ts: r.ts, baris: r.baris, att: at, file: file, kode: kode, con: r.con, ok: ok,
      hard: String(g(sr, 'constrain', 'N')).toUpperCase().charAt(0) === 'Y', model: g(vg, 'model', ''),
      c0: +g(vg, 'co', 0), S: S,
      cari: { maj: +g(se, 'majordist', 0), sf: +g(se, 'semimajfact', 1) || 1, mf: +g(se, 'minorfact', 1) || 1,
        min: +g(se, 'minsamples', 0), max: +g(se, 'maxsamples', 0), mph: +g(se, 'max_samp_per_id', 0) || 0,
        b: +g(se, 'axis_1', 0), p: +g(se, 'axis_2', 0), d: +g(se, 'axis_3', 0), rot: g(se, 'rotationTypes', '') } };
  }

  /* ---------- 2. orientasi Surpac ZXY LRL -> vektor sumbu ---------- */
  /* Surpac ZXY LRL: Z kiri (bearing searah jarum jam), X' KANAN (plunge positif mengangkat sumbu mayor),
     Y' KIRI (dip positif mengangkat sumbu semi). Dihitung sebagai putaran "turun" dengan tanda plunge & dip dibalik.
     Diuji pada BMGC Surpac Zona 3 (run 2026-11-09 18:15, 151/76/80): korelasi blok GC-Ex vs auok 0,871 dengan
     konvensi ini; 0,819 / 0,790 / 0,785 / 0,733 untuk tafsiran tanda lain dan plunge 0. */
  SLOG.vek = function (b, p, d) {
    var r = Math.PI / 180; b *= r; p *= -r; d *= -r;
    var sb = Math.sin(b), cb = Math.cos(b), sp = Math.sin(p), cp = Math.cos(p), sd = Math.sin(d), cd = Math.cos(d);
    var vM = [sb * cp, cb * cp, -sp];                 /* mayor: bearing, menunjam p */
    var s0 = [cb, -sb, 0];                            /* semi sebelum dip: mendatar, kanan mayor */
    var n0 = [sb * sp, cb * sp, cp];                  /* tegak lurus mayor & s0, ke atas */
    var vS = [cd * s0[0] - sd * n0[0], cd * s0[1] - sd * n0[1], cd * s0[2] - sd * n0[2]];
    var vN = [sd * s0[0] + cd * n0[0], sd * s0[1] + cd * n0[1], sd * s0[2] + cd * n0[2]];
    return { vM: vM, vS: vS, vN: vN };
  };

  /* ---------- 3. unsur dari nama berkas komposit ---------- */
  SLOG.unsur = function (run) {
    var E2 = (window.elements || []), k = String(run.kode || run.att || '').toLowerCase().replace(/(ok|id|gpt|pct|ppm)$/,'');
    if (!k) return '';
    var x = E2.filter(function (e) { return e.toLowerCase() === k; })[0] || E2.filter(function (e) { return e.toLowerCase().indexOf(k) === 0; })[0] ||
            E2.filter(function (e) { return k.indexOf(e.toLowerCase()) === 0; })[0];
    return x || '';
  };

  /* ---------- 4. parameter domain dari satu run ---------- */
  SLOG.est = function (run, el, d0) {
    var S = run.S, v = S[0], V = SLOG.vek(v.b, v.p, v.d), P0 = d0 && d0.est;
    var mph = run.cari.mph && run.cari.mph < run.cari.max ? run.cari.mph : 0;
    var sr = run.cari.maj > 0 ? [run.cari.maj, +(run.cari.maj / run.cari.sf).toFixed(3), +(run.cari.maj / run.cari.mf).toFixed(3)] : null;
    var o = { el: el, L: P0 && P0.L ? P0.L : 1, tc: P0 && P0.tc ? P0.tc : 0, nd: SLOG.nd.slice(),
      m: { vM: V.vM, vS: V.vS, vN: V.vN, c0: run.c0, cs: S.map(function (s) { return s.c; }), A: S.map(function (s) { return s.a; }),
           B: S.map(function (s) { return +(s.a / s.sr).toFixed(4); }), Cn: S.map(function (s) { return +(s.a / s.mr).toFixed(4); }) },
      P: [{ mult: 1, min: run.cari.min || 1, max: run.cari.max || 16, mph: mph }], tr: '',
      src: 'log Surpac ' + (SLOG.file || '') + ' · ' + run.ts + ' · ' + (run.att || run.file),
      date: new Date().toISOString().slice(0, 16).replace('T', ' '), n: 0, hard: run.hard,
      surpac: { b: v.b, p: v.p, d: v.d, run: run.ts, baris: run.baris, con: run.con.slice(0, 4) } };
    if (sr) o.sr = sr;
    if (P0 && P0.lim) o.lim = P0.lim;
    return o;
  };

  /* ---------- 5. dialog ---------- */
  function dlgEl() {
    var d = $('slogDlg');
    if (!d) { d = document.createElement('div'); d.id = 'slogDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    return d;
  }
  SLOG.tutup = function () { var d = $('slogDlg'); if (d) d.style.display = 'none'; };
  SLOG.dlg = function (domId) {
    if (!boleh()) { alert('Parameter dari log Surpac adalah acuan dari software lain: hanya untuk jalur Lanjutkan dengan acuan "Parameter estimasi" dicentang (Proyek › Jalur).'); return; }
    if (domId) { SLOG.dom = {}; SLOG.dom[domId] = true; }
    else if (!Object.keys(SLOG.dom).length) (window.GM && GM.doms || []).forEach(function (x) { if (!(typeof gmIsKid === 'function' && gmIsKid(x))) SLOG.dom[x.id] = !meParOf(x); });
    SLOG.render(); dlgEl().style.display = 'flex';
  };
  SLOG.pilihFile = function (inp) {
    var f = inp.files && inp.files[0]; if (!f) return;
    var r = new FileReader();
    r.onload = function () { SLOG.muat(String(r.result || ''), f.name); };
    r.readAsText(f);
  };
  SLOG.muat = function (txt, nama) {
    SLOG.runs = SLOG.parse(txt); SLOG.file = nama || 'log';
    if (SLOG.uji) { SLOG.uji.hasil = {}; SLOG.uji.best = -1; }
    var ok = SLOG.runs.filter(function (r) { return r.ok; });
    /* bawaan: run OK terakhir untuk unsur utama (Au bila ada) */
    var au = ok.filter(function (r) { return /^au$/i.test(SLOG.unsur(r)); });
    SLOG.pil = (au.length ? au[au.length - 1] : ok[ok.length - 1] || { i: -1 }).i;
    SLOG.render(); return SLOG.runs.length;
  };
  SLOG.set = function (k, v) {
    if (k === 'pil') SLOG.pil = +v;
    else if (k === 'nd') SLOG.nd = String(v).split(/[x×*, ]+/).map(Number).filter(function (n) { return n > 0; }).slice(0, 3);
    if (SLOG.nd.length !== 3) SLOG.nd = [1, 1, 1];
    SLOG.render();
  };
  SLOG.domSet = function (id, on) { SLOG.dom[id] = !!on; };
  SLOG.render = function () {
    var d = dlgEl(), R = SLOG.runs, run = R[SLOG.pil], D = (window.GM && GM.doms || []).filter(function (x) { return !(typeof gmIsKid === 'function' && gmIsKid(x)); });
    var h = '<div class=impBox style="width:min(1100px,100%)"><div class=impHead><div class=impBrand><div><b>Isi parameter estimasi dari log Surpac</b>' +
      '<small>Variogram, elipsoid pencarian dan jumlah sampel dari run <i>BM FILL OK</i> pendahulu disalin ke domain. Orientasi Surpac ZXY LRL (bearing / plunge / dip) diubah ke sumbu GC-Ex.</small></div></div>' +
      '<button class="ib ghost" onclick="SLOG.tutup()">Tutup</button></div><div class=impBody>';
    h += '<div class=f><label>Berkas log Surpac (.txt / .log / .ssi)</label><input type=file accept=".txt,.log,.ssi,.tcl,*" onchange="SLOG.pilihFile(this)">' +
      (SLOG.file ? '<div class=hint><b>' + E(SLOG.file) + '</b>: ' + R.length + ' run BM FILL, ' + R.filter(function (r) { return r.ok; }).length + ' run kriging dengan variogram.</div>' : '') + '</div>';
    if (R.length) {
      h += '<div class=cmh>Pilih run (terbaru di atas)</div><div style="max-height:250px;overflow:auto"><table class="pltb metb" style="width:100%;font-size:11.5px"><tr><th></th><th>Waktu</th>' + (Object.keys(SLOG.uji.hasil).length ? '<th title="Korelasi dengan kolom block model acuan pada blok yang diisi semua kandidat; cakupan = blok terisi dibanding kandidat terluas; selisih tonase di atas cut-off">Kecocokan</th>' : '') + '<th>Atribut &middot; komposit &rarr; unsur</th><th>Constraint</th><th>Variogram C0 / C / range</th><th>Bearing / plunge / dip &middot; rasio</th><th>Pencarian &middot; sampel</th></tr>';
      for (var k = R.length - 1; k >= 0; k--) {
        var r = R[k], s = r.S[0];
        h += '<tr' + (r.ok ? '' : ' style="opacity:.45"') + '><td><input type=radio name=slogR ' + (k === SLOG.pil ? 'checked' : '') + (r.ok ? '' : ' disabled') + ' onchange="SLOG.set(\'pil\',' + k + ')"></td><td style="white-space:nowrap">' + E(r.ts) + '</td>' + (Object.keys(SLOG.uji.hasil).length ? '<td style="white-space:nowrap">' + (function () { var u = SLOG.uji.hasil[k]; if (!u) return ''; if (!(u.r > -2)) return '<small class=mu>' + u.n + ' blok</small>'; return (k === SLOG.uji.best ? '<b>&#9733; ' : '') + 'r ' + N(u.rS != null ? u.rS : u.r, 3) + (k === SLOG.uji.best ? '</b>' : '') + '<br><small class=mu>cakupan ' + N((u.cak || 0) * 100, 0) + '% &middot; tonase &ge; ' + N(SLOG.uji.cut, 1) + ' ' + (u.dT >= 0 ? '+' : '') + N(u.dT * 100, 1) + '%</small>'; })() + '</td>' : '') +
          '<td>' + E(r.att || r.cmd.replace('BM FILL ', '')) + ' &middot; ' + E(r.file) + ' &rarr; <b>' + E(SLOG.unsur(r) || '?') + '</b></td><td>' + E(r.con.slice(0, 2).join(', ')) + '</td>' +
          '<td>' + (s ? N(r.c0, 4) + ' / ' + r.S.map(function (x) { return N(x.c, 4); }).join('+') + ' / ' + r.S.map(function (x) { return N(x.a, 1); }).join('+') + ' m' : '-') + '</td>' +
          '<td>' + (s ? s.b + ' / ' + s.p + ' / ' + s.d + ' &middot; ' + N(s.sr) + ' / ' + N(s.mr) : '-') + '</td>' +
          '<td style="white-space:nowrap">' + (r.cari.maj ? N(r.cari.maj, 1) + ' m' : '-') + ' &middot; ' + r.cari.min + '&ndash;' + r.cari.max + ' &middot; ' + (r.hard ? 'hard' : 'soft') + '</td>' +
          '</tr>';
      }
      h += '</table></div>';
    }
    if (run && run.ok) {
      var el = SLOG.unsur(run), V = SLOG.vek(run.S[0].b, run.S[0].p, run.S[0].d), c = run.cari;
      h += '<div class=box style="margin:8px 0"><b>Run ' + E(run.ts) + '</b> (baris ' + run.baris + ' di log) &rarr; unsur <b>' + E(el || '— tidak dikenali —') + '</b>' +
        '<div class=hint>Variogram sferis C0 ' + N(run.c0, 4) + ', ' + run.S.map(function (s, i) { return 'S' + (i + 1) + ' C ' + N(s.c, 4) + ' range ' + N(s.a, 1) + ' / ' + N(s.a / s.sr, 1) + ' / ' + N(s.a / s.mr, 1) + ' m'; }).join('; ') +
        '. Sumbu GC-Ex (azimuth/plunge): mayor ' + meAzPl(V.vM) + ', semi ' + meAzPl(V.vS) + ', minor ' + meAzPl(V.vN) + '.' +
        ' Elipsoid pencarian ' + (c.maj ? N(c.maj, 1) + ' / ' + N(c.maj / c.sf, 1) + ' / ' + N(c.maj / c.mf, 1) + ' m' : 'kosong = range variogram') + ', sampel ' + c.min + '&ndash;' + c.max +
        (c.mph && c.mph < c.max ? ', maks ' + c.mph + ' per lubang' : '') + '. Batas sampel <b>' + (run.hard ? 'hard (hanya sampel domain)' : 'soft (semua sampel, seperti Surpac constrain = N)') + '</b>.' +
        (c.b !== run.S[0].b || c.p !== run.S[0].p || c.d !== run.S[0].d ? ' <span class=warn>Orientasi pencarian (' + c.b + '/' + c.p + '/' + c.d + ') berbeda dengan variogram; GC-Ex memakai orientasi variogram untuk keduanya.</span>' : '') + '</div></div>';
      h += '<div class=g2><div><label>Diskretisasi blok (X×Y×Z)</label><input type=text value="' + SLOG.nd.join('×') + '" onchange="SLOG.set(\'nd\',this.value)"><div class=hint>Log Surpac tidak mencatat diskretisasi. 1×1×1 = taksiran titik di pusat blok.</div></div><div></div></div>';
      h += '<div class=cmh>Domain yang diisi</div><div class=jac>' + (D.length ? D.map(function (x) {
        return '<label style="display:block"><input type=checkbox ' + (SLOG.dom[x.id] ? 'checked' : '') + ' onchange="SLOG.domSet(\'' + x.id + '\',this.checked)"> ' + E(x.name) +
          (meParOf(x) ? ' <small class=mu>(sudah berparameter: ' + E(meParOf(x).src || '') + ' &mdash; akan diganti)</small>' : '') + '</label>';
      }).join('') : '<div class=hint>Belum ada domain. Buat domain dulu (mis. kunci domain ke wireframe Surpac).</div>') + '</div>';
      var kolA = SLOG.kolomAcuan(run);
      h += '<div class=hint style="margin-top:8px"><b>Run mana yang dipakai pendahulu?</b> Yang benar adalah run yang menghasilkan nilai di block model yang diserahkan: atribut sama dengan kolom kadarnya, biasanya run terakhir atribut itu (Surpac menimpa nilai blok tiap run). ' +
        (kolA ? '<b>Uji kecocokan</b> mengestimasi domain terpilih dengan tiap set parameter berbeda di log, lalu membandingkannya dengan kolom <b>' + E(kolA) + '</b> block model aktif.' : 'Uji kecocokan butuh block model hasil Surpac (kolom ' + E(run.att || el) + ') sebagai block model aktif.') + '</div>';
      h += '<div style="margin-top:10px;display:flex;gap:8px;justify-content:flex-end">' +
        '<button class="ib ghost" onclick="SLOG.ujiJalan()"' + (kolA && el && D.length && !SLOG.uji.jalan ? '' : ' disabled') + '>' + (SLOG.uji.jalan ? 'Menguji&hellip;' : 'Uji kecocokan dengan block model acuan') + '</button>' +
        '<button class=ib onclick="SLOG.terapkan()"' + (el && D.length && !SLOG.uji.jalan ? '' : ' disabled') + '>Salin parameter ke domain terpilih</button></div>';
    }
    h += '<div id=slogMsg class=hint></div></div></div>';
    d.innerHTML = h;
  };
  SLOG.terapkan = function (opt) {
    var run = SLOG.runs[SLOG.pil]; if (!run || !run.ok) return 0;
    var el = (opt && opt.el) || SLOG.unsur(run); if (!el) { alert('Unsur run ini tidak dikenali dari nama berkas komposit.'); return 0; }
    var ids = Object.keys(SLOG.dom).filter(function (k) { return SLOG.dom[k]; }), n = 0, ganti = [];
    ids.forEach(function (id) {
      var d = gmDom(id); if (!d) return;
      if (meParOf(d)) ganti.push(d.name);
      d.est = SLOG.est(run, el, d); n++;
    });
    if (!n) { alert('Centang minimal satu domain.'); return 0; }
    try { gmDirty(true); } catch (e) {}
    try { if (window.JLR && JLR.catat) JLR.catat('Parameter estimasi dari log Surpac (' + SLOG.file + ', run ' + run.ts + ', ' + run.att + ') disalin ke ' + n + ' domain' + (ganti.length ? '; mengganti parameter ' + ganti.join(', ') : '')); } catch (e) {}
    try { mePanel(); } catch (e) {}
    var m = $('slogMsg'); if (m) m.innerHTML = '&#10003; Parameter disalin ke <b>' + n + '</b> domain' + (ganti.length ? ' (mengganti: ' + E(ganti.join(', ')) + ')' : '') + '. Periksa di Model Estimation &rsaquo; Domain &amp; parameter.';
    return n;
  };

  /* ---------- 5b. uji kecocokan run dengan block model acuan (pemilik 12 Nov 2026: "apa pertimbangan memilih log?") ----------
     Run yang benar adalah run yang MENGHASILKAN nilai kadar di block model yang diserahkan. Untuk tiap set parameter
     berbeda (run beratribut sama dengan kolom kadar block model, duplikat digabung) GC-Ex mengestimasi domain terpilih
     di blok yang sama lalu membandingkannya dengan kolom itu: korelasi per blok, selisih rata-rata & tonase >= cut-off.
     Parameter domain dikembalikan sesudahnya; kolom <unsur>_est berisi hasil uji terakhir sampai estimasi dijalankan lagi. */
  SLOG.uji = { hasil: {}, jalan: false, cut: 0.3 };
  function kunciPar(r) { var v = r.S[0], c = r.cari; return [r.c0, r.S.map(function (x) { return [x.c, x.a, x.sr, x.mr].join('/'); }).join('+'), v.b, v.p, v.d, c.maj, c.sf, c.mf, c.min, c.max, r.hard ? 1 : 0].join('|'); }
  SLOG.kolomAcuan = function (run) {
    var m = window.BX && BX.m; if (!m || !m.num || !run) return '';
    if (run.att && m.num[run.att]) return run.att;
    var el = SLOG.unsur(run).toLowerCase(); return Object.keys(m.num).filter(function (k) { return k.indexOf(el) === 0 && !/_est$|_final$|_id2$/.test(k); })[0] || '';
  };
  function tunggu(f, ms) { return new Promise(function (res) { var t0 = Date.now(); (function p() { if (f() || Date.now() - t0 > ms) return res(); setTimeout(p, 250); })(); }); }
  function banding(el, kol, cut) {
    var m = BX.m, a = m.num[el.toLowerCase() + '_est'], b = m.num[kol], sg = m.num.sg3 || m.num.sg || m.num.density;
    if (!a || !b) return null;
    var n = 0, sa = 0, sb = 0, sab = 0, saa = 0, sbb = 0, ta = 0, tb = 0;
    for (var i = 0; i < m.n; i++) {
      if (!(a[i] > 0) || !(b[i] >= 0)) continue;
      var t = (m.sx ? m.sx[i] * m.sy[i] * m.sz[i] : 1) * (sg && sg[i] > 0 ? sg[i] : 1);
      n++; sa += a[i]; sb += b[i]; sab += a[i] * b[i]; saa += a[i] * a[i]; sbb += b[i] * b[i];
      if (a[i] >= cut) ta += t; if (b[i] >= cut) tb += t;
    }
    if (n < 10) return { n: n };
    return { n: n, r: (n * sab - sa * sb) / Math.sqrt((n * saa - sa * sa) * (n * sbb - sb * sb)), mA: sa / n, mB: sb / n, dT: tb ? (ta - tb) / tb : 0 };
  }
  SLOG.ujiJalan = async function () {
    var run0 = SLOG.runs[SLOG.pil]; if (!run0 || !run0.ok) return;
    var kol = SLOG.kolomAcuan(run0), el = SLOG.unsur(run0);
    if (!kol) { alert('Block model aktif tidak punya kolom kadar untuk ' + (run0.att || el) + '. Uji kecocokan butuh block model hasil Surpac (versi acuan) sebagai block model aktif.'); return; }
    var ids = Object.keys(SLOG.dom).filter(function (k) { return SLOG.dom[k]; }).filter(function (k) { return gmDom(k); });
    if (!ids.length) { alert('Centang minimal satu domain.'); return; }
    var G = {}; SLOG.runs.forEach(function (r) { if (r.ok && SLOG.kolomAcuan(r) === kol && SLOG.unsur(r) === el) { var k = kunciPar(r); (G[k] = G[k] || []).push(r.i); } });
    var K = Object.keys(G); if (!K.length) return;
    var simpan = {}; ids.forEach(function (id) { var d = gmDom(id); simpan[id] = d.est ? JSON.parse(JSON.stringify(d.est)) : null; });
    var sel0 = JSON.parse(JSON.stringify(ME.sel || {}));
    (window.gmTops ? gmTops() : GM.doms).forEach(function (d) { ME.sel[d.id] = ids.indexOf(d.id) >= 0; });
    SLOG.uji.jalan = true; SLOG.uji.hasil = {}; SLOG.uji.kol = kol; SLOG.render();
    var SIM = [], nRun0 = ME.store && ME.store.runs ? ME.store.runs.length : 0, force0 = ME.opt && ME.opt.force;
    /* tiap kandidat diestimasi penuh (bukan pembaruan bertahap dari kandidat sebelumnya) supaya adil dan aman saat soft <-> hard berganti */
    if (ME.opt) ME.opt.force = true;
    try {
      for (var q = 0; q < K.length; q++) {
        var L = G[K[q]], run = SLOG.runs[L[L.length - 1]];
        var msg = $('slogMsg'); if (msg) msg.innerHTML = 'Menguji set parameter ' + (q + 1) + ' / ' + K.length + ' (run ' + E(run.ts) + ')&hellip;';
        ids.forEach(function (id) { var d = gmDom(id); d.est = SLOG.est(run, el, d); });
        try { gmDirty(true); } catch (e) {}
        meRun();
        await tunggu(function () { return !!ME.job; }, 4000);
        await tunggu(function () { return !ME.job; }, 1800000);
        var H = banding(el, kol, SLOG.uji.cut), A = BX.m.num[el.toLowerCase() + '_est'];
        SIM.push({ L: L, H: H, a: A ? Float32Array.from(A) : null });
        L.forEach(function (i) { SLOG.uji.hasil[i] = H; });
      }
      /* korelasi di blok yang SAMA: elipsoid kecil hanya mengisi blok dekat bor (korelasi tinggi tapi cakupan sempit),
         jadi run dibandingkan pada blok yang diisi semua kandidat; cakupan dilaporkan terpisah. */
      var ref = BX.m.num[kol] || [], nb = ref.length ? BX.m.n : 0, mx = 0;
      SIM.forEach(function (x) { if (x.H && x.H.n > mx) mx = x.H.n; });
      /* kandidat yang praktis tidak mengisi blok (mis. hard boundary dengan sampel domain terlalu sedikit) tidak ikut menentukan irisan */
      SIM = SIM.filter(function (x) { if (x.H && x.H.n >= 10 && x.a) return true; if (x.H) x.H.cak = mx ? (x.H.n || 0) / mx : 0; return false; });
      var mask = new Uint8Array(nb), nm = 0;
      for (var i = 0; i < nb; i++) { var ok = ref[i] >= 0; for (var j = 0; ok && j < SIM.length; j++) if (!(SIM[j].a && SIM[j].a[i] > 0)) ok = false; if (ok) { mask[i] = 1; nm++; } }
      SIM.forEach(function (x) {
        if (!x.H || !x.a) return; var a2 = x.a, n = 0, sa = 0, sb = 0, sab = 0, saa = 0, sbb = 0;
        for (var i2 = 0; i2 < nb; i2++) if (mask[i2]) { var u = a2[i2], v = ref[i2]; n++; sa += u; sb += v; sab += u * v; saa += u * u; sbb += v * v; }
        x.H.rS = n > 9 ? (n * sab - sa * sb) / Math.sqrt((n * saa - sa * sa) * (n * sbb - sb * sb)) : null; x.H.nS = n; x.H.cak = mx ? x.H.n / mx : 0;
      });
      SLOG.uji.nSama = nm;
    } finally {
      ids.forEach(function (id) { var d = gmDom(id); d.est = simpan[id]; });
      ME.sel = sel0; if (ME.opt) ME.opt.force = force0; try { gmDirty(true); } catch (e) {}
      /* run uji tidak masuk riwayat Model Estimation (hanya pembanding) */
      try { if (ME.store && ME.store.runs && ME.store.runs.length > nRun0) ME.store.runs.splice(nRun0); meSaved && meSaved(); mePanel(); } catch (e) {}
      SLOG.uji.jalan = false;
      var best = -1, br = -2; Object.keys(SLOG.uji.hasil).forEach(function (i) { var h = SLOG.uji.hasil[i], v = h && h.rS != null ? h.rS : (h && h.r > -2 && SIM.length < 2 ? h.r : -2); if (v > br + 1e-9 || (v > -2 && Math.abs(v - br) < 1e-9 && +i > best)) { br = v; best = +i; } });
      SLOG.uji.best = best; if (best >= 0) SLOG.pil = best;
      SLOG.render();
      var m2 = $('slogMsg'); if (m2) m2.innerHTML = best >= 0 ? '&#10003; ' + K.length + ' set parameter diuji terhadap kolom <b>' + E(kol) + '</b>. Paling cocok: run <b>' + E(SLOG.runs[best].ts) + '</b> (korelasi ' + N(br, 3) + ' pada ' + N(SLOG.uji.nSama, 0) + ' blok yang diisi semua kandidat; run berparameter sama dihitung sekali, yang terbaru dipilih) &mdash; sudah dipilih. Periksa juga kolom cakupan: run dengan elipsoid lebih kecil mengisi lebih sedikit blok. Parameter domain belum diubah: tekan <b>Salin parameter</b>, lalu jalankan estimasi lagi (kolom ' + E(el.toLowerCase()) + '_est saat ini berisi hasil uji terakhir).' : 'Tidak ada hasil uji.';
      try { if (window.JLR && JLR.catat && best >= 0) JLR.catat('Uji kecocokan log Surpac ' + SLOG.file + ' terhadap kolom ' + kol + ': ' + K.length + ' set parameter; paling cocok run ' + SLOG.runs[best].ts + ' (r ' + br.toFixed(3) + ')'); } catch (e) {}
    }
    return SLOG.uji.hasil;
  };

  /* ---------- 6. pintu: panel parameter domain + menu node Model Estimation ---------- */
  var _ph = window.meParHtml;
  window.meParHtml = meParHtml = function (d) {
    var h = _ph.apply(this, arguments);
    if (!boleh()) return h;
    return h + '<button style="width:100%;margin-top:4px" onclick="SLOG.dlg(\'' + d.id + '\')">&#8681; Isi dari log Surpac&hellip;</button>' +
      (d.est && d.est.surpac ? '<div class=hint>Orientasi Surpac ZXY LRL: bearing ' + d.est.surpac.b + '&deg;, plunge ' + d.est.surpac.p + '&deg;, dip ' + d.est.surpac.d + '&deg; (run ' + E(d.est.surpac.run) + ').</div>' : '');
  };
  if (window.PT && PT.def && typeof PT.def.nodes === 'function' && !PT.def.nodes._slog) {
    var _n = PT.def.nodes;
    PT.def.nodes = function () {
      var L = _n.apply(this, arguments);
      try {
        L.forEach(function (x) {
          if (x.id !== 'me' || typeof x.menu !== 'function' || !boleh()) return;
          var m0 = x.menu;
          x.menu = function () { return m0.apply(this, arguments).concat([{ t: 'Isi parameter dari log Surpac…', fn: function () { SLOG.dlg(); } }]); };
        });
      } catch (e) {}
      return L;
    };
    PT.def.nodes._slog = 1;
  }
})();
