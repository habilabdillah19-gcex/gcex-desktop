# -*- coding: utf-8 -*-
"""Panel Reporting Block Model (Qt): pilihan laporan, tabel hasil, dan ekspor CSV.

Panel ini tidak menghitung apa pun. Angkanya datang dari `gcex_backend.laporan.run()` lewat
`qtbm/laporan_bm.py` -- mesin yang sama yang sudah dibuktikan sama dengan `rpRun()` di aplikasi
HTML. Yang ada di sini hanya kendali, tabel, dan tulisan penjelas.

Laporan dihitung HANYA ketika tombol ditekan, bukan setiap kali kendali disentuh: pada model besar
satu laporan bisa beberapa detik, dan menghitungnya otomatis setiap ketikan akan membuat panel
terasa menggantung tanpa pemakai tahu sebabnya.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional

import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from . import laporan_bm as LB
from . import tampil_bm as TB
from .proyek import BlockModel


class PanelLaporan(QWidget):
    """Reporting Block Model. `minta_saringan` dipakai untuk menanyakan blok mana yang aktif."""

    selesai = Signal()

    def __init__(self, induk=None) -> None:
        super().__init__(induk)
        self.bm: Optional[BlockModel] = None
        self.hasil: Optional[dict] = None
        self.P = LB.Pilihan()
        self.saringan_aktif = None            # callable -> larik bool, dipasang jendela
        # SG hanya boleh punya SATU sumber. Di aplikasi HTML, Reporting BM mengambil SG dari panel
        # TAMPILAN block model (BX.ui.sg / BX.ui.sgCol), bukan dari panel laporan. Jendela memasang
        # `sumber_sg` ke panel Tampilan supaya perilakunya sama; dua kotak SG terpisah akan membuat
        # orang mengisinya dua kali dan tidak tahu mana yang terhitung.
        # callable -> (sg_tetap, nama_kolom_sg) atau (sg_tetap, kolom, sg_nol, sg_ganti).
        # Bentuk 4 nilai ikut membawa perlakuan blok yang kolom SG-nya kosong / nol.
        self.sumber_sg = None

        L = QVBoxLayout(self)
        L.setContentsMargins(0, 0, 0, 0)
        L.setSpacing(6)

        G = QGridLayout()
        r = 0
        G.addWidget(QLabel("Atribut kadar (cut-off)"), r, 0)
        self.cmb_kadar = QComboBox()
        G.addWidget(self.cmb_kadar, r, 1)
        r += 1
        G.addWidget(QLabel("Cut-off"), r, 0)
        self.ed_cuts = QLineEdit("0, 0.3, 0.5, 1")
        self.ed_cuts.setToolTip("Pisahkan dengan koma. Setiap cut-off dilaporkan sebagai ≥ nilai.")
        G.addWidget(self.ed_cuts, r, 1)
        r += 1
        G.addWidget(QLabel("Kelompokkan"), r, 0)
        self.cmb_grup = QComboBox()
        self.cmb_grup.addItem("Total saja", "none")
        self.cmb_grup.addItem("Per RL (bench / flitch)", "bench")
        self.cmb_grup.addItem("Per atribut kategori", "cat")
        self.cmb_grup.currentIndexChanged.connect(self._grup_berubah)
        G.addWidget(self.cmb_grup, r, 1)
        r += 1
        self.lbl_grup_attr = QLabel("Atribut kategori")
        self.cmb_grup_attr = QComboBox()
        G.addWidget(self.lbl_grup_attr, r, 0)
        G.addWidget(self.cmb_grup_attr, r, 1)
        r += 1
        self.lbl_bh = QLabel("Tinggi bench (m) / RL acuan")
        baris_bh = QHBoxLayout()
        self.spn_bh = QDoubleSpinBox()
        self.spn_bh.setRange(0.1, 1000.0)
        self.spn_bh.setValue(5.0)
        self.spn_br = QDoubleSpinBox()
        self.spn_br.setRange(-10000.0, 10000.0)
        self.spn_br.setDecimals(2)
        baris_bh.addWidget(self.spn_bh)
        baris_bh.addWidget(self.spn_br)
        G.addWidget(self.lbl_bh, r, 0)
        G.addLayout(baris_bh, r, 1)
        r += 1
        self.lbl_sg = QLabel("SG tetap / kolom SG")
        G.addWidget(self.lbl_sg, r, 0)
        baris_sg = QHBoxLayout()
        self.spn_sg = QDoubleSpinBox()
        self.spn_sg.setRange(0.1, 20.0)
        self.spn_sg.setDecimals(3)
        self.spn_sg.setValue(2.6)
        self.cmb_sg = QComboBox()
        baris_sg.addWidget(self.spn_sg)
        baris_sg.addWidget(self.cmb_sg, 1)
        G.addWidget(baris_sg_w := QWidget(), r, 1)
        baris_sg_w.setLayout(baris_sg)
        L.addLayout(G)

        L.addWidget(QLabel("Atribut yang dilaporkan kadarnya"))
        self.daftar_att = QListWidget()
        self.daftar_att.setSelectionMode(QAbstractItemView.NoSelection)
        self.daftar_att.setMaximumHeight(110)
        L.addWidget(self.daftar_att)

        self.cb_rl = QCheckBox("Batasi ke rentang RL / saringan tampilan yang aktif")
        self.cb_rl.setToolTip("Memakai saringan yang sama dengan yang sedang tampil di layar "
                              "(batas RL dan sayatan), supaya laporan dan gambar sejalan.")
        L.addWidget(self.cb_rl)
        self.cb_banding = QCheckBox("Bandingkan metode tonase (presisi GC-Ex vs seperti Surpac)")
        L.addWidget(self.cb_banding)

        baris_t = QHBoxLayout()
        self.b_hitung = QPushButton("↻ Hitung laporan")
        self.b_hitung.clicked.connect(self.hitung)
        self.b_csv = QPushButton("↓ Export CSV")
        self.b_csv.setEnabled(False)
        self.b_csv.clicked.connect(self.ekspor)
        baris_t.addWidget(self.b_hitung, 2)
        baris_t.addWidget(self.b_csv, 1)
        L.addLayout(baris_t)

        baris_g = QHBoxLayout()
        baris_g.addWidget(QLabel("Tampilkan"))
        self.cmb_lihat = QComboBox()
        self.cmb_lihat.currentIndexChanged.connect(self._gambar_tabel)
        baris_g.addWidget(self.cmb_lihat, 1)
        L.addLayout(baris_g)

        self.tabel = QTableWidget(0, 0)
        self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        L.addWidget(self.tabel, 1)

        self.pesan = QLabel("")
        self.pesan.setWordWrap(True)
        self.pesan.setStyleSheet("color:#8a93a6")
        L.addWidget(self.pesan)

        self._grup_berubah()

    # ------------------------------------------------------------------ data
    def pasang_model(self, bm: Optional[BlockModel]) -> None:
        self.bm = bm
        self.hasil = None
        self.b_csv.setEnabled(False)
        self.tabel.clear()
        self.tabel.setRowCount(0)
        self.tabel.setColumnCount(0)
        self.cmb_lihat.clear()
        for c in (self.cmb_kadar, self.cmb_grup_attr, self.cmb_sg):
            c.blockSignals(True)
            c.clear()
        self.daftar_att.clear()
        if bm is not None and bm.n:
            self.cmb_sg.addItem("(pakai SG tetap)", "")
            for a in bm.angka:
                self.cmb_kadar.addItem(a)
                self.cmb_sg.addItem(a, a)
                it = QListWidgetItem(a)
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                it.setCheckState(Qt.Unchecked)
                self.daftar_att.addItem(it)
            for a in bm.kategori:
                self.cmb_grup_attr.addItem(a, a)
            # atribut kadar bawaan: sama dengan panel tampilan (AU lebih dulu)
            awal = TB.ui_awal(bm).atribut
            if awal and awal in bm.angka:
                self.cmb_kadar.setCurrentText(awal)
                for i in range(self.daftar_att.count()):
                    if self.daftar_att.item(i).text() == awal:
                        self.daftar_att.item(i).setCheckState(Qt.Checked)
            # Kolom SG TIDAK dipilih otomatis, walaupun ada atribut bernama SG: aplikasi HTML pun
            # bawaannya memakai SG tetap (bxDefUI menyetel sgCol kosong). Memilihnya otomatis di
            # sini akan membuat tonase bawaan kedua aplikasi berbeda untuk model yang sama.
            k = bm.kotak()
            self.spn_br.setValue(round(k[5], 2))      # RL acuan = puncak model
        for c in (self.cmb_kadar, self.cmb_grup_attr, self.cmb_sg):
            c.blockSignals(False)
        self.pesan.setText("" if (bm is not None and bm.n) else "Belum ada block model.")
        self.segarkan_sg()
        self._grup_berubah()

    def segarkan_sg(self) -> None:
        """Tampilkan SG yang BERLAKU (dari panel Tampilan) dan matikan kotaknya di sini."""
        if not callable(self.sumber_sg):
            return
        sg, kolom = self._sg_berlaku()[:2]
        self.spn_sg.blockSignals(True)
        self.cmb_sg.blockSignals(True)
        self.spn_sg.setValue(float(sg))
        i = self.cmb_sg.findData(kolom or "")
        if i >= 0:
            self.cmb_sg.setCurrentIndex(i)
        self.spn_sg.setEnabled(False)
        self.cmb_sg.setEnabled(False)
        self.lbl_sg.setText("SG (dari panel Tampilan)")
        self.lbl_sg.setToolTip("SG diatur di panel Tampilan supaya laporan dan gambar memakai "
                               "angka yang sama — persis seperti di aplikasi HTML.")
        self.spn_sg.blockSignals(False)
        self.cmb_sg.blockSignals(False)

    def _sg_berlaku(self):
        """(sg, kolom, sg_nol, sg_ganti) dari panel Tampilan; bentuk lama (2 nilai) tetap jalan."""
        v = tuple(self.sumber_sg())
        if len(v) >= 4:
            return float(v[0]), (v[1] or ""), (v[2] or ""), (v[3] or "")
        return float(v[0]), (v[1] or ""), "", ""

    def _grup_berubah(self) -> None:
        g = self.cmb_grup.currentData() or "none"
        for w in (self.lbl_grup_attr, self.cmb_grup_attr):
            w.setVisible(g == "cat")
        for w in (self.lbl_bh, self.spn_bh, self.spn_br):
            w.setVisible(g == "bench")

    def _att_tercentang(self) -> List[str]:
        return [self.daftar_att.item(i).text() for i in range(self.daftar_att.count())
                if self.daftar_att.item(i).checkState() == Qt.Checked]

    def _pilihan(self) -> LB.Pilihan:
        P = LB.Pilihan()
        P.kadar = self.cmb_kadar.currentText()
        P.cuts = TB.batas_dari_teks(self.ed_cuts.text()) or [0.0]
        P.atribut = self._att_tercentang() or ([P.kadar] if P.kadar else [])
        P.grup = self.cmb_grup.currentData() or "none"
        P.grup_atribut = self.cmb_grup_attr.currentData() or ""
        P.tinggi_bench = float(self.spn_bh.value())
        P.rl_acuan = float(self.spn_br.value())
        if callable(self.sumber_sg):
            sg, kolom, nol, ganti = self._sg_berlaku()
            P.sg, P.sg_kolom = float(sg), (kolom or "")
            P.sg_nol, P.sg_ganti = nol, ganti
        else:
            P.sg = float(self.spn_sg.value())
            P.sg_kolom = self.cmb_sg.currentData() or ""
        P.bandingkan = self.cb_banding.isChecked()
        return P

    # ------------------------------------------------------------------ hitung
    def hitung(self) -> None:
        # Tidak ada kotak dialog di jalur hitung: pesannya ditulis di panel. Selain lebih tenang
        # dipakai, dialog modal di sini membuat jalur ini tidak bisa diuji otomatis sama sekali
        # (uji akan menggantung menunggu seseorang menekan OK).
        if self.bm is None or not self.bm.n:
            self.pesan.setText("Belum ada block model. Muat block model dulu (CSV atau .mdl).")
            return
        self.P = self._pilihan()
        pakai = None
        if self.cb_rl.isChecked() and callable(self.saringan_aktif):
            pakai = self.saringan_aktif()
        self.b_hitung.setEnabled(False)
        self.pesan.setText("menghitung...")
        try:
            t0 = time.perf_counter()
            self.hasil = LB.jalankan(self.bm, self.P, pakai)
            ms = (time.perf_counter() - t0) * 1000
        except Exception as e:
            self.hasil = None
            self.b_csv.setEnabled(False)
            self.pesan.setText("Laporan gagal: %s" % e)
            return
        finally:
            self.b_hitung.setEnabled(True)
        self._isi_pilihan_lihat()
        self._gambar_tabel()
        n_blok = int(pakai.sum()) if pakai is not None else self.bm.n
        bagian = ["%s blok dihitung dalam %.0f ms." % (LB._ribu(n_blok), ms)]
        for nama, jml in LB.alasan_terbuang(self.hasil):
            bagian.append("%s blok %s." % (LB._ribu(jml), nama))
        bagian += LB.catatan(self.bm, self.hasil)
        self.pesan.setText(" ".join(bagian))
        self.b_csv.setEnabled(True)
        self.selesai.emit()

    def _isi_pilihan_lihat(self) -> None:
        self.cmb_lihat.blockSignals(True)
        self.cmb_lihat.clear()
        self.cmb_lihat.addItem("Total", None)
        if self.hasil and (self.P.grup or "none") != "none":
            for g in LB.daftar_grup(self.hasil):
                self.cmb_lihat.addItem(LB.label_grup(self.hasil, g, self.P), g)
        self.cmb_lihat.blockSignals(False)

    def _gambar_tabel(self) -> None:
        if not self.hasil:
            return
        grup = self.cmb_lihat.currentData()
        judul, baris = LB.tabel(self.hasil, grup, self.P)
        self.tabel.clear()
        self.tabel.setColumnCount(len(judul))
        self.tabel.setHorizontalHeaderLabels(judul)
        self.tabel.setRowCount(len(baris))
        for i, b in enumerate(baris):
            for j, teks in enumerate(b):
                it = QTableWidgetItem(teks)
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter if j else
                                    Qt.AlignLeft | Qt.AlignVCenter)
                if b[1:2] == ["Selisih"]:
                    f = it.font()
                    f.setItalic(True)
                    it.setFont(f)
                self.tabel.setItem(i, j, it)

    def ekspor(self) -> None:
        if not self.hasil:
            return
        f, _ = QFileDialog.getSaveFileName(self, "Simpan laporan CSV",
                                           "laporan_block_model.csv", "CSV (*.csv)")
        if not f:
            return
        grup = self.cmb_lihat.currentData()
        try:
            Path(f).write_text(LB.csv(self.hasil, grup), encoding="utf-8-sig")
        except OSError as e:
            QMessageBox.warning(self, "Gagal menyimpan", str(e))
            return
        self.pesan.setText("CSV disimpan: %s" % f)
