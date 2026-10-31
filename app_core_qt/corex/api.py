"""Panggil rute FastAPI DB-Ex langsung di proses yang sama (tanpa HTTP / port): validasi & logika sama persis dengan
aplikasi web, jadi satu backend dipakai dua antarmuka."""
from __future__ import annotations

import inspect
import typing
import json
import os
import sys
from pathlib import Path
from typing import Any


def _backend_path() -> None:
    here = Path(__file__).resolve()
    for c in (here.parents[2] / "backend", Path(getattr(sys, "_MEIPASS", "")) / "backend"):
        if (c / "gcex_backend").is_dir() and str(c) not in sys.path:
            sys.path.insert(0, str(c))


_backend_path()
from gcex_backend import core_dh, core_io, core_marks, core_outcrop, core_segs  # noqa: E402

_ROUTES: dict[str, Any] = {}
for _m in (core_io, core_dh, core_marks, core_segs, core_outcrop):
    for _r in _m.router.routes:
        _ROUTES[_r.path] = _r.endpoint


class ApiError(Exception):
    pass


def call(path: str, body: dict | None = None, **query) -> Any:
    """call('/core/rows', {'folder': f}) -> dict; rute yang mengembalikan file -> bytes."""
    fn = _ROUTES.get(path)
    if fn is None:
        raise ApiError(f"Rute tidak dikenal: {path}")
    params = list(inspect.signature(fn).parameters.values())
    try:
        if not params:
            out = fn()
        elif query:
            out = fn(**query)
        else:
            model = typing.get_type_hints(fn)[params[0].name]
            out = fn(model(**(body or {})))
    except ApiError:
        raise
    except Exception as e:  # noqa: BLE001 - pesan dibaca pengguna
        msg = getattr(e, "detail", None) or (e.errors()[0].get("msg") if hasattr(e, "errors") else None) or str(e) or type(e).__name__
        raise ApiError(str(msg)) from e
    if hasattr(out, "body") and hasattr(out, "media_type"):  # Response
        if out.media_type == "application/json":
            return json.loads(out.body)
        return bytes(out.body)
    if hasattr(out, "path") and hasattr(out, "media_type"):  # FileResponse
        return Path(out.path)
    return out


def image_file(folder: str, pid: int, w: int) -> Path:
    """w <= 0 = file asli; selain itu JPEG di cache (sisi terpanjang <= w)."""
    p = core_io.get_project(folder)
    f = core_io.photo_path(p, pid)
    return f if w <= 0 else core_io.cached_image(f, max(64, min(w, 4000)))


DEFAULT_HOST = getattr(core_io, "DEFAULT_HOST", "http://127.0.0.1:11434")
os.environ.setdefault("GCEX_APP", "core")
