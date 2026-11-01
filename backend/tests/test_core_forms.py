"""Uji ruang kerja Borang DB-Ex: tambah scan / PDF (per halaman), AI (Ollama tiruan; galat = tanpa data tiruan), edit &
verifikasi, validasi Ore Spotter & RC, kolom turunan & pivot, ekspor Excel / CSV / SQLite / MS Access (tiruan ODBC).
Semua data fiktif."""
import json
import sqlite3
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend import core_forms as cf, core_io  # noqa: E402

ORE_AI = {"header": {"tanggal": "30-Oct-26", "shift": "Siang", "spotter": "Spotter A", "pit": "PIT-X", "block": "24", "elevasi": "250",
                     "jenis_ore": "OX-LG", "tujuan": "ROM 418", "ragu": ["spotter"]},
          "rows": [{"jam": "06.30", "id_truk": "DT 4035", "jenis_ore": "", "tujuan": "", "ton": "30", "ragu": []},
                   {"jam": "06:46", "id_truk": "DT4046", "jenis_ore": "OX-LG", "tujuan": "ROM 418", "ton": "30", "ragu": ["id_truk"]},
                   {"jam": "07:05", "id_truk": "DT4051", "jenis_ore": "OX-MO", "tujuan": "Crusher", "ton": "3O", "ragu": ["ton"]},
                   {"jam": "", "id_truk": "", "jenis_ore": "", "tujuan": "", "ton": ""}],
          "catatan": "baris ke-3 tonase kurang jelas"}
RC_AI = {"header": {"hole_id": "DP-900", "tanggal": "20/01/2026"},
         "rows": [{"sample_id": "DP 900001 ZA", "from_m": "0", "to_m": "1", "remark": ""},
                  {"sample_id": "DP 900002 ZA", "from_m": "1", "to_m": "2", "remark": "std"},
                  {"sample_id": "DP 900003 ZA", "from_m": "2.5", "to_m": "3", "remark": "", "ragu": ["from_m"]},
                  {"sample_id": "DP 900005 ZA", "from_m": "3", "to_m": "3", "remark": "Blank"},
                  {"sample_id": "DP 900005 ZA", "from_m": "3", "to_m": "4", "remark": "xx"}]}


