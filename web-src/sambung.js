/* sambung.js — "Sambungkan file": file sumber proyek yang pindah / hilang (BM 0.24.114, DH 0.24.116).
   Pemilik 26 Nov 2026: "jika ada file direktori hilang karena posisi file sudah berpindah folder, apakah akan ada popup
   agar user dapat menyambungkan file tersebut?" -> "lakukan".

   Sebelumnya FP.findFile hanya mencari di folder proyek + satu tingkat subfolder; bila tidak ketemu proyek dibuka tanpa
   file itu dengan peringatan saja. Sekarang, KHUSUS saat proyek membaca file sumber (FP.loadSrc: block model .mdl / .csv,
   versi block model, AOI / sub-blok Drillhole):
     1. cari lebih dalam di folder proyek (sampai 5 tingkat, tanpa backup / export), cocokkan nama + ukuran;
     2. bila tetap tidak ada -> jendela "Sambungkan file": pengguna memilih file di lokasi barunya; nama / ukuran dicek
        (beda -> peringatan, pengguna yang memutuskan); opsi salin ke folder proyek\sumber\ dengan nama yang tercatat
        di proyek supaya proyek tidak putus lagi;
     3. "Lewati" = perilaku lama (proyek dibuka tanpa file itu + peringatan).
   Pemeriksaan latar (FP.srcState, ekspor proyek) TIDAK memunculkan jendela. Berlaku di aplikasi terpasang dan .html. */
