/* ================= Perataan panel PROPERTI yang adaptif (BM 0.24.116, pemilik 27-11-2026) =================
   Permintaan pemilik: panel yang tidak "allign" (isian sendirian setengah baris, isian sebaris tidak sejajar, pilihan
   terpotong, tombol terlipat, deretan tombol patah, tabel terpotong) harus rapi dan adaptif pada lebar panel berapa pun.
   Satu aturan untuk SEMUA panel (tidak per panel), dijalankan ulang setiap panel digambar ulang atau lebarnya berubah:
     1. Grid 2-3 kolom: sel yang pilihannya / tulisan tombolnya tidak muat -> melebar satu baris penuh.
     2. Baris grid yang tidak penuh (isian sendirian) -> sel terakhirnya mengisi sisa baris.
     3. Isian sebaris selalu sejajar: tinggi label dalam satu baris disamakan (label terlipat tidak menggeser isian).
     4. Deretan tombol yang patah baris: tombol mengisi rata tiap baris (tidak ada tombol menggantung setengah).
     5. Tabel yang lebih lebar dari panel -> bisa digeser ke samping, tidak terpotong.
   Gaya asli elemen disimpan dan dipulihkan sebelum setiap perhitungan, jadi melebarkan panel mengembalikan susunan asli.
   Grid > 4 kolom (tabel warna kelas dsb.) dan Project Tree tidak disentuh. Uji: tools/uji/uji_rata_panel.py */
