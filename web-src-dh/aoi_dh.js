/* ================= KERANGKA BLOK AOI — block model dibuat dari nol (tanpa impor) =================
   Dipakai bila belum ada block model acuan sama sekali: pemodelan betul-betul dari nol, tidak dituntun
   model lama. Berlaku untuk semua tipe deposit (vein, laterit, dll.) karena kerangkanya murni geometri.

   Kerangka = grid persegi seluruh Area of Interest (ore DAN waste), dipotong:
     - topografi aktif  : blok yang pusatnya di atas permukaan dibuang (sisa / in-situ di bawah topo);
     - desain pit       : blok dipertahankan hanya antara dasar pit dan topografi (volume di dalam pit);
     - rentang RL       : batas atas / bawah manual;
     - poligon area     : fitur tertutup menu Map atau string Surpac (sama dengan poligon Reporting BM).

   Dua mode:
     penuh : seluruh AOI diisi blok baru (abaikan block model yang sedang aktif);
     isi   : block model aktif DIPERTAHANKAN utuh (termasuk atribut kadar waste dari .mdl) dan blok baru
             hanya dibuat pada sel AOI yang BELUM tercakup model itu — inilah jalur untuk melengkapi
             .mdl impor yang cakupannya lebih sempit dari AOI.

   Blok baru tidak punya kadar: atribut numerik model lama diisi NaN, atribut kategori diisi '' dan
   atribut kategori AOI_ASAL menandai 'impor' / 'kerangka'. Kadar waste-nya diisi oleh estimasi waste
   (Model Estimation, domain WASTE), bukan oleh modul ini.

   Hasil didaftarkan sebagai versi block model (kind 'aoi'): yang disimpan hanya parameter, bukan blok,
   jadi proyek tetap ringan dan kerangka dibangun ulang saat versi itu diaktifkan.                     */