@pytest.fixture()
def st(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "proyek"
    d.mkdir()
    core_io._PROJECTS.clear()
    cf._STORES.clear()
    return cf.store(str(d)), tmp_path


def _scan(tmp, name="borang.jpg", size=(1200, 900)):
    f = tmp / "scan" / name
    f.parent.mkdir(exist_ok=True)
    im = Image.new("RGB", size, "white")
    dr = ImageDraw.Draw(im)
    for y in range(100, size[1], 60):
        dr.line([(50, y), (size[0] - 50, y)], fill="black", width=2)
    dr.text((60, 40), "BORANG FIKTIF", fill="black")
    im.save(f)
    return f


def _ai(monkeypatch, res):
    calls = []

    def fake(url, body=None, timeout=5.0):
        calls.append(body)
        return {"message": {"content": json.dumps(res)}}
    monkeypatch.setattr(core_io, "_http", fake)
    return calls


def test_add_pdf_pages_and_rotation(st):
    s, tmp = st
    pages = [Image.new("RGB", (800, 1100), "white"), Image.new("RGB", (800, 1100), (250, 250, 250))]
    pdf = tmp / "scan" / "rc_log.pdf"
    pdf.parent.mkdir(exist_ok=True)
    pages[0].save(pdf, save_all=True, append_images=pages[1:])
    made = cf.add_file(s, str(pdf), "rc", "Rina")
    assert [d["name"] for d in made] == ["rc_log.pdf hal 1", "rc_log.pdf hal 2"] and all((s.scans / d["file"]).exists() for d in made)
    assert made[0]["w"] > 1500  # dirender +- 2400 px agar tulisan tangan terbaca
    d = cf.update_doc(s, made[0]["id"], {"rot": 90}, "Rina")
    assert d["rot"] == 90
    with pytest.raises(ValueError, match="Rotasi"):
        cf.update_doc(s, made[0]["id"], {"rot": 45}, "Rina")
    with pytest.raises(ValueError, match="format"):
        bad = tmp / "scan" / "x.txt"
        bad.write_text("x")
        cf.add_file(s, str(bad), "rc", "Rina")
    with pytest.raises(ValueError, match="Jenis"):
        cf.add_file(s, str(_scan(tmp)), "lain", "Rina")
    cf.delete_doc(s, made[1]["id"], "Rina")
    assert [d["id"] for d in cf.docs(s)] == [made[0]["id"]]


def test_ore_spotter_ai_validate_derive_pivot(st, monkeypatch):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp)), "ore", "Rina")[0]["id"]
    calls = _ai(monkeypatch, ORE_AI)
    j = cf.ai_read(s, did, "http://x", "qwen2.5vl:7b", "tulisan miring")
    assert calls[0]["format"]["required"] == ["header", "rows"] and "tulisan miring" in calls[0]["messages"][0]["content"]
    assert len(j["rows"]) == 3 and j["doc"]["status"] == "done" and j["doc"]["hdr_unc"] == ["spotter"]  # baris kosong dilewati
    rs = j["rows"]
    assert rs[1]["unc"] == ["id_truk"] and rs[2]["unc"] == ["ton"]
    d = cf.doc(s, did)
    v = cf.validate(d, rs)
    assert v["rows"][rs[2]["id"]]["ton"] == "tonase harus angka" and not v["header"]
    recs = cf.records(d, rs)
    r0 = recs[0]
    assert (r0["tanggal"], r0["jam"], r0["id_truk"], r0["jenis_ore"], r0["tujuan"], r0["kode_shift"], r0["kode_ore"], r0["kode_tujuan"]) == \
        ("2026-10-30", "06:30", "DT4035", "OX-LG", "ROM 418", "DS", "OXLG", "418")
    assert r0["kunci_poligon"] == "PIT-X_250_24_30Oct26_OXLG_418" and recs[2]["kode_tujuan"] == "CRUSHER"
    # edit baris 3 (ton) -> tidak ragu lagi, ditandai diedit; header diedit tetap saat AI diulang
    rows = [{"id": r["id"], "data": dict(r["data"]), "verified": True} for r in rs]
    rows[2]["data"]["ton"] = "30"
    rs = cf.save_rows(s, did, rows, "Rina")
    assert rs[2]["unc"] == [] and rs[2]["edited"] == ["ton"] and all(r["verified"] for r in rs) and rs[0]["verified_by"] == "Rina"
    cf.update_doc(s, did, {"header": {"spotter": "Spotter B"}}, "Rina")
    assert cf.doc(s, did)["hdr_unc"] == []
    pv = cf.pivots(cf.records(cf.doc(s, did), rs))
    assert pv["shift"] == [{"tanggal": "2026-10-30", "shift": "Siang", "kode_shift": "DS", "ritase": 3, "tonase": 90.0}]
    assert pv["front"][0]["ritase_siang"] == 3 and pv["front"][0]["ritase_malam"] == 0
    assert {(x["tujuan"], x["jenis_ore"], x["ritase"]) for x in pv["tujuan"]} == {("ROM 418", "OX-LG", 2), ("Crusher", "OX-MO", 1)}
    _ai(monkeypatch, ORE_AI)
    cf.ai_read(s, did, "http://x", "m")
    assert cf.doc(s, did)["header"]["spotter"] == "Spotter B"  # editan header tidak ditimpa AI
    # header shift tidak dikenal
    cf.update_doc(s, did, {"header": {"shift": "Sore?"}}, "Rina")
    assert "shift" in cf.validate(cf.doc(s, did), cf.rows(s, did))["header"]


def test_ai_failure_leaves_no_fake_data(st, monkeypatch):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp)), "rc", "Rina")[0]["id"]

    def down(url, body=None, timeout=5.0):
        raise ConnectionRefusedError("Ollama tidak aktif")
    monkeypatch.setattr(core_io, "_http", down)
    with pytest.raises(ConnectionRefusedError):
        cf.ai_read(s, did, "http://x", "m")
    d = cf.doc(s, did)
    assert d["status"] == "error" and "Ollama" in d["error"] and cf.rows(s, did) == []


def test_rc_validation_qaqc_and_cross_doc(st, monkeypatch):
    s, tmp = st
    a = cf.add_file(s, str(_scan(tmp, "a.jpg")), "rc", "Rina")[0]["id"]
    b = cf.add_file(s, str(_scan(tmp, "b.jpg")), "rc", "Rina")[0]["id"]
    _ai(monkeypatch, RC_AI)
    cf.ai_read(s, a, "http://x", "m")
    d, rs = cf.doc(s, a), cf.rows(s, a)
    v = cf.validate(d, rs)["rows"]
    assert "bolong" in v[rs[2]["id"]]["from_m"]
    assert "lebih besar" in v[rs[3]["id"]]["to_m"]
    assert "meloncat" in v[rs[3]["id"]]["sample_id"]
    assert "kembar" in v[rs[4]["id"]]["sample_id"] and "bukan STD" in v[rs[4]["id"]]["remark"]
    assert rs[1]["id"] not in v  # "std" -> STD sah
    recs = cf.records(d, rs)
    assert recs[1]["remark"] == "STD" and recs[3]["remark"] == "BLANK" and recs[0]["tanggal"] == "2026-01-20" and recs[2]["from_m"] == 2.5
    cf.save_rows(s, b, [{"data": {"sample_id": "DP 900002 ZA", "from_m": "5", "to_m": "6", "remark": ""}}], "Rina")
    cf.update_doc(s, b, {"header": {"hole_id": "DP-901", "tanggal": "21/01/2026"}}, "Rina")
    vb = cf.validate(cf.doc(s, b), cf.rows(s, b), cf.other_ids(s, b))["rows"]
    assert "sudah ada di borang" in list(vb.values())[0]["sample_id"]
    with pytest.raises(ValueError, match="tidak bisa diganti"):
        cf.update_doc(s, a, {"type": "ore"}, "Rina")


