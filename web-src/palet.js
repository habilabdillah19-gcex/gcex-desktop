/* ================= GC-Ex Block Model 0.24.109 / Drillhole 0.24.111: GANTI PALET WARNA (10 palet) =================
   Pemilik 18 Nov 2026: "Fitur ganti color palet. Dari 8 palet di artifact, ditambah palet dasar yang pertama banget dan
   palet hitam-putih." Pola sama dengan Ore Works 0.24.0 (owPalet): teks asli setiap <style> bertema disimpan; tiap warna hex
   yang dekat (jarak RGB <= 95) ke salah satu warna jangkar palet bawaan digeser ke jangkar palet terpilih dengan selisih yang
   sama (hover / pilihan / garis tetap proporsional). #FFFFFF / #000000 tidak disentuh. Warna data (skala kadar, blok, domain,
   lapisan) ada di JS / Plotly, bukan di <style>, sehingga tidak berubah.
   Letak: panel Pengaturan tampilan > Tampilan & performa > "Palet warna". Pilihan disimpan per komputer:
   localStorage 'gcex_palet_bm' / 'gcex_palet_dh'. Bawaan = palet 9 "Keluarga GC-Ex" aplikasi itu.
   Palet "Dasar" diambil dari riwayat git: BM = tampilan sebelum keluarga_bm.css (lapisan #keluargaBm dimatikan, persis);
   Drillhole = theme_dh.css (bilah atas kuning #F0C047 / navy #233A7E) + variabel dasar sebelum palette_patch earthy. */
