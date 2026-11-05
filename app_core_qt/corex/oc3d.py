"""Model 3D (fotogrametri) dinding singkapan — jendela kerja dari ruang kerja Singkapan (DB-Ex versi Qt).

Kiri: foto model (3–100; drone 50+). Tengah: foto terpilih (klik titik cat RTK / titik pengukuran). Kanan: tab Titik RTK (tabel Nama, E,
N, RL — tempel dari Excel / CSV, deteksi titik cat otomatis, galat per titik), Ukur bidang (dip / arah dip / strike
sebenarnya dari titik yang diklik di sepanjang jejak / di satu bidang tersingkap) dan Tampilan (denah & tampak awan titik,
ekspor CSV / STR / PLY). Backend: /core/outcrop/m3d/* (core_oc3d)."""
from __future__ import annotations

import base64
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QGraphicsObject, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout,
                               QWidget)

from . import api, oc_paint, theme
from .card import _esc, btn
from .dialogs import Dlg, ask, say
from .util import SET, log, run_bg, show_in_folder

KINDS = [("vein", "Vein"), ("kekar", "Kekar"), ("sesar", "Sesar"), ("kontak", "Kontak"), ("lain", "Lain")]
QCOL = {"baik": "#2f9e44", "sedang": "#B7791F", "lemah": "#C0392B", "tidak pasti": "#C0392B"}


