"""Uji ruang kerja Singkapan Core-Ex: tambah foto (disalin ke proyek), deskripsi AI (skema JSON, editan tidak ditimpa),
fitur garis / poligon / label (validasi, belah, gabung), pustaka jenis fitur & nomor string, skala dari garis skala."""
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend import core_io, core_outcrop as co  # noqa: E402


@pytest.fixture()
def st(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    d = tmp_path / "proyek"
    d.mkdir()
    core_io._PROJECTS.clear()
    co._STORES.clear()
    return co.store(str(d)), tmp_path


def _img(tmp_path, name="Sebunga_RL256.jpg", size=(800, 500)):
    f = tmp_path / "lapangan" / name
    f.parent.mkdir(exist_ok=True)
    Image.new("RGB", size, (120, 140, 130)).save(f)
    return f


def test_add_photo_copied_and_hidden_from_core_scan(st):
    s, tmp = st
    p = co.add_photo(s, str(_img(tmp)), "Rina")
    assert p["w"] == 800 and p["h"] == 500 and p["title"] == "Sebunga_RL256" and not p["missing"]
    assert (s.photos / p["file"]).exists() and s.root.parent.name == core_io.PRJ_DIR
    p2 = co.add_photo(s, str(_img(tmp)), "Rina")  # nama sama -> disalin dengan akhiran
    assert p2["file"] != p["file"]
    # foto singkapan tidak ikut dipindai sebagai foto core box
    assert core_io.scan(core_io.get_project(str(s.root.parents[1])))["total"] == 0
    with pytest.raises(ValueError, match="format foto"):
        bad = tmp / "lapangan" / "catatan.txt"
        bad.write_text("x")
        co.add_photo(s, str(bad), "Rina")
    co.delete_photo(s, p2["id"], "Rina")
    assert [x["id"] for x in co.photos(s)] == [p["id"]]


def test_update_desc_and_ai_does_not_overwrite_edits(st):
    s, tmp = st
    pid = co.add_photo(s, str(_img(tmp)), "Rina")["id"]
    r = co.update_photo(s, pid, {"title": "Trenching Sebunga RL256 Blok 11", "desc:lithology": "Tuf piritik", "info": {"template": "wall"}}, "Rina")
    assert r["title"].startswith("Trenching") and r["edited"] == ["lithology"] and r["info"]["template"] == "wall"
    with pytest.raises(ValueError, match="wall"):
        co.update_photo(s, pid, {"desc:photo_type": "miring"}, "Rina")
    ai = {"photo_type": "wall", "lithology": "Andesit", "alteration": "Propilitik klorit-smektit", "weathering": "W4 atas, W2 bawah",
          "oxidation": None, "veins": "Vein kuarsa-lempung-oksida curam", "structures": "Kekar curam ke kanan", "gsi": "35-45",
          "joint_spacing": "rapat", "zones": "Atas oksida; bawah segar", "notes": "Vein termineralisasi", "confidence": "sedang"}
    r = co.apply_ai(s, pid, ai, "qwen3-vl:8b", 12.3)
    assert r["desc"]["lithology"] == "Tuf piritik"  # editan geologist tetap
    assert r["desc"]["alteration"].startswith("Propilitik") and r["desc"]["photo_type"] == "wall" and r["status"] == "done"
    assert r["ai_conf"] == "sedang" and r["ai_json"]["lithology"] == "Andesit"
    h = co.history(s, pid)
    assert any(x["src"] == "ai:qwen3-vl:8b" and x["what"] == "alteration" for x in h)
    sch = co.ai_schema()
    assert set(sch["required"]) == set(co.DESC_KEYS) | {"confidence"}
    assert "ISRM" in co.ai_prompt() and "mm per piksel" in co.ai_prompt(scale_m_per_px=0.002)


def test_features_validate_split_join(st):
    s, tmp = st
    pid = co.add_photo(s, str(_img(tmp)), "Rina")["id"]
    with pytest.raises(ValueError, match="minimal 3"):
        co.save_feature(s, pid, None, {"kind": "zona_alt", "pts": [[0.1, 0.1], [0.2, 0.2]]}, "Rina")
    with pytest.raises(ValueError, match="tidak dikenal"):
        co.save_feature(s, pid, None, {"kind": "xx", "pts": [[0, 0], [1, 1]]}, "Rina")
    with pytest.raises(ValueError, match="angka"):
        co.save_feature(s, pid, None, {"kind": "channel", "pts": [[0, 0], [1, 1]], "attrs": {"au_ppm": "tinggi"}}, "Rina")
    poly = co.save_feature(s, pid, None, {"kind": "zona_alt", "pts": [[0.1, 0.1], [0.5, 0.1], [0.5, 0.6], [0.1, 0.1]], "name": "Propilitik"}, "Rina")
    assert len(poly["features"][0]["pts"]) == 3  # titik penutup kembar dibuang
    ln = co.save_feature(s, pid, None, {"kind": "sesar", "pts": [[0, 0], [0.2, 0.3], [0.4, 0.5], [0.6, 0.9]]}, "Rina")["id"]
    j = co.split_line(s, ln, 2, "Rina")
    lines = [f for f in j["features"] if f["kind"] == "sesar"]
    assert [len(f["pts"]) for f in lines] == [3, 2] and lines[0]["pts"][-1] == lines[1]["pts"][0]
    with pytest.raises(ValueError, match="tengah"):
        co.split_line(s, ln, 0, "Rina")
    k = co.join_lines(s, lines[1]["id"], lines[0]["id"], "Rina")
    lines = [f for f in k["features"] if f["kind"] == "sesar"]
    assert len(lines) == 1 and len(lines[0]["pts"]) == 4
    other = co.save_feature(s, pid, None, {"kind": "sesar", "pts": [[0.9, 0.1], [0.95, 0.2]]}, "Rina")["id"]
    with pytest.raises(ValueError, match="bersinggungan"):
        co.join_lines(s, lines[0]["id"], other, "Rina")
    lab = co.save_feature(s, pid, None, {"kind": "label", "pts": [[0.3, 0.3], [0.4, 0.4]], "name": "PROPYLITIC TUFF"}, "Rina")
    assert [f for f in lab["features"] if f["kind"] == "label"][0]["pts"] == [[0.3, 0.3]]
    assert co.photo(s, pid)["n_feat"] == 4
    co.delete_feature(s, other, "Rina")
    assert co.photo(s, pid)["n_feat"] == 3


def test_scale_from_scale_line(st):
    s, tmp = st
    pid = co.add_photo(s, str(_img(tmp, size=(1000, 500))), "Rina")["id"]
    assert co.scale_info(s, pid) is None
    co.save_feature(s, pid, None, {"kind": "skala", "pts": [[0.1, 0.5], [0.3, 0.5]], "attrs": {"length_m": "2"}}, "Rina")
    sc = co.scale_info(s, pid)
    assert abs(sc["px"] - 200) < 1e-6 and abs(sc["m_per_px"] - 0.01) < 1e-9
    with pytest.raises(ValueError, match="lebih dari 0"):
        co.save_feature(s, pid, None, {"kind": "skala", "pts": [[0, 0], [1, 0]], "attrs": {"length_m": 0}}, "Rina")


def test_kinds_library_and_string_numbers(st):
    s, _ = st
    ks = co.kinds(s)
    nums = [k["string"] for k in ks]
    assert len(nums) == len(set(nums)) and {k["key"] for k in ks} >= {"sesar", "vein", "channel", "skala"}
    ks = [dict(k) for k in ks]
    next(k for k in ks if k["key"] == "sesar")["string"] = 20
    ks.append({"key": "Dike", "name": "Dike andesit", "shape": "poly", "color": "#333333", "string": 30})
    out = co.save_kinds(s, ks, "Rina")
    assert next(k for k in out if k["key"] == "sesar")["string"] == 20
    assert next(k for k in out if k["key"] == "dike")["shape"] == "poly"
    ks2 = [dict(k) for k in out]
    next(k for k in ks2 if k["key"] == "dike")["string"] = 20
    with pytest.raises(ValueError, match="dipakai dua"):
        co.save_kinds(s, ks2, "Rina")
    assert json.loads(json.dumps(co.kinds(s)))  # bisa dikirim sebagai JSON
