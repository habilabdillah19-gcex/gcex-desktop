/* ================= SUB-BLOCKING DI BATAS SOLID =================
   Blok utuh dihitung berdasarkan titik pusatnya: blok yang separuh di dalam vein dan separuh di luar
   tetap dihitung 100% ore atau 100% waste. Pada vein tebal 2–4 m dengan blok 5 × 5 × 2,5 m, kesalahan
   batas itu sendiri sebesar dilusi yang mau diukur — jadi angka dilusi & ore loss tidak bisa dipercaya
   sebelum blok di perbatasan dipecah.

   Modul ini memecah blok yang MENYEBERANGI batas solid domain menjadi 2 x 2 x 2 blok anak, berulang
   sampai sejumlah tingkat yang dipilih. Pemecahan 2 x 2 x 2 (bukan 2 x 2 x 1) disengaja: block model
   Surpac .mdl adalah octree yang membelah ketiga sumbu bersamaan dengan tingkat yang sama, sehingga
   blok anak tetap jatuh tepat di kisi octree dan model masih bisa ditulis balik ke .mdl.

   Uji "menyeberang" memakai 27 titik (kisi 3 x 3 x 3 di dalam kotak blok): bila semuanya di dalam
   solid atau semuanya di luar, blok dibiarkan utuh; bila bercampur, blok dipecah. Kisi 27 titik dipilih
   supaya vein tipis yang melintas tengah blok tanpa menyentuh sudut tetap terdeteksi.

   SUB-BLOK YANG SUDAH ADA DIHORMATI: blok yang ukurannya sudah mencapai (atau lebih kecil dari) batas
   ukuran minimum tidak dipecah lagi. Jadi model Surpac yang memang sudah ber-sub-blok di sekitar
   wireframe tidak dipecah ulang — pekerjaan itu sudah dilakukan dan hasilnya dipakai apa adanya.

   Atribut blok anak diwarisi dari induknya (kadar berlaku untuk volumenya), termasuk atribut kategori.
   Dijalankan SEBELUM estimasi: posisi blok berubah, sehingga hasil estimasi lama tidak lagi cocok.    */
