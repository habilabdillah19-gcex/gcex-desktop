/* ================= JALUR PROYEK (Drill Hole 0.24.73) — bagian VIEWER =================
   Pasangan jalur_imp_dh.js (halaman pembuka). Modul ini:
     1. menyimpan jalur di pekerjaan proyek (w.jalur = {mode, acuan, log, tebak});
     2. menyaring Project Tree, menu ⋯, ribbon dan panel menurut jalur & acuan:
          pintu acuan WIREFRAME   : node Import Wireframe Geologi, ribbon Wireframe Geologi, panel Wf;
          pintu acuan BLOCK MODEL : Import BM (panel Block Model, Data Spasial › Tambah versi, menu ⋯);
          pintu acuan PARAMETER   : Simpan parameter dari Geostatistik ke domain yang sudah berparameter
                                    meminta konfirmasi dan dicatat di jejak;
     3. menjaga pintu yang tertutup juga dari jalur lain (fungsi dipanggil dari guide.js, skrip lama):
        bxDlg / bmAdd / mdImport(…,'geo') / uiTab('Wf') menolak dengan penjelasan + jalan keluarnya;
     4. menandai objek di jalur Lanjutan: domain eksak (acuan), domain hasil serap, versi block model acuan;
     5. otomasi diperlakukan sesuai jalur:
          Autorun Wireframe  : domain yang TERKUNCI EKSAK ke wireframe acuan tidak ikut (batasnya milik acuan);
          Autorun Estimasi dari Nol / Autorun Estimation (update) / auto-fit variogram : mesinnya tetap satu,
          sudah tidak menimpa parameter yang ada; di jalur Lanjutan + acuan parameter penyimpanan parameter
          baru ke domain berparameter wajib dikonfirmasi & tercatat.
   Tidak ada algoritme estimasi / pemodelan yang diubah: modul ini hanya pintu, label dan pengaman.     */
