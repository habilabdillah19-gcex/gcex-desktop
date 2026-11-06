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

# borang loading pit (fiktif): jam menit saja, nomor truk singkat, tanda ulang, baris yang hanya mengganti elevasi, lewat tengah malam
ORE_AI = {"header": {"tanggal": "30-10-2026", "shift": "II", "crew": "Spotter A", "lokasi": "Pit X", "excavator": "EX-901",
                     "ragu": ["crew"]},
          "rows": [{"no": "1", "start": "22.40", "finish": "", "pit": "Pit X", "elevasi": "120.5", "kelas": "OX-LG", "unit": "7101",
                    "ton": "35", "tujuan": "ROM A1"},
                   {"no": "2", "start": "52", "finish": "", "pit": "", "elevasi": "", "kelas": "OX-LG", "unit": "02", "ton": "31",
                    "tujuan": "〃", "ragu": ["unit"]},
                   {"no": "3", "start": "", "finish": "", "pit": "", "elevasi": "118.0", "kelas": "", "unit": "", "ton": "", "tujuan": ""},
                   {"no": "4", "start": "03", "finish": "", "pit": "", "elevasi": "", "kelas": "OX-HG", "unit": "7103", "ton": "3O",
                    "tujuan": "〃 B2"},
                   {"no": "5", "start": "00.10", "finish": "", "pit": "", "elevasi": "", "kelas": "〃", "unit": "05", "ton": "33",
                    "tujuan": "250"},
                   {"no": "6", "start": "", "finish": "", "pit": "", "elevasi": "", "kelas": "", "unit": "", "ton": "", "tujuan": ""}],
          "catatan": "baris ke-4 tonase kurang jelas"}
# borang ROM / crusher (fiktif)
ROM_AI = {"header": {"tanggal": "31/10/2026", "shift": "I", "crew": "Spotter B", "lokasi": "ROM A1"},
          "rows": [{"no": "1", "unit": "DT 7101", "start": "", "finish": "08.02", "asal": "Pit X", "tujuan": "Crusher", "rehandling": "SP-1",
                    "kelas": "SF-LG", "ton": "39", "status": "Baru", "keterangan": "Direct"},
                   {"no": "2", "unit": "7102", "start": "", "finish": "05", "asal": "〃", "tujuan": "〃", "rehandling": "〃",
                    "kelas": "SF-LG", "ton": "37", "status": "", "keterangan": ""},
                   {"no": "4", "unit": "7103", "start": "", "finish": "11", "asal": "ROM A1", "tujuan": "=", "rehandling": "",
                    "kelas": "SCAT", "ton": "32", "status": "Lama", "keterangan": "Rehandling"}]}
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


def _ai(monkeypatch, res, raw=None):
    calls = []

    def fake(url, body=None, timeout=5.0):
        if raw is not None and not url.endswith("/api/show"):
            calls.append(body)
            return {"message": {"content": raw}}
        if url.endswith("/api/show"):  # cek kemampuan model (think) bukan panggilan baca borang
            return {"capabilities": ["completion", "vision"]}
        calls.append(body)
        return {"message": {"content": json.dumps(res)}}
    monkeypatch.setattr(core_io, "_http", fake)
    return calls


def test_add_pdf_pages_and_rotation(st):
    pytest.importorskip("pypdfium2")  # pustaka visi DB-Ex Qt (requirements-vision); diuji lagi di langkah Qt & selftest exe
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


