# -*- coding: utf-8 -*-
"""Penggambar OpenGL untuk adegan block model (dipakai jendela Qt maupun render tanpa layar).

Dipisahkan dari jendelanya dengan sengaja: bagian ini hanya butuh satu konteks OpenGL yang aktif,
jadi hasilnya bisa diuji di CI tanpa jendela (lewat QOffscreenSurface + framebuffer) -- bukan hanya
dengan "kelihatannya jalan" di layar pengembang.

Cara menggambar block model:
  Satu kubus satuan (36 simpul) digambar BERULANG dengan glDrawArraysInstanced. Tiap blok hanya
  menyumbang 10 angka ke GPU (pusat 3, ukuran 3, warna 4 bita), bukan 36 simpul sendiri-sendiri.
  Jadi 1 juta blok = 1 panggilan gambar dan ~40 MB di GPU, bukan 36 juta simpul. Itu sebabnya
  rancangan ini dipilih untuk block model: bentuknya seragam (kotak sejajar sumbu), tinggal
  diskalakan dan digeser.

Pencahayaan sengaja sederhana (satu arah cahaya + ambient) supaya sisi blok tetap terbaca batasnya
tanpa menambah ongkos.
"""
from __future__ import annotations

import ctypes
import math
from typing import Optional, Tuple

import numpy as np

from PySide6.QtGui import QMatrix4x4, QOpenGLContext, QSurfaceFormat, QVector3D, QVector4D
from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram,
                              QOpenGLVertexArrayObject, QOpenGLVersionFunctionsFactory,
                              QOpenGLVersionProfile)

from .adegan import Adegan

# Konstanta OpenGL. PySide6 TIDAK menyediakannya (QOpenGLFunctions_3_3_Core hanya memuat
# fungsinya), dan PyOpenGL tidak dipasang supaya penampil tetap ringan. Nilai-nilai ini tetap
# menurut spesifikasi OpenGL, jadi aman dituliskan tegas di sini.
GL_TRIANGLES = 0x0004
GL_LINE_STRIP = 0x0003
GL_DEPTH_TEST = 0x0B71
GL_CULL_FACE = 0x0B44
GL_BACK = 0x0405
GL_COLOR_BUFFER_BIT = 0x00004000
GL_DEPTH_BUFFER_BIT = 0x00000100
GL_FRONT_AND_BACK = 0x0408
GL_LINE = 0x1B01
GL_FILL = 0x1B02
GL_UNSIGNED_INT = 0x1405
GL_RENDERER = 0x1F01
GL_FLOAT = 0x1406
GL_UNSIGNED_BYTE = 0x1401

# satu kubus satuan: 36 simpul (6 sisi x 2 segitiga), beserta normal sisinya
_SISI = [
    ((0, 0, -1), [(-.5, -.5, -.5), (.5, .5, -.5), (.5, -.5, -.5), (-.5, -.5, -.5), (-.5, .5, -.5), (.5, .5, -.5)]),
    ((0, 0, 1), [(-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5)]),
    ((0, -1, 0), [(-.5, -.5, -.5), (.5, -.5, .5), (-.5, -.5, .5), (-.5, -.5, -.5), (.5, -.5, -.5), (.5, -.5, .5)]),
    ((0, 1, 0), [(-.5, .5, -.5), (-.5, .5, .5), (.5, .5, .5), (-.5, .5, -.5), (.5, .5, .5), (.5, .5, -.5)]),
    ((-1, 0, 0), [(-.5, -.5, -.5), (-.5, .5, .5), (-.5, .5, -.5), (-.5, -.5, -.5), (-.5, -.5, .5), (-.5, .5, .5)]),
    ((1, 0, 0), [(.5, -.5, -.5), (.5, .5, -.5), (.5, .5, .5), (.5, -.5, -.5), (.5, .5, .5), (.5, -.5, .5)]),
]


def kubus_satuan() -> np.ndarray:
    """(36, 6) float32: posisi (3) + normal (3) per simpul."""
    baris = []
    for normal, titik in _SISI:
        for p in titik:
            baris.append([p[0], p[1], p[2], normal[0], normal[1], normal[2]])
    return np.asarray(baris, dtype=np.float32)


