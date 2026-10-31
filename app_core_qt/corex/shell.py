"""Perilaku jendela yang dulu diurus Electron: satu jendela DB-Ex saja (membuka DB-Ex lagi -> jendela lama tampil &
folder diteruskan), ukuran tampilan (skala antarmuka), buka ulang aplikasi."""
from __future__ import annotations

import getpass
import json
import os
import re
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QObject, QProcess, QThread, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from .util import SET, log

# ukuran tampilan (QT_SCALE_FACTOR); 1.0 = bawaan. Berlaku setelah DB-Ex dibuka ulang (Qt menetapkan skala saat mulai).
ZOOMS = [0.8, 0.9, 1.0, 1.1, 1.25, 1.5]
ZOOM_DEF = 1.0


def zoom_now() -> float:
    try:
        z = float(SET.get("qt_zoom", ZOOM_DEF))
    except (TypeError, ValueError):
        return ZOOM_DEF
    return z if 0.5 <= z <= 2.0 else ZOOM_DEF


def apply_zoom_env() -> None:
    """Dipanggil sebelum QApplication dibuat. Variabel QT_SCALE_FACTOR dari luar tetap diutamakan."""
    z = zoom_now()
    if abs(z - 1.0) > 1e-3 and not os.environ.get("QT_SCALE_FACTOR"):
        os.environ["QT_SCALE_FACTOR"] = f"{z:g}"


def zoom_step(d: int) -> float:
    z = zoom_now()
    i = min(range(len(ZOOMS)), key=lambda k: abs(ZOOMS[k] - z))
    return ZOOMS[max(0, min(len(ZOOMS) - 1, i + d))]


def server_name() -> str:
    try:
        u = getpass.getuser()
    except Exception:  # noqa: BLE001
        u = "user"
    return "CoreEx-" + (re.sub(r"[^A-Za-z0-9_.-]+", "_", u) or "user")


class SingleInstance(QObject):
    """DB-Ex yang pertama mendengarkan; yang kedua mengirim pesan JSON (mis. folder) lalu keluar."""
    message = Signal(dict)

    def __init__(self, name: str | None = None) -> None:
        super().__init__()
        self.name = name or server_name()
        self.server: QLocalServer | None = None
        self.queue: list[dict] = []
        self._ready = False

    @staticmethod
    def send(name: str, payload: dict, timeout_ms: int = 1500) -> bool:
        s = QLocalSocket()
        s.connectToServer(name)
        if not s.waitForConnected(timeout_ms):
            return False
        s.write((json.dumps(payload) + "\n").encode("utf-8"))
        s.flush()
        s.waitForBytesWritten(timeout_ms)
        # bila pengirim & penerima satu proses DAN satu thread (mis. di uji), server tidak akan pernah
        # membaca tanpa event loop diputar dulu. Dari thread lain processEvents() tidak boleh dipakai.
        app = QCoreApplication.instance()
        if app is not None and QThread.currentThread() is app.thread():
            app.processEvents()
        s.waitForReadyRead(timeout_ms)  # jawaban "ok" -> jendela lama sudah menerima
        s.disconnectFromServer()
        return True

    def listen(self) -> bool:
        srv = QLocalServer(self)
        srv.setSocketOptions(QLocalServer.UserAccessOption)
        if not srv.listen(self.name):
            QLocalServer.removeServer(self.name)  # sisa soket dari DB-Ex yang berhenti tidak normal (Linux / macOS)
            if not srv.listen(self.name):
                log("[satu jendela] gagal mendengarkan:", srv.errorString())
                return False
        srv.newConnection.connect(self._conn)
        self.server = srv
        return True

    def _conn(self) -> None:
        while self.server and self.server.hasPendingConnections():
            c = self.server.nextPendingConnection()
            buf = bytearray()

            done = []

            def read(c=c, buf=buf, done=done):
                if done:
                    return
                try:
                    buf.extend(bytes(c.readAll()))
                except RuntimeError:  # soket sudah dihapus
                    return
                if b"\n" not in buf:
                    return
                done.append(True)
                line = bytes(buf).split(b"\n", 1)[0]
                try:
                    msg = json.loads(line.decode("utf-8") or "{}")
                except ValueError:
                    msg = {}
                c.write(b"ok\n")
                c.flush()
                c.disconnectFromServer()
                self._deliver(msg if isinstance(msg, dict) else {})

            c.readyRead.connect(read)
            # bila data dan pemutusan tiba bersamaan, readyRead bisa terlewat -> baca sisa buffer saat putus
            c.disconnected.connect(read)
            c.disconnected.connect(c.deleteLater)

    def _deliver(self, msg: dict) -> None:
        log("[satu jendela] pesan dari DB-Ex kedua:", msg)
        if self._ready:
            self.message.emit(msg)
        else:
            self.queue.append(msg)

    def ready(self) -> None:
        """Jendela utama sudah ada: kirim pesan yang datang selama dialog syarat / lisensi masih terbuka."""
        self._ready = True
        q, self.queue = self.queue, []
        for m in q:
            self.message.emit(m)

    def close(self) -> None:
        if self.server:
            self.server.close()
            self.server = None


def restart(folder: str = "") -> bool:
    """Jalankan DB-Ex baru (dipanggil setelah jendela ditutup & server satu-jendela dilepas)."""
    if getattr(sys, "frozen", False):
        prog, args = sys.executable, []
    else:
        prog, args = sys.executable, [str(Path(__file__).resolve().parents[1] / "main.py")]
    if folder:
        args += ["--folder", folder]
    ok = QProcess.startDetached(prog, args)
    ok = ok[0] if isinstance(ok, tuple) else ok
    log("[buka ulang]", prog, args, "OK" if ok else "gagal")
    return bool(ok)