def test_ore_loading_pit_fill_validate_pivot(st, monkeypatch):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp)), "ore", "Rina")[0]["id"]
    calls = _ai(monkeypatch, ORE_AI)
    j = cf.ai_read(s, did, "http://x", "qwen2.5vl:7b", "tulisan miring")
    assert "format" not in calls[0] and "R|no|start|finish" in calls[0]["messages"][0]["content"]  # jawaban ringkas, bukan JSON
    assert "tulisan miring" in calls[0]["messages"][0]["content"] and calls[0]["options"]["num_predict"] > 0
    assert "〃" in calls[0]["messages"][0]["content"]
    rs = j["rows"]
    assert len(rs) == 4 and j["doc"]["status"] == "done" and j["doc"]["hdr_unc"] == ["crew"]  # baris elevasi saja & kosong tidak jadi baris
    D = [r["data"] for r in rs]
    assert [x["start"] for x in D] == ["22:40", "22:52", "23:03", "00:10"]       # menit saja -> jam lengkap
    assert [x["unit"] for x in D] == ["7101", "7102", "7103", "7105"]           # nomor truk singkat
    assert [x["elevasi"] for x in D] == ["120.5", "120.5", "118.0", "118.0"]    # elevasi dibawa ke baris berikutnya
    assert [x["tujuan"] for x in D] == ["ROM A1", "ROM A1", "ROM B2", "ROM 250"]  # 〃, '〃 B2', angka saja
    assert D[3]["kelas"] == "OX-HG" and D[1]["pit"] == "Pit X"
    assert set(rs[1]["unc"]) >= {"unit", "start", "tujuan", "pit", "elevasi"} and "kelas" in rs[3]["unc"]
    d = cf.doc(s, did)
    v = cf.validate(d, rs)
    assert v["rows"][rs[2]["id"]]["ton"] == "tonase harus angka" and not v["header"]
    recs = cf.records(d, rs)
    assert (recs[0]["tanggal"], recs[0]["kode_shift"], recs[0]["tanggal_muat"], recs[3]["tanggal_muat"]) == \
        ("2026-10-30", "NS", "2026-10-30", "2026-10-31")
    assert (recs[2]["material"], recs[2]["grade"], recs[0]["excavator"], recs[0]["front"]) == ("OKSIDA", "HG", "EX-901", "Pit X · 120.5")
    # edit baris 3 (ton) -> tidak ragu lagi, ditandai diedit; header diedit tetap saat AI diulang
    rows = [{"id": r["id"], "data": dict(r["data"]), "verified": True} for r in rs]
    rows[2]["data"]["ton"] = "30"
    rs = cf.save_rows(s, did, rows, "Rina")
    assert "ton" not in rs[2]["unc"] and rs[2]["edited"] == ["ton"] and all(r["verified"] for r in rs) and rs[0]["verified_by"] == "Rina"
    cf.update_doc(s, did, {"header": {"crew": "Spotter C"}}, "Rina")
    assert cf.doc(s, did)["hdr_unc"] == []
    pv = {p["key"]: p for p in cf.pivots(cf.records(cf.doc(s, did), rs), "ore")}
    assert pv["PIVOT_PER_SHIFT"]["rows"] == [{"tanggal": "2026-10-30", "shift": "II", "kode_shift": "NS", "ritase": 4, "tonase": 129.0}]
    assert {(x["front"], x["ritase"]) for x in pv["PIVOT_PER_FRONT"]["rows"]} == {("Pit X · 120.5", 2), ("Pit X · 118.0", 2)}
    assert ("ROM B2", "OX-HG", 1) in {(x["tujuan"], x["kelas"], x["ritase"]) for x in pv["PIVOT_TUJUAN_KELAS"]["rows"]}
    # pengguna mengetik tanda ulang & menit saja -> diselesaikan saat disimpan
    rows = [{"id": r["id"], "data": dict(r["data"]), "verified": r["verified"]} for r in rs]
    rows.append({"id": None, "data": {"start": "15", "unit": "06", "kelas": '"', "ton": "34", "tujuan": '"'}})
    rs = cf.save_rows(s, did, rows, "Rina")
    assert (rs[4]["data"]["start"], rs[4]["data"]["unit"], rs[4]["data"]["kelas"], rs[4]["data"]["tujuan"]) == ("00:15", "7106", "OX-HG", "ROM 250")
    # jam di luar shift malam & mundur
    rows = [{"id": r["id"], "data": dict(r["data"]), "verified": r["verified"]} for r in rs]
    rows[4]["data"]["start"] = "11:00"
    rs = cf.save_rows(s, did, rows, "Rina")
    assert "di luar shift malam" in cf.validate(cf.doc(s, did), rs)["rows"][rs[4]["id"]]["start"]
    _ai(monkeypatch, ORE_AI)
    cf.ai_read(s, did, "http://x", "m")
    assert cf.doc(s, did)["header"]["crew"] == "Spotter C"  # editan header tidak ditimpa AI
    cf.update_doc(s, did, {"header": {"shift": "Sore?", "excavator": ""}}, "Rina")
    assert {"shift", "excavator"} <= set(cf.validate(cf.doc(s, did), cf.rows(s, did))["header"])


