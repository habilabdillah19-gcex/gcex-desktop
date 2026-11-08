/* ---------- 3D: jangan kirim ulang lapisan yang tidak berubah (Drillhole 0.24.42) ----------
   Plotly gl3d memanggil update() untuk SETIAP lapisan setiap kali satu lapisan saja berubah (geser
   sayatan, centang overlay, lapisan Ore Geometry yang dibangun ulang). Untuk block model ber-ratusan
   ribu titik sudut itu berarti ~1 detik kerja JavaScript per perubahan, walau blok-bloknya sama.
   Di sini update() dilewati bila objek lapisan masukan (data._input) sama persis dengan panggilan
   sebelumnya: properti tingkat atasnya identik (array dibandingkan per referensi, objek kecil seperti
   marker / lighting per isi JSON), visibilitasnya sama, dan skala sumbu adegan (dataScale) tidak
   berubah. Lapisan yang dibangun ulang (objek atau array baru) tetap di-update seperti biasa. */
(function () {
  if (window.GLSKIP) return;
  var G = window.GLSKIP = { on: true, skip: 0, run: 0 };
  function nilai(inp) {
    return Object.keys(inp).map(function (k) {
      var v = inp[k];
      if (v && typeof v === 'object' && !ArrayBuffer.isView(v) && !Array.isArray(v)) { try { return k + '=' + JSON.stringify(v); } catch (e) { return v; } }
      return v;
    });
  }
  function pasang(P) {
    if (!P || P._glskip || typeof P.update !== 'function') return;
    var asli = P.update;
    P.update = function (data) {
      var inp = data && data._input, ds = this.scene && this.scene.dataScale ? this.scene.dataScale.join(',') : '';
      if (G.on && inp) {
        var V = nilai(inp), lama = this._gsV, sama = this._gsIn === inp && this._gsDs === ds && this._gsVis === data.visible && lama && lama.length === V.length;
        if (sama) for (var i = 0; i < V.length; i++) if (V[i] !== lama[i]) { sama = false; break; }
        if (sama) { this.data = data; G.skip++; return; }
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
