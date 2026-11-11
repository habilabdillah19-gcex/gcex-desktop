/* ================= JALUR PROYEK (Drill Hole 0.24.73) — bagian HALAMAN PEMBUKA =================
   Keputusan pemilik 11 Nov 2026: pembedaan "Mulai dari nol" vs "Lanjutkan dari Surpac / Leapfrog"
   ditentukan sejak halaman pembuka dan berlaku ke seluruh node, menu dan panel.

   Aturan (disepakati 18:38):
     - Jalur ditentukan oleh ADA TIDAKNYA objek model dari software lain yang dipakai:
       wireframe / domain, block model (.mdl / CSV), parameter estimasi. Data mentah (bor, topografi,
       as-mined, desain pit, orthofoto, data referensi) tidak dihitung.
     - Mulai dari nol  : setiap tahap hanya "Buat di GC-Ex"; semua pintu acuan tersembunyi.
     - Lanjutan        : setiap tahap punya dua pintu, "Pakai acuan" (bila acuannya dicentang) atau
                         "Buat baru di GC-Ex". Tidak ada alat GC-Ex yang disembunyikan.
     - Jalur Nol = Lanjutan yang semua pintu acuannya ditutup; mesin hitungnya SATU.
   Modul ini hanya memegang pilihan di layar Import; penyaringan node / menu / panel ada di jalur_dh.js
   (sumber viewer). Status disimpan di pekerjaan proyek (w.jalur) oleh jalur_dh.js.               */