VS_BLOK = """#version 330 core
layout(location=0) in vec3 vPos;
layout(location=1) in vec3 vNorm;
layout(location=2) in vec3 iPusat;
layout(location=3) in vec3 iUkuran;
layout(location=4) in vec4 iWarna;
uniform mat4 mvp;
out vec3 fNorm;
out vec4 fWarna;
void main(){
  vec3 p = iPusat + vPos * iUkuran;
  gl_Position = mvp * vec4(p, 1.0);
  fNorm = vNorm;
  fWarna = iWarna;
}
"""

FS_BLOK = """#version 330 core
in vec3 fNorm;
in vec4 fWarna;
uniform vec3 arahCahaya;
out vec4 warna;
void main(){
  float d = max(dot(normalize(fNorm), normalize(arahCahaya)), 0.0);
  float t = 0.45 + 0.55 * d;            // ambient + satu arah cahaya
  warna = vec4(fWarna.rgb * t, fWarna.a);
}
"""

VS_GARIS = """#version 330 core
layout(location=0) in vec3 vPos;
uniform mat4 mvp;
void main(){ gl_Position = mvp * vec4(vPos, 1.0); }
"""

FS_GARIS = """#version 330 core
uniform vec4 warnaGaris;
out vec4 warna;
void main(){ warna = warnaGaris; }
"""


# ---------------------------------------------------------------------------
def matriks_perspektif(fov_deg: float, rasio: float, dekat: float, jauh: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_deg) / 2.0)
    M = np.zeros((4, 4), dtype=np.float32)
    M[0, 0] = f / max(1e-6, rasio)
    M[1, 1] = f
    M[2, 2] = (jauh + dekat) / (dekat - jauh)
    M[2, 3] = (2 * jauh * dekat) / (dekat - jauh)
    M[3, 2] = -1.0
    return M


def matriks_lihat(mata: np.ndarray, sasaran: np.ndarray, atas: np.ndarray) -> np.ndarray:
    f = sasaran - mata
    f = f / max(1e-12, np.linalg.norm(f))
    s = np.cross(f, atas)
    ns = np.linalg.norm(s)
    if ns < 1e-9:                      # pandangan tepat vertikal: pilih sumbu bantu lain
        s = np.cross(f, np.array([0.0, 1.0, 0.0]))
        ns = np.linalg.norm(s)
    s = s / max(1e-12, ns)
    u = np.cross(s, f)
    M = np.eye(4, dtype=np.float32)
    M[0, :3] = s
    M[1, :3] = u
    M[2, :3] = -f
    M[0, 3] = -float(np.dot(s, mata))
    M[1, 3] = -float(np.dot(u, mata))
    M[2, 3] = float(np.dot(f, mata))
    return M


class Kamera:
    """Kamera orbit: berputar mengelilingi satu titik sasaran.

    Dipakai karena itu yang dipakai geolog saat menilai model: memutar-mutar benda, bukan berjalan
    di dalamnya. Azimut diukur seperti di tambang (0 = melihat ke utara, searah jarum jam).
    """

    def __init__(self) -> None:
        self.sasaran = np.zeros(3, dtype=np.float64)
        self.jarak = 1000.0
        self.azimut = 45.0          # derajat
        self.tunduk = 25.0          # derajat di atas horizon
        self.fov = 45.0

    def pas_ke(self, kotak: Tuple[float, float, float, float, float, float]) -> None:
        """Atur sasaran & jarak supaya seluruh kotak masuk layar."""
        self.sasaran = np.array([(kotak[0] + kotak[1]) / 2, (kotak[2] + kotak[3]) / 2,
                                 (kotak[4] + kotak[5]) / 2], dtype=np.float64)
        lebar = max(kotak[1] - kotak[0], kotak[3] - kotak[2], kotak[5] - kotak[4], 1.0)
        self.jarak = lebar / (2 * math.tan(math.radians(self.fov) / 2)) * 1.6

    def mata(self) -> np.ndarray:
        a = math.radians(self.azimut)
        t = math.radians(max(-89.0, min(89.0, self.tunduk)))
        return self.sasaran + self.jarak * np.array([
            math.cos(t) * math.sin(a), math.cos(t) * math.cos(a), math.sin(t)])

    def mvp(self, lebar: int, tinggi: int) -> np.ndarray:
        P = matriks_perspektif(self.fov, max(1, lebar) / max(1, tinggi),
                               max(0.1, self.jarak * 0.001), self.jarak * 10.0)
        V = matriks_lihat(self.mata().astype(np.float32), self.sasaran.astype(np.float32),
                          np.array([0.0, 0.0, 1.0], dtype=np.float32))
        return (P @ V).astype(np.float32)


