// halaman aktivasi lisensi GC-Ex (berjalan di jendela terisolasi, akses lewat window.gcexLic dari activate-preload.js)
(function () {
  'use strict';
  const $ = (i) => document.getElementById(i), L = window.gcexLic;
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const msg = (t, cls) => { const m = $('msg'); m.className = 'msg ' + (cls || ''); m.innerHTML = t || ''; };
  function show(st) {
    document.body.className = st.theme || '';
    $('ttl').textContent = (st.mode === 'info' ? 'Lisensi ' : 'Aktivasi ') + st.appName;
    $('mid').textContent = st.machineId;
    const r = st.check, box = $('stat');
    if (r && r.info && (r.ok || r.info.n)) {
      const I = r.info, apps = (I.a || []).map((a) => a === '*' ? 'Semua aplikasi GC-Ex' : (st.apps[a] || a)).join(', ');
      box.style.display = 'block';
      box.innerHTML = '<div class="lab">' + (r.ok ? 'Lisensi aktif' : 'Lisensi tersimpan (tidak berlaku)') + '</div><table>' +
        '<tr><td>Pemegang</td><td><b>' + esc(I.n) + '</b>' + (I.o ? '<br>' + esc(I.o) : '') + '</td></tr>' +
        '<tr><td>Aplikasi</td><td>' + esc(apps) + '</td></tr>' +
        '<tr><td>Berlaku sampai</td><td>' + (I.e ? esc(I.e) + (r.ok && r.daysLeft != null ? ' (' + r.daysLeft + ' hari lagi)' : '') : 'tanpa batas waktu') + '</td></tr>' +
        '<tr><td>No. lisensi</td><td>' + esc(I.id || '-') + '</td></tr></table>';
      $('rm').style.display = 'inline-block';
    } else box.style.display = 'none';
    $('sub').textContent = st.mode === 'info' ? 'Ganti kunci bila menerima lisensi baru (mis. perpanjangan).' : 'Aplikasi ini memerlukan kunci lisensi yang terikat ke komputer.';
    if (r && !r.ok && !r.none) msg('&#9888; ' + esc(r.reason), 'err');
    $('close').textContent = st.mode === 'info' ? 'Tutup' : 'Keluar';
  }
  $('cp').onclick = async () => { await L.copy($('mid').textContent); $('cp').textContent = 'Tersalin ✓'; setTimeout(() => { $('cp').textContent = 'Salin'; }, 1500); };
  $('go').onclick = async () => {
    const k = $('key').value.trim(); if (!k) { msg('Tempel kunci lisensi dulu.', 'err'); return; }
    $('go').disabled = true; msg('Memeriksa…');
    const r = await L.activate(k); $('go').disabled = false;
    if (r.ok) { msg('&#10003; Lisensi aktif untuk <b>' + esc(r.info.n) + '</b>' + (r.info.e ? ', berlaku sampai ' + esc(r.info.e) : '') + '. Membuka GC-Ex…', 'ok'); setTimeout(() => L.done(), 900); }
    else msg('&#10006; ' + esc(r.reason), 'err');
  };
  $('file').onclick = async () => { const t = await L.openFile(); if (t) { $('key').value = t.trim(); $('go').click(); } };
  $('rm').onclick = async () => { if (await L.remove()) { const st = await L.state(); show(st); msg('Lisensi dihapus dari komputer ini.', ''); } };
  $('close').onclick = () => L.close();
  document.addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) $('go').click(); });
  L.state().then(show);
})();