def test_exports_xlsx_csv_sqlite_access(st, monkeypatch):
    from openpyxl import load_workbook
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp)), "ore", "Rina")[0]["id"]
    _ai(monkeypatch, ORE_AI)
    cf.ai_read(s, did, "http://x", "m")
    rs = cf.rows(s, did)
    # bawaan: hanya baris terverifikasi
    c = cf.collect(s, [], "ore")
    assert c["recs"] == [] and c["skipped_unverified"] == 3
    rows = [{"id": r["id"], "data": dict(r["data"], ton="30"), "verified": i < 2} for i, r in enumerate(rs)]
    cf.save_rows(s, did, rows, "Rina")
    c = cf.collect(s, [did], "ore")
    assert len(c["recs"]) == 2 and c["skipped_unverified"] == 1
    assert len(cf.collect(s, [did], "ore", unverified=True)["recs"]) == 3
    wb = load_workbook(io_bytes(cf.to_xlsx("ore", c["recs"])))
    assert wb.sheetnames == ["Import_Data_A_sampai_K", "Pivot_Per_Shift", "Pivot_Per_Lokasi_Pit", "Pivot_Per_Tujuan_Dumping", "Audit"]
    ws = wb["Import_Data_A_sampai_K"]
    assert [c.value for c in ws[1]][:3] == ["Tanggal", "Shift", "Spotter"] and ws["A2"].value.year == 2026 and ws["K2"].value == 30
    assert ws["O2"].value == "PIT-X_250_24_30Oct26_OXLG_418"
    assert wb["Pivot_Per_Shift"]["D2"].value == 2
    csv = cf.to_csv("ore", c["recs"]).decode("utf-8-sig").splitlines()
    assert csv[0].startswith("TANGGAL,SHIFT,SPOTTER") and csv[1].startswith("2026-10-30,Siang")
    # SQLite: dua kali ekspor tidak menggandakan baris; view pivot
    db = tmp / "out" / "borang.db"
    r1 = cf.to_sqlite(str(db), "ore", c["recs"])
    r2 = cf.to_sqlite(str(db), "ore", cf.collect(s, [did], "ore", unverified=True)["recs"])
    assert (r1["added"], r2["added"], r2["updated"], r2["total"]) == (2, 1, 2, 3)
    cn = sqlite3.connect(str(db))
    assert cn.execute("SELECT RITASE, TONASE FROM PIVOT_PER_SHIFT").fetchone() == (3, 90.0)
    assert cn.execute("SELECT COUNT(*) FROM ORE_SPOTTER WHERE VERIFIED=0").fetchone()[0] == 1
    cn.close()
    # MS Access (ODBC tiruan: memastikan urutan buat db -> tabel -> insert dengan kunci SRC_KEY)
    from gcex_backend import access_io
    log = []
    monkeypatch.setattr(access_io, "create_db", lambda p: log.append(("db", p)))
    monkeypatch.setattr(access_io, "ensure_table", lambda p, t, cols, key=None: log.append(("tb", t, [c[0] for c in cols], key)) or True)
    monkeypatch.setattr(access_io, "insert", lambda p, t, names, data, key_column=None, skip_existing=True:
                        log.append(("ins", t, names, len(data), key_column)) or {"added": len(data), "skipped_existing": []})
    r = cf.to_access(str(tmp / "out" / "borang.accdb"), "ore", c["recs"])
    assert r == {"table": "ORE_SPOTTER", "added": 2, "existing": 0, "db_created": True, "table_created": True}
    assert log[0][0] == "db" and log[1][3] == "SRC_KEY" and "KUNCI_POLIGON" in log[1][2] and log[2][4] == "SRC_KEY"


def io_bytes(b):
    import io
    return io.BytesIO(b)
