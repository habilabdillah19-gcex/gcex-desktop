"""Koneksi MS Access (.accdb / .mdb) lewat ODBC.

Butuh driver "Microsoft Access Driver (*.mdb, *.accdb)" 64-bit di Windows
(terpasang bersama MS Office 64-bit, atau "Microsoft Access Database Engine 2016 Redistributable").
Semua penulisan memakai parameter (aman dari karakter aneh) dan dalam satu transaksi.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import pyodbc  # type: ignore
except Exception:  # pragma: no cover - pyodbc tidak ada di luar Windows/CI
    pyodbc = None

ACCESS_DRIVER_HINT = (
    "Driver MS Access 64-bit tidak ditemukan. Pasang 'Microsoft Access Database Engine 2016 "
    "Redistributable' (x64) dari situs Microsoft, atau MS Office 64-bit."
)


def drivers() -> dict:
    if pyodbc is None:
        return {"pyodbc": False, "drivers": [], "access": None, "hint": "Modul pyodbc tidak tersedia."}
    ds = list(pyodbc.drivers())
    acc = next((d for d in ds if "access" in d.lower() and "accdb" in d.lower()), None)
    return {"pyodbc": True, "drivers": ds, "access": acc, "hint": None if acc else ACCESS_DRIVER_HINT}


@contextmanager
def _connect(path: str | Path, readonly: bool = True):
    """Koneksi yang SELALU ditutup setelah dipakai (file .laccdb tidak tertinggal terkunci)."""
    info = drivers()
    if not info["access"]:
        raise RuntimeError(info["hint"])
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Database tidak ditemukan: {p}")
    cs = f"DRIVER={{{info['access']}}};DBQ={p};" + ("ReadOnly=1;" if readonly else "")
    cn = pyodbc.connect(cs, autocommit=False)
    try:
        yield cn
    finally:
        try:
            cn.close()
        except Exception:
            pass


def _q(name: str) -> str:
    """Kutip nama tabel/kolom Access: [nama]."""
    return "[" + str(name).replace("]", "]]") + "]"


def tables(path: str | Path) -> list[dict]:
    with _connect(path) as cn:
        cur = cn.cursor()
        out = []
        for t in cur.tables(tableType="TABLE"):
            cols = [{"name": c.column_name, "type": c.type_name} for c in cn.cursor().columns(table=t.table_name)]
            out.append({"name": t.table_name, "columns": cols})
        return out


def read(path: str | Path, table: str, limit: int = 1000, where_col: str | None = None, where_val: Any = None) -> dict:
    with _connect(path) as cn:
        cur = cn.cursor()
        sql = f"SELECT TOP {int(limit)} * FROM {_q(table)}"
        params: list[Any] = []
        if where_col:
            sql += f" WHERE {_q(where_col)} = ?"
            params.append(where_val)
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = [[v.isoformat() if hasattr(v, "isoformat") else v for v in r] for r in cur.fetchall()]
        return {"columns": cols, "rows": rows}


def insert(path: str | Path, table: str, columns: list[str], rows: list[list[Any]],
           key_column: str | None = None, skip_existing: bool = True) -> dict:
    """Tambahkan baris ke tabel Access. Kolom yang tidak ada di tabel dilewati (dilaporkan).
    skip_existing + key_column: baris dengan kunci yang sudah ada tidak dimasukkan lagi."""
    with _connect(path, readonly=False) as cn:
        cur = cn.cursor()
        have = {c.column_name.lower(): c.column_name for c in cur.columns(table=table)}
        if not have:
            raise ValueError(f"Tabel '{table}' tidak ditemukan.")
        use = [(i, have[c.lower()]) for i, c in enumerate(columns) if c.lower() in have]
        missing = [c for c in columns if c.lower() not in have]
        if not use:
            raise ValueError("Tidak ada kolom yang cocok dengan tabel Access.")
        existing = set()
        ki = None
        if skip_existing and key_column and key_column.lower() in have:
            ki = columns.index(key_column) if key_column in columns else None
            cur.execute(f"SELECT {_q(have[key_column.lower()])} FROM {_q(table)}")
            existing = {str(r[0]).strip().upper() for r in cur.fetchall() if r[0] is not None}
        sql = f"INSERT INTO {_q(table)} ({', '.join(_q(n) for _, n in use)}) VALUES ({', '.join('?' for _ in use)})"
        added, skipped = 0, []
        try:
            for r in rows:
                if ki is not None and str(r[ki]).strip().upper() in existing:
                    skipped.append(r[ki])
                    continue
                cur.execute(sql, [r[i] if i < len(r) else None for i, _ in use])
                added += 1
            cn.commit()
        except Exception:
            cn.rollback()
            raise
        return {"table": table, "added": added, "skipped_existing": skipped, "missing_columns": missing}


def create_db(path: str | Path) -> None:
    """Buat file .accdb kosong (Windows, lewat driver ODBC Access: SQLConfigDataSourceW CREATE_DB)."""
    import ctypes
    import sys
    p = Path(path)
    if p.exists():
        return
    if sys.platform != "win32":
        raise RuntimeError("Membuat database MS Access baru hanya bisa di Windows.")
    info = drivers()
    if not info["access"]:
        raise RuntimeError(info["hint"])
    p.parent.mkdir(parents=True, exist_ok=True)
    attrs = f'CREATE_DB="{p}" General\0\0'
    ok = ctypes.windll.ODBCCP32.SQLConfigDataSourceW(None, 1, info["access"], attrs)  # 1 = ODBC_ADD_DSN
    if not ok or not p.exists():
        raise RuntimeError(f"Gagal membuat database Access baru: {p}")


def ensure_table(path: str | Path, table: str, cols: list[tuple[str, str]], key: str | None = None) -> bool:
    """Buat tabel bila belum ada (cols: [(nama, 'TEXT'|'NUM'|'DATE'|'BOOL')]); kolom yang belum ada ditambahkan.
    Kembalikan True bila tabel baru dibuat."""
    tmap = {"TEXT": "TEXT(255)", "NUM": "DOUBLE", "DATE": "DATETIME", "BOOL": "BIT"}
    with _connect(path, readonly=False) as cn:
        cur = cn.cursor()
        names = {t.table_name.lower() for t in cur.tables(tableType="TABLE")}
        if table.lower() not in names:
            spec = ", ".join(f"{_q(n)} {tmap[t]}" + (" NOT NULL PRIMARY KEY" if key and n == key else "") for n, t in cols)
            cur.execute(f"CREATE TABLE {_q(table)} ({spec})")
            cn.commit()
            return True
        have = {c.column_name.lower() for c in cn.cursor().columns(table=table)}
        for n, t in cols:
            if n.lower() not in have:
                cur.execute(f"ALTER TABLE {_q(table)} ADD COLUMN {_q(n)} {tmap[t]}")
        cn.commit()
        return False
