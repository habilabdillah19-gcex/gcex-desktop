/* bahasa.js — pemilih bahasa antarmuka GC-Ex (Block Model + Drillhole), tahap 1: menu, tombol, judul panel, label isian.
   Pemilik 19 Nov 2026: "tambahan menu untuk memilih bahasa (Indonesia default, Inggris UK, Inggris US, Spanyol, dan Sunda)".
   - Kamus: window.GXLANG_KAMUS (bahasa_kamus.js, dibuat dari web-src/bahasa/kamus.tsv). Kunci = teks inti Bahasa Indonesia.
   - Penerjemahan di tampilan saja: hanya teks di dalam tombol/label/judul/opsi (SEL) dan atribut title/placeholder.
     Isi data (Hole ID, kode litologi, angka) tidak pernah diubah; nilai <option value> tidak disentuh.
   - Teks asli disimpan per simpul (WeakMap) sehingga kembali ke Indonesia memulihkan teks persis. Bila aplikasi menulis
     ulang sebuah teks, teks baru itu dianggap asli yang baru.
   - Bahasa Indonesia (bawaan) = tidak ada pengamat yang berjalan, tanpa beban kinerja. Disimpan di localStorage gcex_bahasa.
   API: GXLANG.daftar(), GXLANG.pakai(kode), GXLANG.aktif(), GXLANG.t(teks), GXLANG.asli(el) */