(function () {
  if (typeof BX === 'undefined' || typeof G === 'undefined') return;
  var CAP = 4000000; /* batas aman jumlah blok */
  var AOI = { cfg: null, msg: '', busy: false, prev: null };
  window.AOI = AOI;

  function nv(v, d) { var x = parseFloat(String(v == null ? '' : v).replace(',', '.')); return isFinite(x) ? x : d; }
  function aE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function fmt(v, d) { return v == null || !isFinite(v) ? '-' : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }

  /* ---------- nilai bawaan: extent dari lubang bor (+ margin), RL dari topografi ---------- */
  function aoiDef() {
    var mg = 50, bs = 5, bz = 2.5, m = BX.m;
    var x0 = G.x0 - mg + offX, x1 = G.x1 + mg + offX, y0 = G.y0 - mg + offY, y1 = G.y1 + mg + offY;
    if (m && m.ext) { x0 = Math.min(x0, m.ext[0]); x1 = Math.max(x1, m.ext[1]); y0 = Math.min(y0, m.ext[2]); y1 = Math.max(y1, m.ext[3]); }
    var zt = G.z1 + 10, zb = G.z0 - 20;
    if (m && m.ext) { zt = Math.max(zt, m.ext[5]); zb = Math.min(zb, m.ext[4]); }
    return { x0: Math.round(x0), x1: Math.round(x1), y0: Math.round(y0), y1: Math.round(y1),
             zb: Math.round(zb), zt: Math.round(zt), bx: bs, by: bs, bz: bz, snap: true,
             topo: (typeof imTopoOk === 'function' && imTopoOk()) ? 1 : 0, pit: 0, poly: '',
             mode: (m ? 'isi' : 'penuh'), name: '' };
  }
  function aoiO() { if (!AOI.cfg) AOI.cfg = aoiDef(); return AOI.cfg; }

  /* ---------- permukaan: topografi aktif & dasar desain pit (koordinat LOKAL) ---------- */
  function surfFn(which) {
    /* sama dengan Reporting BM: permukaan segitiga (TIN) versi aktif bila ada, kalau tidak titik topo / pit */
    try {
      var a = (typeof spAct === 'function') ? spAct(which) : null;
      if (a && a.tin && typeof rpTinFn === 'function') {
        var f = rpTinFn(a.tin);
        return function (x, y) { var r = f(x + offX, y + offY); return r ? (which === 'pit' ? r[0] : r[1]) : null; };
      }
    } catch (e) {}
    if (which === 'pit') return (typeof OV !== 'undefined' && OV.pitF && OV.pitF.x.length) ? rpSurf(OV.pitF) : null;
    if (typeof imTopoOk === 'function' && !imTopoOk()) return null;
    return rpSurf(OV.topoF);
  }

  /* ---------- sel AOI yang sudah tertutup block model aktif ---------- */
  function coverSet(o, m) {
    var S = new Set(), i, a, b, c, A, B, C;
    var kx = function (v) { return Math.floor((v - o.x0) / o.bx); }, ky = function (v) { return Math.floor((v - o.y0) / o.by); }, kz = function (v) { return Math.floor((v - o.zb) / o.bz); };
    for (i = 0; i < m.n; i++) {
      if (!(m.sx[i] > 0)) continue;
      A = kx(m.x[i] - m.sx[i] / 2); B = kx(m.x[i] + m.sx[i] / 2 - 1e-6);
      for (a = A; a <= B; a++) {
        C = ky(m.y[i] - m.sy[i] / 2); var D = ky(m.y[i] + m.sy[i] / 2 - 1e-6);
        for (b = C; b <= D; b++) {
          var E = kz(m.z[i] - m.sz[i] / 2), F = kz(m.z[i] + m.sz[i] / 2 - 1e-6);
          for (c = E; c <= F; c++) S.add(a + ',' + b + ',' + c);
        }
      }
    }
    return S;
  }

  /* ---------- hitung / bangun ---------- */
  function aoiScan(o, base, build) {
    var nx = Math.max(0, Math.floor((o.x1 - o.x0) / o.bx)), ny = Math.max(0, Math.floor((o.y1 - o.y0) / o.by)), nz = Math.max(0, Math.floor((o.zt - o.zb) / o.bz));
    if (!(nx && ny && nz)) throw new Error('Extent atau ukuran blok tidak valid.');
    if (nx * ny * nz > CAP * 4) throw new Error('Grid ' + fmt(nx * ny * nz) + ' sel terlalu besar. Perbesar ukuran blok atau perkecil extent.');
    var tz = o.topo ? surfFn('topo') : null, pz = o.pit ? surfFn('pit') : null;
    if (o.topo && !tz) throw new Error('Topografi belum ada: matikan "potong topografi" atau impor topografi dulu.');
    if (o.pit && !pz) throw new Error('Desain pit belum ada: matikan "di dalam desain pit" atau impor desain pit dulu.');
    var PL = (o.poly && typeof rpPoly === 'function') ? rpPoly(o.poly) : null;
    var cov = (o.mode === 'isi' && base) ? coverSet(o, base) : null;
    var X = build ? [] : null, Y = build ? [] : null, Z = build ? [] : null;
    var n = 0, out = { topo: 0, pit: 0, poly: 0, cov: 0 }, i, j, k;
    for (i = 0; i < nx; i++) {
      var xa = o.x0 + (i + 0.5) * o.bx, xl = xa - offX;
      for (j = 0; j < ny; j++) {
        var ya = o.y0 + (j + 0.5) * o.by, yl = ya - offY;
        if (PL && PL.f && !PL.f(xl, yl)) { out.poly += nz; continue; }
        var ztv = tz ? tz(xl, yl) : null, zpv = pz ? pz(xl, yl) : null;
        if (o.topo && (ztv == null || !isFinite(ztv))) { out.topo += nz; continue; }
        if (o.pit && (zpv == null || !isFinite(zpv))) { out.pit += nz; continue; }
        for (k = 0; k < nz; k++) {
          var za = o.zb + (k + 0.5) * o.bz;
          if (o.topo && za > ztv) { out.topo++; continue; }
          if (o.pit && za < zpv) { out.pit++; continue; }
          if (cov && cov.has(i + ',' + j + ',' + k)) { out.cov++; continue; }
          n++;
          if (n > CAP) throw new Error('Lebih dari ' + fmt(CAP) + ' blok baru. Perbesar ukuran blok atau perkecil AOI.');
          if (build) { X.push(xa); Y.push(ya); Z.push(za); }
        }
      }
    }
    return { n: n, nx: nx, ny: ny, nz: nz, out: out, x: X, y: Y, z: Z, nBase: base ? base.n : 0 };
  }

  /* ---------- model gabungan: blok lama (utuh) + blok kerangka baru ---------- */
  function aoiModel(o, base, R) {
    var nb = R.nBase && o.mode === 'isi' ? base.n : 0, n = nb + R.n, i;
    var m = { name: o.name || ('Kerangka AOI ' + o.bx + 'x' + o.by + 'x' + o.bz + ' m'), n: n,
              x: new Float64Array(n), y: new Float64Array(n), z: new Float64Array(n),
              sx: new Float32Array(n), sy: new Float32Array(n), sz: new Float32Array(n), num: {}, cat: {} };
    for (i = 0; i < nb; i++) { m.x[i] = base.x[i]; m.y[i] = base.y[i]; m.z[i] = base.z[i]; m.sx[i] = base.sx[i]; m.sy[i] = base.sy[i]; m.sz[i] = base.sz[i]; }
    for (i = 0; i < R.n; i++) { var q = nb + i; m.x[q] = R.x[i]; m.y[q] = R.y[i]; m.z[q] = R.z[i]; m.sx[q] = o.bx; m.sy[q] = o.by; m.sz[q] = o.bz; }
    if (nb) {
      Object.keys(base.num).forEach(function (k) { var A = new Float32Array(n); A.fill(NaN); for (var t = 0; t < nb; t++) A[t] = base.num[k][t]; m.num[k] = A; });
      Object.keys(base.cat).forEach(function (k) {
        var c = base.cat[k], C = new Uint16Array(n), t;
        for (t = 0; t < nb; t++) C[t] = c.codes[t];
        for (t = nb; t < n; t++) C[t] = 65535;
        m.cat[k] = { codes: C, dict: c.dict.slice(), cnt: c.cnt.slice() };
      });
    }
    /* penanda asal blok: 'impor' (dari .mdl / CSV) vs 'kerangka' (dibuat modul ini, belum ada kadar) */
    var AC = new Uint16Array(n);
    for (i = 0; i < n; i++) AC[i] = i < nb ? 0 : 1;
    m.cat['AOI_ASAL'] = { codes: AC, dict: ['impor', 'kerangka'], cnt: [nb, R.n] };
    if (!Object.keys(m.num).length) { var ONE = new Float32Array(n); ONE.fill(1); m.num['AOI_BLOK'] = ONE; }
    var s0 = Infinity, x0 = 1e18, x1 = -1e18, y0 = 1e18, y1 = -1e18, z0 = 1e18, z1 = -1e18, sz = {};
    for (i = 0; i < n; i++) {
      if (!(m.sx[i] > 0)) continue;
      s0 = Math.min(s0, m.sx[i], m.sy[i]);
      if (m.x[i] < x0) x0 = m.x[i]; if (m.x[i] > x1) x1 = m.x[i];
      if (m.y[i] < y0) y0 = m.y[i]; if (m.y[i] > y1) y1 = m.y[i];
      if (m.z[i] < z0) z0 = m.z[i]; if (m.z[i] > z1) z1 = m.z[i];
      var kk = m.sx[i] + 'x' + m.sy[i] + 'x' + m.sz[i]; sz[kk] = (sz[kk] || 0) + 1;
    }
    m.s0 = s0; m.ext = [x0, x1, y0, y1, z0, z1];
    var ks = Object.keys(sz).sort(function (a, b) { return sz[b] - sz[a]; });
    m.sizes = ks.slice(0, 3).join(', ') + ' m' + (ks.length > 1 ? ' (sub-blok)' : '');
    m.aoi = { n: R.n, nBase: nb, out: R.out, cfg: JSON.parse(JSON.stringify(o)) };
    return m;
  }

  /* ---------- muat ulang model dasar (versi 'isi' dibangun ulang saat diaktifkan) ---------- */
  async function aoiBase(src, say) {
    if (!src) return null;
    if (window.FP && FP.dir) { var R = await FP.loadSrc(src, SA.D, say); if (R.miss) throw new Error('file ' + src.name + ' tidak ada di folder proyek (sumber/).'); return R.m; }
    var f = SA.srcFiles && SA.srcFiles[src.name];
    if (!f) throw new Error('file ' + src.name + ' tidak tersedia di sesi ini; import lagi lewat "Tambah versi".');
    if (src.kind === 'csv') { var Rr = await SA.readBMcsv(f), cfg = src.cfg; ['x', 'y', 'z'].forEach(function (a) { if (cfg['s' + a] < 0) cfg['s' + a + 'v'] = bxInfer(Rr, cfg[a]); }); return SA.buildBM(Rr, cfg); }
    return await SA.readMDL(f, function () {});
  }

  /* dipakai modul proyek: bangun ulang kerangka dari parameter saja */
  SA.buildAOI = async function (src, say) {
    var o = JSON.parse(JSON.stringify(src.cfg || {})), base = null;
    if (o.mode === 'isi' && src.base) { if (say) say('Membaca block model dasar <b>' + aE(src.base.name) + '</b>&hellip;'); base = await aoiBase(src.base, say); }
    if (say) say('Membangun kerangka blok AOI&hellip;');
    var m = aoiModel(o, base, aoiScan(o, base, true));
    m.src = { kind: 'aoi', name: src.name, cfg: o, base: src.base || null };
    return m;
  };

  /* ---------- dialog ---------- */
  function row(lab, inner) { return '<div><label>' + lab + '</label>' + inner + '</div>'; }
  function inp(id, v, step) { return '<input type=number step=' + (step || 'any') + ' id=' + id + ' value="' + (v == null ? '' : v) + '" oninput="AOI.set(&#39;' + id.slice(3) + '&#39;,this.value)">'; }

  AOI.set = function (k, v) { var o = aoiO(); o[k] = (k === 'name' || k === 'mode' || k === 'poly') ? v : nv(v, o[k]); AOI.prev = null; AOI.body(); };
  AOI.tog = function (k, v) { aoiO()[k] = v ? 1 : 0; AOI.prev = null; AOI.body(); };

  AOI.dlg = function () {
    var d = document.getElementById('aoiDlg');
    if (!d) { d = document.createElement('div'); d.id = 'aoiDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    AOI.msg = ''; AOI.prev = null;
    d.innerHTML = '<div class=impBox style=width:min(820px,100%)><div class=impHead><div class=impBrand><div><b>Buat kerangka blok (AOI)</b>' +
      '<small>Grid persegi seluruh area of interest &mdash; ore dan waste &mdash; tanpa block model acuan. Kadar diisi kemudian oleh Model Estimation.</small>' +
      '</div></div><button class="ib ghost" onclick="AOI.close()">Tutup</button></div>' +
      '<div class=impBody id=aoiBody></div>' +
      '<div class=impFoot><div id=aoiMsg class=hint></div><button class=ib id=aoiGo onclick="AOI.go()">Buat kerangka &rarr;</button></div></div>';
    d.style.display = 'flex'; AOI.body();
  };
  AOI.close = function () { var d = document.getElementById('aoiDlg'); if (d) d.style.display = 'none'; };

  AOI.body = function () {
    var b = document.getElementById('aoiBody'); if (!b) return;
    var o = aoiO(), m = BX.m, PLs = (typeof rpPolyList === 'function') ? rpPolyList() : [];
    var h = '<div class=cmh>Extent (koordinat sebenarnya)</div><div class=cm>' +
      row('E minimum', inp('aoix0', o.x0)) + row('E maksimum', inp('aoix1', o.x1)) +
      row('N minimum', inp('aoiy0', o.y0)) + row('N maksimum', inp('aoiy1', o.y1)) +
      row('RL dasar', inp('aoizb', o.zb)) + row('RL atas', inp('aoizt', o.zt)) + '</div>' +
      '<div class=cmh>Ukuran blok</div><div class=cm>' +
      row('Ukuran X (m)', inp('aoibx', o.bx)) + row('Ukuran Y (m)', inp('aoiby', o.by)) + row('Ukuran Z / tinggi flitch (m)', inp('aoibz', o.bz)) + '</div>' +
      '<div class=cmh>Batas (blok di luar batas tidak dibuat)</div>' +
      '<label class=sw><input type=checkbox ' + (o.topo ? 'checked' : '') + ' onchange="AOI.tog(&#39;topo&#39;,this.checked)">Potong topografi aktif (hanya blok di bawah permukaan)</label>' +
      '<label class=sw><input type=checkbox ' + (o.pit ? 'checked' : '') + ' onchange="AOI.tog(&#39;pit&#39;,this.checked)">Di dalam desain pit (antara dasar pit dan topografi)</label>' +
      '<div class=f><label>Poligon area</label><select onchange="AOI.set(&#39;poly&#39;,this.value)"><option value="">(tanpa poligon)</option>' +
      PLs.map(function (p) { return '<option value="' + aE(p[0]) + '"' + (String(p[0]) === String(o.poly) ? ' selected' : '') + '>' + aE(p[1]) + '</option>'; }).join('') + '</select></div>';
    h += '<div class=cmh>Block model yang sedang aktif</div>';
    if (m) {
      h += '<div class=hint style="margin-bottom:6px"><b>' + aE(m.name) + '</b> &middot; ' + fmt(m.n) + ' blok &middot; ukuran ' + aE(m.sizes) +
        '<br>E ' + fmt(m.ext[0]) + '&ndash;' + fmt(m.ext[1]) + ' &middot; N ' + fmt(m.ext[2]) + '&ndash;' + fmt(m.ext[3]) + ' &middot; RL ' + fmt(m.ext[4], 1) + '&ndash;' + fmt(m.ext[5], 1) + '</div>' +
        '<div class=f><label>Perlakuan</label><select onchange="AOI.set(&#39;mode&#39;,this.value)">' +
        '<option value=isi' + (o.mode === 'isi' ? ' selected' : '') + '>Pertahankan &amp; isi kekosongan &mdash; blok baru hanya di luar cakupannya</option>' +
        '<option value=penuh' + (o.mode === 'penuh' ? ' selected' : '') + '>Ganti &mdash; kerangka baru seluruh AOI, model aktif diabaikan</option>' +
        '</select></div>';
      if (o.mode === 'isi') h += '<div class=hint>Blok lama dipertahankan utuh beserta seluruh atributnya (termasuk kadar waste dari .mdl). Blok baru tidak punya kadar &mdash; atribut kategori <code>AOI_ASAL</code> membedakan <b>impor</b> dan <b>kerangka</b>.</div>';
    } else h += '<div class=hint>Belum ada block model aktif: kerangka dibuat untuk seluruh AOI.</div>';
    h += '<div class=cmh>Perkiraan</div><div id=aoiPrev class=hint>' + (AOI.prev || '<button onclick="AOI.hit()">Hitung jumlah blok</button>') + '</div>' +
      '<div class=f style="margin-top:6px"><label>Nama block model</label><input type=text value="' + aE(o.name) + '" oninput="AOI.cfg.name=this.value"></div>';
    b.innerHTML = h;
    var mm = document.getElementById('aoiMsg'); if (mm) mm.innerHTML = AOI.msg || '';
  };

  AOI.hit = function () {
    var o = aoiO(), p = document.getElementById('aoiPrev');
    if (p) p.innerHTML = 'Menghitung&hellip;';
    setTimeout(function () {
      try {
        var o2 = norm(o), R = aoiScan(o2, (o2.mode === 'isi' ? BX.m : null), false);
        AOI.prev = 'Grid ' + fmt(R.nx) + ' &times; ' + fmt(R.ny) + ' &times; ' + fmt(R.nz) + ' sel &rarr; <b>' + fmt(R.n) + ' blok baru</b>' +
          (R.nBase && o2.mode === 'isi' ? ' + ' + fmt(R.nBase) + ' blok impor dipertahankan = <b>' + fmt(R.n + R.nBase) + ' blok</b>' : '') +
          '<br>dibuang: ' + fmt(R.out.topo) + ' di atas topografi &middot; ' + fmt(R.out.pit) + ' di luar pit &middot; ' + fmt(R.out.poly) + ' di luar poligon &middot; ' + fmt(R.out.cov) + ' sudah tercakup model impor' +
          '<br>volume blok baru &asymp; ' + fmt(R.n * o2.bx * o2.by * o2.bz) + ' m&sup3;';
      } catch (e) { AOI.prev = '<span class=warn>' + aE(e.message || e) + '</span>'; }
      AOI.body();
    }, 10);
  };

  function norm(o) {
    var c = JSON.parse(JSON.stringify(o));
    ['bx', 'by', 'bz'].forEach(function (k) { if (!(c[k] > 0)) throw new Error('Ukuran blok harus lebih besar dari nol.'); });
    if (c.x1 <= c.x0 || c.y1 <= c.y0 || c.zt <= c.zb) throw new Error('Extent tidak valid: maksimum harus lebih besar dari minimum.');
    if (c.snap) { c.x0 = Math.floor(c.x0 / c.bx) * c.bx; c.y0 = Math.floor(c.y0 / c.by) * c.by; c.zb = Math.floor(c.zb / c.bz) * c.bz; }
    c.x1 = c.x0 + Math.ceil((c.x1 - c.x0) / c.bx) * c.bx;
    c.y1 = c.y0 + Math.ceil((c.y1 - c.y0) / c.by) * c.by;
    c.zt = c.zb + Math.ceil((c.zt - c.zb) / c.bz) * c.bz;
    return c;
  }

  AOI.go = function () {
    if (AOI.busy) return;
    var btn = document.getElementById('aoiGo'), msg = document.getElementById('aoiMsg');
    AOI.busy = true; if (btn) btn.disabled = true; if (msg) msg.innerHTML = 'Membangun kerangka&hellip;';
    setTimeout(function () {
      try {
        var o = norm(aoiO()), base = o.mode === 'isi' ? BX.m : null, R = aoiScan(o, base, true);
        if (!R.n && !(base && o.mode === 'isi')) throw new Error('Tidak ada blok yang terbentuk: periksa extent, RL, dan batas topografi / pit.');
        var m = aoiModel(o, base, R);
        m.src = { kind: 'aoi', name: m.name, cfg: o, base: base && base.src ? base.src : null };
        if (o.mode === 'isi' && base && !base.src) m.src.base = null;
        BX.m = m; BX.ui = bxDefUI(m); BX.ver++; BX.sc = {};
        var sh = document.getElementById('bxShow'); if (sh) sh.checked = true;
        bxPanel();
        if (typeof meApply === 'function') { try { meApply(true); } catch (e) {} }
        if (typeof bxvReg === 'function') { try { bxvReg(); } catch (e) {} }
        if (SA.dirty) { SA.bxDirty = true; SA.dirty(); }
        AOI.close(); updatePlot();
        if (typeof uiTab === 'function') uiTab('BM');
        AOI.msg = '';
        alert('Kerangka blok dibuat: ' + fmt(R.n) + ' blok baru' + (R.nBase && o.mode === 'isi' ? ' + ' + fmt(R.nBase) + ' blok impor dipertahankan' : '') +
          ' (total ' + fmt(m.n) + ').\n\nBlok baru belum punya kadar. Isi dengan Model Estimation: domain vein untuk ore, domain WASTE untuk material di luar solid.');
      } catch (e) {
        console.error(e);
        if (msg) msg.innerHTML = '<span class=warn>' + aE(e.message || e) + '</span>';
      } finally { AOI.busy = false; if (btn) btn.disabled = false; }
    }, 10);
  };

  /* ---------- tombol di panel Block Model ---------- */
  function addBtn() {
    var g = document.querySelector('#pBM .g2'); if (!g || document.getElementById('aoiBtn')) return;
    var w = document.createElement('div'); w.style.gridColumn = 'span 2'; w.style.marginBottom = '6px';
    w.innerHTML = '<button id=aoiBtn class=mdbtn style="margin:0;border:0;width:100%" onclick="AOI.dlg()">&#8862; Buat kerangka blok (AOI)</button>' +
      '<div class=hint style="margin-top:3px">Tanpa block model acuan: grid persegi seluruh AOI (ore + waste), dipotong topografi / desain pit. Bila sudah ada model impor, kekosongannya saja yang diisi.</div>';
    g.parentNode.insertBefore(w, g.nextSibling);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addBtn); else addBtn();
  setTimeout(addBtn, 300);

  /* ---------- aktifkan versi kind 'aoi' (bangun ulang dari parameter) ---------- */
  if (typeof window.bmActivate === 'function') {
    var _ba = window.bmActivate;
    window.bmActivate = async function (id) {
      var v = null; (window.BXV || []).forEach(function (x) { if (x.id === id) v = x; });
      if (!v || !v.src || v.src.kind !== 'aoi') return _ba.apply(this, arguments);
      if (typeof SPV !== 'undefined' && SPV.busy) return;
      if (BX.m && typeof bxvKey === 'function' && bxvKey(BX.m.src) === bxvKey(v.src)) return;
      if (typeof SPV !== 'undefined') SPV.busy = true;
      var say = function (t) { if (typeof SPV !== 'undefined') { SPV.msg = t; if (typeof spPanel === 'function') spPanel(); } };
      try {
        var m = await SA.buildAOI(v.src, say);
        m.name = v.name || m.name; BX.m = m; BX.ui = bxDefUI(m); BX.ver++; BX.sc = {};
        var sh = document.getElementById('bxShow'); if (sh) sh.checked = true;
        bxPanel(); if (SA.dirty) { SA.bxDirty = true; SA.dirty(); }
        say('&#10003; Kerangka blok AOI aktif: <b>' + aE(m.name) + '</b> (' + fmt(m.n) + ' blok). Hasil Model Estimation dipasang ulang per posisi blok.');
        updatePlot();
      } catch (e) { console.error(e); say('<span class=warn>' + aE(e.message || e) + '</span>'); }
      finally { if (typeof SPV !== 'undefined') SPV.busy = false; if (typeof spPanel === 'function') spPanel(); }
    };
  }
})();
