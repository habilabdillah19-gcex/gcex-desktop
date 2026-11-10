/* ================= GC-Ex Block Model 0.24.60: BAGIAN PANEL → JENDELA POP-UP =================
   Usulan pemilik (10 Nov 2026): panel di dalam panel yang harus di-scroll naik-turun diganti pop-up yang bisa
   disembunyikan bila tidak dipakai. Tahap pertama (pilihan pemilik): (1) daftar poligon per flitch As-Mined (Register
   poligon), (2) Layout & export As-Mined, (3) tabel titik atap Solid Vein.

   Cara kerja: tiap bagian punya tombol "⧉ Pop-up" di judulnya. Saat menyala, isi bagian itu DIPINDAH (bukan disalin)
   ke jendela mengambang setiap kali panel digambar ulang (MutationObserver), sehingga semua tombol / isian tetap
   bekerja seperti di panel. Di panel tersisa satu baris "ditampilkan di jendela pop-up · Kembalikan". Jendela bisa
   digeser, diperkecil (–) dan ditutup (×); menutup = kembali ke panel. Pilihan diingat per komputer (localStorage). */
(function () {
  var DEF = [
    { k: 'am.reg', host: 'amBody', t: 'Daftar poligon per flitch (Register poligon)', hd: /^Register poligon/ },
    { k: 'am.ly', host: 'amBody', t: 'Layout & export As-Mined', hd: /^Layout/ },
    { k: 'sv.pts', host: 'svBody', t: 'Solid Vein — titik atap (pick-up roof)', sv: 'pts' }
  ];
  var ON = {}; try { ON = JSON.parse(localStorage.getItem('gcex_popout') || '{}') || {}; } catch (e) { ON = {}; }
  var simpan = function () { try { localStorage.setItem('gcex_popout', JSON.stringify(ON)); } catch (e) {} };
  var sibuk = false;
  function hdOf(d, host) { if (d.sv) { var s = host.querySelector('.svsec[data-sec="' + d.sv + '"]'); return s ? s.querySelector('.svh') : null; }
    var H = host.querySelectorAll('.amh'); for (var i = 0; i < H.length; i++) if (d.hd.test(H[i].textContent.trim())) return H[i]; return null; }
  /* simpul yang dipindah: Solid Vein = isi .svsec selain judul; As-Mined = saudara sesudah judul sampai judul .amh berikutnya */
  function grab(d, hd) { var out = [], n; if (d.sv) { n = hd.nextSibling; while (n) { out.push(n); n = n.nextSibling; } return out; }
    n = hd.nextSibling; while (n && !(n.nodeType === 1 && n.classList && n.classList.contains('amh'))) { out.push(n); n = n.nextSibling; } return out; }
  function win(d) { var id = 'gxpo_' + d.k.replace(/\W/g, '_'), w = document.getElementById(id);
    if (!w) { var i = DEF.indexOf(d); w = window.AMK && AMK.pop ? AMK.pop(id, d.t, '') : null; if (!w) return null; w.style.left = (420 + 28 * i) + 'px'; w.style.top = (80 + 28 * i) + 'px'; w.style.width = 'min(620px,calc(100vw - 440px))';
      w.querySelector('[data-x]').onclick = function () { POP.set(d.k, false); }; }
    return w; }
  function render(host) { if (host === 'amBody') { try { amPanel(); } catch (e) {} } else { try { if (window.SV && SV.panel) SV.panel(); } catch (e) {} } }
  function apply() { if (sibuk) return; amati(); sibuk = true;
    try { DEF.forEach(function (d) { var host = document.getElementById(d.host); if (!host) return; var hd = hdOf(d, host); if (!hd) return;
        if (!hd.querySelector('.gxpob')) { var b = document.createElement('button'); b.type = 'button'; b.className = 'gxpob'; b.title = ON[d.k] ? 'Kembalikan ke panel' : 'Tampilkan bagian ini di jendela pop-up (bisa digeser, diperkecil, ditutup)'; b.innerHTML = ON[d.k] ? '&#8617; Panel' : '&#10697; Pop-up';
          b.onclick = function (e) { e.stopPropagation(); e.preventDefault(); POP.set(d.k, !ON[d.k]); }; hd.appendChild(b); }
        if (!ON[d.k]) return; var N = grab(d, hd); if (!N.length || N.some(function (n) { return n.nodeType === 1 && n.classList && n.classList.contains('gxpoph'); })) return; /* sudah dipindah, panel belum digambar ulang */ var w = win(d); if (!w) return; var body = w.querySelector('.gxpb'), st = body.scrollTop;
        var ph = document.createElement('div'); ph.className = 'gxpoph'; ph.innerHTML = '&#10697; Ditampilkan di jendela pop-up <b>' + d.t.replace(/</g, '&lt;') + '</b> &middot; <a href="#">tampilkan jendela</a> &middot; <a href="#" data-k>kembalikan ke panel</a>';
        ph.querySelector('a').onclick = function (e) { e.preventDefault(); w.style.display = 'flex'; w.classList.remove('min'); }; ph.querySelector('[data-k]').onclick = function (e) { e.preventDefault(); POP.set(d.k, false); };
        hd.parentNode.insertBefore(ph, N[0]); body.innerHTML = ''; N.forEach(function (n) { body.appendChild(n); }); body.scrollTop = st;
        if (!d._shown) { w.style.display = 'flex'; d._shown = 1; } }); } catch (e) { console.error('popout', e); }
    sibuk = false; }
  var POP = window.POP = { def: DEF, apply: apply,
    set: function (k, v) { ON[k] = !!v; simpan(); var d = DEF.filter(function (q) { return q.k === k; })[0]; if (!d) return; var w = document.getElementById('gxpo_' + k.replace(/\W/g, '_'));
      if (!v && w) { w.style.display = 'none'; w.querySelector('.gxpb').innerHTML = ''; } d._shown = 0; render(d.host); setTimeout(apply, 0); },
    on: function (k) { return !!ON[k]; } };
  var T = null, kick = function () { if (sibuk) return; clearTimeout(T); T = setTimeout(apply, 0); };
  function amati() { ['amBody', 'svBody'].forEach(function (id) { var e = document.getElementById(id); if (e && !e._gxpo) { e._gxpo = 1; new MutationObserver(kick).observe(e, { childList: true }); } }); }
  amati(); setTimeout(function () { amati(); apply(); }, 0); setInterval(amati, 3000);
  var st = document.createElement('style'); st.textContent = '.gxpob{float:right;height:20px;padding:0 7px;font-size:11px;font-weight:600;margin-left:6px;border-radius:10px}.gxpoph{font-size:11.5px;color:var(--mu);border:1px dashed var(--bd);border-radius:6px;padding:4px 8px;margin:4px 0}.gxpop .gxpb .amh{margin-top:6px}'; document.head.appendChild(st);
})();