class Overlay(QGraphicsObject):
    """Lapisan di atas foto: titik RTK yang sudah diklik, usulan titik cat, titik pengukuran (draf & tersimpan)."""

    def __init__(self, dlg: "Model3DDialog"):
        super().__init__(dlg.view.root)
        self.d = dlg
        self.setZValue(5)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self) -> QRectF:  # noqa: N802
        v = self.d.view
        return QRectF(0, 0, max(1.0, v.w), max(1.0, v.h))

    def paint(self, p: QPainter, opt, w=None) -> None:
        d, v = self.d, self.d.view
        if not v.w or d.img is None or not d.m:
            return
        f = QFont(theme.SANS)
        f.setPixelSize(max(1, int(v.px(12))))
        f.setBold(True)
        p.setFont(f)
        r = v.px(9)
        for t in d.targets:
            c = QPointF(t["u"] * v.w, t["v"] * v.h)
            p.setPen(QPen(QColor("#15aabf"), v.px(2), Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(c, r * 1.6, r * 1.6)
        sel = d.gcp_row()
        for k, g in enumerate(d.gcps):
            uv = (g.get("obs") or {}).get(str(d.img))
            if not uv:
                continue
            c = QPointF(uv[0] * v.w, uv[1] * v.h)
            col = QColor("#ffd400") if k == sel else QColor("#e64980")
            for wd, cc in ((v.px(4.5), QColor(255, 255, 255, 230)), (v.px(2), col)):
                p.setPen(QPen(cc, wd))
                p.drawLine(QPointF(c.x() - r * 1.6, c.y()), QPointF(c.x() + r * 1.6, c.y()))
                p.drawLine(QPointF(c.x(), c.y() - r * 1.6), QPointF(c.x(), c.y() + r * 1.6))
            p.setPen(QPen(col, v.px(2)))
            p.drawText(QPointF(c.x() + r * 1.4, c.y() - r * 1.2), g["name"])
        for me in d.m.get("measures") or []:
            if me["img"] != d.img:
                continue
            self._poly(p, v, me["pts"], QColor("#C0392B"), me["name"] + self._res(me))
        if d.draft:
            self._poly(p, v, d.draft, QColor("#ffd400"), "")

    @staticmethod
    def _res(me: dict) -> str:
        r = me.get("result") or {}
        return f"  {r['dip']:.0f}/{r['ddir']:03.0f}" if r and not r.get("error") else ""

    def _poly(self, p, v, pts, col, label) -> None:
        P = [QPointF(u * v.w, w_ * v.h) for u, w_ in pts]
        for wd, cc in ((v.px(4), QColor(255, 255, 255, 200)), (v.px(2), col)):
            p.setPen(QPen(cc, wd))
            for a, b in zip(P, P[1:]):
                p.drawLine(a, b)
        p.setBrush(col)
        for q in P:
            p.drawEllipse(q, v.px(4), v.px(4))
        if label and P:
            p.setPen(QPen(col, v.px(2)))
            p.drawText(QPointF(P[0].x() + v.px(8), P[0].y() - v.px(8)), label)


class Tool:
    """Klik di foto: mode 'gcp' = posisi titik RTK terpilih di foto ini; mode 'ukur' = titik jejak / bidang."""

    def __init__(self, dlg: "Model3DDialog"):
        self.d = dlg
        self.mode = "gcp"

    def press(self, pt, e) -> bool:
        d, v = self.d, self.d.view
        if d.img is None or not v.w:
            return False
        uv = [min(1.0, max(0.0, pt.x() / v.w)), min(1.0, max(0.0, pt.y() / v.h))]
        if self.mode == "ukur":
            d.draft.append(uv)
            d.ov.update()
            d.hint()
            return True
        k = d.gcp_row()
        if k < 0:
            d.info.setText("Pilih titik RTK di tabel dulu, lalu klik titik catnya di foto.")
            return True
        # tempel ke usulan titik cat terdekat bila dekat
        tgt = min(d.targets, key=lambda t: (t["u"] - uv[0]) ** 2 + (t["v"] - uv[1]) ** 2, default=None)
        if tgt and ((tgt["u"] - uv[0]) * v.w) ** 2 + ((tgt["v"] - uv[1]) * v.h) ** 2 < (v.px(18)) ** 2:
            uv = [tgt["u"], tgt["v"]]
        d.gcps[k].setdefault("obs", {})[str(d.img)] = uv
        d.save_gcps()
        return True

    def move(self, pt) -> None:
        pass

    def release(self, pt) -> None:
        pass

    def hover(self, pt):
        return Qt.CrossCursor

    def dbl(self, pt) -> None:
        if self.mode == "ukur":
            self.d.finish_measure()

    def key(self, k) -> bool:
        d = self.d
        if self.mode == "ukur":
            if k in (Qt.Key_Return, Qt.Key_Enter):
                d.finish_measure()
                return True
            if k == Qt.Key_Backspace and d.draft:
                d.draft.pop()
                d.ov.update()
                return True
            if k == Qt.Key_Escape:
                d.draft.clear()
                self.mode = "gcp"
                d.ov.update()
                d.hint()
                return True
        if k == Qt.Key_Delete and self.mode == "gcp":
            kk = d.gcp_row()
            if kk >= 0 and str(d.img) in (d.gcps[kk].get("obs") or {}):
                del d.gcps[kk]["obs"][str(d.img)]
                d.save_gcps()
                return True
        return False


class Model3DDialog(Dlg):
    def __init__(self, page):
        super().__init__(page, "Model 3D", "Model <span style='color:#a9c3dd'>3D</span> dinding (fotogrametri)", 1280)
        from .outcrop import OcView
        self.pg = page
        self.folder = page.folder
        self.m: dict | None = None
        self.img: int | None = None
        self.gcps: list[dict] = []
        self.targets: list[dict] = []
        self.draft: list = []
        self.busy = False
        top = QHBoxLayout()
        self.cbM = QComboBox()
        self.cbM.setMinimumWidth(240)
        self.bNew = btn("+ Model baru…", "Pilih 3–100 foto satu dinding / lantai (HP: berjalan sejajar dinding; drone: jalur terbang sejajar; tumpang-tindih ±70 %, tanpa zoom)", pri=True, sm=True)
        self.bBuild = btn("Bangun model 3D", "Fitur SIFT, pencocokan antar foto, rekonstruksi kamera & awan titik (±1 menit untuk 10 foto, ±3–10 menit untuk 60 foto drone)", sm=True)
        self.bDelM = btn("Hapus model", sm=True)
        self.st = QLabel()
        self.st.setObjectName("note")
        self.st.setTextFormat(Qt.RichText)
        self.st.setWordWrap(True)
        for w_ in (QLabel("Model:"), self.cbM, self.bNew, self.bBuild, self.bDelM):
            top.addWidget(w_)
        top.addWidget(self.st, 1)
        self.body.addLayout(top)
        sp = QSplitter(Qt.Horizontal)
        self.lst = QListWidget()
        self.lst.setIconSize(QSize(120, 80))
        self.lst.setMaximumWidth(200)
        sp.addWidget(self.lst)
        self.view = OcView()
        self.view.placeholder("Buat model baru dari 3–100 foto satu dinding / lantai.")
        self.ov = Overlay(self)
        self.tool = Tool(self)
        self.view.set_tool(self.tool)
        self.view.loaded.connect(lambda *_: self.ov.update())
        sp.addWidget(self.view)
        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(400)
        self.tabs.addTab(self._tab_gcp(), "Titik RTK")
        self.tabs.addTab(self._tab_meas(), "Ukur bidang")
        self.tabs.addTab(self._tab_view(), "Tampilan && ekspor")
        sp.addWidget(self.tabs)
        sp.setSizes([180, 760, 420])
        self.body.addWidget(sp, 1)
        self.info = QLabel()
        self.info.setObjectName("note")
        self.info.setWordWrap(True)
        self.info.setTextFormat(Qt.RichText)
        self.body.addWidget(self.info)
        bClose = btn("Tutup", pri=True, sm=True)
        bClose.clicked.connect(self.accept)
        self.foot.addStretch(1)
        self.foot.addWidget(bClose)
        self.cbM.currentIndexChanged.connect(lambda *_: self.open_model(self.cbM.currentData()))
        self.bNew.clicked.connect(self.new_model)
        self.bBuild.clicked.connect(self.build)
        self.bDelM.clicked.connect(self.delete_model)
        self.lst.currentRowChanged.connect(self.pick)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.resize(1400, 860)
        self.reload()

    # ---------------------------------------------------------------- tata letak
    def _tab_gcp(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        n = QLabel("1) Tempel tabel titik cat dari RTK (<b>Nama, E, N, RL</b>) atau impor CSV. 2) Pilih baris, lalu klik titik catnya di "
                   "<b>minimal 2 foto</b> (lingkaran biru = usulan titik cat terdeteksi, klik di dekatnya untuk menempel). "
                   "Delete = hapus klik di foto ini. ≥3 titik lengkap → model berskala & berkoordinat UTM.")
        n.setWordWrap(True)
        n.setObjectName("note")
        n.setTextFormat(Qt.RichText)
        v.addWidget(n)
        r = QHBoxLayout()
        self.bGPaste = btn("Tempel dari Excel", sm=True)
        self.bGCsv = btn("Impor CSV…", sm=True)
        self.bGDet = btn("Deteksi titik cat", "Cari bercak cat mencolok (pink / magenta, kuning neon) di foto ini", sm=True)
        self.bGDel = btn("Hapus titik", sm=True)
        for b in (self.bGPaste, self.bGCsv, self.bGDet, self.bGDel):
            r.addWidget(b)
        r.addStretch(1)
        v.addLayout(r)
        self.gT = QTableWidget(0, 6)
        self.gT.setHorizontalHeaderLabels(["Nama", "E", "N", "RL", "Foto", "Galat m"])
        self.gT.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.gT.horizontalHeader().setStretchLastSection(True)
        self.gT.verticalHeader().hide()
        self.gT.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.gT.setSelectionMode(QAbstractItemView.SingleSelection)
        self.gT.itemChanged.connect(self._gcp_edited)
        self.gT.itemSelectionChanged.connect(lambda: (self.ov.update(), self.hint()))
        v.addWidget(self.gT, 1)
        self.gInfo = QLabel()
        self.gInfo.setObjectName("note")
        self.gInfo.setWordWrap(True)
        self.gInfo.setTextFormat(Qt.RichText)
        v.addWidget(self.gInfo)
        self.bGPaste.clicked.connect(lambda: self.paste_gcps(QGuiApplication.clipboard().text()))
        self.bGCsv.clicked.connect(self.import_gcps)
        self.bGDet.clicked.connect(self.detect)
        self.bGDel.clicked.connect(self.del_gcp)
        return w

    def _tab_meas(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        n = QLabel("Klik titik-titik di sepanjang <b>jejak</b> vein / kekar / sesar yang <b>melintasi permukaan tidak rata</b> (sudut atau "
                   "tonjolan dinding), atau sebar titik di <b>satu bidang yang tersingkap</b>. Enter / klik ganda = selesai, Backspace = "
                   "hapus titik terakhir, Esc = batal. Jejak lurus di dinding rata hanya memberi apparent dip.")
        n.setWordWrap(True)
        n.setObjectName("note")
        n.setTextFormat(Qt.RichText)
        v.addWidget(n)
        r = QHBoxLayout()
        self.cbKind = QComboBox()
        for k, t in KINDS:
            self.cbKind.addItem(t, k)
        self.eName = QLineEdit()
        self.eName.setPlaceholderText("nama (mis. Vein utama)")
        self.bMeas = btn("✎ Ukur bidang", pri=True, sm=True)
        self.bMDel = btn("Hapus", sm=True)
        for b in (self.cbKind, self.eName, self.bMeas, self.bMDel):
            r.addWidget(b)
        v.addLayout(r)
        self.mT = QTableWidget(0, 8)
        self.mT.setHorizontalHeaderLabels(["Nama", "Jenis", "Dip", "Arah dip", "Strike", "Titik", "RMS m", "Mutu"])
        self.mT.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.mT.horizontalHeader().setStretchLastSection(True)
        self.mT.verticalHeader().hide()
        self.mT.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mT.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mT.itemSelectionChanged.connect(self._meas_sel)
        v.addWidget(self.mT, 1)
        self.mInfo = QLabel()
        self.mInfo.setObjectName("note")
        self.mInfo.setWordWrap(True)
        self.mInfo.setTextFormat(Qt.RichText)
        v.addWidget(self.mInfo)
        self.bMeas.clicked.connect(self.start_measure)
        self.bMDel.clicked.connect(self.del_measure)
        return w

    def _tab_view(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.vImg = QLabel()
        self.vImg.setAlignment(Qt.AlignCenter)
        v.addWidget(self.vImg, 1)
        r = QHBoxLayout()
        self.bXCsv = btn("⇩ Bidang (CSV)", "Tabel bidang terukur: E, N, RL, dip, arah dip, strike, mutu", sm=True)
        self.bXStr = btn("⇩ Bidang (STR Surpac)", "Satu titik per bidang dengan D1 jenis, D2 nama, D3 dip, D4 arah dip, D5 strike", sm=True)
        self.bXPly = btn("⇩ Awan titik (PLY)", "Awan titik berwarna dalam koordinat UTM (CloudCompare, Surpac, dll.)", sm=True)
        for b in (self.bXCsv, self.bXStr, self.bXPly):
            r.addWidget(b)
        r.addStretch(1)
        v.addLayout(r)
        self.bXCsv.clicked.connect(lambda: self.export("csv"))
        self.bXStr.clicked.connect(lambda: self.export("str"))
        self.bXPly.clicked.connect(lambda: self.export("ply"))
        return w

    # ---------------------------------------------------------------- model
    def reload(self, sel: int | None = None) -> None:
        j = api.call("/core/outcrop/m3d/list", {"folder": self.folder})
        self.cbM.blockSignals(True)
        self.cbM.clear()
        for x in j["models"]:
            self.cbM.addItem(f"{x['name']} ({x['n_photos']} foto · {x['status']})", x["id"])
        self.cbM.blockSignals(False)
        if self.cbM.count():
            i = self.cbM.findData(sel) if sel else self.cbM.count() - 1
            self.cbM.setCurrentIndex(max(0, i))
            self.open_model(self.cbM.currentData())
        else:
            self.m = None
            self.refresh()

    def open_model(self, mid) -> None:
        if mid is None:
            return
        self.m = api.call("/core/outcrop/m3d/get", {"folder": self.folder, "id": mid})["model"]
        self.gcps = [dict(g, obs=dict(g.get("obs") or {})) for g in self.m.get("gcps") or []]
        self.img = None
        self.lst.blockSignals(True)
        self.lst.clear()
        for ph in self.m["photos"]:
            it = QListWidgetItem(ph["name"])
            p = self.photo_path(ph["i"])
            im = QImage(str(p))
            if not im.isNull():
                it.setIcon(QIcon(QPixmap.fromImage(im.scaled(120, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))))
            self.lst.addItem(it)
        self.lst.blockSignals(False)
        self.lst.setCurrentRow(0)
        self.refresh()

    def photo_path(self, i: int) -> Path:
        return Path(api.call("/core/outcrop/m3d/photo", {"folder": self.folder, "id": self.m["id"], "img": i})["path"])

    def refresh(self) -> None:
        m = self.m
        has = m is not None
        for b in (self.bBuild, self.bDelM, self.bGPaste, self.bGCsv, self.bGDet, self.bGDel, self.bMeas, self.bMDel):
            b.setEnabled(has and not self.busy)
        if not has:
            self.st.setText("Belum ada model. <b>+ Model baru…</b> lalu pilih 3–100 foto satu dinding / lantai.")
            self.view.placeholder("Buat model baru dari 3–100 foto satu dinding / lantai.")
            return
        rec, geo = m.get("recon"), m.get("georef") or {}
        if rec:
            t = (f"<b>{rec['n_points']:,}</b> titik 3D · kamera {rec['n_cams']}/{rec['n_photos']} · galat reproyeksi {rec['reproj_px']} px · "
                 f"{rec.get('secs', 0):.0f} dtk")
            if geo.get("method") == "rtk":
                t += f" · <b style='color:#2f9e44'>georef RTK</b> ({geo['n']} titik, RMS <b>{geo['rms']:.3f} m</b>)"
            elif geo.get("method") == "gps":
                t += f" · <b style='color:#B7791F'>georef GPS kamera (kasar, RMS {geo['rms']:.1f} m)</b>"
            else:
                t += " · <b style='color:#C0392B'>belum berskala</b>"
        else:
            t = {"gagal": f"<b style='color:#C0392B'>Gagal:</b> {_esc(m.get('error') or '')}"}.get(m.get("status"),
                                                                                                  "Belum dibangun — klik <b>Bangun model 3D</b>.")
        self.st.setText(t)
        for i in range(self.lst.count()):
            ok = bool(rec and str(i) in rec["cams"])
            self.lst.item(i).setForeground(QColor(theme.C["ink"] if ok or not rec else "#C0392B"))
            self.lst.item(i).setToolTip("" if ok or not rec else "Foto ini tidak berhasil dipasang di model")
        self.fill_gcps()
        self.fill_measures()
        self.ov.update()
        self.hint()

    def new_model(self) -> None:
        fs, _ = QFileDialog.getOpenFileNames(self, "Foto satu dinding / lantai untuk model 3D (3–100)", SET.get("m3dDir", str(Path.home())),
                                             "Foto (*.jpg *.jpeg *.png *.tif *.tiff)")
        if not fs:
            return
        SET.set("m3dDir", str(Path(fs[0]).parent))
        name = Path(fs[0]).parent.name
        link = self.pg._ask_link(fs)
        if link is None:
            return
        try:
            j = api.call("/core/outcrop/m3d/create", {"folder": self.folder, "name": name, "paths": fs, "by": self.pg.by(), "link": link})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.reload(j["model"]["id"])
        self.info.setText(f"Model <b>{_esc(j['model']['name'])}</b> dibuat dari {len(fs)} foto. Klik <b>Bangun model 3D</b>.")

    def delete_model(self) -> None:
        if not self.m or not ask(self, f"Hapus model 3D \"{self.m['name']}\" beserta salinan fotonya?" + ("\n\nFoto tertaut di folder aslinya tidak dihapus." if self.m.get("linked") else "")):
            return
        api.call("/core/outcrop/m3d/delete", {"folder": self.folder, "id": self.m["id"]})
        self.reload()

    def build(self) -> None:
        if not self.m or self.busy:
            return
        self.busy = True
        self.refresh()
        self.st.setText("Membangun model 3D… (fitur, pencocokan, rekonstruksi; ±1 menit untuk 10 foto, ±3–10 menit untuk 60 foto drone)")
        mid = self.m["id"]
        base = self.st.text()
        tm = QTimer(self)

        def tick():
            try:
                msg = api.call("/core/outcrop/m3d/progress", {"folder": self.folder, "id": mid})["msg"]
            except api.ApiError:
                msg = ""
            if self.busy and msg:
                self.st.setText(base + "<br><b>" + _esc(msg) + "</b>")
        tm.timeout.connect(tick)
        tm.start(1000)
        self._prog_timer = tm

        def ok(j):
            tm.stop()
            self.busy = False
            self.m = j["model"]
            k = self.cbM.findData(mid)
            if k >= 0:
                self.cbM.setItemText(k, f"{self.m['name']} ({len(self.m['photos'])} foto · {self.m['status']})")
            self.refresh()
            self.load_views()
            log("[model3d] dibangun", mid, j["model"]["recon"]["n_points"])

        def err(e):
            tm.stop()
            self.busy = False
            self.open_model(mid)
            say(self, "Model 3D gagal dibangun:\n" + e, warn=True)
        run_bg(api.call, "/core/outcrop/m3d/build", {"folder": self.folder, "id": mid}, ok=ok, err=err)

    def pick(self, i: int) -> None:
        if not self.m or not 0 <= i < len(self.m["photos"]):
            return
        self.img = i
        self.targets = []
        self.draft = []
        self.view.show_file(self.photo_path(i), 10000 + self.m["id"] * 100 + i)
        self.ov.update()
        self.hint()

    def hint(self) -> None:
        if self.tool.mode == "ukur":
            self.info.setText(f"<b>Ukur bidang</b>: {len(self.draft)} titik · klik di sepanjang jejak · Enter / klik ganda = selesai · "
                              "Backspace = hapus titik terakhir · Esc = batal")
            return
        k = self.gcp_row()
        if k >= 0 and self.img is not None:
            g = self.gcps[k]
            self.info.setText(f"<b>Titik RTK {_esc(g['name'])}</b>: klik titik catnya di foto ini "
                              f"({len(g.get('obs') or {})} foto sudah diklik) · Delete = hapus klik di foto ini")
        else:
            self.info.setText("Scroll = zoom, tarik = geser. Pilih titik RTK di tabel untuk mengklik posisinya di foto.")

    def _tab_changed(self, i: int) -> None:
        if i == 2:
            self.load_views()

    def load_views(self) -> None:
        if not self.m or not self.m.get("recon"):
            self.vImg.setText("Bangun model 3D dulu.")
            return

        def ok(j):
            if j.get("png"):
                pm = QPixmap()
                pm.loadFromData(base64.b64decode(j["png"]), "PNG")
                self.vImg.setPixmap(pm.scaledToWidth(min(max(300, self.tabs.width() - 30), pm.width()), Qt.SmoothTransformation))
        run_bg(api.call, "/core/outcrop/m3d/views", {"folder": self.folder, "id": self.m["id"]}, ok=ok)

    # ---------------------------------------------------------------- titik RTK
    def gcp_row(self) -> int:
        r = self.gT.currentRow()
        return r if 0 <= r < len(self.gcps) else -1

    def fill_gcps(self) -> None:
        res = {x["name"]: x for x in ((self.m or {}).get("georef") or {}).get("residuals") or []} \
            if ((self.m or {}).get("georef") or {}).get("method") == "rtk" else {}
        cur = self.gT.currentRow()
        self.gT.blockSignals(True)
        self.gT.setRowCount(len(self.gcps))
        for i, g in enumerate(self.gcps):
            vals = [g["name"], "" if g.get("e") is None else f"{g['e']:.3f}", "" if g.get("n") is None else f"{g['n']:.3f}",
                    "" if g.get("rl") is None else f"{g['rl']:.3f}", str(len(g.get("obs") or {})),
                    f"{res[g['name']]['err']:.3f}" if g["name"] in res else ""]
            for c, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if c >= 4:
                    it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if c == 4 and len(g.get("obs") or {}) < 2:
                    it.setBackground(QColor("#FFF2CC"))
                    it.setForeground(QColor("#141a26"))
                self.gT.setItem(i, c, it)
        self.gT.blockSignals(False)
        if 0 <= cur < len(self.gcps):
            self.gT.selectRow(cur)
        geo = (self.m or {}).get("georef") or {}
        self.gInfo.setText(_esc(geo.get("msg") or "") if geo.get("method") != "rtk" else
                           f"Georef RTK: {geo['n']} titik, RMS <b>{geo['rms']:.3f} m</b>, skala model {geo['scale']:.4g}.")

    def _gcp_edited(self, it: QTableWidgetItem) -> None:
        r, c = it.row(), it.column()
        if not 0 <= r < len(self.gcps) or c > 3:
            return
        key = ("name", "e", "n", "rl")[c]
        v = it.text().strip()
        if key == "name":
            self.gcps[r]["name"] = v
        else:
            try:
                self.gcps[r][key] = float(v.replace(",", ".")) if v else None
            except ValueError:
                say(self, f"{key.upper()} harus angka.", warn=True)
                return
        self.save_gcps()

    def paste_gcps(self, text: str) -> int:
        """Baris 'Nama, E, N, RL' (tab / koma / titik koma). Baris judul dilewati. Nama yang sudah ada diperbarui."""
        n = 0
        for ln in (text or "").replace("\r", "\n").split("\n"):
            parts = [x.strip() for x in (ln.split("\t") if "\t" in ln else ln.replace(";", ",").split(","))]
            parts = [x for x in parts if x != ""]
            if len(parts) < 4:
                continue
            try:
                e, nn, rl = (float(x.replace(" ", "")) for x in parts[1:4])
            except ValueError:
                continue  # baris judul
            g = next((x for x in self.gcps if x["name"] == parts[0]), None)
            if g is None:
                g = {"name": parts[0], "obs": {}}
                self.gcps.append(g)
            g.update(e=e, n=nn, rl=rl)
            n += 1
        if not n:
            say(self, "Tidak ada baris Nama, E, N, RL yang terbaca.", warn=True)
            return 0
        self.save_gcps()
        self.info.setText(f"{n} titik RTK dibaca. Pilih titik di tabel lalu klik titik catnya di minimal 2 foto.")
        return n

    def import_gcps(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Koordinat titik cat RTK (CSV / TXT)", SET.get("m3dDir", str(Path.home())),
                                           "Teks (*.csv *.txt)")
        if f:
            self.paste_gcps(Path(f).read_text(encoding="utf-8-sig", errors="replace"))

    def save_gcps(self) -> None:
        if not self.m:
            return
        try:
            j = api.call("/core/outcrop/m3d/gcps", {"folder": self.folder, "id": self.m["id"], "gcps": self.gcps})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.m = j["model"]
        self.gcps = [dict(g, obs=dict(g.get("obs") or {})) for g in self.m.get("gcps") or []]
        self.refresh()

    def del_gcp(self) -> None:
        k = self.gcp_row()
        if k >= 0 and ask(self, f"Hapus titik RTK {self.gcps[k]['name']}?"):
            del self.gcps[k]
            self.save_gcps()

    def detect(self) -> None:
        if not self.m or self.img is None:
            return
        self.targets = api.call("/core/outcrop/m3d/targets", {"folder": self.folder, "id": self.m["id"], "img": self.img})["targets"]
        self.ov.update()
        self.info.setText(f"{len(self.targets)} usulan titik cat (lingkaran biru). Pilih nama titik di tabel lalu klik di dekat lingkarannya.")

    # ---------------------------------------------------------------- ukur bidang
    def start_measure(self) -> None:
        if not self.m or not self.m.get("recon"):
            say(self, "Bangun model 3D dulu.", warn=True)
            return
        self.tool.mode = "ukur"
        self.draft = []
        self.view.setFocus()
        self.hint()

    def finish_measure(self) -> None:
        pts, self.draft = list(self.draft), []
        self.tool.mode = "gcp"
        self.ov.update()
        if len(pts) < 3:
            self.hint()
            return
        try:
            j = api.call("/core/outcrop/m3d/measure", {"folder": self.folder, "id": self.m["id"], "name": self.eName.text(),
                                                       "kind": self.cbKind.currentData(), "img": self.img, "pts": pts, "by": self.pg.by()})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        self.m = j["model"]
        self.eName.clear()
        self.refresh()
        self.mT.selectRow(self.mT.rowCount() - 1)

    def fill_measures(self) -> None:
        ms = (self.m or {}).get("measures") or []
        self.mT.setRowCount(len(ms))
        for i, me in enumerate(ms):
            r = me.get("result") or {}
            ok = r and not r.get("error")
            vals = [me["name"], dict(KINDS).get(me["kind"], me["kind"]), f"{r['dip']:.0f}°" if ok else "", f"{r['ddir']:03.0f}°" if ok else "",
                    f"{r['strike']:03.0f}°" if ok else "", str(r.get("n", "")) if ok else str(len(me["pts"])), f"{r['rms']:.3f}" if ok else "",
                    r.get("quality", "") if ok else ("belum berskala" if not r else "galat")]
            for c, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if c == 7 and ok:
                    it.setForeground(QColor(QCOL.get(r["quality"], "#141a26")))
                self.mT.setItem(i, c, it)
        self._meas_sel()

    def _meas_sel(self) -> None:
        ms = (self.m or {}).get("measures") or []
        i = self.mT.currentRow()
        if not 0 <= i < len(ms):
            self.mInfo.setText("")
            return
        me = ms[i]
        r = me.get("result") or {}
        if not r:
            self.mInfo.setText("Model belum berskala: klik ≥ 3 titik RTK (atau pakai foto ber-GPS) agar dip / arah dip bisa dihitung.")
        elif r.get("error"):
            self.mInfo.setText(_esc(r["error"]))
        else:
            e, n, z = r["center"]
            self.mInfo.setText(f"<b>{_esc(me['name'])}</b>: dip <b>{r['dip']:.0f}°</b> ke arah <b>{r['ddir']:03.0f}°</b> (strike {r['strike']:03.0f}°, "
                               f"aturan tangan kanan) · pusat E {e:,.2f} N {n:,.2f} RL {z:,.2f} · RMS bidang {r['rms']:.3f} m · "
                               f"mutu <b style='color:{QCOL.get(r['quality'], '#141a26')}'>{r['quality']}</b>"
                               + (f" — {_esc(r['note'])}" if r.get("note") else "")
                               + (" · <span style='color:#B7791F'>georef GPS kamera (kasar)</span>" if r.get("georef") == "gps" else ""))
        if self.img != me["img"] and 0 <= me["img"] < self.lst.count():
            self.lst.setCurrentRow(me["img"])

    def del_measure(self) -> None:
        ms = (self.m or {}).get("measures") or []
        i = self.mT.currentRow()
        if not 0 <= i < len(ms):
            return
        j = api.call("/core/outcrop/m3d/measure/delete", {"folder": self.folder, "id": self.m["id"], "measure": ms[i]["id"]})
        self.m = j["model"]
        self.refresh()

    # ---------------------------------------------------------------- ekspor
    def export(self, fmt: str) -> None:
        if not self.m:
            return
        ext = {"csv": ".csv", "str": ".str", "ply": ".ply"}[fmt]
        start = str(Path(SET.get("lastSaveDir", str(Path.home()))) / (self.m["name"].replace(" ", "_") + ("_bidang" if fmt != "ply" else "_awan_titik") + ext))
        p, _ = QFileDialog.getSaveFileName(self, "Ekspor model 3D", start, f"*{ext}")
        if not p:
            return
        if not p.lower().endswith(ext):
            p += ext
        SET.set("lastSaveDir", str(Path(p).parent))
        try:
            b = api.call("/core/outcrop/m3d/export", {"folder": self.folder, "id": self.m["id"], "fmt": fmt})
        except api.ApiError as e:
            say(self, str(e), warn=True)
            return
        Path(p).write_bytes(b)
        self.pg.toast(f"Ekspor: {Path(p).name}", 3000)
        show_in_folder(p)