(function () {
  if (window.JLR) return;
  var JLR = window.JLR = {
    mode: null,                               /* 'nol' | 'lanjut' | null (belum ditentukan) */
    acuan: { wf: false, bm: false, par: false },
    log: [], tebak: false,
    pend: null                                /* pilihan di layar Import untuk proyek BARU */
  };
  var NAMA = { wf: 'Wireframe / domain (Leapfrog, Surpac)', bm: 'Block model (.mdl / CSV)', par: 'Parameter estimasi (log Surpac / catatan)' };
  JLR.NAMA = NAMA;
  JLR.ACUAN = ['wf', 'bm', 'par'];
  /* boleh(k): pintu "Pakai acuan" untuk tahap k terbuka */
  JLR.boleh = function (k) { return JLR.mode === 'lanjut' && !!JLR.acuan[k]; };
  JLR.bolehPend = function (k) { var p = JLR.pend; return !!(p && p.mode === 'lanjut' && p.acuan && p.acuan[k]); };
  JLR.label = function (m) { return m === 'lanjut' ? 'Lanjutkan dari Surpac / Leapfrog' : m === 'nol' ? 'Mulai dari nol' : 'belum ditentukan'; };

  var $ = function (i) { return document.getElementById(i); };
  var E = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); };
  var imp = function () { return $('imp'); };
  var modeImpor = function () { var i = imp(); if (!i) return 'none'; if (i.classList.contains('ups')) return 'ups'; return window.SA && SA.reopenName ? 'reopen' : 'baru'; };
  var demo = function () { return !!(window.DLAT && DLAT.busy); };

  /* ---------- gaya ---------- */
  var css = document.createElement('style'); css.id = 'jlrImpCss';
  css.textContent =
    '#jlrCard .jlr2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}' +
    '#jlrCard .jlrk{border:1.5px solid var(--bd);border-radius:10px;padding:10px 12px;cursor:pointer;background:var(--sf2);display:flex;flex-direction:column;gap:4px;text-align:left;font:inherit;color:inherit}' +
    '#jlrCard .jlrk:hover{border-color:var(--pr)}' +
    '#jlrCard .jlrk.on{border-color:var(--pr);box-shadow:0 0 0 2px color-mix(in srgb,var(--pr) 35%,transparent)}' +
    '#jlrCard .jlrk b{font-size:13.5px}#jlrCard .jlrk small{opacity:.8;line-height:1.35}' +
    '#jlrCard .jlrAc{margin-top:6px;display:flex;flex-direction:column;gap:3px}' +
    '#jlrCard .jlrAc label{display:flex;gap:6px;align-items:flex-start;font-size:12px;cursor:pointer}' +
    '#jlrCard .jlrMsg{margin-top:6px}' +
    '#jlrCard.ro .jlrk{cursor:default}';
  document.head.appendChild(css);

  /* ---------- kartu di layar Import ---------- */
  function kartu() {
    var i = imp(); if (!i) return null;
    var c = $('jlrCard'); if (c) return c;
    var body = i.querySelector('.impBody'); if (!body) return null;
    c = document.createElement('section'); c.className = 'card upsHide'; c.id = 'jlrCard';
    var pj = $('pjCard');
    if (pj && pj.parentNode === body) body.insertBefore(c, pj.nextSibling); else body.insertBefore(c, body.firstChild);
    return c;
  }
  JLR.impRender = function () {
    var c = kartu(); if (!c) return;
    var md = modeImpor(), p = JLR.pend, ro = md === 'reopen';
    var pilih = function (m, judul, isi) {
      return '<button type=button class="jlrk' + (p && p.mode === m ? ' on' : '') + '" data-jlr="' + m + '"' + (ro ? ' disabled' : '') +
        ' onclick="JLR.pilih(\'' + m + '\')"><b>' + judul + '</b><small>' + isi + '</small></button>';
    };
    var h = '<div class="ch"><span class="no">&#8646;</span><div><b>Jalur proyek</b><small>' +
      (ro ? 'Import ulang mengikuti jalur proyek yang sudah ada: <b>' + E(JLR.label(p && p.mode)) + '</b>. Jalur diubah dari node Proyek &rsaquo; Jalur.'
          : 'Tentukan dulu: semua model dibuat di GC-Ex, atau proyek melanjutkan model dari software lain. Pilihan ini menentukan node, menu dan tombol yang tampil.') +
      '</small></div></div><div class="jlr2">' +
      pilih('nol', 'Mulai dari nol', 'Domain, solid, kerangka blok dan parameter estimasi dibuat di GC-Ex dari data bor. Tidak ada import wireframe atau block model dari software lain.') +
      pilih('lanjut', 'Lanjutkan dari Surpac / Leapfrog', 'Memakai model yang sudah ada sebagai acuan. Tahap yang acuannya tidak dicentang tetap dibuat baru di GC-Ex.') +
      '</div>';
    if (p && p.mode === 'lanjut') {
      h += '<div class="jlrAc"><div class=hint2>Acuan apa yang Anda punya?</div>' + JLR.ACUAN.map(function (k) {
        return '<label><input type=checkbox ' + (p.acuan[k] ? 'checked ' : '') + (ro ? 'disabled ' : '') + 'onchange="JLR.acuanPend(\'' + k + '\',this.checked)">' + E(NAMA[k]) + '</label>';
      }).join('') + '</div>';
    }
    h += '<div class="jlrMsg hint2" id="jlrMsg"></div>';
    c.innerHTML = h; c.classList.toggle('ro', ro);
    JLR.slot();
  };
  JLR.pilih = function (m) {
    var p = JLR.pend || { mode: null, acuan: { wf: false, bm: false, par: false } };
    p.mode = m; if (m === 'nol') p.acuan = { wf: false, bm: false, par: false };
    JLR.pend = p; JLR.impRender();
  };
  JLR.acuanPend = function (k, v) { if (!JLR.pend) return; JLR.pend.acuan[k] = !!v; JLR.impRender(); };

  /* slot Block model di layar Import hanya untuk Lanjutan + acuan block model */
  JLR.slot = function () {
    var i = imp(); if (!i) return;
    var inp = i.querySelector('input[onchange*="SA.bmPick"]'), s = inp && inp.closest('.slot');
    if (!s) return;
    var md = modeImpor(), on = md === 'ups' ? true : JLR.bolehPend('bm');
    s.style.display = on ? '' : 'none';
    var g = s.parentNode; if (g && g.classList) g.classList.toggle('s3', !on);
    var card = s.closest('.card'), b = card && card.querySelector('.ch b');
    if (b && !b.dataset.jlr0) b.dataset.jlr0 = b.innerHTML;
    if (b) b.innerHTML = on ? b.dataset.jlr0 : b.dataset.jlr0.replace(/ &amp; block model| & block model/, '');
    /* file block model yang sudah dipilih sebelum jalur diganti: dilepas, supaya tidak ikut masuk diam-diam */
    if (!on && window.SA && SA.bmF && !demo()) { SA.bmF = null; try { var l = $('sp_bm'); if (l) l.innerHTML = ''; } catch (e) {} try { SA.goState(); } catch (e) {} }
  };

  function pesan(t) { var m = $('jlrMsg'); if (m) m.innerHTML = t ? '<span class=warn>' + t + '</span>' : ''; var c = $('jlrCard'); if (c && t) try { c.scrollIntoView({ block: 'nearest' }); } catch (e) {} }

  /* ---------- tombol Tampilkan viewer: proyek baru wajib memilih jalur ---------- */
  JLR.cekPilih = function () {
    var md = modeImpor();
    if (md !== 'baru' || demo()) return true;
    var p = JLR.pend;
    if (!p || !p.mode) { pesan('Pilih jalur proyek dulu: Mulai dari nol, atau Lanjutkan dari Surpac / Leapfrog.'); return false; }
    if (p.mode === 'lanjut' && !JLR.ACUAN.some(function (k) { return p.acuan[k]; })) { pesan('Jalur Lanjutan: centang minimal satu acuan yang Anda punya (atau pilih Mulai dari nol).'); return false; }
    pesan(''); return true;
  };
  function pasangTombol() {
    var b = $('btnGo'); if (!b || b._jlr) return;
    b._jlr = 1; b.removeAttribute('onclick');
    b.addEventListener('click', function () { if (JLR.cekPilih()) SA.go(); });
  }

  /* ---------- SA.go: jalur proyek baru ditetapkan di sini ----------
     Pemanggilan SA.go() tanpa pilihan (Demo data latihan, skrip uji, import ulang) tidak diblokir:
     jalurnya ditebak dari isinya dan ditandai "perlu konfirmasi" di node Proyek. */
  if (window.SA && typeof SA.go === 'function' && !SA.go._jlr) {
    var _go = SA.go;
    SA.go = function () {
      try {
        /* data latihan: jalur mengikuti tombol yang ditekan, bukan kartu (supaya isi & jalur tidak bertentangan) */
        if (demo()) JLR.pend = JLR.dlatNol ? { mode: 'nol', acuan: { wf: false, bm: false, par: false }, demo: true }
                                         : { mode: 'lanjut', acuan: { wf: true, bm: true, par: false }, demo: true };
        if (!JLR.pend || !JLR.pend.mode) {
          if (demo()) JLR.pend = { mode: 'lanjut', acuan: { wf: true, bm: true, par: false }, demo: true };
          else if (SA.bmF) JLR.pend = { mode: 'lanjut', acuan: { wf: false, bm: true, par: false }, tebak: true };
          else JLR.pend = { mode: 'nol', acuan: { wf: false, bm: false, par: false }, tebak: modeImpor() === 'baru' };
        }
        JLR.pend.go = Date.now();
      } catch (e) {}
      return _go.apply(this, arguments);
    };
    SA.go._jlr = 1;
  }
  /* SA.bmPick dari luar kartu (skrip lama, menu) saat jalur tidak membuka acuan block model */
  if (window.SA && typeof SA.bmPick === 'function' && !SA.bmPick._jlr) {
    var _bp = SA.bmPick;
    SA.bmPick = function (f) {
      if (modeImpor() === 'baru' && JLR.pend && JLR.pend.mode && !JLR.bolehPend('bm') && !demo()) {
        pesan('Block model dari software lain hanya untuk jalur <b>Lanjutkan</b> dengan acuan block model dicentang. Pada jalur Mulai dari nol kerangka blok dibuat di GC-Ex (Block Model &rsaquo; Buat kerangka blok AOI).');
        return;
      }
      return _bp.apply(this, arguments);
    };
    SA.bmPick._jlr = 1;
  }

  /* import ulang: jalur dibaca dari pekerjaan proyek yang tersimpan */
  async function bacaReopen() {
    if (modeImpor() !== 'reopen' || !SA.loadWork) return;
    try { var W = await SA.loadWork(SA.reopenName); if (W && W.jalur && W.jalur.mode) JLR.pend = { mode: W.jalur.mode, acuan: Object.assign({ wf: false, bm: false, par: false }, W.jalur.acuan || {}) }; } catch (e) {}
    JLR.impRender();
  }
  /* ---------- data latihan: dua pintu (pemilik 12 Nov 2026) ----------
     Lanjutkan = seperti sebelumnya (bor + topografi + block model GC + wireframe Leapfrog).
     Mulai dari nol = data bor + topografi + permukaan latihan saja; block model & wireframe latihan tidak dibaca.
     demodata.js (berkas bersama) tidak diubah: DLAT.ada dibungkus selama pemuatan jalur nol. */
  var ACUAN_LAT = /_BM_GC|Leapfrog\.obj$/i, KUNCI_NOL = 'gcex_dlat_nol';
  function bungkusDlat() {
    if (!window.DLAT || DLAT.ada._jlr) return !!window.DLAT;
    var _ada = DLAT.ada;
    DLAT.ada = function (nm) { if (JLR.dlatNol && ACUAN_LAT.test(String(nm))) return false; return _ada.apply(this, arguments); };
    DLAT.ada._jlr = 1;
    var _muat = DLAT.muat;
    DLAT.muat = async function () {
      try { if (JLR.dlatNol) sessionStorage.setItem(KUNCI_NOL, '1'); } catch (e) {}
      try { return await _muat.apply(this, arguments); }
      finally { if (!DLAT.busy) { try { sessionStorage.removeItem(KUNCI_NOL); } catch (e) {} } }
    };
    return true;
  }
  try { if (sessionStorage.getItem(KUNCI_NOL)) { JLR.dlatNol = true; sessionStorage.removeItem(KUNCI_NOL); setTimeout(function () { try { JLR.pilih('nol'); } catch (e) {} }, 0); } } catch (e) {}
  JLR.dlat = function (nol) {
    bungkusDlat();
    JLR.dlatNol = !!nol;
    if (nol) JLR.pilih('nol');
    else { JLR.pilih('lanjut'); JLR.acuanPend('wf', true); JLR.acuanPend('bm', true); }
    var r = DLAT.muat(false);
    Promise.resolve(r).then(function () { var dn = document.getElementById('dsName'); if (nol && dn && /^VeinA_Simulasi$/.test(dn.value)) dn.value = 'VeinA_Nol'; },
                           function () {}).then(function () { JLR.dlatNol = false; });
    return r;
  };
  function tombolLatihan() {
    var b = document.getElementById('dlatBtn');
    if (!b || !window.DLAT) return false;
    bungkusDlat();
    if (document.getElementById('dlatNolBtn')) return true;
    b.innerHTML = '&#8681; Data latihan &mdash; Lanjutkan';
    b.title = 'Data simulasi buku tutorial: bor, topografi, block model GC dan wireframe Leapfrog. Proyek masuk jalur Lanjutkan dari Surpac / Leapfrog. Angka sama dengan tutorial PDF.';
    b.onclick = function () { JLR.dlat(false); };
    var n = b.cloneNode(false);
    n.id = 'dlatNolBtn';
    n.innerHTML = '&#8681; Data latihan &mdash; Mulai dari nol';
    n.title = 'Data simulasi yang sama, tetapi hanya bor, topografi dan permukaan latihan. Block model GC dan wireframe Leapfrog tidak dibaca: domain, solid, kerangka blok dan parameter Anda buat sendiri di GC-Ex.';
    n.onclick = function () { JLR.dlat(true); };
    b.parentNode.insertBefore(n, b.nextSibling);
    /* tampil / sembunyi mengikuti tombol aslinya (DLAT.cari menyalakannya bila berkas latihan ada) */
    var ikut = function () { n.style.display = b.style.display; };
    ikut(); new MutationObserver(ikut).observe(b, { attributes: true, attributeFilter: ['style'] });
    return true;
  }
  var nT = 0, tT = setInterval(function () { if (tombolLatihan() || ++nT > 80) clearInterval(tT); }, 250);

  function mulai() { JLR.impRender(); pasangTombol(); setTimeout(bacaReopen, 400); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mulai); else mulai();
  setTimeout(function () { JLR.impRender(); pasangTombol(); }, 600);
})();
