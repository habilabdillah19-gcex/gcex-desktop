"""Pengaturan (settings.json di folder data DB-Ex, sama dengan versi Electron), pekerja latar (QThreadPool), log & Ollama."""
from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


def appdata() -> Path:
    return Path(os.environ.get("APPDATA") or (Path.home() / ".config"))


def user_dir() -> Path:
    env = os.environ.get("COREX_USERDATA")
    d = Path(env or (appdata() / "DB-Ex"))
    if not env and not d.exists():
        # 0.31.0: Core-Ex berganti nama menjadi DB-Ex; pengaturan, cache & log lama dipindahkan sekali ke folder baru
        for old in ("Core-Ex", "GC-Ex Core Interpretation"):
            o = appdata() / old
            if o.is_dir():
                try:
                    o.rename(d)
                    break
                except OSError:
                    pass
    d.mkdir(parents=True, exist_ok=True)
    return d


def log(*a: Any) -> None:
    line = _dt.datetime.now().isoformat(timespec="seconds") + " " + " ".join(x if isinstance(x, str) else repr(x) for x in a) + "\n"
    try:
        d = user_dir() / "logs"
        d.mkdir(exist_ok=True)
        with open(d / f"corex-{_dt.date.today().isoformat()}.log", "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
    if not getattr(sys, "frozen", False):
        sys.stderr.write(line)


class Settings:
    def __init__(self) -> None:
        self.file = user_dir() / "settings.json"
        try:
            self.d = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            self.d = {}

    def get(self, k: str, default: Any = None) -> Any:
        return self.d.get(k, default)

    def set(self, k: str, v: Any) -> None:
        self.d[k] = v
        try:
            self.file.write_text(json.dumps(self.d, indent=1, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass


SET = Settings()


class _Sig(QObject):
    ok = Signal(object)
    err = Signal(str)


class _Task(QRunnable):
    def __init__(self, fn: Callable, args: tuple, kw: dict):
        super().__init__()
        self.fn, self.args, self.kw, self.sig = fn, args, kw, _Sig()

    def run(self) -> None:
        try:
            r = self.fn(*self.args, **self.kw)
        except Exception as e:  # noqa: BLE001
            log("[tugas]", traceback.format_exc())
            r, e_ = None, str(e) or type(e).__name__
        else:
            e_ = None
        try:  # aplikasi bisa sudah ditutup saat tugas selesai
            self.sig.err.emit(e_) if e_ is not None else self.sig.ok.emit(r)
        except RuntimeError:
            pass


_KEEP: set = set()


def alive(o: Any) -> bool:
    """True bila objek Qt masih hidup (objek C++-nya belum dihapus)."""
    if o is None:
        return False
    try:
        from shiboken6 import isValid
    except Exception:  # noqa: BLE001
        return True
    try:
        return bool(isValid(o))
    except Exception:  # noqa: BLE001
        return False


def _safe(cb: Callable) -> Callable:
    """Hasil tugas latar bisa datang setelah jendela / dialog pemanggilnya ditutup (mis. buka ulang DB-Ex saat cek Ollama
    masih berjalan): widget yang sudah dihapus diabaikan, bukan galat."""
    def f(*a):
        try:
            return cb(*a)
        except RuntimeError as e:
            if "already deleted" not in str(e):
                raise
            log("[tugas] hasil diabaikan, jendela sudah ditutup:", str(e)[:120])
    return f


def run_bg(fn: Callable, *args, ok: Callable | None = None, err: Callable | None = None, **kw) -> None:
    """Jalankan fn di thread pool; ok(hasil) / err(pesan) dipanggil di thread GUI."""
    t = _Task(fn, args, kw)
    _KEEP.add(t.sig)
    if ok:
        t.sig.ok.connect(_safe(ok))
    if err:
        t.sig.err.connect(_safe(err))
    t.sig.ok.connect(lambda *_: _KEEP.discard(t.sig))
    t.sig.err.connect(lambda *_: _KEEP.discard(t.sig))
    t.setAutoDelete(True)
    QThreadPool.globalInstance().start(t)


# ---------------------------------------------------------------- Ollama (port dari electron/main.js gcex:ollamaStart)
def is_local(host: str) -> bool:
    import re
    return bool(re.match(r"^https?://(127\.0\.0\.1|localhost)(:\d+)?/?$", (host or "http://127.0.0.1:11434").strip(), re.I))


def find_ollama() -> tuple[str, bool] | None:
    """(path, is_tray_app) atau None."""
    la = os.environ.get("LOCALAPPDATA")
    if la:
        d = Path(la) / "Programs" / "Ollama"
        if (d / "ollama app.exe").exists():
            return str(d / "ollama app.exe"), True
        if (d / "ollama.exe").exists():
            return str(d / "ollama.exe"), False
    w = shutil.which("ollama")
    return (w, False) if w else None


def _alive(host: str) -> bool:
    try:
        with urllib.request.urlopen(host.rstrip("/") + "/api/version", timeout=2) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def start_ollama(host: str, wait: float = 30) -> dict:
    host = (host or "http://127.0.0.1:11434").strip()
    if _alive(host):
        return {"ok": True, "started": False}
    f = find_ollama()
    if not f:
        return {"ok": False, "code": "notfound", "msg": "Ollama tidak ditemukan."}
    exe, tray = f
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        subprocess.Popen([exe] if tray else [exe, "serve"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=flags, close_fds=True, start_new_session=os.name != "nt")
    except OSError as e:
        return {"ok": False, "code": "spawn", "msg": str(e)}
    t0 = time.time()
    while time.time() - t0 < wait:
        if _alive(host):
            return {"ok": True, "started": True}
        time.sleep(0.7)
    return {"ok": False, "code": "timeout", "msg": "Ollama belum menjawab setelah 30 detik."}


def open_path(p: str | Path) -> None:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))


def show_in_folder(p: str | Path) -> None:
    p = str(p)
    if os.name == "nt":
        subprocess.Popen(["explorer", "/select,", os.path.normpath(p)])
    else:
        open_path(Path(p).parent)


def res_dir(name: str) -> Path:
    """legal/ atau docs/ - di aplikasi terpasang ada di samping exe (resources), di repo di akar repo."""
    base = Path(getattr(sys, "_MEIPASS", "")) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
    for c in (base / name, Path(sys.executable).parent / name, Path(__file__).resolve().parents[2] / name):
        if c.exists():
            return c
    return base / name
