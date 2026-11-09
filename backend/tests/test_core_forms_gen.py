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


def test_potong_area_manual(st, monkeypatch):
    """0.44.4: area potong manual disimpan per borang (pecahan gambar asli) dan dipakai saat AI membaca."""
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "k.jpg")), "rom", "Rina")[0]["id"]
    d = cf.update_doc(s, did, {"crop": [0.9, 0.1, 0.1, 0.6]}, "Rina")
    assert cf.doc(s, did)["crop"] == [0.1, 0.1, 0.9, 0.6]
    from PIL import Image
    w, h = Image.open(s.scans / cf.doc(s, did)["file"]).size
    _b, size = cf._image_b64(s, cf.doc(s, did), 4000)
    assert abs(size[0] - 0.8 * w) <= 2 and abs(size[1] - 0.5 * h) <= 2
    cf.update_doc(s, did, {"rot": 90}, "Rina")
    _b, size = cf._image_b64(s, cf.doc(s, did), 4000)
    assert abs(size[0] - 0.5 * h) <= 2  # dipotong dulu, baru diputar
    cf.update_doc(s, did, {"crop": None}, "Rina")
    assert cf.doc(s, did)["crop"] is None and any(x["what"] == "potong area" for x in cf.history(s, did))
    assert cf.norm_crop([0.1, 0.1, 0.12, 0.9]) is None


def test_rc_kolom_terpotong_tabel_di_catatan(st):
    """0.44.4: foto RC tanpa kolom No / Hole_ID / Tanggal; model menulis kepala tabelnya sendiri dan seluruh tabel di 'c'.
    Tabel diambil dari catatan dan dipetakan menurut kepala kolom yang ditulis model. Data fiktif."""
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "rc.jpg")), "rc", "Rina")[0]["id"]
    c = ("Sample_ID|From|To|Lith|Int_Alt|Min1|Vein_Type\n" "AA_000069_Z9|0|1|VLT|IAR|cly|\n" "AA_000070_Z9|1|2|〃|〃|〃|\n"
         "AA_000071_Z9|2|3|VLT|ARG|ox|")
    res = cf.parse_ai_text("rc", json.dumps({"h": ["", "", "", ""], "r": [], "c": c}))
    assert [r["sample_id"] for r in res["rows"]] == ["AA_000069_Z9", "AA_000070_Z9", "AA_000071_Z9"] and res["catatan"] == ""
    cf.apply_ai(s, did, res, "m", 1)
    rs = [r["data"] for r in cf.rows(s, did)]
    assert [(r["sample_id"], r["from_m"], r["to_m"], r["lith"], r["alt"]) for r in rs][1] == ("AA_000070_Z9", "1", "2", "VLT", "IAR")
    assert "terpotong" in cf.ai_prompt("rc")


