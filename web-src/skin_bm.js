/* ================= GC-Ex Block Model 0.24.74 — TEMA "RASA SOFTWARE" TAHAP 1: PROJECT TREE & PANEL PROPERTI =================
   Keputusan pemilik 13 Nov 2026 (mengacu mockup DB-Ex): bar atas TETAP navy (identitas GC-Ex); mulai dari Project Tree dan
   panel Properti; langsung diterapkan. Warna, huruf, tata letak & alur kerja tetap — hanya lapisan CSS (tanpa ubah fungsi):
   - Project Tree: baris 28 px bersudut 7 px, sorotan biru muda + aksen kiri navy, lencana angka berbentuk pil, kepala putih.
   - Properti: setiap bagian (section) menjadi KARTU putih (sudut 10 px, garis halus, bayangan tipis) di atas latar abu-biru;
     judul kartu tebal huruf biasa; sub-judul kecil; tab bagian berupa segmented control (tab aktif = kartu putih timbul).
   - Kontrol: tombol 32 px sudut 8 px dengan bevel halus (gradasi tipis + garis terang di tepi atas), tombol utama navy
     bergradasi; isian & dropdown 32 px sudut 8 px dengan cincin fokus; sakelar & centang mengikuti warna navy.
   Khusus Block Model (Drillhole memakai ptree.js yang sama tetapi tidak memuat berkas ini). Mode gelap ikut (variabel). */
