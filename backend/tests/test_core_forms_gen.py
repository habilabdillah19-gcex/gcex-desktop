"""Jenis borang generik (0.44): Geological Mapping, Channel Sampling, Drill Progress Report, template kustom, Auto Detect,
riwayat seluruh proyek. Semua data fiktif."""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gcex_backend import core_forms as cf, core_io  # noqa: E402
from test_core_forms import _scan, io_bytes, st  # noqa: E402,F401


def _fake(monkeypatch, content):
    calls = []

    def fake(url, body=None, timeout=5.0):
        if url.endswith(("/api/show", "/api/ps")):
            return {}
        calls.append(body)
        return {"message": {"content": content if isinstance(content, str) else json.dumps(content)}}
    monkeypatch.setattr(core_io, "_http", fake)
    return calls


def test_channel_sampling_ai_validasi_ekspor(st, monkeypatch, tmp_path):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "Channel_A.jpg")), "chn", "Rina")[0]["id"]
    res = {"h": ["05-11-26", "Sampler A", "Pit X", "100", "CH-01", "45", "", ""],
           "r": ["CH-01|SMP-001|0|1|VLT|ARG|qz vein|3.2||", "|SMP-002|1|2|〃|〃||2.9||", "|SMP-003|2.5|3|AND|PRO||3.1||",
                 "|SMP-003|3|4|AND|PRO||abc|XX|"], "c": ""}
    calls = _fake(monkeypatch, res)
    cf.ai_read(s, did, "http://x", "m")
    assert '"r": ["channel_id|sample_id|from_m|to_m' in calls[0]["messages"][0]["content"]
    rs = cf.rows(s, did)
    assert [r["data"]["channel_id"] for r in rs] == ["CH-01"] * 4 and "channel_id" in rs[1]["unc"]  # diteruskan program
    assert rs[1]["data"]["litologi"] == "VLT" and "litologi" in rs[1]["unc"]  # tanda ulang
    v = cf.validate(cf.doc(s, did), rs)["rows"]
    assert "bolong" in v[rs[2]["id"]]["from_m"] and "kembar" in v[rs[3]["id"]]["sample_id"]
    assert "angka" in v[rs[3]["id"]]["berat"] and "STD" in v[rs[3]["id"]]["qaqc"]
    full = cf._full(s, did)
    assert full["recs"][0]["panjang"] == 1 and full["recs"][0]["tanggal"] == "2026-11-05"
    assert [p["key"] for p in full["pivot"]] == ["PIVOT_CHANNEL", "PIVOT_LITOLOGI"] and full["pivot"][0]["rows"][0]["sampel"] == 4
    c = cf.collect(s, [], "chn", True)
    from openpyxl import load_workbook
    wb = load_workbook(io_bytes(cf.to_xlsx("chn", c["recs"])))
    assert "Data_Channel" in wb.sheetnames
    r1 = cf.to_sqlite(str(tmp_path / "x.db"), "chn", c["recs"])
    assert r1["table"] == "CHANNEL_SAMPLE" and r1["added"] == 4
    with sqlite3.connect(str(tmp_path / "x.db")) as cn:
        assert cn.execute("SELECT SAMPLE_ID, PANJANG FROM CHANNEL_SAMPLE ORDER BY SAMPLE_ID LIMIT 1").fetchone() == ("SMP-001", 1.0)


def test_mapping_dan_progress(st, monkeypatch):
    s, tmp = st
    m = cf.add_file(s, str(_scan(tmp, "map.jpg")), "map", "Rina")[0]["id"]
    _fake(monkeypatch, {"h": ["05-11-26", "Geo A", "Prospek X", "UTM 50S", ""],
                        "r": ["ST-01|500100|9000200|150|VLT|ARG|py|vein|120|75|S-1|", "ST-02|500150|9000250|152|AND|PRO||sesar|400|95||"]})
    cf.ai_read(s, m, "http://x", "m")
    rs = cf.rows(s, m)
    v = cf.validate(cf.doc(s, m), rs)["rows"][rs[1]["id"]]
    assert "0-360" in v["strike"] and "0-90" in v["dip"]
    p = cf.add_file(s, str(_scan(tmp, "dpr.jpg")), "dpr", "Rina")[0]["id"]
    _fake(monkeypatch, {"h": ["05-11-26", "I", "RIG-X", "Kontraktor A", "Geo A", "Prospek X"],
                        "r": ["XX-1|60|0|35|drill|0700|1500|", "XX-2|50|0|55|Selesai|1500|1800|"]})
    cf.ai_read(s, p, "http://x", "m")
    full = cf._full(s, p)
    assert [(r["meter"], r["status"], r["progres_pct"]) for r in full["recs"]] == [(35, "Drilling", 58.3), (55, "Selesai", 110.0)]
    assert "rencana" in full["valid"]["rows"][full["rows"][1]["id"]]["to_m"]
    assert full["pivot"][0]["rows"][0]["meter"] == 90