# ---------------------------------------------------------------------------
class Penggambar:
    """Menyiapkan buffer GPU dan menggambar satu adegan. Butuh konteks OpenGL 3.3 yang aktif.

    Program shader, buffer, dan VAO memakai pembungkus Qt (QOpenGLShaderProgram, QOpenGLBuffer,
    QOpenGLVertexArrayObject) karena pembungkus itu yang disediakan PySide6 dengan lengkap.
    Hanya empat hal yang perlu fungsi OpenGL mentah: glVertexAttribDivisor (supaya satu kubus
    dipakai berulang per blok), glDrawArraysInstanced, glDrawElements, dan beberapa pengaturan
    keadaan. Itu diambil dari QOpenGLFunctions_3_3_Core.
    """

    def __init__(self) -> None:
        self.gl = None
        self.prog_blok: Optional[QOpenGLShaderProgram] = None
        self.prog_garis: Optional[QOpenGLShaderProgram] = None
        self.vao_blok: Optional[QOpenGLVertexArrayObject] = None
        self.vao_garis: Optional[QOpenGLVertexArrayObject] = None
        self.vao_topo: Optional[QOpenGLVertexArrayObject] = None
        self.n_blok = 0
        self.garis_awal = np.zeros(0, np.int32)
        self.garis_cacah = np.zeros(0, np.int32)
        self.n_topo = 0
        self.siap = False
        self.galat = ""
        self._pegang: list = []          # buffer ditahan di sini supaya tidak dibuang Python

    # ---------- penyiapan ----------
    def siapkan(self) -> bool:
        """Ambil fungsi OpenGL 3.3 Core dan susun programnya. False bila tidak tersedia."""
        ctx = QOpenGLContext.currentContext()
        if ctx is None:
            self.galat = "tidak ada konteks OpenGL yang aktif"
            return False
        prof = QOpenGLVersionProfile()
        prof.setVersion(3, 3)
        prof.setProfile(QSurfaceFormat.CoreProfile)
        self.gl = QOpenGLVersionFunctionsFactory.get(prof, ctx)
        if self.gl is None:
            self.galat = ("OpenGL 3.3 Core tidak tersedia pada kartu grafis / driver ini "
                          "(versi konteks: %d.%d)" % (ctx.format().majorVersion(),
                                                      ctx.format().minorVersion()))
            return False
        self.gl.initializeOpenGLFunctions()
        self.prog_blok = self._program(VS_BLOK, FS_BLOK)
        self.prog_garis = self._program(VS_GARIS, FS_GARIS)
        if not self.prog_blok or not self.prog_garis:
            return False
        self.gl.glEnable(GL_DEPTH_TEST)
        self.gl.glEnable(GL_CULL_FACE)
        self.gl.glCullFace(GL_BACK)
        self.siap = True
        return True

    def _program(self, vs: str, fs: str) -> Optional[QOpenGLShaderProgram]:
        p = QOpenGLShaderProgram()
        if not p.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, vs):
            self.galat = "gagal menyusun vertex shader: %s" % p.log()
            return None
        if not p.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, fs):
            self.galat = "gagal menyusun fragment shader: %s" % p.log()
            return None
        if not p.link():
            self.galat = "gagal menautkan program: %s" % p.log()
            return None
        return p

    def _vbo(self, data: np.ndarray, indeks: bool = False) -> QOpenGLBuffer:
        b = QOpenGLBuffer(QOpenGLBuffer.Type.IndexBuffer if indeks
                          else QOpenGLBuffer.Type.VertexBuffer)
        b.create()
        b.bind()
        d = np.ascontiguousarray(data)
        b.allocate(d.tobytes(), d.nbytes)
        self._pegang.append(b)
        return b

    @staticmethod
    def _vao() -> QOpenGLVertexArrayObject:
        v = QOpenGLVertexArrayObject()
        v.create()
        return v

    # ---------- unggah adegan ----------
    def unggah(self, A: Adegan) -> None:
        """Pindahkan adegan ke GPU. Dipanggil ulang setiap adegan berubah (saringan, atribut)."""
        if not self.siap:
            return
        gl = self.gl
        self.n_blok = A.n_blok
        if self.n_blok:
            self.vao_blok = self._vao()
            self.vao_blok.bind()
            self._vbo(kubus_satuan())
            # posisi & normal kubus satuan: satu baris 6 float (24 bita)
            self.prog_blok.enableAttributeArray(0)
            self.prog_blok.setAttributeBuffer(0, GL_FLOAT, 0, 3, 24)
            self.prog_blok.enableAttributeArray(1)
            self.prog_blok.setAttributeBuffer(1, GL_FLOAT, 12, 3, 24)
            # per blok: pusat, ukuran, warna -- divisor 1 artinya maju satu nilai per INSTANS
            self._vbo(A.pusat)
            self.prog_blok.enableAttributeArray(2)
            self.prog_blok.setAttributeBuffer(2, GL_FLOAT, 0, 3, 12)
            gl.glVertexAttribDivisor(2, 1)
            self._vbo(A.ukuran)
            self.prog_blok.enableAttributeArray(3)
            self.prog_blok.setAttributeBuffer(3, GL_FLOAT, 0, 3, 12)
            gl.glVertexAttribDivisor(3, 1)
            self._vbo(A.warna)
            gl.glEnableVertexAttribArray(4)
            gl.glVertexAttribPointer(4, 4, GL_UNSIGNED_BYTE, True, 4, 0)
            gl.glVertexAttribDivisor(4, 1)
            self.vao_blok.release()
        if A.garis.shape[0]:
            self.vao_garis = self._vao()
            self.vao_garis.bind()
            self._vbo(A.garis)
            self.prog_garis.enableAttributeArray(0)
            self.prog_garis.setAttributeBuffer(0, GL_FLOAT, 0, 3, 12)
            self.vao_garis.release()
            self.garis_awal = A.garis_awal
            self.garis_cacah = A.garis_cacah
        if A.topo_indeks.size:
            self.vao_topo = self._vao()
            self.vao_topo.bind()
            self._vbo(A.topo_simpul)
            self.prog_garis.enableAttributeArray(0)
            self.prog_garis.setAttributeBuffer(0, GL_FLOAT, 0, 3, 12)
            self._vbo(A.topo_indeks, indeks=True)
            self.vao_topo.release()
            self.n_topo = int(A.topo_indeks.size)

    # ---------- gambar ----------
    def gambar(self, kam: Kamera, lebar: int, tinggi: int, latar=(0.08, 0.10, 0.13, 1.0),
               topo_on: bool = True, bor_on: bool = True) -> None:
        if not self.siap:
            return
        gl = self.gl
        M = QMatrix4x4(*np.ascontiguousarray(kam.mvp(lebar, tinggi)).ravel().tolist())
        gl.glViewport(0, 0, lebar, tinggi)
        gl.glClearColor(*latar)
        gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.n_blok and self.vao_blok is not None:
            self.prog_blok.bind()
            self.prog_blok.setUniformValue(self.prog_blok.uniformLocation("mvp"), M)
            self.prog_blok.setUniformValue(self.prog_blok.uniformLocation("arahCahaya"),
                                           QVector3D(0.4, 0.6, 0.8))
            self.vao_blok.bind()
            gl.glDrawArraysInstanced(GL_TRIANGLES, 0, 36, self.n_blok)
            self.vao_blok.release()
            self.prog_blok.release()
        if topo_on and self.n_topo and self.vao_topo is not None:
            self.prog_garis.bind()
            self.prog_garis.setUniformValue(self.prog_garis.uniformLocation("mvp"), M)
            self.prog_garis.setUniformValue(self.prog_garis.uniformLocation("warnaGaris"),
                                            QVector4D(0.55, 0.58, 0.62, 1.0))
            self.vao_topo.bind()
            gl.glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            gl.glDrawElements(GL_TRIANGLES, self.n_topo, GL_UNSIGNED_INT, 0)
            gl.glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            self.vao_topo.release()
            self.prog_garis.release()
        if bor_on and self.garis_awal.size and self.vao_garis is not None:
            self.prog_garis.bind()
            self.prog_garis.setUniformValue(self.prog_garis.uniformLocation("mvp"), M)
            self.prog_garis.setUniformValue(self.prog_garis.uniformLocation("warnaGaris"),
                                            QVector4D(0.98, 0.85, 0.35, 1.0))
            self.vao_garis.bind()
            for a, c in zip(self.garis_awal.tolist(), self.garis_cacah.tolist()):
                gl.glDrawArrays(GL_LINE_STRIP, int(a), int(c))
            self.vao_garis.release()
            self.prog_garis.release()
