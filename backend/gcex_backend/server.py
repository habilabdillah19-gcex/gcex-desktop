"""Backend GC-Ex (FastAPI). Hanya mendengar di 127.0.0.1 (tidak bisa diakses dari jaringan)."""
from __future__ import annotations

import json
import logging
import os
import traceback
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.background import BackgroundTask
from pydantic import BaseModel

from . import __version__, access_io, core_dh, core_forms, core_io, core_marks, core_outcrop, core_segs, excel_io, mdl_io, xlsx_patch

log = logging.getLogger("gcex")
app = FastAPI(title="GC-Ex Backend", version=__version__)
# halaman GC-Ex dibuka dari file:// (origin "null") di dalam Electron
app.add_middleware(CORSMiddleware, allow_origins=["null", "http://127.0.0.1", "http://localhost"], allow_origin_regex=r"^(file://.*|null)$",
                   allow_methods=["*"], allow_headers=["*"])


def _json_err(request: Request, exc: Exception) -> JSONResponse:
    log.error("galat %s: %s\n%s", request.url.path, exc, "".join(traceback.format_exception(exc)))
    return JSONResponse(status_code=500, content={"ok": False, "error": str(exc), "type": type(exc).__name__})


# Galat yang lazim (file tidak ada, isian salah, driver tidak ada, file terkunci) ditangani penuh di sini.
import sqlite3  # noqa: E402

for _exc in (OSError, ValueError, KeyError, RuntimeError, PermissionError, sqlite3.Error):
    app.add_exception_handler(_exc, lambda request, exc: _json_err(request, exc))


@app.exception_handler(Exception)
async def _err(request: Request, exc: Exception):  # cadangan untuk galat lain: tetap dikembalikan sebagai pesan yang bisa dibaca
    return _json_err(request, exc)


# DB-Ex: foto core box + AI lokal (Ollama)
app.include_router(core_io.router)
app.include_router(core_dh.router)
app.include_router(core_marks.router)
app.include_router(core_segs.router)
app.include_router(core_outcrop.router)
app.include_router(core_forms.router)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "app": "GC-Ex Backend", "version": __version__, "pid": os.getpid()}


@app.get("/info")
def info() -> dict:
    return {"version": __version__, "access": access_io.drivers()}


# ---------- Excel ----------
class Register(BaseModel):
    headers: list[str]
    rows: list[list[Any]]
    sheet: str = "Register"


@app.post("/excel/register")
def excel_register(body: Register) -> Response:
    data = excel_io.build_register(body.headers, body.rows, body.sheet)
    return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


class ExcelAppend(Register):
    path: str
    sheet: Optional[str] = None
    key_header: Optional[str] = None
    backup: bool = True
    skip_existing: bool = True


@app.post("/excel/append")
def excel_append(body: ExcelAppend) -> dict:
    return {"ok": True, **excel_io.append_rows(body.path, body.sheet, body.headers, body.rows, body.key_header, body.backup, body.skip_existing)}


class RegisterWrite(BaseModel):
    """Kirim register as-mined GC-Ex ke workbook yang sudah ada (hanya kolom input; rumus tidak disentuh)."""
    path: str
    headers: list[str]
    rows: list[list[Any]]
    sheet: Optional[str] = None
    key_header: Optional[str] = None
    mode: str = "skip"          # "skip" = kode yang sudah ada dilewati, "update" = kolom inputnya diperbarui
    dry_run: bool = False       # True = hanya rencana (kolom & baris tujuan), file tidak diubah
    backup: bool = True


@app.post("/excel/register-write")
def excel_register_write(body: RegisterWrite) -> dict:
    return {"ok": True, **xlsx_patch.write_register(body.path, body.headers, body.rows, body.sheet, body.key_header,
                                                     body.mode, body.dry_run, body.backup)}


class SheetRead(BaseModel):
    path: str
    sheet: Optional[str] = None
    limit: int = 2000


@app.post("/excel/read")
def excel_read(body: SheetRead) -> dict:
    return {"ok": True, **excel_io.read_sheet(body.path, body.sheet, body.limit)}


# ---------- MS Access ----------
class AccessPath(BaseModel):
    path: str


@app.post("/access/tables")
def access_tables(body: AccessPath) -> dict:
    return {"ok": True, "tables": access_io.tables(body.path)}


class AccessRead(AccessPath):
    table: str
    limit: int = 1000
    where_col: Optional[str] = None
    where_val: Any = None


@app.post("/access/read")
def access_read(body: AccessRead) -> dict:
    return {"ok": True, **access_io.read(body.path, body.table, body.limit, body.where_col, body.where_val)}


class AccessInsert(AccessPath):
    table: str
    columns: list[str]
    rows: list[list[Any]]
    key_column: Optional[str] = None
    skip_existing: bool = True


@app.post("/access/insert")
def access_insert(body: AccessInsert) -> dict:
    if not body.rows:
        raise HTTPException(400, "Tidak ada baris untuk dimasukkan.")
    return {"ok": True, **access_io.insert(body.path, body.table, body.columns, body.rows, body.key_column, body.skip_existing)}


