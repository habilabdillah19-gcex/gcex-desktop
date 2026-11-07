/* ================= REPORTING: BEBERAPA DESAIN PIT & PROGRES TOPO-KE-TOPO =================
   Modul bersama GC-Ex Drill Hole dan GC-Ex Block Model (dipasang sesudah modul Reporting BM).

   Dua pekerjaan nyata yang sebelumnya harus dikerjakan berulang kali secara manual:

   1. BEBERAPA DESAIN PIT, TOPOGRAFI SAMA ("per fase pit")
      Reporting BM hanya memakai desain pit AKTIF, jadi membandingkan Fase 1 / Fase 2 / ultimate
      berarti mengganti versi aktif lalu menghitung lagi, dan angkanya tidak pernah berdampingan.
      Di sini beberapa pit dipilih sekaligus; tiap pit dihitung dengan topografi yang SAMA, lalu
      ditampilkan satu tabel per pit. Untuk pit bersarang (fase berikutnya memuat fase sebelumnya)
      kolom "Tambahan" memberi selisih terhadap pit di atasnya -- tonase dan logam dikurangkan,
      kadar tambahan = logam tambahan / tonase tambahan.

   2. PROGRES TOPO-KE-TOPO (ore reconcile)
      Material yang tergali antara dua survei = blok yang berada DI BAWAH topografi lama dan
      DI ATAS topografi baru. Dengan itu seluruh atribut block model (kadar tiap unsur, logam,
      kategori) bisa dilaporkan untuk periode penambangan itu, mis. akhir Juni -> akhir Juli.
      Catatan penting: hasilnya adalah block model DI ANTARA dua permukaan -- rekonsiliasi
      terhadap timbangan pabrik tetap perlu, karena survei pun punya ketidakpastian.

   Cara kerjanya: modul ini TIDAK menyalin mesin perhitungan Reporting. Ia mengisi RP.ovr
   (override permukaan atas / bawah), memanggil rpRun() milik aplikasi sekali untuk tiap target,
   lalu mengumpulkan RP.res. Jadi semua batasan lain (domain, poligon, RL, filter atribut, SG,
   sb_frac, cut-off) berlaku apa adanya dan angkanya pasti konsisten dengan laporan biasa.      */
