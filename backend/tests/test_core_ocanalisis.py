"""Uji analisis foto singkapan (Fase 1): peta warna oksida / kuarsa, deteksi jejak kekar + set + scanline + Jv / RQD / GSI,
segmentasi SAM otomatis (label warna & label AI tiruan). Foto dinding sintetis fiktif dari buat_data_dummy.wall_photo."""
import json
import sys
from pathlib import Path

import pytest

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "backend"))
sys.path.insert(0, str(R / "docs" / "tutorial-core"))
from gcex_backend import core_io, core_outcrop as O  # noqa: E402

cv2 = pytest.importorskip("cv2")


@pytest.fixture()
def wall(tmp_path, monkeypatch):
    from buat_data_dummy import wall_photo
    from gcex_backend import core_ocanalisis as A
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "proyek"
    d.mkdir()
    core_io._PROJECTS.clear()
    O._STORES.clear()
    s = O.store(str(d))
    f = tmp_path / "lapangan" / "Dinding_Latihan_W01.jpg"
    f.parent.mkdir()
    wall_photo(f)
    p = O.add_photo(s, str(f), "Rina")
    return s, p["id"], A


def test_color_index_oxide_quartz(wall):
    s, pid, A = wall
    r = A.color_index(s, pid, "oks", 5)
    assert 25 < r["pct"] < 45 and r["m2"] is None and not r["scaled"] and r["png"] and r["zones"] == []
    # zona yang sudah didigitasi: % oksida di dalamnya; skala dari garis skala 18 m sepanjang lebar foto
    O.save_feature(s, pid, None, {"kind": "zona_lito", "pts": [[0, 0], [0.25, 0], [0.25, 0.4], [0, 0.4]], "name": "Kiri atas"}, "Rina")
    O.save_feature(s, pid, None, {"kind": "skala", "pts": [[0, 0.99], [1, 0.99]], "attrs": {"length_m": 18}}, "Rina")
    r = A.color_index(s, pid, "oks", 5, propose=True)
    z = r["zones"][0]
    assert z["name"] == "Kiri atas" and z["pct"] > 85 and z["zone_m2"] == pytest.approx(0.25 * 18 * 0.4 * 12, rel=0.05)
    assert r["scaled"] and r["m2"] > 0 and r["made"]
    drafts = [f for f in r["features"] if f["attrs"].get("_draft") == "indeks:oks"]
    assert drafts and all(f["kind"] == "zona_oks" for f in drafts)
    q = A.color_index(s, pid, "kuarsa", 5, propose=True)
    assert 0.5 < q["pct"] < 5 and any(f["kind"] == "zona_vein" for f in q["features"] if f["attrs"].get("_draft") == "indeks:kuarsa")
    # usulan ulang mengganti usulan lama dari jenis yang sama
    n = len([f for f in O.features(s, pid) if f["attrs"].get("_draft") == "indeks:oks"])
    A.color_index(s, pid, "oks", 5, propose=True)
    assert len([f for f in O.features(s, pid) if f["attrs"].get("_draft") == "indeks:oks"]) == n


def test_traces_sets_scanline_gsi(wall):
    s, pid, A = wall
    j = A.propose_traces(s, pid, 5)
    assert len(j["made"]) >= 15 and all(f["kind"] == "kekar" for f in j["features"] if f["id"] in j["made"])
    st = A.structure(s, pid)
    means = sorted(x["mean"] for x in st["sets"])
    assert len(means) == 2 and means[0] == pytest.approx(65, abs=4) and means[1] == pytest.approx(160, abs=4)
    assert st["scan"]["auto"] and st["scan"]["unit"] == "px" and st["scan"]["n"] >= 8 and st["geo"] == {"unit_ok": False}
    # skala 18 m -> spasi dalam meter, kelas ISRM, Jv, RQD, GSI dengan pelapukan W2 dari deskripsi
    O.save_feature(s, pid, None, {"kind": "skala", "pts": [[0, 0.99], [1, 0.99]], "attrs": {"length_m": 18}}, "Rina")
    O.update_photo(s, pid, {"desc:weathering": "W2 (Slightly Weathered)"}, "Rina")
    st = A.structure(s, pid)
    s1 = next(x for x in st["sets"] if abs(x["mean"] - 65) < 5)
    assert s1["spacing"] == pytest.approx(1.36, abs=0.15) and s1["isrm"].startswith("Lebar")
    g = st["geo"]
    assert g["unit_ok"] and 1 < g["jv"] < 3 and g["rqd"] == 100 and g["structure"].startswith("Masif") and g["condition"] == "Baik"
    assert g["gsi"] == "75–85" and st["rose"]
    # scanline pilihan (garis channel tegak di tengah) memotong set landai
    sc = O.save_feature(s, pid, None, {"kind": "channel", "pts": [[0.6, 0.05], [0.6, 0.95]]}, "Rina")["id"]
    st2 = A.structure(s, pid, sc)
    assert not st2["scan"]["auto"] and st2["scan"]["unit"] == "m" and st2["scan"]["length"] == pytest.approx(0.9 * 1200 * 0.01, rel=0.02)
    assert st2["scan"]["n"] >= 4 and all(h["set"] for h in st2["scan"]["hits"])
    # tanpa draf: hanya jejak yang sudah diterima
    assert A.structure(s, pid, drafts=False)["lines"] == []
    O.accept_drafts(s, pid, None, "Rina")
    assert len(A.structure(s, pid, drafts=False)["lines"]) == len(j["made"])


def test_sam_auto_color_and_ai_labels(wall, monkeypatch):
    s, pid, A = wall
    from gcex_backend import core_vision
    if not core_vision.status()["sam"]:
        pytest.skip("model SAM / onnxruntime tidak tersedia")
    j = A.propose_sam(s, pid, "kasar")
    kinds = {f["kind"] for f in j["features"] if f["id"] in j["made"]}
    assert j["regions"] >= 2 and {"zona_oks", "zona_lito"} <= kinds and j["raw"] >= j["regions"]
    oks = [f for f in j["features"] if f["id"] in j["made"] and f["kind"] == "zona_oks"]
    assert max(f["attrs"]["_pct"] for f in oks) > 20
    # label AI (Ollama tiruan): zona 1 diberi nama, zona 2 'abaikan'
    sent = {}

    def fake(url, body, timeout=5.0):
        sent["body"] = body
        return {"message": {"content": json.dumps({"regions": [{"id": 1, "kind": "zona_alt", "name": "Andesit propilitik", "confidence": "sedang"},
                                                                {"id": 2, "kind": "abaikan"}], "notes": "uji"})}}
    monkeypatch.setattr(core_io, "_http", fake)
    j2 = A.propose_sam(s, pid, "kasar", {"host": "http://x", "model": "qwen3-vl:8b"})
    assert "abaikan" in json.dumps(sent["body"]["format"]) and sent["body"]["messages"][0]["images"]
    mine = [f for f in j2["features"] if f["id"] in j2["made"]]
    assert j2["dropped"] == 1 and len(mine) == j2["regions"] - 1 and j2["notes"] == "uji"
    first = next(f for f in mine if f["name"].startswith("Usulan 1:"))
    assert first["kind"] == "zona_alt" and "Andesit propilitik" in first["name"] and first["attrs"]["_conf"] == "sedang"
    # usulan SAM lama diganti, bukan ditumpuk
    assert len([f for f in O.features(s, pid) if f["attrs"].get("_draft") == "sam"]) == len(mine)