def test_template_kustom(st):
    s, tmp = st
    spec = {"name": "Trench Log", "header": [["tanggal", "Tanggal", "date"], ["geologist", "Geologist", "text"]],
            "rows": [["trench_id", "Trench ID", "text"], ["from_m", "From", "num"], ["to_m", "To", "num"], ["litologi", "Litologi", "text"]],
            "hint": "", "gen": {"unique": "", "carry": ["trench_id"], "db": "trench log"}}
    k = cf.save_template(s, "", spec, "Rina")
    assert k == "x_trench_log" and "x_trench_log" in cf.TYPES and cf.DB_TABLE[k] == "TRENCH_LOG"
    tp = {t["key"]: t for t in cf.templates(s)}
    assert tp["chn"]["builtin"] and not tp[k]["builtin"]
    did = cf.add_file(s, str(_scan(tmp, "Trench_Log_A.jpg")), "auto", "Rina")[0]["id"]
    assert cf.doc(s, did)["type"] == k and cf.doc(s, did)["auto"] == 2  # nama template di nama file
    cf.save_rows(s, did, [{"data": {"trench_id": "TR-1", "from_m": "0", "to_m": "2"}}, {"data": {"from_m": "2", "to_m": "1"}}], "Rina")
    v = cf.validate(cf.doc(s, did), cf.rows(s, did))
    assert "lebih besar" in list(v["rows"].values())[0]["to_m"]
    import pytest
    with pytest.raises(ValueError, match="dipakai 1 borang"):
        cf.delete_template(s, k, "Rina")
    with pytest.raises(ValueError, match="bawaan"):
        cf.save_template(s, "chn", spec, "Rina")
    cf.delete_doc(s, did, "Rina")
    cf.delete_template(s, k, "Rina")
    assert k not in cf.TYPES and k not in cf.OUT
    h = cf.history_all(s)
    assert h[0]["what"] == "hapus template" and any(x["what"] == "hapus" and x["doc_name"].startswith("Trench_Log_A") for x in h)
    assert all("Trench" in x["doc_name"] for x in cf.history_all(s, q="trench_log_a"))


def test_auto_detect(st, monkeypatch):
    s, tmp = st
    assert cf.guess_type("DDR_310kt.jpg") == "ddr" and cf.guess_type("Rom 418_Shift 2.pdf") == "rom"
    assert cf.guess_type("Channel_Sampling_Z4.jpg") == "chn" and cf.guess_type("IMG_0001.jpg") == ""
    did = cf.add_file(s, str(_scan(tmp, "IMG_0001.jpg")), "auto", "Rina")[0]["id"]
    assert cf.doc(s, did)["auto"] == 1
    seq = [{"type": "dpr"}, {"h": ["05-11-26", "I", "RIG-X", "", "", ""], "r": ["XX-1|60|0|35|Drilling|0700|1500|"]}]
    calls = []

    def fake(url, body=None, timeout=5.0):
        if url.endswith(("/api/show", "/api/ps")):
            return {}
        calls.append(body)
        return {"message": {"content": json.dumps(seq[len(calls) - 1])}}
    monkeypatch.setattr(core_io, "_http", fake)
    cf.ai_read(s, did, "http://x", "m")
    d = cf.doc(s, did)
    assert d["type"] == "dpr" and d["auto"] == 0 and len(cf.rows(s, did)) == 1
    assert "Drill Progress Report" in calls[0]["format"]["properties"]["jenis"]["enum"]
    assert any(h["what"] == "jenis (Auto Detect AI)" for h in cf.history(s, did))


def test_deteksi_judul_menang_dan_ganti_jenis_baca_ulang(st, monkeypatch):
    """0.44.2: AI memilih 'Drill Progress Report' padahal judul tercetak 'DAILY DRILLING REPORT' -> judul yang menang.
    Jenis salah setelah dibaca -> ganti jenis dengan 'clear' (baris lama dibuang) lalu baca ulang."""
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "IMG_9999.jpg")), "auto", "Rina")[0]["id"]
    _fake(monkeypatch, {"judul": "DAILY DRILLING REPORT", "jenis": "Drill Progress Report"})
    assert cf.ai_detect(s, did, "http://x", "m") == "ddr"
    cf.update_doc(s, did, {"type": "dpr"}, "Rina")
    cf.save_rows(s, did, [{"data": {"hole_id": "XX-1", "mulai": "06:30-07:00"}}], "Rina")
    import pytest
    with pytest.raises(ValueError, match="setelah ada baris"):
        cf.update_doc(s, did, {"type": "ddr"}, "Rina")
    cf.update_doc(s, did, {"type": "ddr", "clear": True}, "Rina")
    assert cf.doc(s, did)["type"] == "ddr" and cf.rows(s, did) == []


