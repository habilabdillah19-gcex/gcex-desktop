"""Mode Transkrip (0.45): AI menyalin teks, pengguna memilih pemisah & pemetaan kolom, program menyusun baris. Data fiktif."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gcex_backend import core_forms as cf, core_io, core_transkrip as tr  # noqa: E402
from test_core_forms import _scan, io_bytes, st  # noqa: E402,F401

DDR_TXT = """Here is the transcription of the form in the image:
Date: 04-11-26
Shift: I
Drill Rig: SDR-01
Driller: Budi
Client: PT X
From | To | Hole ID | Az | Dip | Time | Drilling details
0 | 15 | AB-100 401 | 65 | 60 | 0630-0645 | travel to opp
0 | 15 | AB-100 402 | 68 | 60 | 0645-0720 | general safety talk
- | - | - | - | - | 0720-0730 | travel to location
and start engine
0 | 15 | AB-100 403? | 65 | 60 | 0730-0745 | P2H
0 | 15 | AB-100 403? | 65 | 60 | 0730-0745 | P2H
"""


def test_grid_dan_usulan_pemetaan():
    g = tr.grid(DDR_TXT, "auto")
    assert g["sep"] == "|" and g["ncol"] == 7
    assert g["hdr"][0] == ["Date", "04-11-26"] and len(g["hdr"]) == 5
    assert g["rows"][3][6] == "travel to location and start engine"  # baris lanjutan digabung ke sel terakhir
    assert len(g["rows"]) == 5  # judul + 4 baris (kembar dibuang)
    sg = tr.suggest("ddr", g, None)
    assert sg["title_row"] == 0
    assert sg["cols"] == ["hole:from_m", "hole:to_m", "hole:hole_id", "hole:az", "hole:dip", "jam", "aktivitas"]
    assert sg["hdr"] == ["tanggal", "shift", "rig", "driller", "client"]


def test_terapkan_ddr_lubang_dan_kegiatan_sebaris(st):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "t.jpg")), "ddr", "Rina")[0]["id"]
    pv = tr.preview(s, did, DDR_TXT, "auto")
    tr.apply(s, did, DDR_TXT, pv["sep"], pv["map"]["cols"], pv["map"]["hdr"], "Rina", skip_rows=[pv["map"]["title_row"]])
    d = cf.doc(s, did)
    assert d["header"]["rig"] == "SDR-01" and d["header"]["client"] == "PT X" and d["status"] == "done"
    rs = cf.rows(s, did)
    act = [r for r in rs if not r.get("tbl")]
    hole = [r for r in rs if r.get("tbl") == "hole"]
    assert [(r["data"]["mulai"], r["data"]["aktivitas"]) for r in act] == [
        ("06:30", "travel to opp"), ("06:45", "general safety talk"), ("07:20", "travel to location and start engine"), ("07:30", "P2H")]
    assert [r["data"]["hole_id"] for r in hole] == ["AB_100_401", "AB_100_402", "AB_100_403"]  # norm_bhid
    assert "hole_id" in hole[2]["unc"]  # tanda '?' -> ragu (kuning)
    # pemetaan tersimpan per jenis borang dan dipakai lagi untuk teks tanpa baris judul
    m = tr.load_map(s)["ddr"]
    assert m["cols"][5] == "jam" and m["hdr"]["drillrig"] == "rig"
    pv2 = tr.preview(s, did, "Drill Rig: SDR-02\n0 | 15 | AB-1 | 60 | 60 | 0800-0810 | moving", "auto")
    assert pv2["map"]["cols"] == m["cols"] and pv2["map"]["hdr"] == ["rig"]
    assert any(x["what"] == "teks transkrip diedit" for x in cf.history(s, did))


def test_terapkan_ore_koma_dan_abaikan(st):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "o.jpg")), "ore", "Rina")[0]["id"]
    txt = "Tanggal: 05-11-26\n1, 0905, T01, OX-LG, 30, ROM 1\n2, 0916, T02, SF-LG, 31, ROM 1\n"
    g = tr.grid(txt, ",")
    assert g["ncol"] == 6 and g["sep"] == ","
    opts = {o["key"] for o in tr.options("ore")}
    assert {"kelas", "unit", "ton"} <= opts
    cols = ["no", "start", "unit", "kelas", "ton", "tujuan"]
    tr.apply(s, did, txt, ",", cols, ["tanggal"], "Rina")
    rs = [r["data"] for r in cf.rows(s, did)]
    assert len(rs) == 2 and rs[0]["kelas"] == "OX-LG" and rs[1]["unit"] == "T02"


def test_ai_transcribe_simpan_teks(st, monkeypatch):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "r.jpg")), "rom", "Rina")[0]["id"]
    calls = []

    def fake(url, body=None, timeout=5.0):
        if url.endswith(("/api/show", "/api/ps")):
            return {}
        calls.append(body)
        return {"message": {"content": "```\nTanggal: 05-11-26\n| 1 | 4011 | 1857 |\n| 1 | 4011 | 1857 |\n```"}, "eval_count": 30}
    monkeypatch.setattr(core_io, "_http", fake)
    r = tr.ai_transcribe(s, did, "http://x", "m", by="Rina")
    assert "format" not in calls[0] and "SALIN" in calls[0]["messages"][0]["content"]
    assert r["teks"] == "Tanggal: 05-11-26\n1 | 4011 | 1857"  # pagar kode dibuang, baris kembar dibuang
    assert tr.get_teks(s, did) == r["teks"] and (s.root / "ai_mentah" / f"{did}_teks.txt").exists()
    assert cf.rows(s, did) == []  # menyalin teks tidak mengubah baris
    pv = tr.preview(s, did, None, "auto")
    assert pv["rows"] == [["1", "4011", "1857"]] and pv["type"] == "rom"


def test_terapkan_tanpa_pemetaan_ditolak(st):
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "u.jpg")), "ore", "Rina")[0]["id"]
    try:
        tr.apply(s, did, "1 | 2 | 3", "|", ["", "", ""], [], "Rina")
        raise AssertionError("harus ditolak")
    except ValueError as e:
        assert "dipetakan" in str(e)


def test_gabung_kolom_kanan_dan_bawah(st, monkeypatch):
    """0.45.1: scan kolom satu per satu (kiri -> kanan) -> tiap salinan menjadi kolom baru di kanan; lembar berikutnya di bawah."""
    m = tr.merge("Shift: I\n0 | 15\n0 | 15\n0 | 15", "Hole ID\nAB-1\nAB-2", "kanan", "|")
    assert m.split("\n") == ["Shift: I", "0 | 15 | Hole ID", "0 | 15 | AB-1", "0 | 15 | AB-2"]
    assert tr.merge("a | b", "c\nd", "kanan", "|").split("\n") == ["a | b | c", "- | - | d"]  # baris salinan baru lebih banyak
    assert tr.merge("a | b", "x | y", "bawah") == "a | b\nx | y"
    assert tr.merge("", "x", "kanan") == "x" and tr.merge("lama", "baru", "ganti") == "baru"
    s, tmp = st
    did = cf.add_file(s, str(_scan(tmp, "k.jpg")), "ddr", "Rina")[0]["id"]
    outs = iter(["From | To\n0 | 15\n0 | 15", "Hole ID\nAB-100 401\nAB-100 402", "Az | Dip\n65 | 60\n68 | 60"])

    def fake(url, body=None, timeout=5.0):
        if url.endswith(("/api/show", "/api/ps")):
            return {}
        return {"message": {"content": next(outs)}}
    monkeypatch.setattr(core_io, "_http", fake)
    tr.ai_transcribe(s, did, "http://x", "m", mode="kanan")
    tr.ai_transcribe(s, did, "http://x", "m", mode="kanan")
    r = tr.ai_transcribe(s, did, "http://x", "m", mode="kanan", sep="|")
    assert r["teks"].split("\n")[1] == "0 | 15 | AB-100 401 | 65 | 60"
    pv = tr.preview(s, did, None, "|")
    assert pv["ncol"] == 5 and pv["map"]["title_row"] == 0
    assert pv["map"]["cols"] == ["hole:from_m", "hole:to_m", "hole:hole_id", "hole:az", "hole:dip"]
