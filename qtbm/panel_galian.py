# -*- coding: utf-8 -*-
"""Panel Dig block: flitch, metode tonase, digitasi, daftar string, dan ekspor DXF/STR.

Panel ini TIDAK menghitung apa pun sendiri. Angka tonase & kadar datang dari `qtbm/galian.py`
(yang sudah dibuktikan sama dengan `lyTon`/`lyTonS` aplikasi HTML), warna blok dari
`qtbm/tampil_bm.py`, dan SG dari panel Tampilan lewat `sumber_sg` -- satu sumber, seperti di
panel Laporan. Dua kotak SG terpisah akan membuat dua tonase yang berbeda dan tak ada yang tahu
mana yang terhitung.

TIDAK ADA DIALOG MODAL di jalur hitung. Pesan apa pun masuk ke label `self.pesan`. Dialog modal
membuat uji otomatis (yang berjalan tanpa layar) menggantung selamanya, dan pernah terjadi.
"""
from __future__ import annotations

import math
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QSpinBox, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from . import galian as GA
from . import string_io as SIO
from . import tampil_bm as TB
from .proyek import BlockModel


class PanelGalian(QWidget):
    """Panel Dig block. `kanvas` dipasang dari jendela utama."""

    berubah = Signal()                    # minta kanvas / viewport digambar ulang

    def __init__(self, induk=None) -> None:
        super().__init__(induk)
        self.bm: Optional[BlockModel] = None
        self.T: Optional[TB.Tampilan] = None
        self.kanvas = None                            # Kanvas2D, dipasang dari jendela
        self.sumber_sg: Optional[Callable] = None     # -> (sg, kolom, sg_nol, sg_ganti)
        self.strings: List[SIO.String] = []
        self._sudah_diekspor = False
        self._hasil = None

        L = QVBoxLayout(self)
        L.setContentsMargins(8, 8, 8, 8)
        L.setSpacing(8)

        # ---------- flitch ----------
        gb = QGroupBox("Flitch (bidang galian)")
        f = QFormLayout(gb)
        self.spn_atas = QDoubleSpinBox()
        self.spn_atas.setRange(-1e6, 1e6)
        self.spn_atas.setDecimals(3)
        self.spn_bawah = QDoubleSpinBox()
        self.spn_bawah.setRange(-1e6, 1e6)
        self.spn_bawah.setDecimals(3)
        f.addRow("RL atas", self.spn_atas)
        f.addRow("RL bawah", self.spn_bawah)
        self.cmb_flmode = QComboBox()
        self.cmb_flmode.addItem("Tumpang tindih sebenarnya (composite)", "comp")
        self.cmb_flmode.addItem("Hanya blok di bidang tengah (setebal flitch)", "mid")
        f.addRow("Cara ambil blok", self.cmb_flmode)
        self.btn_turun = QPushButton("Flitch berikut ke bawah")
        f.addRow(self.btn_turun)
        L.addWidget(gb)

        # ---------- perhitungan ----------
        gb2 = QGroupBox("Perhitungan")
        f2 = QFormLayout(gb2)
        self.cmb_kadar = QComboBox()
        f2.addRow("Atribut kadar", self.cmb_kadar)
        self.cmb_metode = QComboBox()
        self.cmb_metode.addItem("Presisi GC-Ex (blok dipotong di garis)", "clip")
        self.cmb_metode.addItem("Seperti Surpac (blok utuh, titik tengah)", "surpac")
        f2.addRow("Metode tonase", self.cmb_metode)
        # Keputusan pemilik: selisih kedua metode TIDAK ditampilkan secara bawaan. Pilihannya
        # tetap ada untuk dipakai saat angka perlu dicocokkan dengan Surpac, tetapi mati kecuali
        # diminta. Catatan untuk sesi berikutnya: selisih ini bersifat GEOMETRIS (blok dipotong di
        # garis poligon vs blok utuh bila titik tengahnya di dalam), jadi ia ADA walaupun block
        # model tanpa `sb_frac` -- pada uji paritas 0,1% sampai 17,9% tergantung posisi garis
        # poligon terhadap grid blok. Jangan menyalakannya kembali tanpa diminta pemilik.
        self.cb_banding = QCheckBox("Tampilkan juga angka metode satunya (pembanding Surpac)")
        self.cb_banding.setChecked(False)
        f2.addRow(self.cb_banding)
        self.cb_lolos = QCheckBox("Hanya blok yang lolos cut-off tampilan")
        f2.addRow(self.cb_lolos)
        self.lbl_sg = QLabel("SG")
        self.lbl_sg_nilai = QLabel("—")
        f2.addRow(self.lbl_sg, self.lbl_sg_nilai)
        L.addWidget(gb2)

        # ---------- waste pengisi ----------
        gb3 = QGroupBox("Waste pengisi (dilusi luas tanpa blok)")
        f3 = QFormLayout(gb3)
        self.cb_waste = QCheckBox("Tambahkan waste pengisi")
        self.cb_waste.setChecked(True)          # sama dengan bawaan aplikasi HTML (dbU: wOn=true)
        f3.addRow(self.cb_waste)
        self.spn_wsg = QDoubleSpinBox()
        self.spn_wsg.setRange(0.0, 20.0)
        self.spn_wsg.setDecimals(3)
        self.spn_wsg.setSpecialValueText("ikut SG panel Tampilan")
        f3.addRow("SG waste", self.spn_wsg)
        self.spn_wg = QDoubleSpinBox()
        self.spn_wg.setRange(0.0, 1e6)
        self.spn_wg.setDecimals(4)
        f3.addRow("Kadar waste", self.spn_wg)
        self.lbl_waste_nb = QLabel("Hanya berlaku pada metode presisi — aplikasi HTML pun tidak "
                                   "menambahkannya pada metode Surpac.")
        self.lbl_waste_nb.setWordWrap(True)
        self.lbl_waste_nb.setStyleSheet("color:#8b97a8")
        f3.addRow(self.lbl_waste_nb)
        L.addWidget(gb3)

        # ---------- digitasi ----------
        gb4 = QGroupBox("Digitasi poligon")
        v4 = QVBoxLayout(gb4)
        b1 = QHBoxLayout()
        self.btn_mulai = QPushButton("Mulai digit")
        # BUKAN "Tutup & simpan": yang terjadi hanyalah poligon ditutup dan masuk daftar di
        # panel ini. Belum ada apa pun yang tersimpan ke berkas, dan string akan HILANG saat
        # jendela ditutup. Label "simpan" di sini pernah ada dan itu menyesatkan: pemakai yang
        # mendigit 20 dig block lalu menutup aplikasi kehilangan satu shift pekerjaan sambil
        # yakin sudah menyimpannya.
        self.btn_tutup = QPushButton("Tutup poligon")
        self.btn_urung = QPushButton("Urung titik")
        self.btn_batal = QPushButton("Batal")
        for b in (self.btn_mulai, self.btn_tutup, self.btn_urung, self.btn_batal):
            b1.addWidget(b)
        v4.addLayout(b1)
        f4 = QFormLayout()
        self.spn_no = QSpinBox()
        self.spn_no.setRange(1, 999999)
        self.spn_no.setValue(1)
        f4.addRow("No. string", self.spn_no)
        self.ed_ket = QLineEdit("ORE")
        f4.addRow("Keterangan", self.ed_ket)
        self.cb_snap = QCheckBox("Tempel ke sudut blok")
        self.cb_snap.setChecked(True)
        f4.addRow(self.cb_snap)
        v4.addLayout(f4)
        self.lbl_hidup = QLabel("—")
        self.lbl_hidup.setWordWrap(True)
        v4.addWidget(self.lbl_hidup)
        L.addWidget(gb4)

        # ---------- daftar string ----------
        gb5 = QGroupBox("String di sesi ini (belum tersimpan ke berkas)")
        v5 = QVBoxLayout(gb5)
        self.tabel = QTableWidget(0, 5)
        self.tabel.setHorizontalHeaderLabels(["No", "Ket.", "Titik", "Luas m²", "Tonase t"])
        self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel.setMinimumHeight(120)
        v5.addWidget(self.tabel)
        b5 = QHBoxLayout()
        self.btn_hitung = QPushButton("Hitung ulang")
        self.btn_hapus = QPushButton("Hapus terpilih")
        self.btn_dxf = QPushButton("Ekspor DXF…")
        self.btn_str = QPushButton("Ekspor STR…")
        for b in (self.btn_hitung, self.btn_hapus, self.btn_dxf, self.btn_str):
            b5.addWidget(b)
        v5.addLayout(b5)
        L.addWidget(gb5)

        self.pesan = QLabel("")
        self.pesan.setWordWrap(True)
        self.pesan.setStyleSheet("color:#ffd92f")
        L.addWidget(self.pesan)
        self.peringatan_simpan = QLabel(
            "⚠ String hanya ada selama jendela terbuka. Belum ada penyimpanan ke folder proyek — "
            "ekspor ke DXF / STR dulu sebelum menutup aplikasi, atau pekerjaannya hilang.")
        self.peringatan_simpan.setWordWrap(True)
        self.peringatan_simpan.setStyleSheet("color:#fc8d59")
        self.peringatan_simpan.setVisible(False)
        L.addWidget(self.peringatan_simpan)
        self.catatan = QLabel("")
        self.catatan.setWordWrap(True)
        self.catatan.setStyleSheet("color:#8b97a8")
        L.addWidget(self.catatan)
        L.addStretch(1)

        # ---------- sambungan ----------
        self.spn_atas.valueChanged.connect(self._flitch_berubah)
        self.spn_bawah.valueChanged.connect(self._flitch_berubah)
        self.cmb_flmode.currentIndexChanged.connect(self._flitch_berubah)
        self.btn_turun.clicked.connect(self.flitch_turun)
        self.btn_mulai.clicked.connect(self.mulai)
        self.btn_tutup.clicked.connect(self.tutup)
        self.btn_urung.clicked.connect(lambda: self.kanvas and self.kanvas.urungkan())
        self.btn_batal.clicked.connect(self.batal)
        self.btn_hitung.clicked.connect(self.hitung_semua)
        self.btn_hapus.clicked.connect(self.hapus_terpilih)
        self.btn_dxf.clicked.connect(lambda: self.ekspor("dxf"))
        self.btn_str.clicked.connect(lambda: self.ekspor("str"))
        self.cb_snap.toggled.connect(self._snap_berubah)
        for w in (self.cmb_kadar, self.cmb_metode):
            w.currentIndexChanged.connect(self.hitung_semua)
        for w in (self.cb_banding, self.cb_lolos, self.cb_waste):
            w.toggled.connect(self.hitung_semua)
        for w in (self.spn_wsg, self.spn_wg):
            w.valueChanged.connect(self.hitung_semua)

    # ---------------------------------------------------------------- model

    def pasang_kanvas(self, kanvas) -> None:
        self.kanvas = kanvas
        kanvas.titik_ditambah.connect(self._hidup)
        kanvas.poligon_selesai.connect(self._simpan_dari_kanvas)
        self._snap_berubah(self.cb_snap.isChecked())

    def pasang_model(self, bm: Optional[BlockModel], T: Optional[TB.Tampilan]) -> None:
        self.bm = bm
        self.T = T
        self.cmb_kadar.blockSignals(True)
        self.cmb_kadar.clear()
        if bm is not None:
            for a in sorted(bm.angka):
                self.cmb_kadar.addItem(a)
            pilih = (T.atribut if (T and T.atribut in bm.angka) else None)
            if pilih is None:
                au = [a for a in sorted(bm.angka) if a.upper().startswith("AU")]
                pilih = au[0] if au else (sorted(bm.angka)[0] if bm.angka else None)
            if pilih:
                self.cmb_kadar.setCurrentText(pilih)
        self.cmb_kadar.blockSignals(False)
        if bm is not None and bm.n:
            _x0, _x1, _y0, _y1, z0, z1 = bm.kotak()
            tebal = float(min(bm.sz)) if len(bm.sz) else 2.5
            self.spn_atas.blockSignals(True)
            self.spn_bawah.blockSignals(True)
            self.spn_atas.setValue(round(z1, 3))
            self.spn_bawah.setValue(round(z1 - tebal, 3))
            self.spn_atas.blockSignals(False)
            self.spn_bawah.blockSignals(False)
        self.segarkan_sg()
        self._flitch_berubah()

    def segarkan_sg(self) -> None:
        """Tampilkan SG yang BERLAKU (dari panel Tampilan); tidak ada kotak SG di panel ini."""
        sg, kolom, nol, ganti = self._sg_berlaku()
        if kolom:
            t = "kolom %s" % kolom
            if nol == "zero":
                t += ", tidak sah → tonase 0"
            elif ganti:
                t += ", tidak sah → %s" % ganti
            else:
                t += ", tidak sah → %.3g" % sg
        else:
            t = "%.3g (tetap)" % sg
        self.lbl_sg_nilai.setText(t)
        self.lbl_sg.setText("SG (dari panel Tampilan)")
        self.lbl_sg.setToolTip("SG diatur di panel Tampilan supaya dig block, laporan dan gambar "
                               "memakai angka yang sama — persis seperti di aplikasi HTML.")

    def _sg_berlaku(self) -> Tuple[float, str, str, str]:
        if callable(self.sumber_sg):
            v = tuple(self.sumber_sg())
            if len(v) >= 4:
                return float(v[0]), (v[1] or ""), (v[2] or ""), (v[3] or "")
            return float(v[0]), (v[1] or ""), "", ""
        if self.T is not None:
            return float(self.T.sg), self.T.sg_kolom, self.T.sg_nol, self.T.sg_ganti
        return 2.6, "", "", ""

    # ---------------------------------------------------------------- flitch

    def _tampilan_sg(self) -> TB.Tampilan:
        """Tampilan yang dipakai hitung: SG selalu dari sumber tunggal, bukan salinan basi."""
        T = self.T if self.T is not None else TB.Tampilan()
        sg, kolom, nol, ganti = self._sg_berlaku()
        T.sg, T.sg_kolom, T.sg_nol, T.sg_ganti = sg, kolom, nol, ganti
        return T

    def opsi(self) -> GA.Opsi:
        return GA.Opsi(
            rl_atas=float(self.spn_atas.value()),
            rl_bawah=float(self.spn_bawah.value()),
            kadar=self.cmb_kadar.currentText(),
            metode=self.cmb_metode.currentData() or "clip",
            mode_flitch=self.cmb_flmode.currentData() or "comp",
            hanya_lolos=self.cb_lolos.isChecked(),
            waste_on=self.cb_waste.isChecked(),
            waste_sg=float(self.spn_wsg.value()),
            waste_kadar=float(self.spn_wg.value()))

    def _flitch_berubah(self, *a) -> None:
        if self.kanvas is not None:
            self.kanvas.set_flitch(self.spn_atas.value(), self.spn_bawah.value(),
                                   self.cmb_flmode.currentData() or "comp")
        self.segarkan_sg()
        self.hitung_semua()
        self.berubah.emit()

    def flitch_turun(self) -> None:
        tebal = abs(self.spn_atas.value() - self.spn_bawah.value()) or 2.5
        self.spn_atas.blockSignals(True)
        self.spn_atas.setValue(self.spn_atas.value() - tebal)
        self.spn_atas.blockSignals(False)
        self.spn_bawah.setValue(self.spn_bawah.value() - tebal)   # ini yang memicu _flitch_berubah

    def _snap_berubah(self, on: bool) -> None:
        if self.kanvas is not None:
            self.kanvas.snap = bool(on)

    # ---------------------------------------------------------------- digitasi

    def mulai(self) -> None:
        if self.bm is None or not self.bm.n:
            self.pesan.setText("Muat block model dulu.")
            return
        if abs(self.spn_atas.value() - self.spn_bawah.value()) < 1e-9:
            self.pesan.setText("RL atas dan RL bawah sama: tinggi flitch nol, tidak ada yang "
                               "bisa dihitung.")
            return
        self.pesan.setText("")
        if self.kanvas is not None:
            self.kanvas.mulai()
            self.kanvas.setFocus()

    def batal(self) -> None:
        if self.kanvas is not None:
            self.kanvas.batal()
        self.lbl_hidup.setText("—")

    def tutup(self) -> None:
        if self.kanvas is None:
            return
        if not self.kanvas.tutup():
            self.pesan.setText("Poligon tertutup butuh minimal 3 titik.")

    def _simpan_dari_kanvas(self) -> None:
        P = self.kanvas.poligon() if self.kanvas else []
        if len(P) < 3:
            return
        z = GA.zs_flitch(GA.bench(self.spn_atas.value(), self.spn_bawah.value()))
        s = SIO.String(no=int(self.spn_no.value()), ket=self.ed_ket.text().strip(),
                       tertutup=True, pts=[(x, y, z) for x, y in P],
                       warna=SIO.String().warna if not self.strings else
                       ["#e8590c", "#2f9e44", "#1971c2", "#c2255c", "#7048e8", "#0c8599",
                        "#f08c00", "#5c940d"][len(self.strings) % 8])
        self.strings.append(s)
        self._sudah_diekspor = False
        self.spn_no.setValue(int(self.spn_no.value()) + 1)
        if self.kanvas is not None:
            self.kanvas.strings = self.strings
            self.kanvas.titik = []
            self.kanvas.update()
        self.pesan.setText("")
        self.hitung_semua()
        self.berubah.emit()

    def _hidup(self) -> None:
        """Tonase sementara selagi mendigit, supaya pemakai tahu sebelum menutup poligon."""
        if self.kanvas is None or self.bm is None:
            return
        P = self.kanvas.poligon()
        if len(P) < 3:
            self.lbl_hidup.setText("%d titik — klik minimal 3 titik" % len(P))
            return
        O = self.opsi()
        banding = self.cb_banding.isChecked()
        try:
            if banding:
                D = GA.bandingkan(self.bm, P, self._tampilan_sg(), O)
            else:
                D = {O.metode: GA.tonase(self.bm, P, self._tampilan_sg(), O)}
        except Exception as e:                      # noqa: BLE001
            self.lbl_hidup.setText("belum bisa dihitung: %s" % e)
            return
        H = D[O.metode]
        kadar = ("%.3f" % H.kadar) if math.isfinite(H.kadar) else "—"
        teks = ("%d titik · %.1f m² · <b>%s t @ %s</b> · blok menutup %d%%"
                % (len(P), H.luas_poligon, _ribuan(H.t), kadar, round(H.cov * 100)))
        if banding:
            lain = D["surpac" if O.metode == "clip" else "clip"]
            beda = ("%+.1f%%" % ((H.t - lain.t) / lain.t * 100.0)) if lain.t else "—"
            teks += (" · %s: <b>%s t</b> (%s)"
                     % (GA.NAMA_METODE.get(lain.metode, lain.metode), _ribuan(lain.t), beda))
        self.lbl_hidup.setText(teks)

    # ---------------------------------------------------------------- hitung

    def ada_belum_diekspor(self) -> bool:
        """True bila ada string yang akan hilang kalau jendela ditutup sekarang."""
        return bool(self.strings) and not self._sudah_diekspor

    def hitung_semua(self, *a) -> None:
        self.peringatan_simpan.setVisible(self.ada_belum_diekspor())
        self.tabel.setRowCount(0)
        self.catatan.setText("")
        if self.bm is None or not self.bm.n or not self.strings:
            return
        T = self._tampilan_sg()
        O = self.opsi()
        banding = self.cb_banding.isChecked()
        kolom = ["No", "Ket.", "Titik", "Luas m²"]
        if banding:
            kolom += ["Presisi t", "Surpac t", "Selisih %", "Kadar", "Blok %"]
        else:
            kolom += ["Tonase t", "Kadar", "Logam", "Blok %"]
        self.tabel.setColumnCount(len(kolom))
        self.tabel.setHorizontalHeaderLabels(kolom)
        semua_catatan: List[str] = []
        for s in self.strings:
            P = s.xy()
            if len(P) < 3:
                continue
            try:
                if banding:
                    H = GA.bandingkan(self.bm, P, T, O)
                else:
                    H = {O.metode: GA.tonase(self.bm, P, T, O)}
            except Exception as e:                  # noqa: BLE001
                self._baris(s, ["gagal: %s" % e])
                continue
            utama = H[O.metode]
            kadar = ("%.3f" % utama.kadar) if math.isfinite(utama.kadar) else "—"
            if banding:
                a_, b_ = H["clip"].t, H["surpac"].t
                sel = ("%+.2f" % ((a_ - b_) / b_ * 100.0)) if b_ else "—"
                nilai = [_ribuan(a_), _ribuan(b_), sel, kadar,
                         "%d" % round(utama.cov * 100)]
            else:
                nilai = [_ribuan(utama.t), kadar, _ribuan(utama.logam),
                         "%d" % round(utama.cov * 100)]
            self._baris(s, nilai)
            for c in GA.catatan(self.bm, H, O):
                if c not in semua_catatan:
                    semua_catatan.append(c)
        self.tabel.resizeColumnsToContents()
        if semua_catatan:
            self.catatan.setText("⚠ " + "\n⚠ ".join(semua_catatan))

    def _baris(self, s: SIO.String, nilai: List[str]) -> None:
        r = self.tabel.rowCount()
        self.tabel.insertRow(r)
        awal = [str(s.no), s.ket or "—", str(len(s.pts)), "%.1f" % GA.luas(s.xy())]
        for c, v in enumerate(awal + nilai):
            if c < self.tabel.columnCount():
                self.tabel.setItem(r, c, QTableWidgetItem(v))

    def hapus_terpilih(self) -> None:
        baris = sorted({i.row() for i in self.tabel.selectedIndexes()}, reverse=True)
        if not baris:
            self.pesan.setText("Pilih dulu baris string yang mau dihapus.")
            return
        for r in baris:
            if 0 <= r < len(self.strings):
                self.strings.pop(r)
        if self.kanvas is not None:
            self.kanvas.strings = self.strings
            self.kanvas.update()
        self.pesan.setText("")
        self.hitung_semua()
        self.berubah.emit()

    # ---------------------------------------------------------------- ekspor

    def ekspor(self, fmt: str) -> None:
        tampil = [s for s in self.strings if s.tampil]
        if not tampil:
            self.pesan.setText("Belum ada string untuk diekspor.")
            return
        nama = "String_%s.%s" % ((self.bm.nama or "GCEX").replace(" ", "_") if self.bm
                                 else "GCEX", fmt)
        jalur, _ = QFileDialog.getSaveFileName(
            self, "Ekspor %s" % fmt.upper(), nama,
            "Surpac string (*.str)" if fmt == "str" else "DXF (*.dxf)")
        if not jalur:
            return
        try:
            SIO.tulis(jalur, tampil, (self.bm.nama if self.bm else "GCEX") or "GCEX")
        except Exception as e:                      # noqa: BLE001
            self.pesan.setText("Ekspor gagal: %s" % e)
            return
        self._sudah_diekspor = True
        self.peringatan_simpan.setVisible(False)
        self.pesan.setText("Tersimpan: %s (%d string, koordinat penuh)" % (jalur, len(tampil)))


def _ribuan(v: float) -> str:
    if not math.isfinite(v):
        return "—"
    return "{:,.2f}".format(v).replace(",", " ")