(function () {
  var ROOT = 'side', SKIP = '#ptree,#ptHdr,#ptPH,#gxNolOv', TANDA = 'data-rata';
  var cv = null;
  function lebarTeks(el, t) {
    cv = cv || document.createElement('canvas').getContext('2d');
    var cs = getComputedStyle(el); cv.font = cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily; return cv.measureText(t).width;
  }
  function tampak(e) { var r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }
  function simpan(e, p) { var k = TANDA + '-' + p; if (!e.hasAttribute(k)) e.setAttribute(k, e.style[p] || ''); e.setAttribute(TANDA, '1'); }
  function pulihkan(root) {
    [].forEach.call(root.querySelectorAll('[' + TANDA + ']'), function (e) {
      ['gridColumn', 'gridTemplateColumns', 'marginTop', 'flex', 'whiteSpace', 'flexBasis'].forEach(function (p) { var k = TANDA + '-' + p; if (e.hasAttribute(k)) { e.style[p] = e.getAttribute(k); e.removeAttribute(k); } });
      e.removeAttribute(TANDA);
    });
  }
  function kolom(g) { var t = getComputedStyle(g).gridTemplateColumns; return t && t !== 'none' ? t.split(' ').filter(Boolean).length : 1; }
  function anak(g) { return [].filter.call(g.children, function (c) { return c.tagName !== 'SCRIPT' && c.tagName !== 'STYLE' && getComputedStyle(c).display !== 'none' && tampak(c); }); }
  function rentang(c, cols) { var cs = getComputedStyle(c), s = cs.gridColumnStart, e = cs.gridColumnEnd, m = /span (\d+)/.exec(e) || /span (\d+)/.exec(s);
    if (m) return Math.min(cols, +m[1]); if (e === '-1' || (s === '1' && e === '-1')) return cols; var a = parseInt(s, 10), b = parseInt(e, 10); return a > 0 && b > a ? b - a : 1; }
  function kontrol(c) { return c.matches('select,input,button,textarea') ? c : c.querySelector('select,input:not([type=checkbox]):not([type=radio]):not([type=color]),button,textarea'); }
  function tidakMuat(c) {
    var s = c.tagName === 'SELECT' ? [c] : [].slice.call(c.querySelectorAll('select'));
    var b = c.matches('button,label.mdbtn,.btn') ? [c] : [].slice.call(c.querySelectorAll('button,label.mdbtn'));
    return s.some(function (x) { if (x.selectedIndex < 0 || !x.options.length) return false; var cs = getComputedStyle(x), ruang = x.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) - 16;
        return lebarTeks(x, x.options[x.selectedIndex].text) > ruang + 1; }) ||
      b.some(function (x) { var t = (x.textContent || '').trim(); if (t.length < 4) return false; var cs = getComputedStyle(x), ruang = x.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
        return lebarTeks(x, t) > ruang + 1 || x.scrollHeight > x.clientHeight + 2; });
  }
  function baris(g, ch) { var R = []; ch.forEach(function (c) { var t = Math.round(c.getBoundingClientRect().top), r = R.filter(function (x) { return Math.abs(x.t - t) < 4; })[0]; if (!r) R.push(r = { t: t, c: [] }); r.c.push(c); }); return R; }
  function ratakanGrid(g) {
    var cols = kolom(g); if (cols < 2 || cols > 4) return; var ch = anak(g); if (!ch.length) return;
    /* 0. kolom terlalu sempit (grid 3-4 kolom di panel sempit) -> jumlah kolom menyesuaikan lebar */
    if (cols > 2 && g.clientWidth / cols < 92) { simpan(g, 'gridTemplateColumns'); g.style.gridTemplateColumns = 'repeat(auto-fit,minmax(92px,1fr))'; cols = kolom(g); }
    /* 1. sel yang tidak muat -> satu baris penuh */
    ch.forEach(function (c) { if (rentang(c, cols) < cols && tidakMuat(c)) { simpan(c, 'gridColumn'); c.style.gridColumn = '1 / -1'; } });
    /* 2. baris tidak penuh -> sel terakhir mengisi sisa */
    baris(g, ch).forEach(function (r) { var pakai = r.c.reduce(function (s, c) { return s + rentang(c, cols); }, 0);
      if (pakai < cols) { var z = r.c[r.c.length - 1]; simpan(z, 'gridColumn'); z.style.gridColumn = 'span ' + (cols - pakai + rentang(z, cols)); } });
    /* 3. isian sebaris sejajar: isian yang lebih tinggi didorong turun setara isian terendah (label terlipat tidak menggeser) */
    baris(g, anak(g)).forEach(function (r) {
      if (r.c.length < 2) return; var K = r.c.map(function (c) { var k = c.querySelector('select,input:not([type=checkbox]):not([type=radio]):not([type=color]),textarea'); return k && c.firstElementChild && c.firstElementChild.tagName === 'LABEL' ? k : null; });
      if (K.some(function (k) { return !k; })) return; var T = K.map(function (k) { return k.getBoundingClientRect().top; }), mx = Math.max.apply(null, T);
      K.forEach(function (k, i) { var d = mx - T[i]; if (d > 0.5) { simpan(k, 'marginTop'); k.style.marginTop = (parseFloat(getComputedStyle(k).marginTop) || 0) + d + 'px'; } });
    });
  }
  function ratakanFlex(f) {
    var cs = getComputedStyle(f); if (cs.display !== 'flex' || cs.flexWrap !== 'wrap' || cs.flexDirection.indexOf('column') === 0) return;
    var ch = anak(f), btn = ch.filter(function (c) { return c.tagName === 'BUTTON'; }); if (btn.length < 1 || btn.length < ch.length - 1) return;
    if (baris(f, ch).length < 2) return;
    var kep = ch[0].tagName !== 'BUTTON' ? ch[0] : null; if (kep) { simpan(kep, 'flexBasis'); kep.style.flexBasis = '100%'; }
    btn.forEach(function (b) { simpan(b, 'flex'); simpan(b, 'whiteSpace'); b.style.flex = '1 1 auto'; b.style.whiteSpace = 'nowrap'; });
  }
  function ratakanTabel(t) {
    var p = t.parentElement; if (!p || p.classList.contains('rataGeser')) return;
    if (t.getBoundingClientRect().width <= p.clientWidth + 1) return;
    var ov = getComputedStyle(p).overflowX; if (ov === 'auto' || ov === 'scroll') return;
    var w = document.createElement('div'); w.className = 'rataGeser'; p.insertBefore(w, t); w.appendChild(t);
  }
  var jalan = false, jadwal = 0;
  function ratakan() {
    var root = document.getElementById(ROOT); if (!root || jalan) return; jalan = true;
    try {
      pulihkan(root);
      var semua = [].filter.call(root.querySelectorAll('*'), function (e) { return !e.closest(SKIP) && !e.closest('table') && tampak(e); });
      semua.forEach(function (e) { if (getComputedStyle(e).display === 'grid') ratakanGrid(e); });
      semua.forEach(function (e) { ratakanFlex(e); });
      [].forEach.call(root.querySelectorAll('table'), function (t) { if (!t.closest(SKIP) && tampak(t)) ratakanTabel(t); });
    } catch (e) { console.error(e); } finally { jalan = false; }
  }
  function nanti() { if (jadwal) return; jadwal = requestAnimationFrame(function () { jadwal = 0; ratakan(); }); }
  function pasang() {
    var root = document.getElementById(ROOT); if (!root) return setTimeout(pasang, 500);
    var st = document.createElement('style');
    st.textContent = '.rataGeser{overflow-x:auto;max-width:100%}.rataGeser>table{margin:0}#side .g2>*,#side .g3>*{min-width:0}#side .g2 input,#side .g3 input,#side .g2 select,#side .g3 select{max-width:100%;min-width:0}';
    document.head.appendChild(st);
    new MutationObserver(function (m) { if (jalan) return; if (m.some(function (x) { return x.type === 'childList' || (x.type === 'attributes' && x.attributeName !== 'style' && x.attributeName.indexOf(TANDA) !== 0); })) nanti(); })
      .observe(root, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'hidden', 'open'] });
    if (window.ResizeObserver) new ResizeObserver(nanti).observe(root);
    root.addEventListener('change', function (e) { if (e.target && e.target.tagName === 'SELECT') nanti(); }, true);
    window.RATA = { jalan: ratakan };
    nanti();
  }
  pasang();
})();