(function () {
  'use strict';
  var BAHASA = [
    { k: 'id', nm: 'Bahasa Indonesia', i: -1 },
    { k: 'en-GB', nm: 'English (UK)', i: 0 },
    { k: 'en-US', nm: 'English (US)', i: 1 },
    { k: 'es', nm: 'Español', i: 2 },
    { k: 'su', nm: 'Basa Sunda', i: 3 }
  ];
  var KUNCI = 'gcex_bahasa';
  var SEL = 'button,label,option,optgroup,h1,h2,h3,h4,h5,summary,legend,th,.tb,.tab,[role=tab],.menu a,.mi,.sb,.ttl,.hd,.sec,.pnlT,.ptl,.ptn,.pi2~b';
  var LEWAT = 'script,style,textarea,pre,code,svg,.js-plotly-plot,[contenteditable],[data-gx-asli-saja]';
  var K = window.GXLANG_KAMUS || {}, KL = {}, KN = {};
  Object.keys(K).forEach(function (k) { KL[k.toLowerCase()] = K[k]; if (k.indexOf('#') >= 0) KN[k] = K[k]; });
  var PK = 'id'; try { PK = localStorage.getItem(KUNCI) || 'id'; } catch (e) { }
  if (!BAHASA.some(function (b) { return b.k === PK; })) PK = 'id';
  var idx = function () { for (var i = 0; i < BAHASA.length; i++) if (BAHASA[i].k === PK) return BAHASA[i].i; return -1; };

  var reDepan = /^[^0-9A-Za-zÀ-ɏ(\[{<]*/, reBelakang = /[\s:….▾▸►›»→←▲▼▶◀]*$/;
  function terjemah(s, ix) {
    if (ix < 0 || !s) return s;
    var a = s.match(reDepan)[0], r = s.slice(a.length), b = r.match(reBelakang)[0], inti = r.slice(0, r.length - b.length);
    if (!inti || inti.length > 140) return s;
    var v = K[inti] || KL[inti.toLowerCase()];
    if (v) return a + v[ix] + b;
    if (/\d/.test(inti)) {   /* pola angka: "Panel tersembunyi (3)" -> kunci "Panel tersembunyi (#)" */
      var nums = [], pola = inti.replace(/\d+(?:[.,]\d+)?/g, function (m) { nums.push(m); return '#'; }), w = KN[pola];
      if (w) { var j = 0; return a + w[ix].replace(/#/g, function () { return nums[j++]; }) + b; }
    }
    return s;
  }

  var asliT = new WeakMap(), pasangT = new WeakMap(), asliA = new WeakMap();
  function bolehEl(p) { return p && p.nodeType === 1 && (p.matches(SEL) || (p.parentElement && p.parentElement.matches(SEL))) && !p.closest(LEWAT); }
  function prosesTeks(n, ix) {
    var v = n.nodeValue; if (!v || !/[A-Za-z]{2}/.test(v)) return;
    if (pasangT.get(n) !== v) asliT.set(n, v);            /* belum pernah / sudah ditulis ulang oleh aplikasi */
    var o = asliT.get(n), t = ix < 0 ? o : terjemah(o, ix);
    if (t !== v) { n.nodeValue = t; }
    pasangT.set(n, t);
  }
  function prosesAttr(e, ix) {
    ['title', 'placeholder'].forEach(function (a) {
      if (!e.hasAttribute(a)) return; var v = e.getAttribute(a), m = asliA.get(e) || {};
      if (!m[a] || m[a][1] !== v) m[a] = [v, v];
      var t = ix < 0 ? m[a][0] : terjemah(m[a][0], ix); m[a][1] = t; asliA.set(e, m);
      if (t !== v) e.setAttribute(a, t);
    });
  }
  function proses(akar, ix) {
    if (!akar) return;
    if (akar.nodeType === 3) { if (bolehEl(akar.parentElement)) prosesTeks(akar, ix); return; }
    if (akar.nodeType !== 1 || akar.closest(LEWAT)) return;
    var w = document.createTreeWalker(akar, NodeFilter.SHOW_TEXT, null), n;
    while ((n = w.nextNode())) if (bolehEl(n.parentElement)) prosesTeks(n, ix);
    if (akar.matches('[title],[placeholder]')) prosesAttr(akar, ix);
    akar.querySelectorAll('[title],[placeholder]').forEach(function (e) { if (!e.closest(LEWAT)) prosesAttr(e, ix); });
  }

  var antri = [], jadwal = 0, mo = null;
  function kuras() { jadwal = 0; var ix = idx(), q = antri; antri = []; if (ix < 0) return; mo && mo.takeRecords(); q.forEach(function (n) { if (n.isConnected) proses(n, ix); }); mo && mo.takeRecords(); }
  function amati() {
    if (mo) return;
    mo = new MutationObserver(function (rs) {
      rs.forEach(function (r) {
        if (r.type === 'childList') r.addedNodes.forEach(function (n) { antri.push(n); });
        else antri.push(r.target);
      });
      if (!jadwal) jadwal = requestAnimationFrame(kuras);
    });
    mo.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['title', 'placeholder'] });
  }

  function pakai(k) {
    if (!BAHASA.some(function (b) { return b.k === k; })) return;
    var lama = PK; PK = k; try { localStorage.setItem(KUNCI, k); } catch (e) { }
    document.documentElement.lang = k === 'id' ? 'id' : k;
    var ix = idx();
    if (mo) mo.disconnect(), mo = null;
    if (ix >= 0 || lama !== 'id') proses(document.body, ix);
    if (ix >= 0) amati();
    gambarUI();
    try { window.dispatchEvent(new CustomEvent('gxbahasa', { detail: { bahasa: k } })); } catch (e) { }
  }

  function gambarUI() {
    var host = document.getElementById('pView'); if (!host) return;
    var box = document.getElementById('gxLang');
    if (!box) {
      box = document.createElement('div'); box.id = 'gxLang'; box.className = 'uisec';
      var pal = document.getElementById('gxPal'); host.insertBefore(box, pal ? pal : host.firstChild);
    }
    var ix = idx(), judul = ix < 0 ? 'Bahasa' : (K['Bahasa'] || ['Language', 'Language', 'Idioma', 'Basa'])[ix];
    box.setAttribute('data-gx-asli-saja', '');   /* nama bahasa selalu ditulis dalam bahasanya sendiri */
    box.innerHTML = '<h4 style="margin:2px 0 6px">' + judul + ' <span style="font-weight:400;opacity:.7">· Language</span></h4>' +
      '<select id=gxLangSel style="width:100%">' + BAHASA.map(function (b) {
        return '<option value="' + b.k + '"' + (b.k === PK ? ' selected' : '') + '>' + b.nm + (b.k === 'id' ? ' (bawaan)' : '') + '</option>';
      }).join('') + '</select>' +
      '<div style="font-size:11px;opacity:.75;margin-top:4px">' + (ix < 0 ? 'Tahap 1: menu, tombol, judul panel &amp; label. Pesan &amp; laporan masih Bahasa Indonesia.' :
        ['Stage 1: menus, buttons, panel titles &amp; labels. Messages &amp; reports are still in Indonesian.',
          'Stage 1: menus, buttons, panel titles &amp; labels. Messages &amp; reports are still in Indonesian.',
          'Etapa 1: menús, botones, títulos y etiquetas. Los mensajes e informes siguen en indonesio.',
          'Tahap 1: ménu, tombol, judul panel &amp; labél. Pesen &amp; laporan masih dina Basa Indonésia.'][ix]) + '</div>';
    box.querySelector('select').onchange = function () { pakai(this.value); };
  }

  window.GXLANG = {
    daftar: function () { return BAHASA.map(function (b) { return { k: b.k, nm: b.nm }; }); },
    pakai: pakai, aktif: function () { return PK; },
    t: function (s) { return terjemah(s, idx()); },
    asli: function (el) { if (!el) return ''; var s = ''; el.childNodes.forEach(function (c) { if (c.nodeType === 3) s += asliT.get(c) || c.nodeValue; }); return s; }
  };
  var mulai = function () { gambarUI(); if (PK !== 'id') pakai(PK); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(mulai, 50); }); else setTimeout(mulai, 50);
})();