def test_buang_bagian_kosong_dan_header_halaman_lain(st, tmp_path, monkeypatch):
    """0.44.5: (1) bagian bawah tabel tanpa tinta dibuang (tanda tangan kecil di bawah tidak menghalangi);
    (2) halaman PDF berikutnya: header disalin dari halaman yang sudah terisi, AI hanya membaca tabel. Data fiktif."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (1000, 1400), "white")
    g = ImageDraw.Draw(im)
    for y in range(100, 1300, 40):
        g.line((50, y, 950, y), fill="black", width=2)  # garis tabel tercetak sampai bawah
    for y in range(120, 560, 40):
        g.text((100, y), "4028   :57   340", fill=(30, 40, 200))
        g.line((300, y + 5, 520, y + 12), fill=(30, 40, 200), width=4)  # tulisan pena biru di 40 % atas
    g.line((700, 1340, 800, 1350), fill=(30, 40, 200), width=3)  # tanda tangan kecil di bawah
    out, cut = cf.trim_empty(im)
    assert 0.35 < cut < 0.6 and 560 < out.height < 800
    polos = Image.new("RGB", (800, 1000), "white")
    assert cf.trim_empty(polos)[1] == 0.0
    # header dari halaman lain PDF yang sama
    s, tmp = st
    # dua halaman dari satu file (tanpa pembaca PDF di mesin uji): dua scan, lalu src & halaman disamakan seperti hasil pecah PDF
    ids = [cf.add_file(s, str(_scan(tmp, f"hal{i}.jpg")), "rom", "Rina")[0]["id"] for i in (1, 2)]
    with s.lock, s.conn() as c:
        for i, did in enumerate(ids, 1):
            c.execute("UPDATE docs SET src=?, page=? WHERE id=?", ("C:/x/dua.pdf", i, did))
    cf.update_doc(s, ids[0], {"header": {"tanggal": "07-11-26", "shift": "II", "crew": "A / B", "lokasi": "ROM X"}}, "Rina")
    calls = _fake(monkeypatch, {"r": ["1|T1|-|:57|340|Crusher|-|OX-LG|37|Baru|Direct"]})
    out = cf.ai_read(s, ids[1], "http://x", "m")
    assert "h" not in calls[0]["format"]["properties"] and "JANGAN baca header" in calls[0]["messages"][0]["content"]
    d = cf.doc(s, ids[1])
    assert d["header"]["lokasi"] == "ROM X" and "lokasi" in d["hdr_unc"] and out["perf"]["hdr_prev"]
    calls = _fake(monkeypatch, {"h": ["", "", "", ""], "r": ["1|T1|-|:57|340|Crusher|-|OX-LG|37|Baru|Direct"]})
    cf.ai_read(s, ids[1], "http://x", "m", hdr_prev=False)
    assert "h" in calls[0]["format"]["properties"]


def test_ddr_header_ringkas_dan_nama_isian_dibuang():
    """0.44.6: DDR hanya minta 6 isian header (atas borang); nama isian yang disalin model (DHP_ID, WH, bit_on) dikosongkan;
    jumlah baris jawaban dibatasi."""
    sch = cf.ai_schema_compact("ddr")
    assert sch["properties"]["h"]["minItems"] == 6 and sch["properties"]["r"]["maxItems"] == 80
    pr = cf.ai_prompt("ddr")
    assert "<DHP ID>" in pr and "dhp_id, wh" not in pr
    res = cf.parse_ai_text("ddr", json.dumps({"h": ["04-11-26", "I", "SDR-006", "Driller A", "PT. ABC", "DHP_ID"],
                                              "r": ["0630-0645|travel to rom 370", "jam|aktivitas"], "lubang": ["0|15|XX-1|60|60"]}))
    assert res["header"]["dhp_id"] == "" and res["header"]["rig"] == "SDR-006" and len(res["rows"]) == 1


def test_teks_baris_tanpa_tanda_r_dan_lubang_berulang():
    """0.44.5: jawaban mentah uji DDR — hanya baris pertama bertanda R|, lainnya diawali '|'; tabel LUBANG berisi
    kegiatan (rentang jam) dan baris yang terus berulang. Data fiktif mengikuti pola jawaban itu."""
    raw = ("H|04-11-26|I|RIG-X|Driller A|Klien A|-\n"
           "R|0630-0700|TRAVELING TO 370\n|0700-0705|P5M\n|0705-0710|P2H\n|0710-0720|START ENGINE\n"
           "LUBANG|from_m|to_m|hole_id|az|dip\n|0|15|XX-400|60|60\n|0|15|XX-401|89|60\n|0700-0705|P5M\n|0|15|XX-401|89|60\n")
    p = cf.parse_ai_text("ddr", raw)
    assert [r["aktivitas"] for r in p["rows"]] == ["TRAVELING TO 370", "P5M", "P2H", "START ENGINE"]
    assert [x["hole_id"] for x in p["lubang"]] == ["XX-400", "XX-401"]


def test_ollama_500_diulang_dengan_gambar_kecil_lalu_pesan_jelas(st, monkeypatch):
    """0.44.5: HTTP 500 dari Ollama (memori penuh) -> diulang sekali dengan gambar lebih kecil; tetap gagal -> pesan asli
    Ollama + saran yang bisa dilakukan pengguna."""
    import io
    import urllib.error
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "z.jpg")), "rom", "Rina")[0]["id"]
    n = []

    def boom(url, body=None, timeout=5.0):
        if url.endswith(("/api/show", "/api/ps")):
            return {}
        n.append(body)
        if len(n) == 1:
            raise urllib.error.HTTPError(url, 500, "Internal Server Error", {}, io.BytesIO(b'{"error":"llama runner process has terminated: exit status 2"}'))
        return {"message": {"content": json.dumps({"h": ["", "", "", ""], "r": ["1|T1|-|1857|PIT-1|Crusher|-|OX-LG|37|Baru|Direct"]})}}
    monkeypatch.setattr(cf.time, "sleep", lambda *_: None)
    monkeypatch.setattr(core_io, "_http", boom)
    cf.ai_read(s, did, "http://x", "m", max_px=1600)
    assert len(n) == 2 and len(cf.rows(s, did)) == 1
    n.clear()

    def boom2(url, body=None, timeout=5.0):
        if url.endswith(("/api/show", "/api/ps")):
            return {}
        n.append(1)
        raise urllib.error.HTTPError(url, 500, "Internal Server Error", {}, io.BytesIO(b'{"error":"model requires more system memory"}'))
    monkeypatch.setattr(core_io, "_http", boom2)
    import pytest
    with pytest.raises(ValueError, match="memori komputer tidak cukup"):
        cf.ai_read(s, did, "http://x", "m")
    assert "requires more system memory" in cf.doc(s, did)["error"]


def test_ddr_satu_sel_per_elemen_disusun_ulang(st):
    """0.44.7: model menulis tabel lubang (dan kegiatan) SATU NILAI per elemen -> dulu 30 'lubang' berisi satu angka / jam."""
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "f.jpg")), "ddr", "Rina")[0]["id"]
    lub = ["0", "15", "AB-100", "401", "65", "60", "0", "15", "AB-100", "402", "68", "60", "0", "15", "AB-100 403", "65", "60",
           "06:30-06:45", "travel to opp", "06:45-07:20", "general safety talk", "0720-0730", "travel", "to location"]
    res = cf.parse_ai_text("ddr", json.dumps({"h": ["08/11/26", "I", "SDR-01", "Driller A", "PT X", "RDC"], "r": [], "lubang": lub}))
    assert [(x["from_m"], x["to_m"], x["hole_id"], x["az"], x["dip"]) for x in res["lubang"]] == [
        ("0", "15", "AB-100 401", "65", "60"), ("0", "15", "AB-100 402", "68", "60"), ("0", "15", "AB-100 403", "65", "60")]
    cf.apply_ai(s, did, res, "m", 1)
    rs = [r["data"] for r in cf.rows(s, did) if not r.get("tbl")]
    assert [(r["mulai"], r["selesai"], r["aktivitas"]) for r in rs] == [
        ("06:30", "06:45", "travel to opp"), ("06:45", "07:20", "general safety talk"), ("07:20", "07:30", "travel to location")]
    # kegiatan juga satu sel per elemen di 'r'; lubang sudah benar -> tidak diubah
    res = cf.parse_ai_text("ddr", json.dumps({"h": [], "r": ["0630-0645", "travel", "0645-0700", "P5M"], "lubang": ["0|15|AB-1|60|60"]}))
    assert len(res["rows"]) == 2 and res["lubang"][0]["hole_id"] == "AB-1"


def test_isian_macet_dikosongkan(st):
    """0.44.7: '?|?|?' (model macet) tidak masuk header; nilai sampah lama di header ikut dibersihkan saat dibaca ulang."""
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "g.jpg")), "ddr", "Rina")[0]["id"]
    with s.conn() as c:
        c.execute("UPDATE docs SET header_json=? WHERE id=?", (json.dumps({"geologist": "? | ? | ? | ?", "rig": "SDR-01"}), did))
    res = cf.parse_ai_text("ddr", "H|08/11/26|I|?|-|PT X|RDC\nR|0630-0700|travel\nR|-|-\nR|?|?")
    cf.apply_ai(s, did, res, "m", 1)
    d = cf.doc(s, did)
    assert d["header"]["geologist"] == "" and d["header"]["rig"] == "SDR-01" and d["header"]["client"] == "PT X"
    assert len([r for r in cf.rows(s, did) if not r.get("tbl")]) == 1


def test_ddr_jawaban_mentah_lapangan(st):
    """0.44.7 (jawaban mentah uji lapangan, ID diganti fiktif): Hole ID ber-'|' (6 sel) dan kegiatan kembar berturut-turut."""
    res = cf.parse_ai_text("ddr", json.dumps({"h": ["04-11-2026", "I", "SDR-01", "A", "PT X", "RDO"],
                                              "r": ["", "0650-0700|travel", "07.00-07.05|p2h", "07.00-07.05|p2h", "07.00-07.05|P2H"],
                                              "lubang": ["0|15|AB-100|400|60|60", "0|15|AB-100|401|89|60", "0|15|AB-1|60|60"]}))
    assert [x["hole_id"] for x in res["lubang"]] == ["AB-100 400", "AB-100 401", "AB-1"]
    assert [(x["az"], x["dip"]) for x in res["lubang"][:2]] == [("60", "60"), ("89", "60")]
    assert len(res["rows"]) == 2
    p = cf.ai_prompt("ddr")
    assert "TRAVELING TO 370" not in p and "0650-0700" not in p