(function () {
  if (typeof BX === 'undefined') return;
  var CAP = 4000000;
  var SB = { cfg: null, msg: '', busy: false, prev: null };
  window.SB = SB;

  function sE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function fmt(v, d) { return v == null || !isFinite(v) ? '-' : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
  function nv(v, d) { var x = parseFloat(String(v == null ? '' : v).replace(',', '.')); return isFinite(x) ? x : d; }

  function defCfg() { return { lv: 2, nama: '' }; }
  function cfg() { if (!SB.cfg) SB.cfg = defCfg(); return SB.cfg; }

  /* ---------- solid seluruh domain ---------- */
  function solids() {
    var L = (window.gmTops ? gmTops() : (window.GM ? GM.doms : [])) || [], W = [];
    L.forEach(function (d) {
      var R = (typeof meGrpR === 'function') ? meGrpR(d) : null;
      if (R && R.mesh) W.push({ name: d.name, w: R.W || (R._W || (R._W = wfInside(R.mesh))), bb: meBBox(R.mesh) });
    });
    return W;
  }

  /* 0 = seluruhnya di luar, 1 = seluruhnya di dalam, 2 = menyeberang batas */
  function straddle(W, cx, cy, cz, sx, sy, sz) {
    var hx = sx / 2, hy = sy / 2, hz = sz / 2, nIn = 0, nAll = 0, i, j, k;
    /* lewati solid yang kotak pembatasnya tidak bersinggungan dengan blok ini */
    var act = [];
    for (i = 0; i < W.length; i++) {
      var b = W[i].bb;
      if (cx + hx < b[0] || cx - hx > b[1] || cy + hy < b[2] || cy - hy > b[3] || cz + hz < b[4] || cz - hz > b[5]) continue;
      act.push(W[i]);
    }
    if (!act.length) return 0;
    for (i = 0; i < 3; i++) for (j = 0; j < 3; j++) for (k = 0; k < 3; k++) {
      var x = cx + (i - 1) * hx * 0.98, y = cy + (j - 1) * hy * 0.98, z = cz + (k - 1) * hz * 0.98, inside = false;
      for (var q = 0; q < act.length && !inside; q++) if (act[q].w.f(x, y, z)) inside = true;
      nAll++; if (inside) nIn++;
    }
    return nIn === 0 ? 0 : (nIn === nAll ? 1 : 2);
  }

  /* ---------- hitung / pecah ---------- */
  function scan(c, build) {
    var m = BX.m;
    if (!m) throw new Error('Belum ada block model aktif.');
    var W = solids();
    if (!W.length) throw new Error('Belum ada solid domain yang terbangun (Geological Modelling ④). Sub-blocking memakai batas solid sebagai acuan.');
    var lv = Math.max(1, Math.min(3, Math.round(+c.lv || 1))), i;
    /* ukuran minimum dihitung dari ukuran blok DOMINAN (bukan terkecil) dibagi 2^tingkat, per sumbu.
       Blok yang sudah lebih halus dari batas itu - mis. sub-blok bawaan Surpac - tidak dipecah lagi. */
    var sd = domSize(m);
    if (!sd) throw new Error('Ukuran blok tidak terbaca.');
    var lim = [sd[0] / Math.pow(2, lv), sd[1] / Math.pow(2, lv), sd[2] / Math.pow(2, lv)];
    var OUT = build ? { x: [], y: [], z: [], sx: [], sy: [], sz: [], src: [] } : null;
    var n = 0, nSplit = 0, nKeep = 0, nSudah = 0, nStr = 0;
    /* tumpukan: [cx,cy,cz,sx,sy,sz,indukAsli] */
    var push = function (x, y, z, sx, sy, sz, p) { n++; if (n > CAP) throw new Error('Hasil melebihi ' + fmt(CAP) + ' blok. Kurangi tingkat pecah.'); if (build) { OUT.x.push(x); OUT.y.push(y); OUT.z.push(z); OUT.sx.push(sx); OUT.sy.push(sy); OUT.sz.push(sz); OUT.src.push(p); } };
    for (i = 0; i < m.n; i++) {
      if (!(m.sx[i] > 0)) { push(m.x[i], m.y[i], m.z[i], m.sx[i], m.sy[i], m.sz[i], i); nKeep++; continue; }
      var st = [[m.x[i], m.y[i], m.z[i], m.sx[i], m.sy[i], m.sz[i]]], anyStr = false;
      while (st.length) {
        var b = st.pop(), s = straddle(W, b[0] - offX, b[1] - offY, b[2], b[3], b[4], b[5]);
        if (s !== 2) { push(b[0], b[1], b[2], b[3], b[4], b[5], i); continue; }
        anyStr = true;
        /* anak hanya dibuat bila ukurannya masih >= batas minimum pada KETIGA sumbu */
        if (b[3] / 2 < lim[0] * (1 - 1e-9) || b[4] / 2 < lim[1] * (1 - 1e-9) || b[5] / 2 < lim[2] * (1 - 1e-9)) {
          push(b[0], b[1], b[2], b[3], b[4], b[5], i); nSudah++; continue;
        }
        var hx = b[3] / 2, hy = b[4] / 2, hz = b[5] / 2;
        for (var a = -1; a <= 1; a += 2) for (var q = -1; q <= 1; q += 2) for (var r = -1; r <= 1; r += 2)
          st.push([b[0] + a * hx / 2, b[1] + q * hy / 2, b[2] + r * hz / 2, hx, hy, hz]);
        nSplit++;
      }
      if (anyStr) nStr++;
    }
    return { n: n, nAsal: m.n, nSplit: nSplit, nStr: nStr, nSudah: nSudah, lim: lim, sd: sd, lv: lv, nDom: W.length, OUT: OUT };
  }

  /* ukuran blok dominan (triple yang paling banyak muncul) */
  function domSize(m) {
    var cnt = {}, st = Math.max(1, Math.floor(m.n / 50000)), i;
    for (i = 0; i < m.n; i += st) { if (!(m.sx[i] > 0)) continue; var k = m.sx[i] + '_' + m.sy[i] + '_' + m.sz[i]; cnt[k] = (cnt[k] || 0) + 1; }
    var b = Object.keys(cnt).sort(function (p, q) { return cnt[q] - cnt[p]; })[0];
    return b ? b.split('_').map(Number) : null;
  }
  window.sbDomSize = domSize;

  function build(c, R) {
    var m = BX.m, O = R.OUT, n = R.n, i;
    var o = { name: c.nama || (m.name + ' (sub-blok batas solid)'), n: n,
              x: new Float64Array(n), y: new Float64Array(n), z: new Float64Array(n),
              sx: new Float32Array(n), sy: new Float32Array(n), sz: new Float32Array(n), num: {}, cat: {} };
    for (i = 0; i < n; i++) { o.x[i] = O.x[i]; o.y[i] = O.y[i]; o.z[i] = O.z[i]; o.sx[i] = O.sx[i]; o.sy[i] = O.sy[i]; o.sz[i] = O.sz[i]; }
    Object.keys(m.num).forEach(function (k) { var A = m.num[k], B = new Float32Array(n); for (var t = 0; t < n; t++) B[t] = A[O.src[t]]; o.num[k] = B; });
    Object.keys(m.cat).forEach(function (k) {
      var c0 = m.cat[k], C = new Uint16Array(n), cnt = c0.dict.map(function () { return 0; });
      for (var t = 0; t < n; t++) { var v = c0.codes[O.src[t]]; C[t] = v; if (v !== 65535 && v < cnt.length) cnt[v]++; }
      o.cat[k] = { codes: C, dict: c0.dict.slice(), cnt: cnt };
    });
    var s0 = Infinity, x0 = 1e18, x1 = -1e18, y0 = 1e18, y1 = -1e18, z0 = 1e18, z1 = -1e18, sz = {};
    for (i = 0; i < n; i++) {
      if (!(o.sx[i] > 0)) continue;
      s0 = Math.min(s0, o.sx[i], o.sy[i]);
      if (o.x[i] < x0) x0 = o.x[i]; if (o.x[i] > x1) x1 = o.x[i];
      if (o.y[i] < y0) y0 = o.y[i]; if (o.y[i] > y1) y1 = o.y[i];
      if (o.z[i] < z0) z0 = o.z[i]; if (o.z[i] > z1) z1 = o.z[i];
      var kk = o.sx[i] + 'x' + o.sy[i] + 'x' + o.sz[i]; sz[kk] = (sz[kk] || 0) + 1;
    }
    o.s0 = s0; o.ext = [x0, x1, y0, y1, z0, z1];
    var ks = Object.keys(sz).sort(function (a, b) { return sz[b] - sz[a]; });
    o.sizes = ks.slice(0, 3).join(', ') + ' m' + (ks.length > 1 ? ' (sub-blok)' : '');
    /* octree .mdl: origin & ukuran blok akar tetap, tingkat bertambah -> model masih bisa ditulis balik */
    if (m.mdl) o.mdl = Object.assign({}, m.mdl, { levels: (m.mdl.levels || 0) + R.lv, add: [] });
    o.sub = { lv: R.lv, nAsal: R.nAsal, nSplit: R.nSplit, nStr: R.nStr, nSudah: R.nSudah };
    return o;
  }

  /* ---------- muat ulang model dasar (versi 'sub' dibangun ulang saat diaktifkan) ---------- */
  async function baseOf(src, say) {
    if (!src) throw new Error('model dasar tidak tercatat; import / buat ulang modelnya.');
    if (src.kind === 'aoi') return await SA.buildAOI(src, say);
    if (window.FP && FP.dir) { var R = await FP.loadSrc(src, SA.D, say); if (R.miss) throw new Error('file ' + src.name + ' tidak ada di folder proyek (sumber/).'); return R.m; }
    var f = SA.srcFiles && SA.srcFiles[src.name];
    if (!f) throw new Error('file ' + src.name + ' tidak tersedia di sesi ini; import lagi lewat "Tambah versi".');
    if (src.kind === 'csv') { var Rr = await SA.readBMcsv(f), cf = src.cfg; ['x', 'y', 'z'].forEach(function (a) { if (cf['s' + a] < 0) cf['s' + a + 'v'] = bxInfer(Rr, cf[a]); }); return SA.buildBM(Rr, cf); }
    return await SA.readMDL(f, function () {});
  }

  SA.buildSub = async function (src, say) {
    var keep = BX.m;
    if (say) say('Membaca block model dasar&hellip;');
    var b = await baseOf(src.base, say);
    BX.m = b;
    try {
      if (say) say('Memecah blok di batas solid&hellip;');
      var c = JSON.parse(JSON.stringify(src.cfg || defCfg())), R = scan(c, true), m = build(c, R);
      m.src = { kind: 'sub', name: src.name, cfg: c, base: src.base };
      return m;
    } finally { BX.m = keep; }
  };

  /* ---------- dialog ---------- */
  SB.set = function (k, v) { var c = cfg(); c[k] = (k === 'nama') ? v : nv(v, c[k]); SB.prev = null; SB.body(); };

  SB.dlg = function () {
    var d = document.getElementById('sbDlg');
    if (!d) { d = document.createElement('div'); d.id = 'sbDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    SB.msg = ''; SB.prev = null;
    d.innerHTML = '<div class=impBox style=width:min(780px,100%)><div class=impHead><div class=impBrand><div><b>Pecah blok di batas solid (sub-blocking)</b>' +
      '<small>Blok yang separuh di dalam vein dan separuh di luar dipecah 2 &times; 2 &times; 2, supaya volume ore / waste per blok akurat untuk dilusi &amp; ore loss.</small>' +
      '</div></div><button class="ib ghost" onclick="SB.close()">Tutup</button></div>' +
      '<div class=impBody id=sbBody></div>' +
      '<div class=impFoot><div id=sbMsg class=hint></div><button class=ib id=sbGo onclick="SB.go()">Pecah blok &rarr;</button></div></div>';
    d.style.display = 'flex'; SB.body();
  };
  SB.close = function () { var d = document.getElementById('sbDlg'); if (d) d.style.display = 'none'; };

  SB.body = function () {
    var b = document.getElementById('sbBody'); if (!b) return;
    var c = cfg(), m = BX.m, W = [];
    try { W = solids(); } catch (e) {}
    var sd = m ? sbDomSize(m) : null;
    var h = '';
    if (!m) h += '<div class=hint><span class=warn>Belum ada block model aktif.</span> Import block model, atau buat kerangka blok (AOI) dulu.</div>';
    else h += '<div class=hint><b>' + sE(m.name) + '</b> &middot; ' + fmt(m.n) + ' blok &middot; ukuran ' + sE(m.sizes) + '</div>';
    if (!W.length) h += '<div class=hint><span class=warn>Belum ada solid domain terbangun.</span> Sub-blocking memakai batas solid sebagai acuan: bangun solid di Geological Modelling &#9315; dulu.</div>';
    else h += '<div class=hint>Acuan: ' + W.length + ' solid &mdash; ' + sE(W.map(function (q) { return q.name; }).join(', ')) + '</div>';
    h += '<div class=cmh>Tingkat pecah</div><div class=cm>' +
      '<div><label title="Setiap tingkat membelah blok menjadi 2 x 2 x 2 (8 anak). Hanya blok yang menyeberangi batas solid yang dipecah.">Jumlah tingkat</label>' +
      '<select onchange="SB.set(&#39;lv&#39;,this.value)">' +
      [1, 2, 3].map(function (q) { return '<option value=' + q + (c.lv === q ? ' selected' : '') + '>' + q + ' tingkat (1 : ' + Math.pow(2, q) + ' per sumbu, 1 : ' + Math.pow(8, q) + ' per volume)</option>'; }).join('') +
      '</select></div>' +
      '<div><label title="Dihitung dari ukuran blok dominan model ini">Ukuran blok terkecil setelah dipecah</label><input type=text disabled value="' +
      (sd ? sd.map(function (q) { return (q / Math.pow(2, Math.max(1, Math.min(3, c.lv)))).toFixed(3); }).join(' x ') + ' m (dari ' + sd.join(' x ') + ' m)' : '-') + '"></div></div>';
    h += '<div class=hint>Blok yang ukurannya <b>sudah mencapai batas itu</b> tidak dipecah lagi: sub-blok yang sudah ada di model Surpac dihormati, bukan dipecah ulang.</div>';
    h += '<div class=cmh>Perkiraan</div><div id=sbPrev class=hint>' + (SB.prev || '<button onclick="SB.hit()">Hitung jumlah blok</button>') + '</div>';
    h += '<div class=f style="margin-top:6px"><label>Nama block model hasil</label><input type=text value="' + sE(c.nama) + '" oninput="SB.cfg.nama=this.value"></div>';
    if (window.ME && ME.store && ME.store.B && ME.store.B.x.length)
      h += '<div class=warn style="margin-top:6px">&#9888; Sudah ada hasil Model Estimation (' + fmt(ME.store.B.x.length) + ' baris). Posisi blok berubah setelah dipecah, sehingga hasil lama tidak lagi cocok dan harus dijalankan ulang. Lakukan sub-blocking <b>sebelum</b> estimasi.</div>';
    b.innerHTML = h;
    var mm = document.getElementById('sbMsg'); if (mm) mm.innerHTML = SB.msg || '';
  };

  SB.hit = function () {
    var p = document.getElementById('sbPrev');
    if (p) p.innerHTML = 'Menghitung&hellip;';
    setTimeout(function () {
      try {
        var R = scan(cfg(), false);
        SB.prev = fmt(R.nStr) + ' dari ' + fmt(R.nAsal) + ' blok menyeberangi batas solid &rarr; dipecah ' + fmt(R.nSplit) + ' kali' +
          '<br>hasil: <b>' + fmt(R.n) + ' blok</b> (semula ' + fmt(R.nAsal) + ', bertambah ' + fmt(R.n - R.nAsal) + ')' +
          '<br>ukuran terkecil ' + R.lim.map(function (q) { return q.toFixed(3); }).join(' &times; ') + ' m (dari blok dominan ' + R.sd.join(' &times; ') + ' m)' +
          (R.nSudah ? '<br>' + fmt(R.nSudah) + ' blok sudah mencapai batas ukuran minimum &rarr; dibiarkan utuh' : '');
      } catch (e) { SB.prev = '<span class=warn>' + sE(e.message || e) + '</span>'; }
      SB.body();
    }, 10);
  };

  SB.go = function () {
    if (SB.busy) return;
    var btn = document.getElementById('sbGo'), msg = document.getElementById('sbMsg');
    SB.busy = true; if (btn) btn.disabled = true; if (msg) msg.innerHTML = 'Memecah blok&hellip;';
    setTimeout(function () {
      try {
        var c = cfg(), base = BX.m, R = scan(c, true);
        if (!R.nSplit) throw new Error('Tidak ada blok yang menyeberangi batas solid: tidak ada yang perlu dipecah. (Blok yang sudah cukup halus dihormati.)');
        var m = build(c, R);
        m.src = { kind: 'sub', name: m.name, cfg: c, base: base && base.src ? base.src : null };
        BX.m = m; BX.ui = bxDefUI(m); BX.ver++; BX.sc = {};
        var sh = document.getElementById('bxShow'); if (sh) sh.checked = true;
        bxPanel();
        if (typeof meApply === 'function') { try { meApply(true); } catch (e) {} }
        if (typeof bxvReg === 'function') { try { bxvReg(); } catch (e) {} }
        if (SA.dirty) { SA.bxDirty = true; SA.dirty(); }
        var fr = SB.frac(10, true);
        SB.close(); updatePlot();
        if (typeof uiTab === 'function') uiTab('BM');
        var vol = 0, FQ = m.num['sb_frac'];
        if (FQ) for (var t = 0; t < m.n; t++) vol += m.sx[t] * m.sy[t] * m.sz[t] * FQ[t];
        alert('Sub-blocking selesai: ' + fmt(R.nStr) + ' blok di perbatasan dipecah, hasil ' + fmt(m.n) + ' blok (semula ' + fmt(R.nAsal) + ').' +
          (fr ? '\n\nAtribut sb_frac ikut dihitung: ' + fmt(fr.nFull) + ' blok seluruhnya di dalam solid, ' + fmt(fr.nPart) + ' di perbatasan (proporsi 0–1).' +
                '\nVolume ore berbobot: ' + fmt(vol) + ' m\u00b3. Pilih sb_frac pada "Timbang volume & tonase" di Reporting BM.' : '') +
          '\n\nJalankan Model Estimation sesudah ini.');
      } catch (e) {
        console.error(e);
        if (msg) msg.innerHTML = '<span class=warn>' + sE(e.message || e) + '</span>';
      } finally { SB.busy = false; if (btn) btn.disabled = false; }
    }, 10);
  };

  /* ================= PROPORSI VOLUME ORE PER BLOK (sb_frac) =================
     Sub-blocking memperkecil kesalahan batas tetapi tidak menghilangkannya: blok tetap dihitung utuh
     berdasarkan titik pusatnya, sehingga blok terkecil di perbatasan masih dihitung 100% ore atau 100%
     waste. Uji pada vein mendatar tebal 4 m dengan blok 5 m memperlihatkannya: utuh -100%, 1 tingkat
     +25%, 3 tingkat -6% — membaik, tetapi berayun, bukan menuju nol dengan rapi.

     Jalan keluarnya: simpan PROPORSI volume blok yang berada di dalam solid sebagai atribut sb_frac
     (0..1), lalu Reporting BM menimbang volume & tonase dengan atribut itu. Blok di perbatasan ikut
     seadanya — 0,35 blok ore dan 0,65 blok waste — bukan dibulatkan ke salah satu.

     Proporsi dihitung dengan cuplikan kisi di dalam kotak blok: 0 bila seluruh 27 titik di luar, 1 bila
     seluruhnya di dalam, dan bila bercampur dicuplik lebih halus (nF^3 titik, bawaan 10^3 = 1.000).      */
  SB.frac = function (nF, quiet) {   /* nF = titik cuplikan per sumbu; bawaan 10 (1.000 titik per blok perbatasan) */
    var m = BX.m;
    if (!m) { if (!quiet) alert('Belum ada block model aktif.'); return null; }
    var W;
    try { W = solids(); } catch (e) { if (!quiet) alert(e.message || e); return null; }
    if (!W.length) { if (!quiet) alert('Belum ada solid domain terbangun (Geological Modelling ④).'); return null; }
    var N = Math.max(4, Math.min(16, Math.round(+nF || 10)));
    var F = new Float32Array(m.n), nPart = 0, nFull = 0, nNol = 0, i;
    for (i = 0; i < m.n; i++) {
      var cx = m.x[i] - offX, cy = m.y[i] - offY, cz = m.z[i], s = straddle(W, cx, cy, cz, m.sx[i], m.sy[i], m.sz[i]);
      if (s === 0) { F[i] = 0; nNol++; continue; }
      if (s === 1) { F[i] = 1; nFull++; continue; }
      var hx = m.sx[i] / 2, hy = m.sy[i] / 2, hz = m.sz[i] / 2, nIn = 0, a, b, c;
      for (a = 0; a < N; a++) for (b = 0; b < N; b++) for (c = 0; c < N; c++) {
        /* titik tengah sel cuplikan: integrasi titik-tengah, bukan titik sudut */
        var x = cx - hx + (2 * a + 1) * hx / N, y = cy - hy + (2 * b + 1) * hy / N, z = cz - hz + (2 * c + 1) * hz / N, ins = false;
        for (var q = 0; q < W.length && !ins; q++) if (W[q].w.f(x, y, z)) ins = true;
        if (ins) nIn++;
      }
      F[i] = nIn / (N * N * N); nPart++;
    }
    m.num['sb_frac'] = F;
    if (m.mdl) m.mdl.add = (m.mdl.add || []).filter(function (a2) { return a2.name !== 'sb_frac'; }).concat([{ name: 'sb_frac', type: 2, dec: 3, def: 0 }]);
    BX.sc = {}; BX.ver++;
    if (typeof bxPanel === 'function') bxPanel();
    if (SA.dirty) { SA.bxDirty = true; SA.dirty(); }
    var out = { nPart: nPart, nFull: nFull, nNol: nNol, N: N };
    if (!quiet) {
      var vol = 0; for (i = 0; i < m.n; i++) vol += m.sx[i] * m.sy[i] * m.sz[i] * F[i];
      alert('Atribut sb_frac dihitung (cuplikan ' + N + '\u00b3 = ' + (N * N * N) + ' titik per blok perbatasan).\n\n' +
        fmt(nFull) + ' blok seluruhnya di dalam solid\n' + fmt(nPart) + ' blok di perbatasan (proporsi 0–1)\n' + fmt(nNol) + ' blok seluruhnya di luar\n\n' +
        'Volume ore berbobot: ' + fmt(vol) + ' m\u00b3.\n\nDi Reporting BM pilih sb_frac pada "Timbang volume & tonase" agar blok perbatasan ikut seadanya.');
    }
    return out;
  };

  /* ---------- tombol di panel Block Model ---------- */
  function addBtn() {
    var g = document.getElementById('aoiBtn');
    g = g ? g.parentNode : document.querySelector('#pBM .g2');
    if (!g || document.getElementById('sbBtn')) return;
    var w = document.createElement('div'); w.style.marginBottom = '6px';
    w.innerHTML = '<button id=sbBtn class=mdbtn style="margin:0;border:0;width:100%" onclick="SB.dlg()">&#9707; Pecah blok di batas solid</button>' +
      '<div class=hint style="margin-top:3px">Blok yang separuh di dalam vein dipecah 2 &times; 2 &times; 2 (berulang), supaya volume ore / waste per blok akurat untuk dilusi &amp; ore loss. Sub-blok yang sudah ada dihormati. Jalankan <b>sebelum</b> estimasi.</div>' +
      '<button id=sbFracBtn style="width:100%;margin-top:4px" onclick="SB.frac(10)">&#9634; Hitung proporsi volume ore per blok (sb_frac)</button>' +
      '<div class=hint style="margin-top:3px">Tanpa memecah blok: proporsi volume tiap blok yang berada di dalam solid, 0&ndash;1. Dipakai Reporting BM untuk menimbang volume &amp; tonase, sehingga blok perbatasan ikut <b>seadanya</b> alih-alih dibulatkan ke ore atau waste.</div>';
    g.parentNode.insertBefore(w, g.nextSibling);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addBtn); else addBtn();
  setTimeout(addBtn, 400);

  /* ---------- aktifkan versi kind 'sub' ---------- */
  if (typeof window.bmActivate === 'function') {
    var _ba = window.bmActivate;
    window.bmActivate = async function (id) {
      var v = null; (window.BXV || []).forEach(function (x) { if (x.id === id) v = x; });
      if (!v || !v.src || v.src.kind !== 'sub') return _ba.apply(this, arguments);
      if (typeof SPV !== 'undefined' && SPV.busy) return;
      if (BX.m && typeof bxvKey === 'function' && bxvKey(BX.m.src) === bxvKey(v.src)) return;
      if (typeof SPV !== 'undefined') SPV.busy = true;
      var say = function (t) { if (typeof SPV !== 'undefined') { SPV.msg = t; if (typeof spPanel === 'function') spPanel(); } };
      try {
        var m = await SA.buildSub(v.src, say);
        m.name = v.name || m.name; BX.m = m; BX.ui = bxDefUI(m); BX.ver++; BX.sc = {};
        var sh = document.getElementById('bxShow'); if (sh) sh.checked = true;
        bxPanel(); if (SA.dirty) { SA.bxDirty = true; SA.dirty(); }
        say('&#10003; Block model sub-blok aktif: <b>' + sE(m.name) + '</b> (' + fmt(m.n) + ' blok).');
        updatePlot();
      } catch (e) { console.error(e); say('<span class=warn>' + sE(e.message || e) + '</span>'); }
      finally { if (typeof SPV !== 'undefined') SPV.busy = false; if (typeof spPanel === 'function') spPanel(); }
    };
  }
})();
