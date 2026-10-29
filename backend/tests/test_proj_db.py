import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend import proj_db as P  # noqa: E402


def _tables(n=3, ton=100.0):
    return [{"name": "digblock", "key": ["id"], "cols": ["id", "rl_atas", "rl_bawah", "nama", "material", "tujuan", "luas", "ton", "kadar", "flag", "titik"],
             "rows": [[f"d{i}", 292.5, 290, f"DB{i}", "HG", "R418", 25.0, ton + i, 1.2, "Ore Sulfide" if i == 0 else "", [[0, 0], [1, 0], [1, 1]]] for i in range(n)]},
            {"name": "asmined", "key": ["id"], "cols": ["id", "rl_atas", "rl_bawah", "kode", "nama", "aktif", "dihitung", "bcm", "ton", "kadar", "titik"],
             "rows": [["a0", 292.5, 290, "HGOX", "AM1", 1, 1, 40.0, 98.0, 1.0, [[0, 0]]]]}]


def test_sync_history_and_view(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "c"))
    k = "folderA|Latihan"
    r = P.sync(k, "bm", "Habil", "0.20.3", _tables())
    assert r["tabel"]["digblock"]["baris"] == 3 and r["tabel"]["digblock"]["tambah"] == 3
    t = _tables(n=2, ton=150.0)  # d0,d1 berubah tonase, d2 dihapus
    r = P.sync(k, "bm", "Habil", "0.20.3", t)
    assert r["tabel"]["digblock"] == {"baris": 2, "tambah": 0, "ubah": 2, "hapus": 1}
    db = tmp_path / "x.db"
    db.write_bytes(P.read_bytes(k))
    c = sqlite3.connect(db)
    acts = [a for (a,) in c.execute("SELECT aksi FROM riwayat WHERE tabel='digblock' ORDER BY id")]
    assert acts == ["impor", "ubah", "ubah", "hapus"]
    rk = c.execute("SELECT dig_block, ton_rencana, poligon_asmined, ton_aktual FROM rekap_flitch").fetchone()
    assert rk == (2, 301.0, 1, 98.0)
    assert c.execute("SELECT COUNT(*) FROM sinkron").fetchone()[0] == 2
    # kolom baru ditambahkan tanpa menghapus yang lama
    t[0]["cols"].append("catatan")
    for row in t[0]["rows"]:
        row.append("ok")
    P.sync(k, "bm", "Habil", "0.20.3", t)
    c2 = sqlite3.connect(":memory:")
    c2.close()
    db.write_bytes(P.read_bytes(k))
    c = sqlite3.connect(db)
    assert "catatan" in [r[1] for r in c.execute("PRAGMA table_info(digblock)")]


def test_load_rejects_non_sqlite(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "c"))
    import pytest
    with pytest.raises(ValueError):
        P.load("k", b"bukan sqlite")
    P.sync("k2", "dh", "u", "0.20.1", _tables())
    data = P.read_bytes("k2")
    assert P.load("k3", data)["loaded"] and P.info("k3")["tabel"]["digblock"] == 3