def test_rom_crusher_fill_and_derive(st, monkeypatch):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp)), "rom", "Rina")[0]["id"]
    _ai(monkeypatch, ROM_AI)
    rs = cf.ai_read(s, did, "http://x", "m")["rows"]
    D = [r["data"] for r in rs]
    assert [x["finish"] for x in D] == ["08:02", "08:05", "08:11"]
    assert (D[1]["asal"], D[1]["tujuan"], D[1]["rehandling"], D[1]["status"], D[1]["keterangan"]) == ("Pit X", "Crusher", "SP-1", "Baru", "Direct")
    assert D[2]["tujuan"] == "Crusher" and D[2]["rehandling"] == ""
    v = cf.validate(cf.doc(s, did), rs)
    assert "tidak urut" not in str(v) and not v["header"]
    # jam shift site: I / DS 06-18, II / NS 18-06
    late = [dict(r, data=dict(r["data"], finish=t)) for r, t in zip(rs, ("05:59", "17:59", "18:00"))]
    bad = cf.validate(cf.doc(s, did), late)["rows"]
    assert "06:00-18:00" in bad[rs[0]["id"]]["finish"] and "finish" not in bad.get(rs[1]["id"], {}) and "finish" in bad[rs[2]["id"]]
    recs = cf.records(cf.doc(s, did), rs)
    assert (recs[0]["unit"], recs[0]["jenis"], recs[2]["jenis"], recs[2]["material"], recs[0]["kode_shift"]) == \
        ("7101", "DIRECT", "REHANDLING", "SCAT", "DS")
    pv = {p["key"]: p for p in cf.pivots(recs, "rom")}
    assert {(x["asal"], x["jenis"], x["ritase"]) for x in pv["PIVOT_ASAL_TUJUAN"]["rows"]} == {("Pit X", "DIRECT", 2), ("ROM A1", "REHANDLING", 1)}


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
    assert c["recs"] == [] and c["skipped_unverified"] == 4
    rows = [{"id": r["id"], "data": dict(r["data"], ton="30"), "verified": i < 2} for i, r in enumerate(rs)]
    cf.save_rows(s, did, rows, "Rina")
    c = cf.collect(s, [did], "ore")
    assert len(c["recs"]) == 2 and c["skipped_unverified"] == 2
    assert len(cf.collect(s, [did], "ore", unverified=True)["recs"]) == 4
    wb = load_workbook(io_bytes(cf.to_xlsx("ore", c["recs"])))
    assert wb.sheetnames == ["Data_Loading_Pit", "Pivot_Per_Shift", "Pivot_Per_Front", "Pivot_Tujuan_Kelas", "Audit"]
    ws = wb["Data_Loading_Pit"]
    hd = [c.value for c in ws[1]]
    assert hd[:4] == ["Tanggal", "Shift", "Kode Shift", "Nama Crew"] and ws["A2"].value.year == 2026
    assert ws.cell(2, hd.index("Tonnage") + 1).value == 30 and ws.cell(2, hd.index("Truck") + 1).value == "7101"
    assert wb["Pivot_Per_Shift"]["D2"].value == 2
    csv = cf.to_csv("ore", c["recs"]).decode("utf-8-sig").splitlines()
    assert csv[0].startswith("TANGGAL,SHIFT,KODE_SHIFT,CREW") and csv[1].startswith("2026-10-30,II,NS")
    # SQLite: dua kali ekspor tidak menggandakan baris; view pivot
    db = tmp / "out" / "borang.db"
    r1 = cf.to_sqlite(str(db), "ore", c["recs"])
    r2 = cf.to_sqlite(str(db), "ore", cf.collect(s, [did], "ore", unverified=True)["recs"])
    assert (r1["added"], r2["added"], r2["updated"], r2["total"]) == (2, 2, 2, 4)
    cn = sqlite3.connect(str(db))
    assert cn.execute("SELECT RITASE, TONASE FROM ORE_LOADING_PIT_PIVOT_PER_SHIFT").fetchone() == (4, 120.0)
    assert cn.execute("SELECT COUNT(*) FROM ORE_LOADING_PIT WHERE VERIFIED=0").fetchone()[0] == 2
    cn.close()
    # MS Access (ODBC tiruan: memastikan urutan buat db -> tabel -> insert dengan kunci SRC_KEY)
    from gcex_backend import access_io
    log = []
    monkeypatch.setattr(access_io, "create_db", lambda p: log.append(("db", p)))
    monkeypatch.setattr(access_io, "ensure_table", lambda p, t, cols, key=None: log.append(("tb", t, [c[0] for c in cols], key)) or True)
    monkeypatch.setattr(access_io, "insert", lambda p, t, names, data, key_column=None, skip_existing=True:
                        log.append(("ins", t, names, len(data), key_column)) or {"added": len(data), "skipped_existing": []})
    r = cf.to_access(str(tmp / "out" / "borang.accdb"), "ore", c["recs"])
    assert r == {"table": "ORE_LOADING_PIT", "added": 2, "existing": 0, "db_created": True, "table_created": True}
    assert log[0][0] == "db" and log[1][3] == "SRC_KEY" and "EXCAVATOR" in log[1][2] and log[2][4] == "SRC_KEY"