(function () {
  if (document.getElementById('skinBm')) return;
  document.body && document.body.classList.add('skin-bm');
  var C = [
    ':root{--sk-bg:#f1f4f9;--sk-card:#ffffff;--sk-ln:#e1e6ee;--sk-ln2:#cfd7e3;--sk-hv:#eef2f8;--sk-sel:#e6eefc;--sk-seltx:var(--pr,#1d4785);--sk-tx:#1c2733;--sk-mu:#64748b;--sk-acc:var(--pr,#1d4785);' +
      '--sk-sh:0 1px 2px rgba(16,24,40,.05),0 1px 3px rgba(16,24,40,.07);--sk-bev:linear-gradient(#ffffff,#f5f7fb);--sk-bevh:linear-gradient(#ffffff,#eef2f8);--sk-pri:linear-gradient(#2d5aa0,var(--pr,#1d4785));--sk-prih:linear-gradient(#3566b0,#22509a)}',
    'body.dark{--sk-bg:#111a24;--sk-card:#16202c;--sk-ln:#263446;--sk-ln2:#33445a;--sk-hv:#1c2836;--sk-sel:#203453;--sk-seltx:#cfe0ff;--sk-tx:#dbe3ec;--sk-mu:#93a3b6;--sk-acc:#7fa2e8;' +
      '--sk-sh:0 1px 2px rgba(0,0,0,.35);--sk-bev:linear-gradient(#1c2836,#18222f);--sk-bevh:linear-gradient(#223044,#1c2836)}',
    /* ---------- PROJECT TREE ---------- */
    'body.skin-bm #ptCol{background:var(--sk-bg);border-right:1px solid var(--sk-ln)}',
    'body.skin-bm #ptWrap .pth{height:34px;padding:0 8px 0 12px;background:var(--sk-card);border-bottom:1px solid var(--sk-ln);box-shadow:0 1px 0 rgba(16,24,40,.03)}',
    'body.skin-bm #ptWrap .ptt,body.skin-bm #ptPH .pp{font:700 10.5px/1 "Segoe UI",Roboto,Arial,sans-serif;letter-spacing:.09em;color:var(--sk-mu)}',
    'body.skin-bm #ptWrap .ptb button{width:24px;height:24px;line-height:24px;border-radius:6px}body.skin-bm #ptWrap .ptb button:hover{background:var(--sk-hv);color:var(--sk-acc)}',
    'body.skin-bm #ptree{padding:6px 0 10px;font:12.5px "Segoe UI",Roboto,Arial,sans-serif}',
    'body.skin-bm .ptr{height:28px;margin:1px 6px;padding:0 6px 0 calc(6px + var(--d)*14px);border:0;border-radius:7px;color:var(--sk-tx);gap:4px;transition:background .12s}',
    'body.skin-bm .ptr:hover{background:var(--sk-hv)}',
    'body.skin-bm .ptr.sel{background:var(--sk-sel);color:var(--sk-seltx);box-shadow:none}body.skin-bm .ptr.sel .ptl{font-weight:600}',
    'body.skin-bm #ptree:focus .ptr.sel{box-shadow:0 0 0 1px var(--sk-ln2)}',
    'body.skin-bm .ptr.fold>.ptl{font-weight:650}body.skin-bm .ptr.dim .ptl{color:var(--sk-mu)}',
    'body.skin-bm .pti{color:var(--sk-acc)}body.skin-bm .ptr.sel .pti{color:var(--sk-seltx)}',
    'body.skin-bm .ptc{flex:0 0 14px;font-size:9px;color:var(--sk-mu)}',
    'body.skin-bm .ptk{flex:0 0 15px;height:15px;border:1.5px solid #9aa8bb;border-radius:4px;background:var(--sk-card)}body.skin-bm .ptk.on{background:var(--sk-acc);border-color:var(--sk-acc)}',
    'body.skin-bm .ptk.on::after{left:4px;top:1px}body.skin-bm .ptk.no{border-color:transparent;background:none}',
    'body.skin-bm .ptn{padding:0 7px;margin-left:auto;border-radius:10px;background:var(--sk-hv);color:var(--sk-mu);font-size:10.5px;line-height:17px}',
    'body.skin-bm .ptr.sel .ptn{background:var(--sk-card);color:var(--sk-seltx)}',
    'body.skin-bm .ptm{border-radius:10px;line-height:16px;background:var(--sk-acc)}',
    'body.skin-bm .ptx{border-radius:6px}body.skin-bm .ptx:hover{background:var(--sk-card);color:var(--sk-acc)}',
    'body.skin-bm .ptr.ptadd .ptl{color:var(--sk-acc)}',
    'body.skin-bm #ptSplit{flex:0 0 6px;background:var(--sk-bg);border-top:1px solid var(--sk-ln);border-bottom:1px solid var(--sk-ln)}',
    'body.skin-bm #ptMenu{border-radius:10px;border-color:var(--sk-ln2);box-shadow:0 8px 24px rgba(16,24,40,.16);padding:6px}',
    'body.skin-bm #ptMenu button{border-radius:6px;padding:6px 12px}',
    /* ---------- PANEL PROPERTI ---------- */
    'body.skin-bm #side{background:var(--sk-bg);padding:0 10px 12px}',
    'body.skin-bm #ptPH{height:38px;margin:0 -10px 10px;padding:0 10px 0 12px;background:var(--sk-card);border-bottom:1px solid var(--sk-ln);box-shadow:0 1px 0 rgba(16,24,40,.03)}',
    'body.skin-bm #ptPH b{font-size:13px;color:var(--sk-tx)}body.skin-bm #ptPH .pi2{color:var(--sk-acc)}',
    'body.skin-bm #side>section:not([hidden]),body.skin-bm #ptCard{background:var(--sk-card);border:1px solid var(--sk-ln);border-radius:10px;box-shadow:var(--sk-sh);padding:12px 12px 12px;margin:0 0 10px}',
    'body.skin-bm #side h3{margin:0 0 10px;font:700 13.5px/1.25 "Segoe UI",Roboto,Arial,sans-serif;letter-spacing:0;text-transform:none;color:var(--sk-tx)}body.skin-bm #side h3:after{display:none}',
    'body.skin-bm #side h4{margin:14px 0 6px;font:700 10.5px/1.2 "Segoe UI",Roboto,Arial,sans-serif;letter-spacing:.08em;color:var(--sk-mu)}',
    'body.skin-bm .uisec.dock{border-left:0;padding-left:0;margin-left:0}body.skin-bm .uisec .uisec.dock{border-left:0;padding-left:0}',
    'body.skin-bm .lab{font-size:11.5px;color:var(--sk-mu)}body.skin-bm .hint{color:var(--sk-mu)}',
    /* tab bagian = segmented control */
    'body.skin-bm #side .uitabs{gap:2px;margin:6px 0 10px;padding:3px;background:var(--sk-hv);border:1px solid var(--sk-ln);border-radius:9px;position:sticky;top:38px}',
    'body.skin-bm #side .uisec .uitabs{position:static;border-style:solid}',
    'body.skin-bm #side .uitabs button,body.skin-bm #side .uitabs button:not(.x):not(.ptx){min-height:28px!important;height:auto;padding:4px 8px!important;border:0!important;border-radius:7px!important;margin:0!important;background:transparent!important;box-shadow:none!important;color:var(--sk-mu)!important;font-weight:600;font-size:12px}',
    'body.skin-bm #side .uitabs button:not(.on):hover{background:rgba(255,255,255,.6)!important;color:var(--sk-tx)!important}',
    'body.skin-bm #side .uitabs button.on,body.skin-bm #side .uitabs button.on:not(.x):not(.ptx){background:var(--sk-card)!important;background-image:none!important;color:var(--sk-seltx)!important;box-shadow:0 1px 2px rgba(16,24,40,.14),0 0 0 1px var(--sk-ln)!important}',
    /* kontrol */
    'body.skin-bm #side button:not(.x):not(.ptx){min-height:32px;padding:5px 12px;border:1px solid var(--sk-ln2);border-radius:8px;background:var(--sk-bev);color:var(--sk-tx);font-weight:600;box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 1px 1px rgba(16,24,40,.05);transition:background .12s,border-color .12s}',
    'body.skin-bm #side button:not(.x):not(.ptx):hover{background:var(--sk-bevh);border-color:#9fb3d9}',
    'body.skin-bm #side button:not(.x):not(.ptx):active{box-shadow:inset 0 1px 2px rgba(16,24,40,.12)}',
    'body.skin-bm #side button:disabled{opacity:.5;cursor:not-allowed}',
    'body.skin-bm #side .btn-pri:not(:disabled),body.skin-bm #side button.btn-pri:not(.x):not(:disabled),body.skin-bm #side .mdbtn{background:var(--sk-pri)!important;background-image:var(--sk-pri)!important;border:1px solid #163a72!important;color:#fff!important;border-radius:8px!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.2),0 1px 2px rgba(22,58,114,.35)!important}',
    'body.skin-bm #side .btn-pri:not(:disabled):hover,body.skin-bm #side .mdbtn:hover{background-image:var(--sk-prih)!important}',
    'body.skin-bm #side .sg button{border-radius:0;margin-left:-1px}body.skin-bm #side .sg button:first-child{border-radius:8px 0 0 8px;margin-left:0}body.skin-bm #side .sg button:last-child{border-radius:0 8px 8px 0}',
    'body.skin-bm #side select,body.skin-bm #side input[type=number],body.skin-bm #side input[type=text]{height:32px;border:1px solid var(--sk-ln2);border-radius:8px;background-color:var(--sk-card);box-shadow:inset 0 1px 1px rgba(16,24,40,.04)}',
    'body.skin-bm #side select:focus,body.skin-bm #side input[type=number]:focus,body.skin-bm #side input[type=text]:focus{border-color:var(--sk-acc);box-shadow:0 0 0 3px rgba(46,76,158,.15)}',
    'body.skin-bm #side .sw input:checked{background:var(--sk-acc)}',
    'body.skin-bm #side input[type=range]{accent-color:var(--sk-acc)}',
    'body.skin-bm #side .mdrow{border-color:var(--sk-ln);border-radius:8px;background:var(--sk-bg)}',
    'body.skin-bm #side table.pltb{border-radius:8px;overflow:hidden}',
    'body.skin-bm #ptNav{background:var(--sk-card);border-top:1px solid var(--sk-ln);margin:14px -10px -12px;padding:8px 10px 10px}'
  ];
  var s = document.createElement('style'); s.id = 'skinBm'; s.textContent = C.join('\n');
  (document.head || document.documentElement).appendChild(s);
  if (!document.body) document.addEventListener('DOMContentLoaded', function () { document.body.classList.add('skin-bm'); });
})();
