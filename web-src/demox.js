/* ================= TOMBOL DEMO: URUTAN TUTORIAL, TEKS PENDEK, TEMPO LEBIH CEPAT =================
   Modul bersama GC-Ex Drill Hole dan GC-Ex Block Model, dipasang paling akhir.

   Tiga hal yang diperbaiki, sesuai permintaan pemilik:
   1. URUTAN. Demo lama menyusuri menu dari atas ke bawah (Data, Warna, Tampilan, Sayatan, ...).
      Sekarang langkahnya diurutkan mengikuti BUKU TUTORIAL: alur kerja nyata pemodelan-estimasi
      (Drill Hole) dan grade control harian (Block Model), sehingga penonton demo dan pembaca
      tutorial melihat urutan yang sama.
   2. TEKS. Keterangan tiap langkah dipendekkan menjadi satu kalimat (sebagian tadinya 300 huruf
      dan tidak terbaca selesai sebelum langkahnya berganti).
   3. TEMPO. Kecepatan bawaan dipercepat (0,55x durasi lama) dan pembaruan kursor / highlight
      dinaikkan ke 20 fps supaya gerakannya halus, bukan tersendat.

   Ditambah: langkah untuk menu yang selama ini belum pernah masuk demo (serap wireframe Leapfrog,
   kerangka AOI, estimasi waste, autorun, pemeriksaan dig block, preset, ringkasan harian, laporan
   periode, dan laporan per desain pit / progres topo-ke-topo), serta satu langkah pembuka yang
   menyebutkan DATA yang sedang dipakai -- demo dimaksudkan dijalankan di atas data latihan
   simulasi (SIM_* dari folder Data-Latihan), dan bila yang terbuka bukan data itu, langkah pembuka
   menyebutkannya dengan jelas daripada berpura-pura.                                            */
