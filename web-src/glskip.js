/* ---------- 3D: jangan kirim ulang lapisan yang tidak berubah (Drillhole 0.24.42; Block Model 0.24.47 — berkas bersama web-src/glskip.js) ----------
   Plotly gl3d memanggil update() untuk SETIAP lapisan setiap kali satu lapisan saja berubah (geser
   sayatan, centang overlay, lapisan Ore Geometry yang dibangun ulang). Untuk block model ber-ratusan
   ribu titik sudut itu berarti ~1 detik kerja JavaScript per perubahan, walau blok-bloknya sama.
   Di sini update() dilewati bila ISI lapisan masukan (data._input) sama dengan panggilan
   sebelumnya: properti tingkat atasnya sama (larik per panjang + checksum isi, objek kecil seperti
   marker / lighting per isi JSON), visibilitasnya sama, dan skala sumbu adegan (dataScale) tidak
   berubah. Lapisan yang dibangun ulang (objek atau array baru) tetap di-update seperti biasa. */
(function () {
  if (window.GLSKIP) return;
  var G = window.GLSKIP = { on: true, skip: 0, run: 0, debug: false, alasan: [] };
  /* Sidik jari larik: panjang + checksum SELURUH isi untuk larik angka (dua jumlah berbobot; O(n) tetapi jauh lebih murah
     daripada mengunggah ulang ke GPU), atau panjang + 16 contoh untuk larik teks / bersarang. Dibandingkan per NILAI, bukan
     per referensi: Block Model & Drill Hole membuat larik baru dengan isi sama setiap membangun ulang lapisan (mis. mencentang
     collar), dan sebelumnya itu selalu dianggap berubah. Larik yang diubah di tempat juga tertangkap. */
  function sidik(a) {
    var n = a.length, s = n + ':';
    if (!n) return s;
    var v0 = a[0];
    if (typeof v0 === 'number' || ArrayBuffer.isView(a)) {
      var s1 = 0, s2 = 0, nn = 0;
      for (var i = 0; i < n; i++) { var v = a[i]; if (v == null || v !== v) { nn++; continue; } s1 += v; s2 += v * ((i & 15) + 1); }
      return s + s1 + ':' + s2 + ':' + nn;
    }
    var ix = [0, n - 1], st = Math.max(1, Math.floor(n / 14)); for (var q = st; q < n - 1; q += st) ix.push(q);
    for (var j = 0; j < ix.length; j++) { var w = a[ix[j]]; s += (w && typeof w === 'object' ? (w.length != null ? 'L' + w.length : 'o') : w) + ','; }
    return s;
  }
  function nilai(inp) {
    var out = [];
    Object.keys(inp).forEach(function (k) {
      var v = inp[k];
      if (v && typeof v === 'object' && (ArrayBuffer.isView(v) || Array.isArray(v))) { out.push(k + '#' + sidik(v)); return; }
      if (v && typeof v === 'object') { try { out.push(k + '=' + JSON.stringify(v)); } catch (e) { out.push(v); } return; }
      out.push(v);
    });
    return out;
  }
  function pasang(P) {
    if (!P || P._glskip || typeof P.update !== 'function') return;
    var asli = P.update;
    P.update = function (data) {
      var inp = data && data._input, ds = this.scene && this.scene.dataScale ? this.scene.dataScale.join(',') : '';
      if (G.on && inp) {
        /* Objek lapisan boleh BARU (Block Model membuat objek trace baru tiap updatePlot) — yang dibandingkan nilainya:
           larik per panjang + checksum isi, objek kecil per JSON, skalar per nilai. */
        var V = nilai(inp), lama = this._gsV, sama = this._gsDs === ds && this._gsVis === data.visible && lama && lama.length === V.length;
        var beda = -1; if (sama) for (var i = 0; i < V.length; i++) if (V[i] !== lama[i]) { sama = false; beda = i; break; }
        if (sama) { this.data = data; G.skip++; return; }
        /* G.debug=true -> G.alasan mencatat mengapa lapisan di-update (diagnosis dari konsol / uji) */
        if (G.debug) { var ks = Object.keys(inp); G.alasan.push((inp.name || inp.type) + ': ' + (!lama ? 'baru' : this._gsDs !== ds ? 'dataScale' : this._gsVis !== data.visible ? 'visible' : lama.length !== V.length ? 'jumlah properti' : beda >= 0 ? ('properti ' + (typeof V[beda] === 'string' && V[beda].indexOf('#') > 0 ? V[beda].split('#')[0] : ks[Math.min(beda, ks.length - 1)])) : '?')); if (G.alasan.length > 60) G.alasan.shift(); }
        this._gsIn = inp; this._gsDs = ds; this._gsVis = data.visible; this._gsV = V;
      }
      G.run++;
      return asli.apply(this, arguments);
    };
    P._glskip = 1;
  }
  function pindai(gd) {
    try {
      var fl = gd && gd._fullLayout; if (!fl) return;
      Object.keys(fl).forEach(function (k) {
        if (!/^scene\d*$/.test(k) || !fl[k] || !fl[k]._scene) return;
        var tr = fl[k]._scene.traces || {};
        Object.keys(tr).forEach(function (u) { pasang(Object.getPrototypeOf(tr[u])); });
      });
    } catch (e) {}
  }
  function bungkus() {
    var P = window.Plotly; if (!P || P._glskipW) return !!(P && P._glskipW);
    ['react', 'newPlot'].forEach(function (n) {
      var f = P[n]; if (typeof f !== 'function') return;
      P[n] = function (gd) {
        var r = f.apply(this, arguments), el = typeof gd === 'string' ? document.getElementById(gd) : gd;
        if (r && typeof r.then === 'function') r.then(function () { pindai(el); }); else pindai(el);
        return r;
      };
    });
    P._glskipW = 1; return true;
  }
  if (!bungkus()) { var n = 0, t = setInterval(function () { if (bungkus() || ++n > 200) clearInterval(t); }, 50); }
})();