def test_rom_kamus_site_dan_menit(st):
    """0.44.1: kamus site dari baris terverifikasi (prompt + rapikan salah baca), menit bertitik ('.05'). Data fiktif."""
    s, tmp = st
    a = cf.add_file(s, str(_scan(tmp, "a.jpg")), "rom", "Rina")[0]["id"]
    rows = [{"data": {"unit": "T1", "finish": "19:00", "asal": "PIT ABC", "tujuan": "Crusher", "kelas": "OX-LG", "ton": "30",
                      "status": "Baru", "keterangan": "Direct"}, "verified": True} for _ in range(3)]
    cf.save_rows(s, a, rows, "Rina")
    v = cf.site_vocab(s, "rom")
    assert v["asal"] == ["PIT ABC"] and v["keterangan"] == ["Direct"]
    assert "PIT ABC" in cf.ai_prompt("rom", vocab=v) and "jangan |" in cf.ai_prompt("rom")
    assert cf.snap("P1T A8C", ["PIT ABC"]) == "PIT ABC" and cf.snap("Crusher", ["PIT ABC"]) is None
    b = cf.add_file(s, str(_scan(tmp, "b.jpg")), "rom", "Rina")[0]["id"]
    res = cf.parse_ai_text("rom", json.dumps({"h": ["05-11-26", "II", "", ""], "r": [
        "1|T2|-|20.10|P1T A8C|Crusher|-|OX-LG|31|Baru|Direct", "2|T3|-|.05|〃|〃|SPR (Z2)|OX-HG|35|〃|〃"]}))
    cf.apply_ai(s, b, res, "m", 1)
    rs = cf.rows(s, b)
    d1, d2 = rs[0]["data"], rs[1]["data"]
    assert d1["asal"] == "PIT ABC" and "asal" in rs[0]["unc"] and d1["start"] == ""
    assert (d2["kelas"], d2["ton"], d2["finish"], d2["asal"], d2["status"], d2["rehandling"]) == ("OX-HG", "35", "21:05", "PIT ABC", "Baru", "SPR (Z2)")


def test_baris_raksasa_dipecah_dan_sel_meleset_kuning():
    """0.44.3: seluruh tabel dalam satu teks -> dipecah per nomor urut; jumlah sel meleset -> isian baris kuning."""
    big = "1|T1|-|18:57|340|Crusher|-|OX-LG|37|Baru|Direct|2|T2|-|:16|〃|〃|-|OX-LG|36|〃|〃|3|T3|-|:24|418|〃|-|SCAT|29|〃|〃"
    p = cf.parse_ai_text("rom", json.dumps({"h": ["", "", "", ""], "r": [big, "4|T4|:30|418|Crusher|OX-LG|33"]}))
    assert [r["no"] for r in p["rows"]] == ["1", "2", "3", "4"] and p["rows"][2]["kelas"] == "SCAT"
    assert not p["rows"][0]["ragu"] and set(p["rows"][3]["ragu"]) >= {"unit", "start", "finish"}
    assert "TEPAT 11 nilai" in cf.ai_prompt("rom") and "TEPAT 9 nilai" in cf.ai_prompt("ore")


def test_ddr_tabel_dalam_satu_teks_dipecah(st):
    """0.44.3: Daily Drilling Report dengan semua kegiatan dalam satu teks (dulu 0 baris) -> dipecah per rentang jam."""
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "d.jpg")), "ddr", "Rina")[0]["id"]
    big = ("0630-0645|travel to opp|0645-0700|general safety talk|0700-0715|travel to location and start engine compressor"
           "|0715-0730|start drilling + cleaning cyclone and splitter")
    res = cf.parse_ai_text("ddr", json.dumps({"h": [], "r": [big], "lubang": []}))
    cf.apply_ai(s, did, res, "m", 1)
    rs = [r["data"] for r in cf.rows(s, did) if not r.get("tbl")]
    assert [(r["mulai"], r["aktivitas"]) for r in rs][:2] == [("06:30", "travel to opp"), ("06:45", "general safety talk")]
    assert len(rs) == 4