def io_bytes(b):
    import io
    return io.BytesIO(b)


DDR_AI = {"header": {"tanggal": "31-10-26", "shift": "I", "rig": "hansin sdr-07", "driller": "Driller A", "client": "Klien A", "dhp_id": "KTR",
                     "wh": "5hr", "dl": "7hrs", "mntc": "", "bd": "", "rain": "", "std": "", "hm_start": "1200.5", "hm_finish": "1203.7",
                     "hm_running": "", "catatan": "area drillpad longsor, menunggu area baru", "ragu": ["dhp_id"]},
          "rows": [{"mulai": "0650", "selesai": "0700", "aktivitas": "Traveling to ROM", "kategori": ""},
                   {"mulai": "07.00", "selesai": "07.05", "aktivitas": "P5M", "kategori": ""},
                   {"mulai": "0705", "selesai": "0710", "aktivitas": "Traveling to pit", "kategori": ""},
                   {"mulai": "0710", "selesai": "0725", "aktivitas": "P2H", "kategori": ""},
                   {"mulai": "0725", "selesai": "0840", "aktivitas": "Start engine + cleaning siklon", "kategori": ""},
                   {"mulai": "0840", "selesai": "1150", "aktivitas": "Start drilling + cleaning siklon", "kategori": ""},
                   {"mulai": "1150", "selesai": "1200", "aktivitas": "Traveling unit ke jarak aman blasting", "kategori": ""},
                   {"mulai": "1200", "selesai": "1300", "aktivitas": "Restaem", "kategori": ""},
                   {"mulai": "1300", "selesai": "1500", "aktivitas": "Standby area titik bor longsor", "kategori": ""},
                   {"mulai": "1500", "selesai": "1900", "aktivitas": "Waiting informasi area titik bor", "kategori": "", "ragu": ["selesai"]}],
          "lubang": [{"from_m": "0", "to_m": "30", "hole_id": "XX-100-S-05", "az": "70", "dip": "60"},
                     {"from_m": "0", "to_m": "30", "hole_id": "XX-100-S-01", "az": "60", "dip": "60"},
                     {"from_m": "0", "to_m": "30", "hole_id": "XX-100-S-02", "az": "60", "dip": "60", "ragu": ["az"]}]}