(function () {
  if (window.DMX || typeof dmSteps !== 'function' || typeof DM === 'undefined') return;
  var DH = typeof window.meAN === 'function';                     /* Drill Hole vs Block Model */
  var DMX = window.DMX = { dh: DH, spd: 0.55 };
  var $ = function (i) { return document.getElementById(i); };

  DM.fps = 20;

  /* ---------- urutan bagian = urutan bab tutorial ---------- */
  var ORD = DH
    ? ['Pembuka', 'Data & filter', 'Warna', 'Tampilan', 'Geologi', 'Sayatan', 'Geomodeller Vein',
       'Geostatistik', 'Model Estimation', 'Block Model', 'Autorun', 'Laporan', 'Overlay', 'Plan Bor', 'Penutup']
    : ['Pembuka', 'Block model', 'Tampilan', 'Sayatan', 'Dig block', 'Pemeriksaan', 'Laporan',
       'Layout PDF', 'As-mined', 'Periode', 'Proyek', 'Penutup'];

  /* ---------- langkah yang dibuang: tidak ada di tutorial / tidak menambah pemahaman ---------- */
  var DROP = DH ? ['Tema gelap', 'Tampak atas', 'Sayatan 2D (section)', 'Bandingkan', 'Kembali ke warna kadar']
                : ['Tema gelap'];

  /* ---------- keterangan pendek per judul langkah (satu kalimat) ---------- */
  var TXT = {
    /* Drill Hole */
    'Model 3D lubang bor': 'Tiap lubang digambar mengikuti dip & azimuth survey; warna = kadar per interval sampel.',
    'Ganti unsur': 'Kolom unsur dibaca otomatis dari header assay, jadi bisa berganti unsur kapan saja.',
    'Cutoff tampilan': 'Sembunyikan interval di bawah ambang agar zona kadar tinggi terlihat; statistik tidak terpengaruh.',
    'Kelas kadar': 'Warna per kelas kadar; tombol Kuartil mengisi batas kelas dari data.',
    'Sudut pandang cepat': 'Top, Front, Side dan Iso memindahkan kamera dalam satu klik.',
    'Log geologi di trajectory': 'Kolom sheet Geologi digambar sebagai pita di sepanjang lubang.',
    'Ganti atribut geologi': 'Setiap kolom geologi menjadi atribut dengan legenda dan hatch sendiri.',
    'Sayatan horizontal': 'Potong model pada satu elevasi dengan tebal slab; hanya data di dalam slab yang tampil.',
    'Geser slab': 'Tombol Maju / Mundur memindahkan slab satu tebal, seperti membuka bench satu per satu.',
    'Sayatan 2D (plan)': 'Mode 2D menampilkan slab berskala dengan label assay — siap dicetak.',
    'Garis sayatan manual': 'Sayatan vertikal digambar langsung di peta: arah dan panjang bebas.',
    'Sayatan searah pengeboran': 'Garis sayatan tegak lurus strike vein, kamera otomatis menghadap bidangnya.',
    'Sayatan miring (dip)': 'Bidang sayatan bisa dimiringkan mengikuti kemiringan vein.',
    'Digitasi string pada penampang': 'String digambar di Penampang 2D, terkunci pada bidang slab, lalu diexport ke DXF / STR.',
    'Domain vein, flag interval & string kontrol': 'Domain vein, flag interval dari kadar, lalu string kontrol HW / FW per section.',
    'Model vein HW / FW → solid (RBF)': 'Permukaan HW dan FW di-RBF, lalu solid vein di antaranya; dibangun ulang tiap flag berubah.',
    'Layer & export ke software resmi': 'Panel Layer mengatur apa yang tampil; solid diexport ke OBJ, DXF atau STR+DTM.',
    'Analisis geostatistik slab': 'Statistik komposit domain aktif: CV, histogram, top-cut, declustering.',
    'Variogram': 'Variogram eksperimental downhole dan arah utama beserta modelnya.',
    'Anisotropi (fan)': 'Variogram 36 arah memperlihatkan arah kemenerusan terpanjang.',
    'Model variogram': 'Model sferis di-fit otomatis: nugget, sill, range dan orientasi elipsoid.',
    'Kriging Neighbourhood Analysis': 'KNA menguji jumlah sampel × radius, dipilih yang SoR dan KE-nya terbaik.',
    'Estimasi Ordinary Kriging': 'Uji estimasi 3 pass untuk menilai parameter sebelum disimpan ke domain.',
    'Block model 3D': 'Hasil estimasi tampil sebagai blok berwarna kadar bersama lubang bor.',
    'Estimasi block model GC per domain': 'Model Estimation mengestimasi blok di dalam solid tiap domain dan menambah blok yang belum ada.',
    'Plan bor: rencana pengeboran': 'Titik bor rencana dibuat per titik, sepanjang garis, atau grid di dalam area.',
    'Preview 3D & export CSV': 'Rencana tampil bersama lubang lama, lengkap dengan jarak dan kadar perkiraan; export CSV.',
    'Block model grade control': 'Block model GC (.mdl / CSV) diimport, diwarnai per kelas, dan difilter cut-off.',
    'Data referensi': 'Solid, DTM dan titik survey dari software lain tampil sebagai acuan.',
    'Topografi & orthofoto': 'Topografi dan orthofoto resolusi tinggi memberi konteks lapangan.',
    /* Block Model */
    'Import block model': 'Block model Surpac .mdl dibaca langsung (octree, sub-blok, atribut kalkulasi) atau dari CSV.',
    'Warna per material': 'Warnai dengan atribut apa pun; kode kategori bisa ditampilkan satu-satu.',
    'Cut-off tampilan': 'Tampilkan hanya blok di atas cut-off agar tubuh ore jelas; ringkasan ikut menyesuaikan.',
    'Penampang vertikal melintang ore': 'Garis sayatan melintang ore; profil topografi dan desain pit ikut tampil.',
    'Sayatan BM: komposit seluruh tebal flitch': 'Kadar flitch = Σ(kadar × tebal × SG) / Σ(tebal × SG), jadi ore pada sub-blok tipis tidak hilang.',
    'Kelas kadar dig block': 'Tabel kelas menentukan string number, warna dan material dari kadar tiap poligon.',
    'Tujuan (DEST) per material': 'Aturan material & sulfida memberi tujuan tiap dig block, mis. LG→S340, HG→R418.',
    'Digit manual + running grade': 'Digit manual menempel ke sudut blok; kotak running grade menghitung ton @ kadar seketika.',
    'Dig block otomatis': 'Satu klik: blok lolos kelas disatukan, lubang diisi, lebar minimum alat dijaga, tanpa overlap.',
    'Running grade & tonnage': 'Tabel dig block: luas, ton @ kadar, subtotal per material dan per tujuan.',
    'Edit string satu per satu': 'Klik string di Penampang 2D untuk mengubah nomor, warna, material dan tujuannya.',
    'Hapus banyak dig block sekaligus': 'Pilih dengan centang, Ctrl+klik atau kotak Shift+tarik, lalu hapus — bisa diurungkan.',
    'Edit bentuk dengan kursor': 'Tarik titik (menempel ke sudut blok); tonase diperbarui tiap titik dilepas.',
    'Waste default & string ganda sulfida': 'Area tanpa blok dihitung waste; dig block sulfida mendapat string kedua putus-putus.',
    'Export string Surpac': 'STR binary, STR teks dan DXF, dengan nama berkas DigPlan_<zona>_<TOP>-<BOT>.',
    'Layout & Plot PDF': 'Dig plan siap cetak: kop gambar, A4–A2, skala otomatis, dig block berdempet jadi satu halaman.',
    'Pratinjau PDF': 'Pratinjau tiap halaman sebelum diunduh; PDF vektor dibuat di browser.',
    'Model as-mined (rekonsiliasi bulanan)': 'Boundary aktual galian + sampel as-mined dihitung, lalu dibandingkan dengan model resmi.',
    'Proyek & penyimpanan': 'Semua pekerjaan tersimpan ke folder proyek dengan backup berversi.',
    'Selesai': 'Tekan Esc atau Stop untuk mengembalikan tampilan semula.'
  };

  /* ---------- data yang dipakai demo ---------- */
  function namaData() {
    try {
      if (DH) return (window.SA && SA.D && SA.D.name) || '(tanpa nama)';
      return (window.BX && BX.m && BX.m.name) || '(tanpa nama)';
    } catch (e) { return '(tanpa nama)'; }
  }
  function dataLatihan() { return /sim|latihan|simulasi|veina|lensa/i.test(namaData()); }
  function ringkasData() {
    try {
      if (DH) return collars.length.toLocaleString('id-ID') + ' lubang bor, ' + assays.length.toLocaleString('id-ID') + ' sampel assay' +
        (window.BX && BX.m ? ', block model ' + BX.m.n.toLocaleString('id-ID') + ' blok' : '');
      return BX.m.n.toLocaleString('id-ID') + ' blok ' + (BX.m.sizes || '');
    } catch (e) { return ''; }
  }

  /* ---------- langkah tambahan (menu yang belum pernah masuk demo) ---------- */
  function tab(n) { try { uiTab(n); } catch (e) {} }
  /* langkah paling awal: menyebutkan data yang sedang terbuka (demo dirancang untuk data latihan) */
  function stepData() {
    return { s: 'Pembuka', t: 'Data yang dipakai demo ini', dur: 5,
      d: 'Dataset ' + namaData() + ' — ' + ringkasData() + '. ' +
         (dataLatihan() ? 'Ini data latihan simulasi, urutan demo mengikuti buku tutorial.'
                        : 'Demo dirancang untuk data latihan SIM_* (folder Data-Latihan); dengan data lain langkahnya tetap sama.'),
      run: function (A) { A(0, function () { tab(DH ? 'Data' : 'BM'); }); } };
  }
  function extraSteps() {
    var S = [];
    if (DH) {
      S.push({ s: 'Geomodeller Vein', t: 'Wireframe Leapfrog menjadi domain', dur: 6, el: 'rbGM',
        d: 'Wireframe implicit dari Leapfrog diserap menjadi string HW / FW: jadi domain GC-Ex yang bisa diedit.',
        run: function (A) { A(0, function () { tab('GM'); }); } });
      S.push({ s: 'Block Model', t: 'Kerangka blok AOI & sub-blocking', dur: 6, el: 'rbBM',
        d: 'Block model bisa dibuat dari nol (kerangka AOI) dan dipecah di batas solid; sb_frac menimbang blok perbatasan.',
        run: function (A) { A(0, function () { tab('BM'); }); } });
      S.push({ s: 'Block Model', t: 'Estimasi waste di luar solid', dur: 6, el: 'rbME',
        d: 'Blok di luar semua solid diestimasi sebagai domain WASTE, sehingga dilusi dan ore loss ikut terhitung.',
        run: function (A) { A(0, function () { tab('ME'); }); } });
      S.push({ s: 'Autorun', t: 'Autorun wireframe & estimasi', dur: 6, el: 'rbGM',
        d: 'Sesudah bor baru masuk: satu perintah menarik string tiap section, bangun solid, lalu estimasi ulang per domain.',
        run: function (A) { A(0, function () { tab('GM'); }); } });
      S.push({ s: 'Laporan', t: 'Reporting BM: grade × tonase', dur: 6,
        d: 'Tonase × kadar dengan batasan topografi, desain pit, domain, poligon dan RL, plus klasifikasi keyakinan.',
        run: function (A) { A(0, function () { tab('Rep'); }); } });
    } else {
      S.push({ s: 'Pemeriksaan', t: 'Pemeriksaan dig block sebelum terbit', dur: 7,
        d: 'Lebar di bawah lebar alat, poligon menyilang diri, tanpa tujuan material dan nama ganda diperiksa lebih dulu.',
        run: function (A) {
          A(0, function () { tab('BM'); });
          A(1.2, function () { try { GCO.qcRun(false); GCO.qcDlg(); } catch (e) {} });
          A(6.2, function () { try { GCO.qcClose(); } catch (e) {} });
        } });
      S.push({ s: 'Pemeriksaan', t: 'Preset kelas kadar & tujuan', dur: 5,
        d: 'Kelas kadar dan aturan tujuan disimpan sebagai preset per pit, lalu dipakai ulang tiap flitch.',
        run: function (A) { A(0, function () { tab('BM'); }); } });
      S.push({ s: 'Laporan', t: 'Ringkasan harian flitch aktif', dur: 6,
        d: 'Satu kotak: ton dan kadar per material dan per tujuan untuk flitch yang sedang dikerjakan.',
        run: function (A) { A(0.8, function () { try { GCO.dayDlg(); } catch (e) {} }); A(5.2, function () { try { GCO.dayClose(); } catch (e) {} }); } });
      S.push({ s: 'Laporan', t: 'Reporting block model', dur: 6,
        d: 'Tonase × kadar seluruh model dengan batasan topografi, pit, RL dan poligon; hasilnya bisa diexport CSV.',
        run: function (A) { A(0, function () { tab('Rep'); }); } });
      S.push({ s: 'Periode', t: 'Laporan mingguan & bulanan', dur: 6,
        d: 'Register as-mined dijumlahkan per minggu atau bulan, per shift / tujuan / flitch, dibanding periode sebelumnya.',
        run: function (A) { A(0.8, function () { try { PRD.dlg(); } catch (e) {} }); A(5.2, function () { try { PRD.close(); } catch (e) {} }); } });
    }
    /* fitur baru: beberapa desain pit sekaligus & progres topo-ke-topo */
    S.push({ s: 'Laporan', t: 'Beberapa pit & progres topo-ke-topo', dur: 8,
      d: 'Beberapa desain pit dilaporkan sekaligus dengan topografi sama, dan material tergali antara dua survei topografi.',
      run: function (A) {
        A(0, function () { tab('Rep'); });
        A(1.2, function () { try { if (window.RP && window.RPX) { RP.sec = 'x'; RPX.panel(); } } catch (e) {} });
      } });
    return S;
  }

  /* ---------- susun ulang: buang, pendekkan, tambah, urutkan per bagian ---------- */
  var _ds = dmSteps;
  window.dmSteps = dmSteps = function () {
    var S;
    try { S = _ds.apply(this, arguments) || []; } catch (e) { console.error(e); return []; }
    if (S.length < 3) return S;                                   /* mis. pesan "belum ada block model" */
    S = S.filter(function (st) { return DROP.indexOf(st.t) < 0; });
    S.forEach(function (st) {
      var t = TXT[st.t];
      if (t) st.d = t;
      else if (st.d && st.d.length > 150) {                        /* pendekkan sisanya: satu kalimat pertama */
        var p = st.d.indexOf('. ');
        st.d = p > 40 ? st.d.slice(0, p + 1) : st.d.slice(0, 140).replace(/\s+\S*$/, '') + '…';
      }
    });
    extraSteps().forEach(function (st) { S.push(st); });
    var ix = function (st) { var k = ORD.indexOf(st.s); return k < 0 ? ORD.length - 1.5 : k; };
    S = S.map(function (st, i) { return [ix(st), i, st]; })
          .sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; })
          .map(function (q) { return q[2]; });
    S.unshift(stepData());                                        /* data dulu, baru pembuka */
    return S;
  };

  /* ---------- tempo bawaan lebih cepat + pilihan kecepatan baru ---------- */
  function pasangKecepatan() {
    var row = document.querySelector('#dmMenu .sprow');
    if (!row) return false;
    row.innerHTML = '<button class=sp data-v=1>Pelan</button><button class=sp data-v=0.75>Sedang</button>' +
                    '<button class=sp data-v=0.55>Cepat</button><button class=sp data-v=0.4>Kilat</button>';
    row.querySelectorAll('button.sp').forEach(function (b) { b.onclick = function () { dmSpd(+b.getAttribute('data-v')); }; });
    try { dmSpd(DMX.spd); } catch (e) {}
    return true;
  }
  var n = 0, t = setInterval(function () { if (pasangKecepatan() || ++n > 40) clearInterval(t); }, 250);

  /* daftar "Mulai dari bagian" di menu Demo dibuat ulang dari bagian yang BENAR-BENAR ada:
     daftar lamanya ditulis tangan, jadi bagian baru (Geomodeller Vein, Model Estimation, Autorun,
     Laporan, Pemeriksaan, Periode) tidak pernah muncul di situ. */
  function pasangBagian() {
    var m = $('dmMenu'); if (!m) return;
    var S;
    try { S = dmSteps(); } catch (e) { return; }
    if (!S || S.length < 3) return;
    var urut = [], ada = {};
    S.forEach(function (st) { if (st.s && !ada[st.s] && st.s !== 'Pembuka' && st.s !== 'Penutup') { ada[st.s] = 1; urut.push(st.s); } });
    var lama = m.querySelectorAll('button.sub');
    if (!lama.length) return;
    var sesudah = lama[lama.length - 1].nextSibling, induk = lama[0].parentNode;
    Array.prototype.forEach.call(lama, function (b) { b.remove(); });
    urut.forEach(function (nm) {
      var b = document.createElement('button');
      b.className = 'sub'; b.setAttribute('data-s', '1'); b.textContent = nm;
      b.onclick = function () { dmStart(nm); };
      induk.insertBefore(b, sesudah);
    });
  }
  (function () {
    var _m = window.dmMenu;
    if (typeof _m !== 'function') return;
    window.dmMenu = dmMenu = function (show) {
      var r = _m.apply(this, arguments);
      try { var el = $('dmMenu'); if (el && el.style.display === 'block') pasangBagian(); } catch (e) {}
      return r;
    };
  })();
})();