(function () {
  if (window.RPX || typeof BX === 'undefined' || typeof rpRun !== 'function') return;
  var RPX = window.RPX = { mode: 'pit', pits: [], topo: '', ta: '', tb: '', allAtt: true, res: null, busy: false, msg: '', ci: 0 };
  var $ = function (i) { return document.getElementById(i); };
  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function N(v, d) { if (v == null || !isFinite(v)) return '-'; return (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
  function tot(G) { var r = { n: 0, v: 0, t: 0, s: {} }; Object.keys(G || {}).forEach(function (k) { var a = G[k]; r.n += a.n; r.v += a.v; r.t += a.t; Object.keys(a.s).forEach(function (at) { var q = r.s[at] || (r.s[at] = { tw: 0, w: 0 }); q.tw += a.s[at].tw; q.w += a.s[at].w; }); }); return r; }
  function metal(t, g, u) { return u === '%' ? t * g / 100 : u === 'ppb' ? t * g / 1000 : t * g; }
  function metU(u) { return u === '%' ? 't' : 'g'; }
  function api(k) { return (window.RP && RP.api && RP.api[k]) || null; }

  /* ---------- sumber permukaan: versi Data Spasial (Drill Hole) + DTM Data Referensi + permukaan aktif ---------- */
  function srcs(role) {
    var L = [];
    if (window.spL && window.SPN) {                                   /* Drill Hole: versi per jenis */
      (role === 'pit' ? ['pit', 'topo'] : ['topo', 'pit']).forEach(function (r) {
        try {
          spL(r).forEach(function (v) {
            L.push(['sp:' + r + ':' + v.id, SPN[r] + ': ' + v.name + (spAct(r) === v ? ' (aktif)' : '') + (v.tin ? ' · DTM' : '')]);
          });
        } catch (e) {}
      });
    } else {                                                          /* Block Model: satu permukaan aktif per jenis */
      if (window.OV && OV.topoF && OV.topoF.x && OV.topoF.x.length) L.push(['ov:topo', 'Topografi aktif']);
      if (window.OV && OV.pitF && OV.pitF.x && OV.pitF.x.length) L.push(['ov:pit', 'Desain pit aktif']);
    }
    (window.MD && MD.models || []).forEach(function (w, i) { L.push(['wf:' + i, 'Data Referensi: ' + w.name]); });
    return L;
  }
  function labOf(k) { var r = srcs('topo').filter(function (p) { return p[0] === k; })[0]; return r ? r[1] : k; }

  /* fungsi z permukaan dalam koordinat LOKAL blok; which = 'hi' (atap) / 'lo' (lantai).
     DTM segitiga dipakai persis (seperti Surpac); titik / kontur diinterpolasi IDW seperti Reporting biasa. */
  function zf(k, which) {
    if (!k) return null;
    var ox = window.offX || 0, oy = window.offY || 0, j = which === 'lo' ? 0 : 1;
    if (k.indexOf('wf:') === 0) {
      var w = (window.MD && MD.models || [])[+k.slice(3)], tf = w && api('tin') ? api('tin')(w) : null;
      if (!tf) return null;
      return { n: 'Data Referensi ' + w.name, tin: true, f: function (x, y) { var r = tf(x + ox, y + oy); return r ? r[j] : null; } };
    }
    if (k.indexOf('ov:') === 0) {
      var o = k === 'ov:pit' ? (window.OV && OV.pitF) : (window.OV && OV.topoF);
      if (!(o && o.x && o.x.length) || !api('surf')) return null;
      var fn = api('surf')(o);
      return { n: k === 'ov:pit' ? 'desain pit aktif' : 'topografi aktif', tin: false, f: fn };
    }
    var a = k.split(':'), v = null;
    try { spL(a[1]).forEach(function (x) { if (x.id === a[2]) v = x; }); } catch (e) {}
    if (!v) return null;
    if (v.tin && api('tin')) { var tf2 = api('tin')(v.tin); return { n: SPN[a[1]] + ' ' + v.name, tin: true, f: function (x, y) { var r = tf2(x + ox, y + oy); return r ? r[j] : null; } }; }
    /* versi non-aktif menyimpan datanya sendiri; versi aktif isinya ada di topoData / pitData */
    var data = v.data != null ? v.data : (window.SA && SA.D ? SA.D[SPK[a[1]]] : null);
    if (!(data && data.length) || !window.prep || !api('surf')) return null;
    var P = prep(data, false);
    if (!(P && P.x && P.x.length)) return null;
    return { n: SPN[a[1]] + ' ' + v.name, tin: false, f: api('surf')(P) };
  }

  /* ---------- satu kali hitung dengan permukaan atas / bawah yang ditentukan ---------- */
  function once(atas, bawah, lab) {
    var o = rpO(); if (!o) throw new Error('Block model belum ada.');
    /* rpRun() milik aplikasi memindahkan tab ke "Hasil" (RP.sec='2') dan menggambar panelnya;
       simpan dan pulihkan supaya tab "Pit & progres" tetap yang tampil. */
    var s0 = o.surf, a0 = o.atts, sh0 = o.show, sec0 = RP.sec;
    RP.ovr = { tz: atas ? atas.f : null, pz: bawah ? bawah.f : null, tzT: !!(atas && atas.tin), pzT: !!(bawah && bawah.tin), lab: lab };
    o.surf = 'none'; o.show = false;
    if (RPX.mode === 'tt' && RPX.allAtt) {
      var m = BX.m, all = Object.keys(m.num).filter(function (n) {
        return !/^(sb_frac|est_|sg|dens|density|bd|x|y|z|xc|yc|zc|dx|dy|dz)$/i.test(n) && !/^est_/i.test(n);
      }).slice(0, 14);
      if (all.indexOf(o.gr) < 0) all.unshift(o.gr);
      o.atts = all;
    }
    try { rpRun(); } finally { o.surf = s0; o.atts = a0; o.show = sh0; RP.ovr = null; RP.sec = sec0; }
    var R = RP.res;
    if (!R) throw new Error('Perhitungan tidak menghasilkan apa pun.');
    return { lab: lab, res: JSON.parse(JSON.stringify({ rows: R.rows, cuts: R.cuts, atts: R.atts, unit: R.unit, nb: R.nb, nOut: R.nOut, lab: R.lab, grp: R.grp, bh: R.bh, br: R.br || 0, frac: R.frac || '', sg: R.sg, bm: R.bm })) };
  }

  RPX.run = function () {
    if (RPX.busy) return; RPX.busy = true; RPX.msg = ''; RPX.res = null;
    try {
      if (!BX.m) throw new Error('Block model belum ada.');
      var out = [], i;
      if (RPX.mode === 'pit') {
        var T = zf(RPX.topo, 'hi');
        if (!T) throw new Error('Pilih topografi dulu (permukaan atas untuk semua pit).');
        if (!RPX.pits.length) throw new Error('Centang minimal satu desain pit.');
        for (i = 0; i < RPX.pits.length; i++) {
          var P = zf(RPX.pits[i], 'lo');
          if (!P) throw new Error('Desain pit tidak terbaca: ' + RPX.pits[i]);
          out.push(once(T, P, labOf(RPX.pits[i])));
        }
        RPX.res = { mode: 'pit', topo: T.n, rows: out, date: new Date().toLocaleString('id-ID') };
      } else {
        var A = zf(RPX.ta, 'hi'), B = zf(RPX.tb, 'lo');
        if (!A || !B) throw new Error('Pilih topografi atas (lama) dan bawah (baru).');
        if (RPX.ta === RPX.tb) throw new Error('Topografi atas dan bawah sama: tidak ada material di antaranya.');
        out.push(once(A, B, labOf(RPX.ta) + ' → ' + labOf(RPX.tb)));
        RPX.res = { mode: 'tt', atas: A.n, bawah: B.n, rows: out, date: new Date().toLocaleString('id-ID') };
      }
      RPX.ci = Math.min(RPX.ci || 0, (out[0].res.cuts.length || 1) - 1);
    } catch (e) {
      console.error(e); RPX.msg = '<span class=warn>' + E(e.message || e) + '</span>';
    } finally { RPX.busy = false; RPX.panel(); }
  };

  /* ---------- tabel hasil ---------- */
  function rowTot(r, ci) { var q = r.res.rows[ci] || r.res.rows[0]; return tot(q.G); }
  function tabel() {
    var X = RPX.res; if (!X) return '';
    var ci = RPX.ci || 0, at = X.rows[0].res.atts, un = X.rows[0].res.unit, inc = X.mode === 'pit' && X.rows.length > 1;
    var h = '<div class=rpwrap><table class="pltb rptb"><tr><th>' + (X.mode === 'pit' ? 'Desain pit' : 'Periode') + '</th><th>Blok</th><th>Volume<br><small>m³</small></th><th>Tonase<br><small>t</small></th>' +
      at.map(function (a) { return '<th>' + E(a) + '<br><small>' + E(un[a] || 'g/t') + '</small></th><th>Logam<br><small>' + metU(un[a]) + '</small></th>'; }).join('') + '</tr>';
    var prev = null;
    X.rows.forEach(function (r) {
      var T = rowTot(r, ci);
      h += '<tr><td>' + E(r.lab) + '</td><td>' + N(T.n) + '</td><td>' + N(T.v) + '</td><td><b>' + N(T.t) + '</b></td>' +
        at.map(function (a) { var q = T.s[a], g = q && q.w ? q.tw / q.w : NaN; return '<td><b>' + N(g, 3) + '</b></td><td>' + N(isFinite(g) ? metal(T.t, g, un[a]) : NaN, un[a] === '%' ? 1 : 0) + '</td>'; }).join('') + '</tr>';
      if (inc && prev) {
        var dt = T.t - prev.t, dv = T.v - prev.v, dn = T.n - prev.n;
        h += '<tr class=rpxinc><td>&nbsp;&nbsp;↳ tambahan</td><td>' + N(dn) + '</td><td>' + N(dv) + '</td><td>' + N(dt) + '</td>' +
          at.map(function (a) {
            var q = T.s[a], p = prev.s[a], m1 = q && q.w ? metal(T.t, q.tw / q.w, un[a]) : NaN, m0 = p && p.w ? metal(prev.t, p.tw / p.w, un[a]) : NaN, dm = m1 - m0;
            var gg = (isFinite(dm) && dt > 0) ? (un[a] === '%' ? dm * 100 / dt : un[a] === 'ppb' ? dm * 1000 / dt : dm / dt) : NaN;
            return '<td>' + N(gg, 3) + '</td><td>' + N(dm, un[a] === '%' ? 1 : 0) + '</td>';
          }).join('') + '</tr>';
      }
      prev = T;
    });
    return h + '</table></div>';
  }
  function grupTabel() {
    var X = RPX.res; if (!X || X.mode !== 'tt') return '';
    var R = X.rows[0].res, r = R.rows[RPX.ci || 0] || R.rows[0], at = R.atts, un = R.unit, keys = Object.keys(r.G);
    if (R.grp === 'none' || !keys.length) return '';
    keys.sort(function (a, b) { return R.grp === 'bench' ? (+b) - (+a) : String(a).localeCompare(String(b)); });
    var lab = function (k) { return R.grp === 'bench' ? ('RL ' + N((R.br || 0) + (+k + 1) * R.bh, 1) + ' – ' + N((R.br || 0) + (+k) * R.bh, 1)) : k; };
    var h = '<div class=rpwrap><table class="pltb rptb"><tr><th>' + (R.grp === 'bench' ? 'RL' : 'Kategori') + '</th><th>Blok</th><th>Tonase t</th>' +
      at.map(function (a) { return '<th>' + E(a) + '</th>'; }).join('') + '</tr>';
    keys.forEach(function (k) {
      var g = r.G[k];
      h += '<tr><td>' + E(lab(k)) + '</td><td>' + N(g.n) + '</td><td>' + N(g.t) + '</td>' +
        at.map(function (a) { var q = g.s[a]; return '<td>' + N(q && q.w ? q.tw / q.w : NaN, 3) + '</td>'; }).join('') + '</tr>';
    });
    return h + '</table></div>';
  }
  RPX.csv = function () {
    var X = RPX.res; if (!X) return;
    var ci = RPX.ci || 0, at = X.rows[0].res.atts, un = X.rows[0].res.unit;
    var L = ['# Reporting ' + (X.mode === 'pit' ? 'per desain pit (topografi sama: ' + X.topo + ')' : 'progres topo-ke-topo (' + X.atas + ' → ' + X.bawah + ')'),
             '# Block model: ' + X.rows[0].res.bm, '# Cut-off: >= ' + X.rows[0].res.cuts[ci], '# Batasan lain: ' + (X.rows[0].res.lab || '-') + ' · ' + (X.rows[0].res.sg || ''),
             '# Tanggal: ' + X.date];
    L.push(['TARGET', 'BLOK', 'VOLUME_M3', 'TONASE_T'].concat(at.map(function (a) { return a + '_' + (un[a] || 'g/t').replace('/', '_'); }), at.map(function (a) { return 'LOGAM_' + a + '_' + metU(un[a]).toUpperCase(); })).join(','));
    X.rows.forEach(function (r) {
      var T = rowTot(r, ci);
      L.push(['"' + r.lab + '"', T.n, T.v.toFixed(1), T.t.toFixed(1)]
        .concat(at.map(function (a) { var q = T.s[a]; return q && q.w ? (q.tw / q.w).toFixed(4) : ''; }),
                at.map(function (a) { var q = T.s[a]; return q && q.w ? metal(T.t, q.tw / q.w, un[a]).toFixed(2) : ''; })).join(','));
    });
    if (X.mode === 'tt') {
      var R = X.rows[0].res, rr = R.rows[ci] || R.rows[0];
      L.push('', '# Rincian per ' + (R.grp === 'bench' ? 'RL' : R.grp === 'cat' ? 'kategori' : 'grup'));
      L.push(['GRUP', 'BLOK', 'TONASE_T'].concat(at).join(','));
      Object.keys(rr.G).sort(function (a, b) { return R.grp === 'bench' ? (+b) - (+a) : String(a).localeCompare(String(b)); }).forEach(function (k) {
        var g = rr.G[k], nm = R.grp === 'bench' ? ('RL ' + ((R.br || 0) + (+k + 1) * R.bh).toFixed(1) + ' - ' + ((R.br || 0) + (+k) * R.bh).toFixed(1)) : k;
        L.push(['"' + nm + '"', g.n, g.t.toFixed(1)].concat(at.map(function (a) { var q = g.s[a]; return q && q.w ? (q.tw / q.w).toFixed(4) : ''; })).join(','));
      });
    }
    var nm2 = (X.mode === 'pit' ? 'Reporting_per_pit_' : 'Reporting_progres_topo_') + rpDateX() + '.csv';
    if (window.dgDl) dgDl(L.join('\r\n') + '\r\n', nm2, 'text/csv');
  };
  function rpDateX() { var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; }; return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()); }

  /* ---------- panel (tab tambahan di Reporting) ---------- */
  RPX.set = function (k, v) { RPX[k] = v; RPX.panel(); };
  RPX.pit = function (k, on) { var i = RPX.pits.indexOf(k); if (on && i < 0) RPX.pits.push(k); if (!on && i >= 0) RPX.pits.splice(i, 1); RPX.panel(); };
  RPX.open = function () { if (window.RP) RP.sec = 'x'; if (window.uiTab) uiTab('Rep'); RPX.panel(); };
  RPX.panel = function () {
    if (!window.RP || RP.sec !== 'x') { if (window.rpPanel) rpPanel(); return; }
    var b = $('rpBody'); if (!b) return;
    if (!BX.m) { b.innerHTML = '<div class="box gmstate">Belum ada block model.</div>'; return; }
    var sel = function (opts, val, on) { return '<select onchange="' + on + '">' + opts.map(function (p) { return '<option value="' + E(p[0]) + '"' + (String(p[0]) === String(val) ? ' selected' : '') + '>' + E(p[1]) + '</option>'; }).join('') + '</select>'; };
    var SP = srcs('pit'), ST = srcs('topo');
    if (!RPX.topo && ST.length) RPX.topo = ST[0][0];
    if (!RPX.ta && ST.length) RPX.ta = ST[0][0];
    if (!RPX.tb && ST.length > 1) RPX.tb = ST[1][0];
    var h = '<i id=rpxBody hidden></i><div class="uitabs rptabs"><button onclick="RP.sec=\'1\';rpPanel()">Atribut</button><button onclick="RP.sec=\'c\';rpPanel()">Constraint</button><button onclick="RP.sec=\'2\';rpPanel()">Hasil</button><button class="on rpxtab">Pit &amp; progres</button></div>';
    h += '<div class=hint style="margin:4px 0 8px">Memakai <b>atribut, cut-off, pengelompokan, domain, poligon dan SG</b> yang sudah diatur di tab <b>Atribut</b> dan <b>Constraint</b>. Yang diganti di sini hanya <b>permukaan atas &amp; bawah</b>.</div>';
    h += '<div class="uitabs rptabs" style="margin-bottom:6px"><button class="' + (RPX.mode === 'pit' ? 'on' : '') + '" onclick="RPX.set(\'mode\',\'pit\')">Per desain pit</button><button class="' + (RPX.mode === 'tt' ? 'on' : '') + '" onclick="RPX.set(\'mode\',\'tt\')">Progres topo-ke-topo</button></div>';
    if (RPX.msg) h += '<div class="box gmstate">' + RPX.msg + '</div>';
    if (RPX.mode === 'pit') {
      h += '<h4>Topografi (sama untuk semua pit)</h4>' + (ST.length ? sel(ST, RPX.topo, "RPX.set('topo',this.value)") : '<div class=hint><span class=warn>Belum ada permukaan.</span> Import di Data Spasial / Data Referensi.</div>');
      h += '<h4>Desain pit yang dilaporkan</h4>' + (SP.length ? '<div class=rpcat>' + SP.map(function (p) {
        return '<label><input type=checkbox ' + (RPX.pits.indexOf(p[0]) >= 0 ? 'checked' : '') + ' onchange="RPX.pit(\'' + E(p[0]) + '\',this.checked)"> ' + E(p[1]) + '</label>';
      }).join('') + '</div>' : '<div class=hint><span class=warn>Belum ada desain pit / DTM.</span></div>');
      h += '<div class=hint>Centang beberapa fase pit. Tiap pit dihitung dengan topografi di atas: blok dihitung bila titik pusatnya <b>di bawah topografi</b> dan <b>di atas desain pit</b> itu. Urutkan centangnya dari pit terkecil ke terbesar supaya kolom <b>tambahan</b> bermakna (hanya benar untuk pit bersarang).</div>';
    } else {
      h += '<h4>Topografi atas (lebih awal)</h4>' + sel(ST.length ? ST : [['', '(belum ada)']], RPX.ta, "RPX.set('ta',this.value)");
      h += '<h4>Topografi bawah (lebih baru)</h4>' + sel(ST.length ? ST : [['', '(belum ada)']], RPX.tb, "RPX.set('tb',this.value)");
      h += '<label class=sw style="margin-top:6px"><input type=checkbox ' + (RPX.allAtt ? 'checked' : '') + ' onchange="RPX.set(\'allAtt\',this.checked)"> Laporkan <b>semua</b> atribut kadar block model (bukan hanya yang dicentang di )</label>';
      h += '<div class=hint>Material tergali antara dua survei = blok <b>di bawah</b> topografi atas dan <b>di atas</b> topografi bawah. Pakai ini untuk rekonsiliasi bulanan: mis. atas = akhir Juni, bawah = akhir Juli.</div>';
    }
    h += '<button class=btn-pri style="width:100%;height:32px;margin-top:8px" onclick="RPX.run()" ' + (RPX.busy ? 'disabled' : '') + '>&#9654; ' + (RPX.busy ? 'Menghitung…' : 'Hitung ' + (RPX.mode === 'pit' ? 'per pit' : 'progres')) + '</button>';
    var X = RPX.res;
    if (X) {
      var R0 = X.rows[0].res;
      h += '<h4 style="margin-top:10px">Hasil</h4><div class="box gmstate rpsum"><small>' + E(X.mode === 'pit' ? 'Topografi: ' + X.topo : 'Atas: ' + X.atas + ' · bawah: ' + X.bawah) +
        '<br>' + E([R0.lab, R0.sg, R0.frac].filter(Boolean).join(' · ')) + '<br>' + E(X.date) + '</small></div>';
      if (R0.cuts.length > 1) h += '<div class="g2 f"><label style="align-self:center">Cut-off ' + E(R0.gr || '') + '</label>' + sel(R0.cuts.map(function (c, i) { return [i, '≥ ' + c]; }), RPX.ci || 0, "RPX.set('ci',+this.value)") + '</div>';
      h += tabel() + grupTabel();
      h += '<div class="g2 f" style="margin-top:8px"><button class=btn-pri onclick="RPX.csv()">&#8681; Export CSV</button><button onclick="RP.sec=\'2\';rpPanel()">Laporan rinci terakhir</button></div>';
    }
    b.innerHTML = h;
  };

  /* Tab tambahan disisipkan ke bilah tab Reporting milik aplikasi tanpa mengubah rpPanel-nya.
     Dipasang lewat pengamat DOM, bukan hanya pembungkus window.rpPanel: di Block Model, rpPanel
     dipanggil lewat ikatan LOKAL di dalam IIFE-nya sehingga pembungkus window saja tidak kena. */
  (function () {
    function pasangTab() {
      var bar = document.querySelector('#rpBody .rptabs');
      /* Selain kelas .rpxtab, dicek juga teksnya: panel lain boleh saja menggambar tombol
         "Pit & progres" sendiri, dan tombol kedua dengan nama sama persis adalah cacat yang
         terlihat langsung oleh pemakai (dua tab bernama sama di satu bilah). */
      if (!bar) return;
      var ada = bar.querySelector('.rpxtab') ||
        [].slice.call(bar.children).some(function (b) { return /pit\s*&(amp;)?\s*progres/i.test(b.innerHTML || ''); });
      if (ada) return;
      var b2 = document.createElement('button');
      b2.className = 'rpxtab'; b2.innerHTML = 'Pit &amp; progres';
      b2.title = 'Beberapa desain pit sekaligus, dan progres penambangan topo-ke-topo';
      b2.onclick = function () { RP.sec = 'x'; RPX.panel(); };
      bar.appendChild(b2);
    }
    function periksa() {
      try {
        if (window.RP && RP.sec === 'x') { if (!document.getElementById('rpxBody')) RPX.panel(); return; }
        pasangTab();
      } catch (e) {}
    }
    var mo = null, t0 = setInterval(function () {
      var b = document.getElementById('rpBody');
      if (!b || mo) return;
      clearInterval(t0);
      mo = new MutationObserver(periksa);
      mo.observe(b, { childList: true });
      periksa();
    }, 400);
    var _p = window.rpPanel;
    window.rpPanel = function () {
      if (window.RP && RP.sec === 'x') { RPX.panel(); return; }
      var r = _p.apply(this, arguments);
      try { pasangTab(); } catch (e) {}
      return r;
    };
    var css = document.createElement('style'); css.id = 'rpxCss';
    css.textContent = '.rptb tr.rpxinc td{color:var(--mu,#6b7785);font-style:italic;border-bottom-style:dotted}';
    document.head.appendChild(css);
  })();

  /* node Project Tree di bawah Reporting */
  window.rpxTree = function () {
    var X = RPX.res, b = X ? (X.mode === 'pit' ? X.rows.length + ' pit' : 'progres') : '';
    return [{
      id: 'rep.x', t: 'Per desain pit & progres topo-ke-topo', ic: 'pit', b: b,
      hint: 'Beberapa desain pit sekaligus dengan topografi yang sama, dan tonase × kadar material tergali antara dua survei topografi',
      /* Node ini punya PANEL sendiri (bagian "Pit & progres" di Reporting), bukan sekadar perintah.
         Tanpa `tab`, Project Tree menganggapnya node aksi dan memunculkan kartu tombol -- padahal
         RPX.open() memang membuka panelnya, hanya saja kartu itu menutupinya. Akibatnya tombol
         birunya terlihat seperti tidak melakukan apa-apa, lalu judul panel kembali ke "Reporting
         (constraint)" begitu panelnya menggambar ulang. Dengan `tab`, panelnya yang tampil. */
      tab: 'Rep',
      go: function () { RPX.open(); },
      menu: function () {
        return [{ t: 'Laporan per desain pit', fn: function () { RPX.mode = 'pit'; RPX.open(); } },
                { t: 'Progres penambangan topo-ke-topo', fn: function () { RPX.mode = 'tt'; RPX.open(); } },
                { sep: 1 },
                { t: 'Hitung ulang', fn: function () { RPX.open(); RPX.run(); }, dis: !(RPX.pits.length || RPX.mode === 'tt') },
                { t: 'Export CSV hasil terakhir', fn: function () { RPX.csv(); }, dis: !RPX.res }];
      }
    }];
  };
})();