# ---------- Block model .mdl besar (tahap 3) ----------
class MdlPath(BaseModel):
    path: str


@app.post("/mdl/open")
def mdl_open(body: MdlPath) -> dict:
    """Status cache file .mdl; bila belum ada, cache dibangun di latar belakang (panggil berulang untuk progres)."""
    return {"ok": True, **mdl_io.open_model(body.path)}


@app.post("/mdl/cancel")
def mdl_cancel(body: MdlPath) -> dict:
    return {"ok": True, "cancelled": mdl_io.cancel_build(body.path)}


@app.post("/mdl/stat")
def mdl_stat(body: MdlPath) -> dict:
    p = __import__("pathlib").Path(body.path)
    return {"ok": True, "exists": p.exists(), "size": p.stat().st_size if p.exists() else None}


class MdlSubset(MdlPath):
    z_min: Optional[float] = None
    z_max: Optional[float] = None
    bbox: Optional[list[Optional[float]]] = None
    center: bool = False  # True = pilih menurut titik tengah blok (filter GC-Ex Drillhole)
    max_n: Optional[int] = None  # batas blok per pemuatan (RAM/VRAM); rentang RL dipersempit dari atas bila lebih


# ---------------------------------------------------------------- database proyek (SQLite) di folder proyek
from . import proj_db  # noqa: E402


class ProjKey(BaseModel):
    key: str


class ProjLoad(ProjKey):
    db_b64: str = ""


class ProjSync(ProjKey):
    app: str = ""
    user: str = ""
    version: str = ""
    tables: list[dict]


@app.post("/proj/db/load")
def proj_db_load(body: ProjLoad):
    import base64
    try:
        return proj_db.load(body.key, base64.b64decode(body.db_b64) if body.db_b64 else b"")
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(e)})


@app.post("/proj/db/sync")
def proj_db_sync(body: ProjSync):
    """Perbarui database proyek; hasil = file gcex_proyek.db (header X-GCEx-Sync = ringkasan JSON)."""
    r = proj_db.sync(body.key, body.app, body.user, body.version, body.tables)
    return Response(proj_db.read_bytes(body.key), media_type="application/vnd.sqlite3",
                    headers={"X-GCEx-Sync": json.dumps(r, ensure_ascii=True), "Access-Control-Expose-Headers": "X-GCEx-Sync"})


@app.post("/proj/db/info")
def proj_db_info(body: ProjKey):
    return proj_db.info(body.key)


@app.post("/mdl/subset")
def mdl_subset(body: MdlSubset):
    """Potongan model (RL & kotak XY) sebagai file .mdl mini yang sah; header X-GCEx-N = jumlah blok."""
    import tempfile
    c, m = mdl_io.open_cache(body.path)
    z0, z1, capped, n_req = mdl_io.fit_window(c, body.z_min, body.z_max, body.max_n)
    idx = mdl_io.select(c, z0, z1, body.bbox, body.center)
    fd, tmp = tempfile.mkstemp(suffix=".mdl", prefix="gcex-sub-")
    with os.fdopen(fd, "wb") as fh:
        nb = mdl_io.write_subset(c, idx, fh)
    return FileResponse(tmp, media_type="application/octet-stream", background=BackgroundTask(os.remove, tmp),
                        headers={"X-GCEx-N": str(len(idx)), "X-GCEx-Total": str(m["n"]), "X-GCEx-Bytes": str(nb),
                                 "X-GCEx-Capped": "1" if capped else "0", "X-GCEx-Zmin": "" if z0 is None else repr(z0),
                                 "X-GCEx-Zmax": "" if z1 is None else repr(z1), "X-GCEx-Nreq": str(n_req),
                                 "Access-Control-Expose-Headers": "X-GCEx-N, X-GCEx-Total, X-GCEx-Bytes, X-GCEx-Capped, X-GCEx-Zmin, X-GCEx-Zmax, X-GCEx-Nreq"})


class MdlBench(MdlPath):
    bench: float
    ref: float
    attrs: list[str]
    sg_col: Optional[str] = None
    sg: float = 2.6
    sg_zero: str = "rep"
    sg_rep: Optional[float] = None
    cut_attr: Optional[str] = None
    cut: Optional[float] = None
    z_min: Optional[float] = None
    z_max: Optional[float] = None


@app.post("/mdl/benches")
def mdl_benches(body: MdlBench) -> dict:
    return {"ok": True, **mdl_io.bench_summary(body.path, body.bench, body.ref, body.attrs, body.sg_col, body.sg,
                                                body.sg_zero, body.sg_rep, body.cut_attr, body.cut, body.z_min, body.z_max)}


@app.get("/mdl/cache")
def mdl_cache() -> dict:
    return {"ok": True, "root": str(mdl_io.cache_root()), "items": mdl_io.cache_list()}


@app.post("/mdl/cache/clear")
def mdl_cache_clear() -> dict:
    return {"ok": True, "removed": mdl_io.clear_cache()}