def test_daily_drilling_report_tables_summary_exports(st, monkeypatch):
    from openpyxl import load_workbook
    import zipfile
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp)), "ddr", "Rina")[0]["id"]
    calls = _ai(monkeypatch, DDR_AI)
    cf.ai_read(s, did, "http://x", "m")
    assert "LUBANG|from_m|to_m|hole_id|az|dip" in calls[0]["messages"][0]["content"]
    rs = cf.rows(s, did)
    act = [r for r in rs if r["tbl"] == ""]
    hole = [r for r in rs if r["tbl"] == "hole"]
    assert len(act) == 10 and len(hole) == 3 and hole[2]["unc"] == ["az"]
    assert [r["data"]["hole_id"] for r in hole] == ["XX_100_S_05", "XX_100_S_01", "XX_100_S_02"]  # Hole ID baku: garis bawah
    assert cf.doc(s, did)["header"]["rig"] == "Hanjin 007" and "rig" in cf.doc(s, did)["hdr_unc"]
    assert (act[0]["data"]["mulai"], act[0]["data"]["selesai"]) == ("06:50", "07:00")
    assert [r["data"]["kategori"] for r in act] == ["TRAVELING KE LOKASI", "P5M", "TRAVELING KE LOKASI", "P2H", "PERSIAPAN", "DRILLING",
                                                   "WAIT BLASTING", "ISTIRAHAT", "STANDBY", "STANDBY"]
    assert "kategori" in act[0]["unc"]
    d = cf.doc(s, did)
    v = cf.validate(d, rs)
    assert "di luar shift siang" in v["rows"][act[9]["id"]]["selesai"]  # lembur sampai 19:00
    sm = cf.ddr_summary(d, rs)
    assert (sm["wh"], sm["dl"], sm["wh_akt"], sm["dl_akt"], sm["jam_aktivitas"]) == (5.0, 7.0, 4.75, 7.42, 12.17)
    assert (sm["meter"], sm["n_lubang"], sm["jam_drilling"], sm["hm_running"], sm["m_per_jam"]) == (90.0, 3, 3.17, 3.2, 28.39)
    assert "wh" not in v["header"] and "dl" not in v["header"]  # selisih <= 0.5 jam masih dalam toleransi
    # edit tabel meterage saja tidak menyentuh tabel aktivitas
    hr = [{"id": r["id"], "data": dict(r["data"]), "verified": True} for r in hole]
    hr[2]["data"]["az"] = "65"
    cf.save_rows(s, did, hr, "Rina", "hole")
    rs = cf.rows(s, did)
    assert len([r for r in rs if r["tbl"] == ""]) == 10 and [r for r in rs if r["tbl"] == "hole"][2]["data"]["az"] == "65"
    # kategori diubah pengguna -> WH/DL dari aktivitas berubah, selisih besar ditandai di header
    ar = [{"id": r["id"], "data": dict(r["data"]), "verified": False} for r in rs if r["tbl"] == ""]
    ar[9]["data"]["kategori"] = "drilling"
    rs2 = cf.save_rows(s, did, ar, "Rina")
    assert [r for r in rs2 if r["tbl"] == ""][9]["data"]["kategori"] == "DRILLING"
    assert "wh" in cf.validate(cf.doc(s, did), rs2)["header"]
    ar[9]["data"]["kategori"] = ""  # kosong -> diisi lagi dari kata kunci
    cf.save_rows(s, did, ar, "Rina")
    cf.verify_all(s, did, True, "Rina")
    pv = {p["key"]: p for p in cf.pivots(cf.records(cf.doc(s, did), cf.rows(s, did)), "ddr")}
    assert {(x["kelompok"], x["jam"]) for x in pv["PIVOT_JAM_KELOMPOK"]["rows"]} == {("WH", 4.75), ("DL", 7.42)}
    assert pv["PIVOT_METER_RIG"]["rows"][0]["meter"] == 90.0 and pv["PIVOT_METER_RIG"]["rows"][0]["lubang"] == 3
    c = cf.collect(s, [did], "ddr")
    assert len(c["recs"]) == 17 and [r["_tbl"] for r in c["recs"][13:]] == ["_shift", "_dash", "_dash", "_dash"] and c["recs"][13]["_verified"]
    wb = load_workbook(io_bytes(cf.to_xlsx("ddr", c["recs"])))
    assert wb.sheetnames[:4] == ["Data_Dashboard", "DDR_Aktivitas", "DDR_Meterage", "DDR_Ringkasan_Shift"] and "Pivot_Jam_Kelompok" in wb.sheetnames
    assert wb["DDR_Meterage"].max_row == 4 and wb["DDR_Ringkasan_Shift"].max_row == 2 and wb["Audit"].max_row == 14
    ws = wb["Data_Dashboard"]
    assert [c.value for c in ws[1]][:16] == ["Date", "EqType", "Location", "Shift", "Prospect", "BHID", "Interval_m", "WH", "Maint", "BD",
                                             "Delay", "Standby", "Rain", "Remarks", "Azimuth", "Dip"]
    r2 = [c.value for c in ws[2]][:16]
    assert r2[0].strftime("%d-%b-%Y") == "31-Oct-2026" and ws["A2"].number_format == "dd-mmm-yyyy"
    assert r2[1:8] == ["Hanjin 007", None, "S01", "XX", "XX_100_S_05", 30, 5] and r2[10] == 7 and r2[13].startswith("area drillpad") and r2[14:] == [70, 60]
    r3 = [c.value for c in ws[3]][:16]
    assert r3[5] == "XX_100_S_01" and r3[6] == 30 and r3[7] is None and r3[10] is None and r3[14:] == [60, 60]  # jam hanya di baris pertama
    z = zipfile.ZipFile(io_bytes(cf.to_csv("ddr", c["recs"])))
    assert sorted(z.namelist()) == ["DDR_AKTIVITAS.csv", "DDR_DASHBOARD.csv", "DDR_METERAGE.csv", "DDR_SHIFT.csv"]
    assert z.read("DDR_DASHBOARD.csv").decode("utf-8-sig").startswith("Date,EqType,Location,Shift,Prospect,BHID,Interval_m,WH,Maint")
    db = tmp / "out" / "ddr.db"
    r1 = cf.to_sqlite(str(db), "ddr", c["recs"])
    r2 = cf.to_sqlite(str(db), "ddr", c["recs"])
    assert (r1["added"], r2["added"], r2["updated"]) == (13, 0, 13) and r1["table"] == "DDR_DASHBOARD, DDR_AKTIVITAS, DDR_METERAGE, DDR_SHIFT"
    cn = sqlite3.connect(str(db))
    assert cn.execute("SELECT METER, LUBANG FROM DDR_METERAGE_PIVOT_METER_RIG").fetchone() == (90.0, 3)
    assert cn.execute("SELECT WH, WH_AKT, METER FROM DDR_SHIFT").fetchone() == (5.0, 4.75, 90.0)
    assert cn.execute("SELECT COUNT(*), SUM(INTERVAL_M), SUM(WH), SUM(DELAY) FROM DDR_DASHBOARD").fetchone() == (3, 90.0, 5.0, 7.0)
    cn.close()
    # shift tanpa lubang (mis. standby penuh): satu baris dashboard berisi jam saja
    cf.save_rows(s, did, [], "Rina", "hole")
    dash = cf.ddr_dashboard(cf.doc(s, did), cf.rows(s, did))
    assert len(dash) == 1 and dash[0]["bhid"] == "" and dash[0]["wh"] == 5.0 and dash[0]["dl"] == 7.0


