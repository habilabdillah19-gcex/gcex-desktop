"""Backend GC-Ex (FastAPI). Hanya mendengar di 127.0.0.1 (tidak bisa diakses dari jaringan)."""
from __future__ import annotations

import logging
import os
import traceback
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.background import BackgroundTask
from pydantic import BaseModel

from . import __version__, access_io, core_io, excel_io, mdl_io, xlsx_patch

log = logging.getLogger("gcex")
app = FastAPI(title="GC-Ex Backend", version=__version__)
# halaman GC-Ex dibuka dari file:// (origin "null") di dalam Electron
app.add_middleware(CORSMiddleware, allow_origins=["null", "http://127.0.0.1", "http://localhost"], allow_origin_regex=r"^(file://.*|null)$",
                   allow_methods=["*"], allow_headers=["*"])


def _json_err(request: Request, exc: Exception) -> JSONResponse:
    log.error("galat %s: %s\n%s", request.url.path, exc, "".join(traceback.format_exception(exc)))
    return JSONResponse(status_code=500, content={"ok": False, "error": str(exc), "type": type(exc).__name__})


# Galat yang lazim (file tidak ada, isian salah, driver tidak ada, file terkunci) ditangani penuh di sini.
for _exc in (OSError, ValueError, KeyError, RuntimeError, PermissionError):
    app.add_exception_handler(_exc, lambda request, exc: _json_err(request, exc))


@app.exception_handler(Exception)
async def _err(request: Request, exc: Exception):  # cadangan untuk galat lain: tetap dikembalikan sebagai pesan yang bisa dibaca
    return _json_err(request, exc)


# GC-Ex Core Interpretation: foto core box + AI lokal (Ollama)
app.include_router(core_io.router)


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


@app.post("/mdl/subset")
def mdl_subset(body: MdlSubset):
    """Potongan model (RL & kotak XY) sebagai file .mdl mini yang sah; header X-GCEx-N = jumlah blok."""
    import tempfile
    c, m = mdl_io.open_cache(body.path)
    idx = mdl_io.select(c, body.z_min, body.z_max, body.bbox, body.center)
    fd, tmp = tempfile.mkstemp(suffix=".mdl", prefix="gcex-sub-")
    with os.fdopen(fd, "wb") as fh:
        nb = mdl_io.write_subset(c, idx, fh)
    return FileResponse(tmp, media_type="application/octet-stream", background=BackgroundTask(os.remove, tmp),
                        headers={"X-GCEx-N": str(len(idx)), "X-GCEx-Total": str(m["n"]), "X-GCEx-Bytes": str(nb),
                                 "Access-Control-Expose-Headers": "X-GCEx-N, X-GCEx-Total, X-GCEx-Bytes"})


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