(function () {
  var JLR = window.JLR; if (!JLR || JLR._viewer) return; JLR._viewer = 1;
  var $ = function (i) { return document.getElementById(i); };
  var fn = function (n) { return typeof window[n] === 'function'; };
  var E = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); };
  var ok = function (f, d) { try { var r = f(); return r === undefined ? d : r; } catch (e) { return d; } };
  var BASE = function () { return { wf: false, bm: false, par: false }; };

  /* ---------- keadaan awal: pilihan halaman pembuka untuk proyek baru ---------- */
  if (JLR.pend && JLR.pend.mode && JLR.pend.go) {
    JLR.mode = JLR.pend.mode; JLR.acuan = Object.assign(BASE(), JLR.pend.acuan || {});
    JLR.tebak = !!JLR.pend.tebak; JLR.log = [];
    catat(JLR.pend.demo ? 'Proyek data latihan (Demo): jalur Lanjutan, acuan wireframe & block model'
      : JLR.pend.tebak ? 'Jalur ditebak dari isi import (tanpa pilihan di halaman pembuka): ' + JLR.label(JLR.mode)
      : 'Proyek dibuat dari halaman pembuka: ' + JLR.label(JLR.mode) + ringkasAcuan());
  }
  function ringkasAcuan(A) {
    A = A || JLR.acuan; var L = JLR.ACUAN.filter(function (k) { return A[k]; }).map(function (k) { return { wf: 'wireframe', bm: 'block model', par: 'parameter' }[k]; });
    return L.length ? ' (acuan: ' + L.join(', ') + ')' : '';
  }
  function catat(t) { JLR.log = JLR.log || []; JLR.log.push({ t: new Date().toISOString(), ket: t, user: ok(function () { return localStorage.getItem('gcex_user') || ''; }, '') }); if (JLR.log.length > 200) JLR.log.splice(0, JLR.log.length - 200); try { if (SA.dirty) SA.dirty(); } catch (e) {} }
  JLR.catat = catat;

  /* ---------- objek acuan yang ada di proyek ---------- */
  function srcAcuan(s) { if (!s) return false; if (s.kind === 'mdl' || s.kind === 'csv') return true; if (s.kind === 'aoi' || s.kind === 'sub') return srcAcuan(s.base); return false; }
  JLR.srcAcuan = srcAcuan;
  JLR.ada = function () {
    var wfN = ok(function () { return MD.models.filter(function (m) { return m.jenis !== 'surf'; }).length; }, 0),
        wfE = ok(function () { return GM.doms.filter(function (d) { return d.wfx; }).length; }, 0),
        wfS = ok(function () { return GM.doms.filter(function (d) { return !d.wfx && serap(d); }).length; }, 0), wf = wfN + wfE;
    var bmL = ok(function () { return BXV.filter(function (v) { return srcAcuan(v.src); }); }, []);
    if (!bmL.length && ok(function () { return BX.m && srcAcuan(BX.m.src); }, false)) bmL = [{ name: BX.m.name, src: BX.m.src }];
    return { wf: wf, wfN: wfN, wfE: wfE, wfS: wfS, bm: bmL.length, bmL: bmL };
  };
  /* domain hasil serap wireframe: punya string berasal 'wf:<nama>' */
  function serap(d) { return ok(function () { return GM.str.some(function (s) { return s.dom === d.id && /^wf:/.test(String(s.src || '')); }); }, false); }
  JLR.serap = serap;
  function ringWf(A) { var r = []; if (A.wfN) r.push(A.wfN + ' wireframe'); if (A.wfE) r.push(A.wfE + ' domain eksak'); if (A.wfS) r.push(A.wfS + ' domain diserap'); return r.join(' · '); }

  /* ---------- sinkron: jalur & acuan harus cocok dengan isi proyek ---------- */
  JLR.sinkron = function (diam) {
    var A = JLR.ada(), ubah = false;
    if (!JLR.mode) {
      JLR.mode = (A.wf || A.bm) ? 'lanjut' : 'nol'; JLR.acuan = { wf: !!A.wf, bm: !!A.bm, par: false }; JLR.tebak = true;
      catat('Proyek dibuat sebelum ada pilihan jalur; GC-Ex menebak dari isinya: ' + JLR.label(JLR.mode) + ringkasAcuan()); ubah = true;
    }
    if (JLR.mode === 'nol' && (A.wf || A.bm)) {
      JLR.mode = 'lanjut'; JLR.tebak = true;
      catat('Proyek jalur Mulai dari nol ternyata berisi objek dari software lain (' + (A.wf ? 'wireframe' : '') + (A.wf && A.bm ? ', ' : '') + (A.bm ? 'block model' : '') + ') — jalur diubah ke Lanjutan, perlu konfirmasi'); ubah = true;
    }
    if (JLR.mode === 'lanjut') {
      if (A.wf && !JLR.acuan.wf) { JLR.acuan.wf = true; catat('Acuan wireframe dinyalakan otomatis (ada wireframe di proyek)'); ubah = true; }
      if (A.bm && !JLR.acuan.bm) { JLR.acuan.bm = true; catat('Acuan block model dinyalakan otomatis (ada block model acuan di proyek)'); ubah = true; }
    }
    if (ubah || !diam) JLR.terapkan();
    return ubah;
  };

  /* ---------- simpan di pekerjaan proyek ---------- */
  if (window.SA && SA.collectWork && !SA.collectWork._jlr) {
    var _c = SA.collectWork;
    SA.collectWork = function () { var w = _c.apply(this, arguments); try { if (JLR.mode) w.jalur = { mode: JLR.mode, acuan: JLR.acuan, log: JLR.log || [], tebak: !!JLR.tebak }; } catch (e) {} return w; };
    SA.collectWork._jlr = 1;
    var _a = SA.applyWork;
    SA.applyWork = function (W) {
      try {
        if (W && W.jalur && W.jalur.mode) {
          JLR.mode = W.jalur.mode; JLR.acuan = Object.assign(BASE(), W.jalur.acuan || {}); JLR.log = (W.jalur.log || []).slice(); JLR.tebak = !!W.jalur.tebak;
        } else if (W && !(JLR.pend && JLR.pend.go && SA.reopenName !== SA.pname)) { JLR.mode = null; }
      } catch (e) {}
      var r = _a.apply(this, arguments);
      setTimeout(function () { try { JLR.sinkron(); } catch (e) {} }, 1500);
      return r;
    };
  }
  setTimeout(function () { try { JLR.sinkron(); } catch (e) {} }, 1800);

  /* ---------- tampilan: kelas body + pita di Properti ---------- */
  var css = document.createElement('style'); css.id = 'jlrCss';
  css.textContent =
    'body.jlr-nowf #rbWf,body.jlr-nowf #pWf{display:none!important}' +
    'body.jlr-nobm #pBM button[onclick="bxDlg()"],body.jlr-nobm button[onclick="bmAdd()"],body.jlr-nobm button[onclick^="bmAdd("]{display:none!important}' +
    'body.pt-card #side>#jlrPita:not(#ptPH):not(#ptCard):not(#ptNav){display:flex!important}' +
    '#jlrPita{display:flex;align-items:center;gap:6px;margin:-4px 0 8px;padding:3px 8px;border-radius:6px;font-size:11px;line-height:1.3;cursor:pointer}' +
    '#jlrPita.nol{background:color-mix(in srgb,#2e9e6b 14%,transparent);color:#1f6f4b}' +
    '#jlrPita.lanjut{background:color-mix(in srgb,#d99a1e 18%,transparent);color:#7a5408}' +
    '#jlrPita .tb{margin-left:auto;font-weight:700}' +
    '.jlrDlg .impBody{display:block}.jlrDlg .jac label{display:flex;gap:6px;align-items:flex-start;margin:3px 0}' +
    '.jlrDlg table{width:100%;border-collapse:collapse;font-size:11.5px}.jlrDlg td{border-top:1px solid var(--bd);padding:3px 4px;vertical-align:top}';
  document.head.appendChild(css);

  JLR.terapkan = function () {
    var b = document.body; if (!b) return;
    var lj = JLR.mode === 'lanjut';
    b.classList.toggle('jlr-nol', JLR.mode === 'nol'); b.classList.toggle('jlr-lanjut', lj);
    b.classList.toggle('jlr-nowf', !JLR.boleh('wf')); b.classList.toggle('jlr-nobm', !JLR.boleh('bm')); b.classList.toggle('jlr-nopar', !JLR.boleh('par'));
    pita(); teks();
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
    try { if (JLR.boleh('wf') === false && window.PT && /^wf(\.|$)/.test(String(PT.sel || ''))) PT.select('gm'); } catch (e) {}
  };
  function pita() {
    var ph = $('ptPH'); if (!ph || !JLR.mode) return;
    var p = $('jlrPita');
    if (!p) { p = document.createElement('div'); p.id = 'jlrPita'; p.title = 'Jalur proyek — klik untuk detail, ubah acuan, atau jejak'; p.onclick = function () { JLR.dlg(); }; ph.parentNode.insertBefore(p, ph.nextSibling); }
    var lj = JLR.mode === 'lanjut';
    p.className = lj ? 'lanjut' : 'nol';
    p.innerHTML = (lj ? '&#128274; Jalur Lanjutan' + E(ringkasAcuan()) : '&#10022; Jalur Mulai dari nol &middot; semua model dibuat di GC-Ex') +
      (JLR.tebak ? '<span class=tb>perlu konfirmasi</span>' : '');
  }
  /* teks panel yang menyebut import block model: di jalur tanpa acuan BM diganti ke jalan GC-Ex */
  function teks() {
    var nb = !JLR.boleh('bm') && !!JLR.mode;
    var h = document.querySelector('#aoiBtn + .hint');
    if (h) { if (!h.dataset.jlr0) h.dataset.jlr0 = h.innerHTML; h.innerHTML = nb ? 'Kerangka blok dibuat di GC-Ex: grid persegi seluruh AOI (ore + waste), dipotong topografi / desain pit. Kadar diisi Model Estimation.' : h.dataset.jlr0; }
    var bb = $('bxBody');
    if (bb && !(window.BX && BX.m)) bb.innerHTML = nb ? '<div class=hint>Belum ada block model. Klik <b>Buat kerangka blok (AOI)</b>.</div>' : '<div class=hint>Belum ada block model. Klik <b>Import block model</b>' + (JLR.mode === 'lanjut' ? '' : '') + ', atau <b>Buat kerangka blok (AOI)</b>.</div>';
  }
  (function () {
    var f = window.bxPanel; if (typeof f !== 'function' || f._jlr) return;
    var g = function () { var r = f.apply(this, arguments); try { if (!(window.BX && BX.m)) teks(); } catch (e) {} return r; };
    g._jlr = 1; window.bxPanel = g; try { bxPanel = g; } catch (e) {}
  })();
  (function tunggu(n) { if ($('ptPH')) { pita(); return; } if (n < 80) setTimeout(function () { tunggu(n + 1); }, 250); })(0);
  /* dialog kerangka AOI: di jalur tanpa acuan block model, label snap tidak menyebut .mdl / Surpac */
  (function () {
    if (!window.AOI || typeof AOI.body !== 'function' || AOI.body._jlr) return;
    var f = AOI.body;
    AOI.body = function () {
      var r = f.apply(this, arguments);
      try {
        if (JLR.mode && !JLR.boleh('bm')) {
          var bd = $('aoiBody'); if (bd) bd.querySelectorAll('label.sw').forEach(function (l) {
            if (/origin block model \.mdl/.test(l.innerHTML)) l.innerHTML = l.innerHTML.replace(/\(bawaan: origin block model \.mdl aktif\) &mdash; blok sejajar dengan model Surpac|\(bawaan: origin block model \.mdl aktif\) — blok sejajar dengan model Surpac/, '&mdash; blok sejajar dengan kisi origin di atas');
          });
        }
      } catch (e) {}
      return r;
    };
    AOI.body._jlr = 1;
  })();

  /* ---------- dialog Jalur proyek (node Proyek › Jalur, pita) ---------- */
  JLR.dlg = function () {
    var d = $('jlrDlg');
    if (!d) { d = document.createElement('div'); d.id = 'jlrDlg'; d.className = 'bxdlg jlrDlg'; document.body.appendChild(d); }
    var A = JLR.ada(), lj = JLR.mode === 'lanjut';
    var h = '<div class=impBox style=width:min(720px,100%)><div class=impHead><div class=impBrand><div><b>Jalur proyek: ' + E(JLR.label(JLR.mode)) + '</b>' +
      '<small>' + (lj ? 'Model dari software lain dipakai sebagai acuan; tahap yang acuannya tidak dicentang dibuat baru di GC-Ex.' : 'Semua model dibuat di GC-Ex dari data bor. Pintu import wireframe dan block model dari software lain tersembunyi.') +
      '</small></div></div><button class="ib ghost" onclick="JLR.dlgTutup()">Tutup</button></div><div class=impBody>';
    if (JLR.tebak) h += '<div class=box style="margin-bottom:8px"><b>Perlu konfirmasi.</b> Jalur ini ditebak GC-Ex dari isi proyek, bukan dipilih di halaman pembuka. ' +
      '<button class=ib onclick="JLR.konfirmasi()">Benar, pakai jalur ini</button></div>';
    if (lj) {
      h += '<div class=cmh>Acuan yang dipakai</div><div class=jac>' + JLR.ACUAN.map(function (k) {
        var kunci = (k === 'wf' && A.wf) || (k === 'bm' && A.bm);
        var ket = k === 'wf' ? (A.wf ? ringWf(A) + ' di proyek' : 'belum ada wireframe') :
          k === 'bm' ? (A.bm ? A.bmL.map(function (v) { return E(v.name || (v.src && v.src.name)); }).join(', ') : 'belum ada block model acuan') :
          'parameter dari log Surpac / catatan pendahulu; diisi di Model Estimation';
        return '<label><input type=checkbox ' + (JLR.acuan[k] ? 'checked ' : '') + (kunci ? 'disabled ' : '') + 'onchange="JLR.setAcuan(\'' + k + '\',this.checked)"><span><b>' + E(JLR.NAMA[k]) + '</b><br><span class=hint>' + ket +
          (kunci ? ' &middot; tidak bisa dimatikan selama objeknya masih ada di proyek' : '') + '</span></span></label>';
      }).join('') + '</div>';
      var bisaNol = !A.wf && !A.bm;
      h += '<div class=cmh>Pindah jalur</div><button class=ib ' + (bisaNol ? '' : 'disabled ') + 'onclick="JLR.keNol()">Kembali ke Mulai dari nol</button>' +
        '<div class=hint>' + (bisaNol ? 'Tidak ada objek acuan di proyek: pindah ke jalur Mulai dari nol tidak mengubah data.' : 'Hanya bisa bila tidak ada wireframe / block model acuan di proyek (hapus atau lepaskan dulu).') + '</div>';
    } else {
      h += '<div class=cmh>Pindah jalur</div><button class=ib onclick="JLR.keLanjut()">Jadikan jalur Lanjutan&hellip;</button>' +
        '<div class=hint>Untuk proyek yang sekarang harus memakai wireframe / block model / parameter dari software lain (misalnya wireframe konsultan). ' +
        'Pindah jalur tidak mengubah data atau hasil apa pun; hanya membuka pintu acuan yang Anda centang, dan tercatat di jejak di bawah.</div>';
    }
    var L = (JLR.log || []).slice(-30).reverse();
    h += '<div class=cmh>Jejak jalur</div>' + (L.length ? '<table>' + L.map(function (r) {
      return '<tr><td style="white-space:nowrap">' + E(new Date(r.t).toLocaleString('id-ID')) + '</td><td>' + E(r.ket) + (r.user ? ' <span class=hint>(' + E(r.user) + ')</span>' : '') + '</td></tr>';
    }).join('') + '</table>' : '<div class=hint>Belum ada catatan.</div>');
    h += '</div></div>';
    d.innerHTML = h; d.style.display = 'flex';
  };
  JLR.dlgTutup = function () { var d = $('jlrDlg'); if (d) d.style.display = 'none'; };
  JLR.konfirmasi = function () { JLR.tebak = false; catat('Jalur dikonfirmasi pemakai: ' + JLR.label(JLR.mode) + ringkasAcuan()); JLR.terapkan(); JLR.dlg(); };
  JLR.setAcuan = function (k, v) {
    var A = JLR.ada();
    if (!v && ((k === 'wf' && A.wf) || (k === 'bm' && A.bm))) { JLR.dlg(); return; }
    JLR.acuan[k] = !!v; catat((v ? 'Acuan dinyalakan: ' : 'Acuan dimatikan: ') + JLR.NAMA[k]);
    if (!JLR.ACUAN.some(function (q) { return JLR.acuan[q]; })) catat('Jalur Lanjutan tanpa acuan: semua tahap dibuat baru di GC-Ex');
    JLR.terapkan(); JLR.dlg();
  };
  JLR.keLanjut = function () {
    var d = $('jlrDlg'); if (!d) return;
    var h = '<div class=impBox style=width:min(620px,100%)><div class=impHead><div class=impBrand><div><b>Jadikan jalur Lanjutan</b><small>Centang acuan dari software lain yang akan dipakai proyek ini.</small></div></div>' +
      '<button class="ib ghost" onclick="JLR.dlg()">Batal</button></div><div class=impBody><div class=jac>' +
      JLR.ACUAN.map(function (k) { return '<label><input type=checkbox id="jlrK_' + k + '"><b>' + E(JLR.NAMA[k]) + '</b></label>'; }).join('') +
      '</div><div class=hint>Data dan hasil yang sudah ada tidak diubah. Domain, solid dan block model buatan GC-Ex tetap milik GC-Ex; yang dibuka hanya pintu import acuan.</div>' +
      '<div class=impFoot style="padding:8px 0 0"><div></div><button class=ib onclick="JLR.keLanjutGo()">Pindah ke jalur Lanjutan &rarr;</button></div></div></div>';
    d.innerHTML = h; d.style.display = 'flex';
  };
  JLR.keLanjutGo = function () {
    var a = BASE(); JLR.ACUAN.forEach(function (k) { var c = $('jlrK_' + k); a[k] = !!(c && c.checked); });
    if (!JLR.ACUAN.some(function (k) { return a[k]; })) { alert('Centang minimal satu acuan.'); return; }
    var fp = window.FP && FP.dir && FP.flush ? FP.flush('sebelum pindah jalur') : null;
    Promise.resolve(fp).then(function () {
      JLR.mode = 'lanjut'; JLR.acuan = a; JLR.tebak = false;
      catat('Pindah jalur: Mulai dari nol → Lanjutan' + ringkasAcuan(a));
      JLR.terapkan(); JLR.dlg();
    });
  };
  JLR.keNol = function () {
    var A = JLR.ada(); if (A.wf || A.bm) { JLR.dlg(); return; }
    JLR.mode = 'nol'; JLR.acuan = BASE(); JLR.tebak = false; catat('Pindah jalur: Lanjutan → Mulai dari nol (tidak ada objek acuan)');
    JLR.terapkan(); JLR.dlg();
  };

  /* ---------- pengaman pintu yang tertutup ---------- */
  function tolak(apa, jalan) {
    var t = apa + ' hanya ada di jalur <b>Lanjutkan dari Surpac / Leapfrog</b> dengan acuan ' + jalan + ' dicentang. ' +
      (JLR.mode === 'nol' ? 'Proyek ini jalur <b>Mulai dari nol</b>.' : 'Acuan itu belum dicentang di proyek ini.') +
      ' Ubah lewat node Proyek &rsaquo; Jalur bila proyek memang harus memakai acuan.';
    try { if (window.FP && FP.toast) FP.toast(t, true, 9000); else alert(t.replace(/<[^>]+>/g, '')); } catch (e) { alert(t.replace(/<[^>]+>/g, '')); }
  }
  function bungkus(nama, syarat, apa, jalan, alt) {
    var f = window[nama]; if (typeof f !== 'function' || f._jlr) return;
    var g = function () { if (!syarat.apply(this, arguments)) { if (alt && alt()) return; tolak(apa, jalan); return; } return f.apply(this, arguments); };
    g._jlr = 1; window[nama] = g;
    try { if (nama === 'bxDlg') bxDlg = g; else if (nama === 'bmAdd') bmAdd = g; else if (nama === 'mdImport') mdImport = g; } catch (e) {}
  }
  /* jalan GC-Ex untuk block model = kerangka AOI: pintasan "Import BM…" (panduan pesan, skrip lama) dialihkan ke sana */
  var keAOI = function () {
    if (!(window.AOI && AOI.dlg)) return false;
    try { if (window.FP && FP.toast) FP.toast('Jalur ' + (JLR.mode === 'nol' ? 'Mulai dari nol' : 'Lanjutan tanpa acuan block model') + ': block model dibuat di GC-Ex sebagai <b>kerangka blok (AOI)</b>, bukan diimport.', false, 8000); } catch (e) {}
    AOI.dlg(); return true;
  };
  bungkus('bxDlg', function () { return JLR.boleh('bm') || !JLR.mode || JLR.tebak; }, 'Import block model dari file', 'block model', keAOI);
  bungkus('bmAdd', function () { return JLR.boleh('bm') || !JLR.mode || JLR.tebak; }, 'Tambah versi block model dari file', 'block model', keAOI);
  bungkus('mdImport', function (inp, jenis) { return jenis === 'surf' || JLR.boleh('wf') || !JLR.mode || JLR.tebak || !!(window.DLAT && DLAT.busy); }, 'Import wireframe geologi', 'wireframe');
  (function () {
    var u = window.uiTab; if (typeof u !== 'function' || u._jlr) return;
    var g = function (n) { if (n === 'Wf' && JLR.mode && !JLR.tebak && !JLR.boleh('wf')) { tolak('Panel Import Wireframe Geologi', 'wireframe'); return; } return u.apply(this, arguments); };
    Object.keys(u).forEach(function (k) { g[k] = u[k]; }); g._jlr = 1; window.uiTab = g; try { uiTab = g; } catch (e) {}
  })();

  /* ---------- parameter acuan: menyimpan hasil Geostatistik ke domain berparameter ---------- */
  (function () {
    var f = window.meFromGs; if (typeof f !== 'function' || f._jlr) return;
    var g = function (id) {
      var d = ok(function () { return gmDom(id); }, null), P = d && fn('meParOf') ? ok(function () { return meParOf(d); }, null) : null;
      if (d && P && JLR.boleh('par')) {
        if (!confirm('Domain "' + d.name + '" sudah memakai parameter (jalur Lanjutan, acuan parameter).\n\nGanti dengan parameter hasil Geostatistik GC-Ex?\nPerubahan dicatat di jejak jalur proyek, supaya selisih bulan ini vs bulan lalu bisa dijelaskan.')) return false;
        var r = f.apply(this, arguments); if (r !== false) catat('Parameter acuan domain ' + d.name + ' diganti dengan hasil Geostatistik GC-Ex');
        return r;
      }
      return f.apply(this, arguments);
    };
    g._jlr = 1; window.meFromGs = g; try { meFromGs = g; } catch (e) {}
  })();

  /* ---------- otomasi: Autorun Wireframe tidak menyentuh domain eksak (batasnya milik acuan) ---------- */
  (function () {
    var f = window.arWfDoms; if (typeof f !== 'function' || f._jlr) return;
    var g = function () { return (f.apply(this, arguments) || []).filter(function (d) { return !d.wfx; }); };
    g._jlr = 1; window.arWfDoms = g;
  })();

  /* ---------- Project Tree ---------- */
  function saringMenu(L, buang) { return (L || []).filter(function (it) { return !(it && it.t && buang.test(it.t)); }); }
  JLR.tree = function (L) {
    if (!JLR.mode) return L;
    var lj = JLR.mode === 'lanjut', out = [];
    L.forEach(function (n) {
      if (!n) return;
      if (n.id === 'wf' && !JLR.boleh('wf') && !(JLR.tebak && JLR.ada().wf)) return;
      if (n.id === 'bm' && !JLR.boleh('bm') && typeof n.menu === 'function') {
        var m0 = n.menu; n.menu = function () { return saringMenu(m0.apply(this, arguments), /^Import block model dari file/); };
      }
      if (n.id === 'bm' && lj && n.kids) n.kids.forEach(function (k) {
        if (!/^bm\.v\./.test(k.id)) return;
        var v = ok(function () { return BXV.filter(function (x) { return 'bm.v.' + x.id === k.id; })[0]; }, null);
        if (v && srcAcuan(v.src)) { k.b = (k.b ? k.b + ' · ' : '') + 'acuan'; k.hint = (k.hint ? k.hint + ' · ' : '') + 'Block model dari software lain (acuan)'; }
      });
      if (n.id === 'gm' && lj) {
        var tandai = function (k) {
          var d = ok(function () { return GM.doms.filter(function (x) { return 'gm.' + x.id === k.id; })[0]; }, null);
          if (d && d.wfx) { k.b = (k.b ? k.b + ' · ' : '') + 'acuan eksak'; k.hint = 'Batas domain = wireframe acuan "' + d.wfx + '" (terkunci, tidak diedit di GC-Ex)'; }
          else if (d && serap(d)) { k.b = (k.b ? k.b + ' · ' : '') + 'diserap'; k.hint = 'Diserap dari wireframe acuan: string bisa diedit, solid ikut bor baru'; }
          (k.kids || []).forEach(tandai);
        };
        (n.kids || []).forEach(tandai);
      }
      if (n.id === 'proj') {
        var A = JLR.ada();
        var info = function (id, t, b) { return { id: id, t: t, ic: 'ref', info: 1, b: b || '' }; };
        var kids = lj ? JLR.ACUAN.map(function (k) {
          var on = JLR.acuan[k];
          return info('proj.jalur.' + k, { wf: 'Acuan wireframe', bm: 'Acuan block model', par: 'Acuan parameter estimasi' }[k],
            !on ? 'dibuat baru di GC-Ex' : k === 'wf' ? (A.wf ? ringWf(A) : 'belum diimport') : k === 'bm' ? (A.bm ? A.bm + ' versi' : 'belum diimport') : 'dari log / catatan');
        }) : [];
        n.kids = [{
          id: 'proj.jalur', t: 'Jalur: ' + JLR.label(JLR.mode), ic: 'gear', fold: lj ? 1 : 0, kids: kids,
          b: JLR.tebak ? 'perlu konfirmasi' : '', mark: lj ? 'lanjutan' : 'nol',
          hint: lj ? 'Model dari software lain dipakai sebagai acuan. Detail, ubah acuan dan jejak di kartu / menu \u22ef.' : 'Semua model dibuat di GC-Ex. Detail, pindah jalur dan jejak di kartu / menu \u22ef.',
          /* tanpa go: memilih node menampilkan kartu aksi (dialog dibuka dari tombolnya, tidak meloncat sendiri) */
          card: { acts: [{ t: 'Buka detail jalur & jejak…', fn: function () { JLR.dlg(); }, pri: 1 }]
            .concat(JLR.tebak ? [{ t: 'Konfirmasi jalur ini', fn: function () { JLR.konfirmasi(); } }] : [])
            .concat(lj ? [] : [{ t: 'Jadikan jalur Lanjutan…', fn: function () { JLR.dlg(); JLR.keLanjut(); } }]) },
          menu: function () {
            return [{ t: 'Buka detail jalur & jejak…', fn: function () { JLR.dlg(); } },
              JLR.tebak ? { t: 'Konfirmasi jalur ini', fn: function () { JLR.konfirmasi(); } } : null,
              lj ? null : { t: 'Jadikan jalur Lanjutan…', fn: function () { JLR.dlg(); JLR.keLanjut(); } }].filter(Boolean);
          }
        }].concat(n.kids || []);
      }
      out.push(n);
    });
    return out;
  };
  (function pasang(n) {
    if (window.PT && PT.def && typeof PT.def.nodes === 'function') {
      if (PT.def.nodes._jlr) return;
      var f = PT.def.nodes; PT.def.nodes = function () { var L = f.apply(this, arguments); try { return JLR.tree(L); } catch (e) { console.warn('jalur tree', e); return L; } };
      PT.def.nodes._jlr = 1; try { PT.render(true); } catch (e) {}
      return;
    }
    if (n < 120) setTimeout(function () { pasang(n + 1); }, 250);
  })(0);

  setTimeout(function () { try { JLR.terapkan(); } catch (e) {} }, 300);

  /* ================= Demo: langkah "Jalur proyek" sesudah pembuka (hanya menampilkan, tidak mengubah jalur) ================= */
  if (typeof dmSteps === 'function' && !dmSteps._jlr) {
    var _dsJ = dmSteps;
    dmSteps = window.dmSteps = function () {
      var S = _dsJ.apply(this, arguments), k = -1;
      S.forEach(function (st, i) { if (st.s === 'Pembuka') k = i; });
      S.splice(k + 1, 0, { s: 'Pembuka', t: 'Jalur proyek: ' + JLR.label(JLR.mode), el: '#jlrPita', dur: 9,
        d: 'Setiap proyek berada di satu jalur, dipilih di halaman pembuka. Mulai dari nol: domain, solid, kerangka blok dan parameter dibuat di GC-Ex; fitur adaptasi (import wireframe / block model, Serap, Eksak) tidak tampil. Lanjutkan dari Surpac / Leapfrog: tiap tahap bisa memakai acuan yang dicentang atau dibuat baru. Detail dan jejaknya di Proyek \u203a Jalur.',
        run: function (A) {
          A(0, function () { try { PT.open['proj'] = 1; PT.render(true); } catch (e) {} });
          A(1, function () { dmPoint('.ptr[data-id="proj.jalur"]'); });
          A(5, function () { dmPoint('#jlrPita'); });
        } });
      return S;
    };
    dmSteps._jlr = 1;
  }
})();