(function () {
  if (window.GXPAL) return;
  var DH = (window.GCEX_APP || window.SHELL_APP || 'bm') === 'dh';
  var hx = function (h) { h = h.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; };
  var th = function (a) { return '#' + a.map(function (v) { v = Math.round(Math.max(0, Math.min(255, v))).toString(16); return v.length < 2 ? '0' + v : v; }).join('').toUpperCase(); };
  var mix = function (a, b, t) { var A = hx(a), B = hx(b); return th(A.map(function (v, i) { return v + (B[i] - v) * t; })); };
  var lum = function (h) { return hx(h).map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }).reduce(function (s, v, i) { return s + v * [0.2126, 0.7152, 0.0722][i]; }, 0); };
  var kontras = function (a, b) { var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  /* tombol bertulisan putih: gelapkan sampai kontras >= 4,5:1 */
  /* 4,9 (bukan 4,5) supaya teks berwarna aksen di panel krem (#FAF8F4 dsb.) juga tetap >= 4,5:1 */
  var tombol = function (c) { for (var k = 0; k < 30 && kontras(c, '#FFFFFF') < 4.9; k++) c = mix(c, '#000000', 0.06); return c; };

  /* jangkar = palet bawaan (palet 9) aplikasi ini: warna TERUKUR di aplikasi (getComputedStyle), bukan nama variabel */
  var BASE = DH
    ? { chrome: '#1B2333', chrome2: '#34425F', chromeTx: '#ECE9E1', bar: '#ECEBE6', dock: '#FBFAF7', line: '#D3CDC1', accent: '#B5893E', btn: '#2C3B57', sel: '#DBE6F6', sub: '#5B6478' }
    : { chrome: '#1C2733', chrome2: '#2C3B57', chromeTx: '#E8ECF2', bar: '#EDEBE6', dock: '#F7F5F0', line: '#D3CDC1', accent: '#B8692E', accent2: '#B5893E', btn: '#9C5522', sel: '#F3E3D3', sub: '#5C6672' };
  var HANGAT = { terang: ['#D9D6CC', '#F8F6F1'], gelap: ['#1C2733', '#3A4658'] };
  var PAL = [
    DH ? { k: 'dasar', nm: 'Dasar (palet pertama Drill Hole)', c: { chrome: '#F0C047', chrome2: '#2E4C9E', chromeTx: '#1D2B5E', tx: '#1C2733', bar: '#EEF1F5', dock: '#FFFFFF', line: '#D9DEE5', accent: '#F0C047', accent2: '#233A7E', btn: '#233A7E', sel: '#FFF4C2', sub: '#5B6B7C' }, bg: { terang: ['#DFE6F0', '#FFFFFF'], gelap: ['#1B2333', '#3A4D74'] } }
       : { k: 'dasar', nm: 'Dasar (palet pertama Block Model)', asli: true, c: { chrome: '#1B2333', chrome2: '#283350', chromeTx: '#E9EEF5', bar: '#E7E4DD', dock: '#F8F6F1', line: '#D3CDC1', accent: '#B5893E', accent2: '#1F3A5F', sel: '#E2E5EA', sub: '#62656A' } },
    { k: 'malakit', nm: 'Malakit', c: { chrome: '#14322F', chromeTx: '#E4EFEC', bar: '#F3F1EC', dock: '#FAF8F4', line: '#D5D0C6', accent: '#1E8C6E', accent2: '#B8692E', sel: '#D7EDE5', sub: '#5C6660' }, vp: '#EEF1EE' },
    { k: 'oksida', nm: 'Oksida', c: { chrome: '#262321', chromeTx: '#F1ECE6', bar: '#F4F1ED', dock: '#FBF9F6', line: '#D8D1C8', accent: '#C4571E', accent2: '#3F7D74', sel: '#F5E1D3', sub: '#665E57' }, vp: '#F1EFEC' },
    { k: 'kuarsa', nm: 'Kuarsa-Emas', c: { chrome: '#1F2328', chromeTx: '#ECEDEF', bar: '#F2F2F0', dock: '#FAFAF8', line: '#D3D3CF', accent: '#A88412', accent2: '#4A6B8A', sel: '#F1E7C4', sub: '#5D6168' }, vp: '#EFF0F0' },
    { k: 'azurit', nm: 'Azurit', c: { chrome: '#16205A', chromeTx: '#E6E9F7', bar: '#F3F4F9', dock: '#FAFAFD', line: '#D2D5E4', accent: '#2F4BC4', accent2: '#1E8C6E', sel: '#DCE2FA', sub: '#5A5F75' }, vp: '#EEF0F6' },
    { k: 'garnierit', nm: 'Garnierit', c: { chrome: '#1E3A2C', chromeTx: '#E8F1E6', bar: '#F4F3EB', dock: '#FBFAF4', line: '#D6D3C2', accent: '#4E9A3E', accent2: '#A8692A', sel: '#E0EED3', sub: '#5D6655' }, vp: '#F0F2EC' },
    { k: 'garmal', nm: 'Garnierit-Malakit', c: { chrome: '#1B3A30', chromeTx: '#E6F0EA', bar: '#F4F3EC', dock: '#FBFAF5', line: '#D4D2C3', accent: '#17806B', accent2: '#A8692A', sel: '#D5ECE4', sub: '#5A645B' }, vp: '#EFF2EE' },
    { k: 'gcex', nm: 'GC-Ex (seperti Drill Hole)', c: { chrome: '#1C2733', chrome2: '#2C3B57', chromeTx: '#E8ECF2', bar: '#EDEBE6', dock: '#F7F5F0', line: '#D3CDC1', accent: '#B5893E', accent2: '#2C3B57', btn: '#2C3B57', sel: '#F0E5CF', sub: '#5C6672' }, bg: HANGAT },
    { k: 'bawaan', nm: DH ? 'Keluarga GC-Ex · aksen Drill Hole (bawaan)' : 'Keluarga GC-Ex · aksen Block Model (bawaan)', bawaan: true, c: BASE, bg: HANGAT },
    { k: 'hp', nm: 'Hitam-putih', c: { chrome: '#141414', chrome2: '#2A2A2A', chromeTx: '#F2F2F2', bar: '#EEEEEE', dock: '#F8F8F8', line: '#CFCFCF', accent: '#2B2B2B', accent2: '#7A7A7A', sel: '#E1E1E1', sub: '#5E5E5E' }, bg: { terang: ['#D4D4D4', '#FAFAFA'], gelap: ['#141414', '#3A3A3A'] } }
  ];
  /* teks gelap punya jangkar sendiri (DH: --tx #1F2430 dan teks dasar #1C2733) supaya tidak ikut warna bilah atas bila bilah itu
     terang (DH Dasar = kuning). Di BM teks = #1C2733 = bilah atas, dan BM Dasar memakai lapisan asli, jadi tidak perlu. */
  var ANK = Object.keys(BASE).map(function (k) { return [k, hx(BASE[k])]; });
  if (DH) { ANK.push(['tx', hx('#1F2430')]); ANK.push(['tx', hx('#1C2733')]); }
  function target(P) {
    var c = {}; for (var k in P.c) c[k] = P.c[k];
    if (!c.chrome2) c.chrome2 = mix(c.chrome, '#FFFFFF', 0.12);
    if (!c.accent2) c.accent2 = c.accent;
    c.btn = c.btn ? c.btn : tombol(c.accent);
    if (!c.tx) c.tx = lum(c.chrome) < 0.25 ? c.chrome : '#1C2733';
    return c;
  }
  function peta(P) {
    var c = target(P), cache = {};
    return function (h) {
      var k = h.toUpperCase(); if (cache[k]) return cache[k]; var v = hx(k), best = null, bd = 1e9;
      if (k !== '#FFFFFF' && k !== '#000000') ANK.forEach(function (a) { var d = Math.sqrt(Math.pow(v[0] - a[1][0], 2) + Math.pow(v[1] - a[1][1], 2) + Math.pow(v[2] - a[1][2], 2)); if (d < bd) { bd = d; best = a; } });
      /* aksen berwarna (tembaga / emas / pilihan) hanya menarik warna yang benar-benar dekat (<= 45): merah / oranye status
         (#E03131, #E8590C) dan warna lain yang mirip aksen tetap; jangkar netral (bingkai, panel, garis) <= 95 seperti Ore Works */
      var r = h; if (best && bd <= (/^(accent|accent2|btn|sel)$/.test(best[0]) ? 45 : 95)) { var t = hx(c[best[0]]), a = best[1]; r = th(v.map(function (x, i) { return t[i] + (x - a[i]); })); }
      cache[k] = r; return r;
    };
  }
  var ASLI = new WeakMap(), RX = new RegExp(Object.keys(BASE).map(function (k) { return BASE[k]; }).concat(DH ? ['#1F2430', '#1C2733'] : []).join('|'), 'i');
  function bertema(s) { if (s.id === 'gxPalBg') return false; if (ASLI.has(s)) return true; var t = s.textContent || ''; if (RX.test(t)) { ASLI.set(s, t); return true; } return false; }
  var KEY = DH ? 'gcex_palet_dh' : 'gcex_palet_bm', PK = 'bawaan', tunda = false;
  try { PK = localStorage.getItem(KEY) || 'bawaan'; } catch (e) { }
  function bgP(P) {
    if (P.bg) return P.bg; var c = P.c, vp = P.vp || c.dock;
    return { terang: [mix(vp, c.line, 0.55), mix(vp, '#FFFFFF', 0.45)], gelap: [c.chrome, mix(c.chrome, '#FFFFFF', 0.16)] };
  }
  function latar(P) {
    var s = document.getElementById('gxPalBg');
    if (P.bawaan || P.asli) { if (s) s.remove(); return; }
    var B = bgP(P); if (!s) { s = document.createElement('style'); s.id = 'gxPalBg'; }
    s.textContent = '#stage,#stage.bglat-lembut{background:linear-gradient(' + B.terang[0] + ',' + B.terang[1] + ')!important}#stage.bglat-navy{background:linear-gradient(' + B.gelap[0] + ',' + B.gelap[1] + ')!important}' +
      /* bilah atas terang (Dasar DH = kuning): bilah status bawah tetap gelap, kalau tidak teks terangnya hilang */
      (P.c && kontras(P.c.chrome, '#000000') > kontras(P.c.chrome, '#FFFFFF') ? '#status{background:' + (P.c.accent2 || P.c.btn || '#233A7E') + '!important}' : '');
    document.body.appendChild(s);
  }
  function terapkan(k) {
    var P = PAL.filter(function (p) { return p.k === k; })[0] || PAL.filter(function (p) { return p.bawaan; })[0];
    PK = P.k; try { localStorage.setItem(KEY, PK); } catch (e) { }
    tunda = true;
    var f = P.bawaan || P.asli ? null : peta(P);
    document.querySelectorAll('style').forEach(function (s) {
      if (s.id === 'keluargaBm') { s.media = P.asli ? 'not all' : ''; }
      if (!bertema(s)) return; var t = ASLI.get(s);
      var n = f ? t.replace(/#[0-9a-fA-F]{6}(?=[0-9a-fA-F]{2}(?![0-9a-fA-F])|(?![0-9a-fA-F]))/g, function (m0) { return f(m0); }) : t;
      if (s.textContent !== n) s.textContent = n;
    });
    tunda = false; document.body.dataset.palet = PK; latar(P); gambarUI(); setTimeout(jagaKontras, 0);
    try { if (window.Plotly && document.getElementById('plotDiv') && document.getElementById('plotDiv')._fullLayout) Plotly.Plots.resize('plotDiv'); } catch (e) { }
  }
  /* ---- penjaga kontras teks (pemilik 18 Nov 2026: "sudah tidak ada warna yang menghalangi pembacaan tulisan?") ----
     Audit semua teks yang tampil di ke-10 palet menemukan teks di bilah atas yang warnanya ikut aksen / abu redup (subjudul
     logo, jam di tombol Proyek, tombol Geostatistik DH) dan pita Jalur Lanjutan. Untuk elemen-elemen itu warna teks diukur
     terhadap latar sebenarnya; bila < 4,5:1 warnanya digeser ke arah putih / hitam (mana yang lebih kontras) sampai lolos. */
  var JAGA = '.gcxm,#pjTime,.tb.pri,#top .tb,#jlrPita,#jlrPita *,#top .brand small,.tplg-h,#status>span,#status span';
  var rgbS = function (s) { var m = (s || '').match(/[\d.]+/g); return m ? [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1] : null; };
  var keHex = function (c) { return th([c[0], c[1], c[2]]); };
  /* latar efektif; bila ada gradien, semua titik warnanya (alpha >= 0,5) jadi kandidat dan teks harus lolos di semuanya */
  function latarEl(e) {
    var st = [];
    for (var p = e; p && p.nodeType === 1; p = p.parentElement) {
      var cs = getComputedStyle(p);
      if (/gradient/.test(cs.backgroundImage || '')) { var g = (cs.backgroundImage.match(/rgba?\([^)]*\)/g) || []).map(rgbS).filter(function (c) { return c[3] >= 0.5; }); if (g.length) return g.map(keHex); }
      var c = rgbS(cs.backgroundColor); if (c && c[3] > 0.05) { st.push(c); if (c[3] >= 0.95) break; }
    }
    var r = [255, 255, 255]; for (var i = st.length - 1; i >= 0; i--) { var c = st[i], a = c[3]; r = [c[0] * a + r[0] * (1 - a), c[1] * a + r[1] * (1 - a), c[2] * a + r[2] * (1 - a)]; } return [keHex(r)];
  }
  function jagaKontras() {
    document.querySelectorAll(JAGA).forEach(function (e) {
      if (e.dataset.gxKon) { e.style.removeProperty('color'); delete e.dataset.gxKon; }
      if (!e.offsetWidth) return; var fg = rgbS(getComputedStyle(e).color); if (!fg) return; var f = keHex(fg), bgs = latarEl(e);
      var min = function (c) { return Math.min.apply(null, bgs.map(function (b) { return kontras(c, b); })); };
      if (min(f) >= 4.5) return;
      var gelap = bgs.reduce(function (s, b) { return s + (kontras('#FFFFFF', b) >= kontras('#000000', b) ? 1 : 0); }, 0) * 2 >= bgs.length;
      var arah = gelap ? '#FFFFFF' : '#000000', c = f;
      for (var k = 0; k < 40 && min(c) < 4.5; k++) c = mix(c, arah, 0.08);
      e.style.setProperty('color', c, 'important'); e.dataset.gxKon = '1';
    });
  }
  /* <style> bertema yang ditambahkan belakangan ikut diwarnai */
  var mo = new MutationObserver(function (ms) { if (tunda || PK === 'bawaan') return; for (var i = 0; i < ms.length; i++) for (var j = 0; j < ms[i].addedNodes.length; j++) { var n = ms[i].addedNodes[j]; if (n.tagName === 'STYLE' && n.id !== 'gxPalBg' && bertema(n)) { terapkan(PK); return; } } });

  /* ---- UI: Pengaturan tampilan > Tampilan & performa > Palet warna ---- */
  var css = document.createElement('style'); css.id = 'gxPalUi';
  css.textContent = '#gxPal{margin:2px 0 10px}#gxPal .pr{display:flex;align-items:center;gap:7px;width:100%;padding:4px 6px;border:1px solid transparent;border-radius:3px;background:none;cursor:pointer;font:12px/1.3 inherit;text-align:left;color:inherit}' +
    '#gxPal .pr:hover{background:rgba(0,0,0,.05)}#gxPal .pr.on{border-color:currentColor}#gxPal .ck{width:12px;font-weight:700}#gxPal .sw{display:inline-flex;border:1px solid rgba(0,0,0,.25)}#gxPal .sw i{width:11px;height:13px;display:block}';
  document.head.appendChild(css);
  function gambarUI() {
    var host = document.getElementById('pView'); if (!host) return;
    var box = document.getElementById('gxPal');
    if (!box) { box = document.createElement('div'); box.id = 'gxPal'; box.className = 'uisec'; host.insertBefore(box, host.firstChild); }
    box.innerHTML = '<h4 style="margin:2px 0 6px">Palet warna</h4>' + PAL.map(function (p, i) {
      var c = target(p), on = p.k === PK;
      return '<button type=button class="pr' + (on ? ' on' : '') + '" data-k="' + p.k + '"><span class=ck>' + (on ? '&#10003;' : '') + '</span><span class=sw>' +
        [c.chrome, c.accent, c.accent2, c.dock].map(function (x) { return '<i style="background:' + x + '"></i>'; }).join('') + '</span><span>' + (i + 1) + '. ' + p.nm + '</span></button>';
    }).join('');
    box.querySelectorAll('.pr').forEach(function (b) { b.onclick = function () { terapkan(b.getAttribute('data-k')); }; });
  }
  window.GXPAL = { daftar: function () { return PAL.map(function (p) { return { k: p.k, nm: p.nm, c: target(p) }; }); }, pakai: terapkan, aktif: function () { return PK; }, kontras: kontras, jaga: function () { jagaKontras(); } };
  var mulai = function () { mo.observe(document.head, { childList: true }); mo.observe(document.body, { childList: true }); gambarUI(); if (PK !== 'bawaan') terapkan(PK); setTimeout(jagaKontras, 300); setTimeout(jagaKontras, 3000);
    /* legenda & bilah atas digambar ulang belakangan: jaga lagi (dibatasi) */
    var jd = null; new MutationObserver(function () { if (jd) return; jd = setTimeout(function () { jd = null; jagaKontras(); }, 400); }).observe(document.getElementById('top') || document.body, { childList: true, subtree: true, characterData: true }); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(mulai, 0); }); else setTimeout(mulai, 0);
})();
