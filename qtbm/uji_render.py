# -*- coding: utf-8 -*-
"""Render tanpa layar + ukur kecepatan, untuk dijalankan di CI.

Kenapa ada: penampil 3D tidak bisa dipercaya hanya karena "kelihatannya jalan di komputer saya".
Berkas ini menggambar adegan ke framebuffer tanpa membuka jendela, lalu MEMERIKSA GAMBARNYA:
  - latar tidak kosong: ada piksel yang bukan warna latar (artinya blok benar-benar tergambar)
  - blok terwarnai beragam: jumlah warna berbeda > 1 (artinya pewarnaan atribut bekerja)
  - saringan bekerja: membatasi RL harus mengurangi jumlah piksel yang terisi
lalu mengukur fps pada beberapa jumlah blok.

Dipakai: python -m qtbm.uji_render [berkas_bm.csv] [--png keluaran.png] [--blok 200000]
Keluar dengan kode 0 bila semua pemeriksaan lulus.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from PySide6.QtGui import QOffscreenSurface, QOpenGLContext, QSurfaceFormat
from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
from PySide6.QtWidgets import QApplication

from . import adegan as AD
from . import proyek as PR
from .render import Kamera, Penggambar

LEBAR, TINGGI = 800, 600
LATAR = (0.08, 0.10, 0.13, 1.0)


def _format() -> QSurfaceFormat:
    f = QSurfaceFormat()
    f.setVersion(3, 3)
    f.setProfile(QSurfaceFormat.CoreProfile)
    f.setDepthBufferSize(24)
    return f


class Papan:
    """Konteks OpenGL tanpa jendela + framebuffer, supaya bisa menggambar di CI."""

    def __init__(self) -> None:
        self.fmt = _format()
        self.surf = QOffscreenSurface()
        self.surf.setFormat(self.fmt)
        self.surf.create()
        self.ctx = QOpenGLContext()
        self.ctx.setFormat(self.fmt)
        if not self.ctx.create():
            raise RuntimeError("tidak bisa membuat konteks OpenGL")
        if not self.ctx.makeCurrent(self.surf):
            raise RuntimeError("tidak bisa mengaktifkan konteks OpenGL")
        ff = QOpenGLFramebufferObjectFormat()
        ff.setAttachment(QOpenGLFramebufferObject.Attachment.Depth)
        self.fbo = QOpenGLFramebufferObject(LEBAR, TINGGI, ff)
        self.fbo.bind()
        self.pg = Penggambar()
        if not self.pg.siapkan():
            raise RuntimeError("penggambar tidak siap: %s" % self.pg.galat)

    def gambar(self, A: AD.Adegan, kam: Kamera, ulang: int = 1) -> Tuple[np.ndarray, float]:
        """Gambar `ulang` bingkai; hasil: (gambar RGBA, detik per bingkai)."""
        self.pg = Penggambar()
        self.pg.siapkan()
        self.pg.unggah(A)
        self.pg.gambar(kam, LEBAR, TINGGI, LATAR)        # bingkai pertama: pemanasan
        self.ctx.functions().glFinish()
        t0 = time.perf_counter()
        for _ in range(max(1, ulang)):
            self.pg.gambar(kam, LEBAR, TINGGI, LATAR)
        self.ctx.functions().glFinish()
        dt = (time.perf_counter() - t0) / max(1, ulang)
        img = self.fbo.toImage()
        img = img.convertToFormat(img.Format.Format_RGBA8888)
        b = img.constBits()
        arr = np.frombuffer(bytes(b), dtype=np.uint8).reshape(img.height(), img.width(), 4).copy()
        return arr, dt


def _latar_uint8() -> np.ndarray:
    return np.array([int(c * 255 + 0.5) for c in LATAR[:3]], dtype=np.int16)


def terisi(img: np.ndarray, toleransi: int = 12) -> int:
    """Jumlah piksel yang jelas BUKAN warna latar."""
    d = np.abs(img[:, :, :3].astype(np.int16) - _latar_uint8()[None, None, :]).max(axis=2)
    return int(np.count_nonzero(d > toleransi))


def bm_contoh(n: int, y0: float = 9011700.0) -> PR.BlockModel:
    """Block model buatan: kubus n blok, koordinat tambang sungguhan (northing 9 juta)."""
    s = max(1, int(round(n ** (1 / 3))))
    g = np.arange(s, dtype=np.float64)
    X, Y, Z = np.meshgrid(505000 + g * 5, y0 + g * 5, 240 + g * 2.5, indexing="ij")
    x, y, z = X.ravel(), Y.ravel(), Z.ravel()
    uk = np.full(x.size, 5.0)
    return PR.BlockModel(x=x, y=y, z=z, sx=uk, sy=uk, sz=np.full(x.size, 2.5),
                         angka={"AU": np.linspace(0.0, 3.0, x.size)}, nama="contoh %d" % x.size)


def main(argv: Optional[list] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    png = None
    nblok = 200_000
    berkas = None
    for i, a in enumerate(argv):
        if a == "--png" and i + 1 < len(argv):
            png = Path(argv[i + 1])
        elif a == "--blok" and i + 1 < len(argv):
            nblok = int(argv[i + 1])
        elif not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--png", "--blok")):
            berkas = Path(a)

    QSurfaceFormat.setDefaultFormat(_format())
    app = QApplication([])                                     # noqa: F841 (Qt perlu ini hidup)
    try:
        papan = Papan()
    except RuntimeError as e:
        print("TIDAK BISA MERENDER:", e)
        print("Di mesin tanpa OpenGL 3.3 (mis. kontainer tanpa Mesa), pemeriksaan ini dilewati.")
        return 77                                              # kode khusus: dilewati, bukan gagal
    gl = papan.ctx.format()
    print("OpenGL %d.%d | %s" % (gl.majorVersion(), gl.minorVersion(),
                                 papan.ctx.functions().glGetString(0x1F01) or ""))

    gagal = []

    # ---- 1. block model sungguhan (bila diberikan) atau buatan ----
    if berkas and berkas.exists():
        bm = PR.baca_bm(berkas)
        print("block model: %s" % bm.ringkas())
    else:
        bm = bm_contoh(nblok)
        print("block model buatan: %d blok" % bm.n)

    kam = Kamera()
    A = AD.susun(bm, atribut="AU_GC" if "AU_GC" in bm.angka else "AU")
    kam.pas_ke(A.kotak)
    img, dt = papan.gambar(A, kam, ulang=10)
    isi = terisi(img)
    print("bingkai: %d x %d | piksel terisi %d (%.1f%%) | %.1f fps"
          % (img.shape[1], img.shape[0], isi, 100 * isi / (img.shape[0] * img.shape[1]), 1 / dt))
    if isi < 0.01 * img.shape[0] * img.shape[1]:
        gagal.append("gambar hampir kosong: blok tidak tergambar (piksel terisi %d)" % isi)

    warna = np.unique(img[:, :, :3].reshape(-1, 3), axis=0)
    print("warna berbeda di gambar: %d" % warna.shape[0])
    if warna.shape[0] < 8:
        gagal.append("warna terlalu seragam (%d): pewarnaan atribut tidak bekerja"
                     % warna.shape[0])

    if png:
        from PySide6.QtGui import QImage
        QImage(img.tobytes(), img.shape[1], img.shape[0],
               QImage.Format.Format_RGBA8888).save(str(png))
        print("gambar disimpan:", png)

    # ---- 2. saringan RL harus mengurangi yang tergambar ----
    k = bm.kotak()
    tengah = (k[4] + k[5]) / 2
    A2 = AD.susun(bm, atribut="AU_GC" if "AU_GC" in bm.angka else "AU",
                  saringan=AD.Saringan(rl=(tengah, k[5])))
    img2, _ = papan.gambar(A2, kam, ulang=2)
    isi2 = terisi(img2)
    print("setelah dibatasi RL >= %.1f: %d blok, piksel terisi %d" % (tengah, A2.n_blok, isi2))
    if not (A2.n_blok < A.n_blok):
        gagal.append("saringan RL tidak mengurangi jumlah blok")
    if not (isi2 < isi):
        gagal.append("saringan RL tidak mengurangi piksel terisi (%d vs %d)" % (isi2, isi))

    # ---- 3. kecepatan pada beberapa jumlah blok ----
    print()
    print("%-12s %-10s %s" % ("blok", "unggah", "gambar"))
    for n in (50_000, 200_000, 1_000_000):
        b = bm_contoh(n)
        t0 = time.perf_counter()
        Ax = AD.susun(b, atribut="AU")
        ms_susun = (time.perf_counter() - t0) * 1000
        _, dtx = papan.gambar(Ax, Kamera(), ulang=5)
        print("%-12s %-10s %.1f fps (%.1f ms)"
              % (f"{Ax.n_blok:,}".replace(",", "."), "%.0f ms" % ms_susun, 1 / dtx, dtx * 1000))

    print()
    if gagal:
        print("GAGAL (%d):" % len(gagal))
        for g in gagal:
            print("  -", g)
        return 1
    print("LULUS: blok tergambar, pewarnaan atribut bekerja, dan saringan RL berpengaruh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