(function pasang(coba) {
  'use strict';
  /* FP didefinisikan di skrip yang berjalan sesudah modul ini: tunggu sampai ada (maks. ~60 s) */
  if (!window.FP || typeof FP.findFile !== 'function' || typeof FP.loadSrc !== 'function') { if ((coba || 0) < 600) setTimeout(function () { pasang((coba || 0) + 1); }, 100); return; }
  if (FP.sambungDialog) return;
  var _find = FP.findFile, _load = FP.loadSrc;
  var LEWAT = /^(backup|export)$/i, MAXD = 5, MAXDIR = 600;
  var e = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var uk = function (b) { b = +b || 0; return b >= 1073741824 ? (b / 1073741824).toFixed(2) + ' GB' : b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : (b / 1024).toFixed(0) + ' KB'; };

  /* pencarian dalam (BFS) di folder proyek */
  FP.findDeep = async function (name, size) {
    if (!FP.dir || !name) return null;
    var antri = [[FP.dir, '', 0]], n = 0, cadangan = null;
    while (antri.length && n < MAXDIR) {
      var a = antri.shift(), d = a[0], pre = a[1], lv = a[2]; n++;
      try { var fh = await d.getFileHandle(name); var f = await fh.getFile(); if (!size || f.size === size) return { f: f, path: pre + name }; if (!cadangan) cadangan = { f: f, path: pre + name, beda: true }; } catch (x) { }
      if (lv >= MAXD) continue;
      var L = []; try { L = await FP.list(d); } catch (x) { }
      L.forEach(function (c) { if (c.kind === 'directory' && !(lv === 0 && LEWAT.test(c.name)) && !/^\./.test(c.name)) antri.push([c, pre + c.name + '/', lv + 1]); });
    }
    return cadangan;
  };

  /* salin file pilihan ke folder proyek\sumber\<nama tercatat> */
  FP.salinSumber = async function (f, nama, say) {
    var D = await FP.sub(['sumber']), fh = await D.getFileHandle(nama, { create: true }), w = await fh.createWritable();
    if (say) say('Menyalin <b>' + e(f.name) + '</b> (' + uk(f.size) + ') ke folder proyek\\sumber\\&hellip;');
    await w.write(f); await w.close();
    return 'sumber/' + nama;
  };

  var pilihFile = function () {
    if (window.showOpenFilePicker) return window.showOpenFilePicker({ multiple: false }).then(function (h) { return h[0].getFile(); }).catch(function () { return null; });
    return new Promise(function (res) {
      var i = document.createElement('input'); i.type = 'file'; i.style.display = 'none'; document.body.appendChild(i);
      i.onchange = function () { var f = i.files && i.files[0]; i.remove(); res(f || null); };
      window.addEventListener('focus', function fk() { window.removeEventListener('focus', fk); setTimeout(function () { if (i.isConnected && !(i.files && i.files.length)) { i.remove(); res(null); } }, 800); });
      i.click();
    });
  };

  /* jendela "Sambungkan file" -> {f, path} | null */
  FP.sambungDialog = function (src, jenis) {
    return new Promise(function (res) {
      var lama = document.getElementById('gxSambung'); if (lama) lama.remove();
      var bg = document.createElement('div'); bg.id = 'gxSambung';
      bg.style.cssText = 'position:fixed;inset:0;z-index:100000;background:rgba(20,26,36,.45);display:flex;align-items:center;justify-content:center;font:13px Inter,Segoe UI,sans-serif';
      var asal = src.path || src.full || src.lokasi || '';
      bg.innerHTML = '<div role=dialog aria-modal=true style="background:#fff;color:#1F2430;border-radius:10px;max-width:520px;width:92%;box-shadow:0 12px 40px rgba(0,0,0,.3);overflow:hidden">' +
        '<div style="background:#1C2733;color:#fff;padding:11px 16px;font-weight:600">&#128279; Sambungkan file</div>' +
        '<div style="padding:14px 16px;line-height:1.5">' +
        '<div>' + e(jenis || 'File sumber') + ' <b>' + e(src.name) + '</b>' + (src.size ? ' (' + uk(src.size) + ')' : '') + ' tidak ditemukan di folder proyek' + (FP.dir && FP.dir.name ? ' <b>' + e(FP.dir.name) + '</b>' : '') + ', juga di subfoldernya.</div>' +
        (asal ? '<div style="color:#5C6672;margin-top:4px">Lokasi terakhir yang tercatat: <code>' + e(asal) + '</code></div>' : '') +
        '<div style="color:#5C6672;margin-top:6px">Mungkin file sudah dipindah. Tunjukkan lokasi barunya supaya proyek dibuka lengkap.</div>' +
        '<label style="display:flex;gap:7px;align-items:flex-start;margin-top:10px"><input type=checkbox id=gxSbSalin checked style="margin-top:3px">' +
        '<span>Salin ke folder proyek\\sumber\\ setelah tersambung <span style="color:#5C6672">(disarankan: proyek tidak putus lagi bila file asli dipindah)</span></span></label>' +
        '<div id=gxSbMsg style="color:#A1441C;margin-top:8px;min-height:1em"></div></div>' +
        '<div style="display:flex;gap:8px;justify-content:flex-end;padding:0 16px 14px">' +
        '<button id=gxSbLewat style="padding:7px 12px;border:1px solid #D3CDC1;background:#fff;border-radius:6px;cursor:pointer">Lewati (buka tanpa file ini)</button>' +
        '<button id=gxSbCari style="padding:7px 14px;border:0;background:#9C5522;color:#fff;border-radius:6px;cursor:pointer;font-weight:600">Cari file&hellip;</button></div></div>';
      document.body.appendChild(bg);
      var tutup = function (v) { bg.remove(); res(v); };
      var M = bg.querySelector('#gxSbMsg');
      bg.querySelector('#gxSbLewat').onclick = function () { tutup(null); };
      bg.querySelector('#gxSbCari').onclick = async function () {
        var f = await pilihFile(); if (!f) return;
        var beda = [];
        if (f.name !== src.name) beda.push('nama "' + f.name + '" (tercatat "' + src.name + '")');
        if (src.size && f.size !== src.size) beda.push('ukuran ' + uk(f.size) + ' (tercatat ' + uk(src.size) + ')');
        if (beda.length && !confirm('File yang dipilih berbeda dari yang tercatat di proyek:\n- ' + beda.join('\n- ') +
          '\n\nBisa jadi ini file lain atau versi yang sudah diubah, sehingga isi model / laporan berbeda.\nTetap pakai file ini?')) return;
        var path = null;
        if (FP.dir && bg.querySelector('#gxSbSalin').checked) {
          try { M.style.color = '#5C6672'; M.innerHTML = 'Menyalin ' + e(f.name) + ' (' + uk(f.size) + ')&hellip;'; path = await FP.salinSumber(f, src.name); }
          catch (x) { M.style.color = '#A1441C'; M.textContent = 'Gagal menyalin ke folder proyek (' + (x && x.message || x) + '); file tetap dipakai dari lokasinya.'; await new Promise(function (r) { setTimeout(r, 1500); }); }
        }
        try { if (window.SA && SA.srcFiles) SA.srcFiles[src.name] = f; } catch (x) { }
        tutup({ f: f, path: path, sambung: true });
      };
      setTimeout(function () { var b = bg.querySelector('#gxSbCari'); if (b) b.focus(); }, 30);
    });
  };

  var aktif = null;
  FP.findFile = async function (name, size) {
    var r = await _find.apply(this, arguments); if (r) return r;
    if (!aktif || aktif.src.name !== name) return null;
    if (aktif.done) return aktif.hasil;
    aktif.done = true;
    var d = await FP.findDeep(name, aktif.src.size);
    if (d && !d.beda) { aktif.hasil = d; try { FP.toast('&#128279; File <b>' + e(name) + '</b> ditemukan di <code>' + e(d.path) + '</code>.', false, 6000); } catch (x) { } return d; }
    aktif.hasil = await FP.sambungDialog(aktif.src, aktif.src.kind === 'mdl' || aktif.src.kind === 'csv' ? 'File block model' : 'File sumber');
    if (!aktif.hasil) {
      /* dilewati: pesan peringatan dasar bisa tertimpa pesan "Terhubung ke folder" -> ulangi sesudahnya */
      setTimeout(function () { try { FP.toast('&#9888; File <b>' + e(name) + '</b> tidak ditemukan dan tidak disambungkan. Proyek dibuka tanpa file itu; sambungkan lewat Import, lalu Proyek &rarr; Salin file ke folder.', true, 0); } catch (x) { } }, 3500);
    }
    if (aktif.hasil) { try { FP.toast('&#128279; <b>' + e(name) + '</b> tersambung' + (aktif.hasil.path ? ' dan disalin ke <code>' + e(aktif.hasil.path) + '</code>.' : ' (dibaca dari lokasinya; Proyek &rarr; Salin file block model ke folder bila perlu).'), false, 7000); } catch (x) { } }
    return aktif.hasil;
  };
  FP.loadSrc = async function (src) {
    var simpan = aktif; aktif = { src: src || {}, done: false, hasil: null };
    try { return await _load.apply(this, arguments); } finally { aktif = simpan; }
  };
})(0);
