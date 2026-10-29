"""Database proyek GC-Ex (SQLite) - satu file `gcex_proyek.db` di folder proyek.

GC-Ex (Block Model / Drill Hole Ultimate) mengirim isi proyek sebagai tabel (kolom + baris) setiap kali proyek
disimpan ke folder. Backend memperbarui salinan kerja SQLite (cache per proyek), mencatat setiap perubahan baris di
tabel `riwayat` (tambah / ubah / hapus beserta data lama), lalu mengembalikan file .db untuk ditulis ke folder proyek.
File .db bisa dibuka langsung dengan DB Browser for SQLite, Excel (ODBC), QGIS, Python, dll.

Tabel dibuat otomatis dari spesifikasi yang dikirim: {"name", "key": [kolom kunci], "cols": [kolom], "rows": [[...]]}.
Kolom baru ditambahkan (ALTER TABLE) tanpa menghapus kolom lama. Impor pertama sebuah tabel dicatat ringkas (satu baris).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

from . import mdl_io

DB_NAME = "gcex_proyek.db"
SCHEMA_VER = 1
_LOCK = threading.Lock()
_IDENT = re.compile(r"[^0-9A-Za-z_]+")


def _ident(s: str) -> str:
    """Nama tabel / kolom SQLite yang aman (huruf, angka, _)."""
    t = _IDENT.sub("_", str(s)).strip("_") or "kolom"
    if t[0].isdigit():
        t = "k_" + t
    return t[:60]


def cache_path(key: str) -> Path:
    d = mdl_io.cache_root() / "projdb"
    d.mkdir(parents=True, exist_ok=True)
    return d / (hashlib.sha1(key.encode("utf-8")).hexdigest()[:24] + ".db")


def _connect(p: Path) -> sqlite3.Connection:
    c = sqlite3.connect(str(p), timeout=30)
    c.execute("PRAGMA journal_mode=DELETE")  # satu file saja (tanpa -wal) supaya aman disalin ke folder proyek
    c.execute("PRAGMA foreign_keys=OFF")
    c.executescript(
        """CREATE TABLE IF NOT EXISTS meta(kunci TEXT PRIMARY KEY, nilai TEXT);
        CREATE TABLE IF NOT EXISTS riwayat(id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT, pengguna TEXT, aplikasi TEXT,
            tabel TEXT, kunci TEXT, aksi TEXT, data_lama TEXT, data_baru TEXT);
        CREATE INDEX IF NOT EXISTS ix_riwayat_tabel ON riwayat(tabel, kunci);
        CREATE TABLE IF NOT EXISTS sinkron(id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT, pengguna TEXT, aplikasi TEXT,
            versi TEXT, ringkasan TEXT);""")
    return c


def load(key: str, data: bytes) -> dict:
    """Pasang file .db dari folder proyek sebagai salinan kerja (dipanggil saat folder proyek dibuka)."""
    p = cache_path(key)
    if not data:
        return {"ok": True, "loaded": False}
    if not data.startswith(b"SQLite format 3\x00"):
        raise ValueError(f"{DB_NAME} di folder proyek bukan file SQLite.")
    with _LOCK:
        tmp = p.with_suffix(".tmp")
        tmp.write_bytes(data)
        c = sqlite3.connect(str(tmp))
        try:
            ok = c.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            c.close()
        if ok != "ok":
            tmp.unlink(missing_ok=True)
            raise ValueError(f"{DB_NAME} rusak ({ok}); salinan kerja tidak diganti.")
        os.replace(tmp, p)
    return {"ok": True, "loaded": True, "bytes": len(data)}


def _cols(c: sqlite3.Connection, t: str) -> list[str]:
    return [r[1] for r in c.execute(f'PRAGMA table_info("{t}")')]


def _norm(v: Any) -> Any:
    if isinstance(v, float) and v != v:
        return None
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    return v


def sync(key: str, app: str, user: str, version: str, tables: list[dict]) -> dict:
    """Perbarui tabel proyek & catat riwayat. Hasil: ringkasan per tabel."""
    p = cache_path(key)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    summ = {}
    with _LOCK:
        c = _connect(p)
        try:
            c.execute("BEGIN")
            for T in tables:
                name = _ident(T["name"])
                cols = [_ident(x) for x in T["cols"]]
                key_cols = [_ident(x) for x in T.get("key") or cols[:1]]
                rows = T.get("rows") or []
                ki = [cols.index(k) for k in key_cols]
                exist = _cols(c, name)
                first = not exist
                if first:
                    c.execute(f'CREATE TABLE "{name}" (' + ", ".join(f'"{x}"' for x in cols) + ")")
                    c.execute(f'CREATE INDEX "ix_{name}_kunci" ON "{name}" (' + ", ".join(f'"{x}"' for x in key_cols) + ")")
                else:
                    for x in cols:
                        if x not in exist:
                            c.execute(f'ALTER TABLE "{name}" ADD COLUMN "{x}"')
                exist = _cols(c, name)
                # isi lama (kolom yang dikirim saja) per kunci
                sel = ", ".join(f'"{x}"' for x in cols)
                old: dict[str, tuple] = {}
                if not first:
                    for r in c.execute(f'SELECT rowid, {sel} FROM "{name}"'):
                        k = json.dumps([r[1 + i] for i in ki], ensure_ascii=False)
                        old[k] = r
                n_add = n_upd = n_del = 0
                seen = set()
                log = []
                ins = f'INSERT INTO "{name}" ({sel}) VALUES (' + ",".join("?" * len(cols)) + ")"
                upd = f'UPDATE "{name}" SET ' + ", ".join(f'"{x}"=?' for x in cols) + " WHERE rowid=?"
                for r in rows:
                    v = tuple(_norm(x) for x in r)
                    k = json.dumps([v[i] for i in ki], ensure_ascii=False)
                    if k in seen:
                        continue
                    seen.add(k)
                    o = old.get(k)
                    if o is None:
                        c.execute(ins, v)
                        n_add += 1
                        if not first:
                            log.append((k, "tambah", None, json.dumps(dict(zip(cols, v)), ensure_ascii=False)))
                    elif tuple(o[1:]) != v:
                        c.execute(upd, v + (o[0],))
                        n_upd += 1
                        log.append((k, "ubah", json.dumps(dict(zip(cols, o[1:])), ensure_ascii=False),
                                    json.dumps(dict(zip(cols, v)), ensure_ascii=False)))
                if T.get("full", True):
                    for k, o in old.items():
                        if k not in seen:
                            c.execute(f'DELETE FROM "{name}" WHERE rowid=?', (o[0],))
                            n_del += 1
                            log.append((k, "hapus", json.dumps(dict(zip(cols, o[1:])), ensure_ascii=False), None))
                if first and rows:
                    log = [("*", "impor", None, json.dumps({"baris": len(seen), "kolom": cols}, ensure_ascii=False))]
                if len(log) > 5000:  # perubahan massal (mis. impor ulang database): ringkas + 5000 contoh
                    log = log[:5000] + [("*", "ringkas", None, json.dumps({"tambah": n_add, "ubah": n_upd, "hapus": n_del}))]
                c.executemany("INSERT INTO riwayat(waktu,pengguna,aplikasi,tabel,kunci,aksi,data_lama,data_baru) VALUES (?,?,?,?,?,?,?,?)",
                              [(now, user, app, name, k, a, lo, ln) for k, a, lo, ln in log])
                summ[name] = {"baris": len(seen), "tambah": n_add if not first else len(seen), "ubah": n_upd, "hapus": n_del}
            for v in T_VIEWS:
                try:
                    c.execute(v)
                except sqlite3.OperationalError:
                    pass  # tabel sumber view belum ada di aplikasi ini
            c.execute("INSERT OR REPLACE INTO meta VALUES ('schema', ?)", (str(SCHEMA_VER),))
            c.execute("INSERT OR REPLACE INTO meta VALUES ('kunci_proyek', ?)", (key,))
            c.execute("INSERT OR REPLACE INTO meta VALUES ('terakhir_" + _ident(app) + "', ?)", (now,))
            c.execute("INSERT INTO sinkron(waktu,pengguna,aplikasi,versi,ringkasan) VALUES (?,?,?,?,?)",
                      (now, user, app, version, json.dumps(summ, ensure_ascii=False)))
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise
        finally:
            c.close()
    return {"ok": True, "tabel": summ, "waktu": now, "bytes": p.stat().st_size}


T_VIEWS = [
    # rekap per flitch: rencana (dig block) vs aktual (as-mined)
    """CREATE VIEW IF NOT EXISTS rekap_flitch AS
       SELECT f.rl_atas, f.rl_bawah,
              (SELECT COUNT(*) FROM digblock d WHERE d.rl_atas=f.rl_atas AND d.rl_bawah=f.rl_bawah) AS dig_block,
              (SELECT ROUND(SUM(ton),1) FROM digblock d WHERE d.rl_atas=f.rl_atas AND d.rl_bawah=f.rl_bawah) AS ton_rencana,
              (SELECT ROUND(SUM(ton*kadar)/NULLIF(SUM(CASE WHEN kadar IS NOT NULL THEN ton END),0),3) FROM digblock d WHERE d.rl_atas=f.rl_atas AND d.rl_bawah=f.rl_bawah) AS kadar_rencana,
              (SELECT COUNT(*) FROM asmined a WHERE a.rl_atas=f.rl_atas AND a.rl_bawah=f.rl_bawah) AS poligon_asmined,
              (SELECT ROUND(SUM(ton),1) FROM asmined a WHERE a.rl_atas=f.rl_atas AND a.rl_bawah=f.rl_bawah AND a.dihitung=1 AND a.aktif=1) AS ton_aktual,
              (SELECT ROUND(SUM(ton*kadar)/NULLIF(SUM(CASE WHEN kadar IS NOT NULL THEN ton END),0),3) FROM asmined a WHERE a.rl_atas=f.rl_atas AND a.rl_bawah=f.rl_bawah AND a.dihitung=1 AND a.aktif=1) AS kadar_aktual
       FROM (SELECT rl_atas, rl_bawah FROM digblock UNION SELECT rl_atas, rl_bawah FROM asmined) f
       ORDER BY f.rl_atas DESC""",
    # interval assay dengan domain (Drill Hole Ultimate)
    """CREATE VIEW IF NOT EXISTS assay_domain AS
       SELECT a.*, (SELECT f.domain FROM flag_domain f WHERE f.hole_id=a.hole_id AND f.dari<=(a.dari+a.sampai)/2.0
                    AND (a.dari+a.sampai)/2.0<f.sampai LIMIT 1) AS domain
       FROM assay a""",
]


def info(key: str, n_hist: int = 15) -> dict:
    p = cache_path(key)
    if not p.exists():
        return {"ok": True, "ada": False}
    c = sqlite3.connect(str(p))
    try:
        tabs = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sqlite_sequence') ORDER BY name")]
        cnt = {t: c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tabs}
        views = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")]
        hist = [dict(zip(["waktu", "pengguna", "aplikasi", "tabel", "kunci", "aksi"], r)) for r in
                c.execute("SELECT waktu,pengguna,aplikasi,tabel,kunci,aksi FROM riwayat ORDER BY id DESC LIMIT ?", (n_hist,))]
        syn = c.execute("SELECT waktu,pengguna,aplikasi,versi FROM sinkron ORDER BY id DESC LIMIT 1").fetchone()
    finally:
        c.close()
    return {"ok": True, "ada": True, "tabel": cnt, "view": views, "riwayat": hist, "bytes": p.stat().st_size,
            "sinkron": dict(zip(["waktu", "pengguna", "aplikasi", "versi"], syn)) if syn else None}


def read_bytes(key: str) -> bytes:
    p = cache_path(key)
    with _LOCK:
        return p.read_bytes() if p.exists() else b""
