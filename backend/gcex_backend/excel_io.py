"""Excel I/O untuk GC-Ex: buat workbook register & tambahkan baris ke workbook yang sudah ada.

Prinsip: tidak pernah menimpa data yang ada; baris baru ditambahkan di bawah data terakhir,
kolom dicocokkan berdasarkan NAMA header (bukan posisi), tabel Excel (ListObject) diperpanjang.
"""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any, Iterable

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F3A5F")


def _norm(s: Any) -> str:
    """Normalisasi nama kolom: huruf kecil, tanpa spasi/tanda baca (toleran beda penulisan)."""
    return re.sub(r"[^a-z0-9]+", "", str(s or "").lower())


def build_register(headers: list[str], rows: list[list[Any]], sheet: str = "Register") -> bytes:
    """Workbook baru berisi satu tabel register. Hasil: isi file .xlsx (bytes)."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet[:31]
    for j, h in enumerate(headers, 1):
        c = ws.cell(1, j, h)
        c.font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
        c.fill = HEADER_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for i, r in enumerate(rows, 2):
        for j, v in enumerate(r, 1):
            c = ws.cell(i, j, v)
            c.font = Font(name="Arial", size=10)
    for j, h in enumerate(headers, 1):
        width = max([len(str(h))] + [len(str(r[j - 1])) for r in rows if j - 1 < len(r)]) + 2
        ws.column_dimensions[get_column_letter(j)].width = min(max(width, 8), 40)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{max(1, len(rows) + 1)}"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def find_header_row(ws, headers: Iterable[str], max_scan: int = 30) -> tuple[int, dict[str, int]]:
    """Cari baris header yang paling banyak cocok dengan daftar header. Hasil: (nomor baris, {norm: kolom})."""
    want = {_norm(h) for h in headers if _norm(h)}
    best = (0, {})
    for r in range(1, min(ws.max_row, max_scan) + 1):
        found = {}
        for c in range(1, ws.max_column + 1):
            k = _norm(ws.cell(r, c).value)
            if k in want and k not in found:
                found[k] = c
        if len(found) > len(best[1]):
            best = (r, found)
    return best


def last_data_row(ws, header_row: int, key_cols: list[int]) -> int:
    """Baris terakhir yang berisi data pada kolom kunci (mengabaikan baris kosong berformat)."""
    last = header_row
    for r in range(header_row + 1, ws.max_row + 1):
        if any(ws.cell(r, c).value not in (None, "") for c in key_cols):
            last = r
    return last


def append_rows(path: str | Path, sheet: str | None, headers: list[str], rows: list[list[Any]],
                key_header: str | None = None, backup: bool = True, skip_existing: bool = True) -> dict:
    """Tambahkan baris ke workbook yang sudah ada (lewat penyunting langsung xlsx_patch, tanpa menyimpan ulang
    workbook, sehingga grafik, link eksternal & makro tetap utuh; kolom rumus tidak ditimpa)."""
    from . import xlsx_patch
    return xlsx_patch.write_register(path, headers, rows, sheet, key_header,
                                     "skip" if skip_existing else "update", False, backup)


def read_sheet(path: str | Path, sheet: str | None = None, limit: int = 2000) -> dict:
    """Baca isi sheet (nilai, bukan rumus) untuk ditampilkan / dipakai GC-Ex."""
    wb = load_workbook(Path(path), read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    rows = []
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i >= limit:
            break
        rows.append([v.isoformat() if hasattr(v, "isoformat") else v for v in r])
    return {"sheets": wb.sheetnames, "sheet": ws.title, "rows": rows}