def test_ddr_kategori_kelompok_site():
    k = cf.ddr_kat
    assert k("Traveling unit ke titik bor berikutnya") == "TRAVELING ANTAR TITIK BOR" and k("Pindah lubang") == "TRAVELING ANTAR TITIK BOR"
    assert k("Traveling to ROM") == "TRAVELING KE LOKASI" and k("Traveling to pit") == "TRAVELING KE LOKASI"
    assert k("Standby tidak ada operator") == "STANDBY TIDAK ADA OPERATOR" and k("Standby, tidak ada lokasi") == "STANDBY TIDAK ADA LOKASI"
    assert k("Standby area titik bor longsor") == "STANDBY" and k("Waiting blasting") == "WAIT BLASTING" and k("PSM") == "P5M"
    assert [cf.DDR_GROUP[x] for x in ("TRAVELING ANTAR TITIK BOR", "TRAVELING KE LOKASI", "WAIT BLASTING", "STANDBY TIDAK ADA OPERATOR",
                                      "STANDBY TIDAK ADA LOKASI", "P5M", "HUJAN")] == ["WH", "DL", "DL", "STD", "STD", "WH", "RAIN"]
    assert cf.kat_norm("safety talk") == "P5M" and cf.kat_norm("drilling") == "DRILLING" and cf.kat_norm("Tidak ada operator") == \
        "STANDBY TIDAK ADA OPERATOR"
    assert set(cf.DDR_GROUP) == set(cf.DDR_KAT_NAMES)


def test_norm_bhid_rig():
    assert cf.norm_bhid("Z2-265-S-05") == "Z2_265_S_05" and cf.norm_bhid(" z4 270.56 ") == "Z4_270_56" and cf.norm_bhid("Z4__295--49") == "Z4_295_49"
    assert cf.norm_rig("hansin - sdr - 07") == "Hanjin 007" and cf.norm_rig("Hanjin 6") == "Hanjin 006" and cf.norm_rig("HANWA 1") == "Hanwa 001"
    assert cf.norm_rig("Rig lain") == "Rig lain" and cf.norm_rig("XYZ-12") == "XYZ-12"


def test_bhid_rig_on_manual_edit(st):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp)), "ddr", "Rina")[0]["id"]
    cf.update_doc(s, did, {"header": {"rig": "hanjin 6"}}, "Rina")
    assert cf.doc(s, did)["header"]["rig"] == "Hanjin 006"
    rs = cf.save_rows(s, did, [{"data": {"from_m": "0", "to_m": "17", "hole_id": "z4-315-09"}}], "Rina", "hole")
    assert rs[0]["data"]["hole_id"] == "Z4_315_09"
    rc = cf.add_file(s, str(_scan(tmp, "rc.jpg")), "rc", "Rina")[0]["id"]
    cf.update_doc(s, rc, {"header": {"hole_id": "dp 900"}}, "Rina")
    assert cf.doc(s, rc)["header"]["hole_id"] == "DP_900"


def test_rc_logging_jawaban_ringkas(st, monkeypatch):
    """Jawaban ringkas H| / R| (bukan JSON): Hole ID & tanggal diteruskan per lubang, tanda ulang geologi dari baris atas,
    sel bertanda '?' jadi ragu, baris QAQC tanpa interval tidak memutus urutan. Data fiktif."""
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp)), "rc", "Rina")[0]["id"]
    txt = "\n".join([
        "H||",
        "R|hole_id|tanggal|sample_id|from_m|to_m|lith|alt|min1|vein|qt|remark",  # model mengulang nama kolom: diabaikan
        "R|XX-100-01|05-11-26|SMP_000101_ZZ|0|1|VLT|ARG|ox||||",
        "R|||SMP_000102_ZZ|1|2|〃|〃|cly||||",
        "R|||SMP_000103_ZZ|2|3|QMN?|SIL|Qz-Mn|QMN|||",
        "R|||SMP_000104_ZZ||||||||BLANK",
        "R|XX-100-02|05-11-26|SMP_000105_ZZ|0|1|VLT|PRO|chl-cly||||",
        "R|||SMP_000106_ZZ|1|2|{|{|{||||",
        "C|fiktif"])
    _ai(monkeypatch, None, raw=txt)
    cf.ai_read(s, did, "http://x", "m")
    rs = cf.rows(s, did)
    assert [r["data"]["hole_id"] for r in rs] == ["XX_100_01"] * 4 + ["XX_100_02"] * 2
    assert rs[1]["data"]["lith"] == "VLT" and rs[1]["data"]["alt"] == "ARG" and {"lith", "alt", "hole_id"} <= set(rs[1]["unc"])
    assert rs[2]["data"]["lith"] == "QMN" and "lith" in rs[2]["unc"]
    assert rs[5]["data"]["lith"] == "VLT" and rs[5]["data"]["min1"] == "chl-cly"
    v = cf.validate(cf.doc(s, did), rs)
    assert not any(k in ("from_m", "to_m") for x in v["rows"].values() for k in x), v  # urutan per lubang, BLANK tidak memutus
    rec = cf.records(cf.doc(s, did), rs)
    assert rec[4]["hole_id"] == "XX_100_02" and rec[0]["tanggal"] == "2026-11-05" and rec[3]["remark"] == "BLANK"


def test_konteks_secukupnya_dan_porsi_gpu(monkeypatch):
    """num_ctx mengikuti ukuran gambar (bukan 16384 tetap, yang bisa mendorong model keluar dari VRAM);
    porsi GPU dibaca dari /api/ps."""
    assert cf.ctx_for((1280, 905), "x" * 1500) == 5120
    assert cf.ctx_for((2000, 1414), "x" * 1500) == 6144
    monkeypatch.setattr(cf.core_io, "_http", lambda url, body=None, timeout=5.0: {"models": [
        {"name": "qwen3-vl:4b", "size": 6_000_000_000, "size_vram": 3_000_000_000}]})
    assert cf.gpu_share("http://x", "qwen3-vl:4b") == 50
    assert cf.gpu_share("http://x", "lain:1b") is None
