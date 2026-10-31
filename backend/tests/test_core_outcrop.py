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


def _wall_pts(w=1000, h=800, n=5, persp=False):
    """Dinding fiktif berarah 060° (tegak), 20 m x 16 m; piksel -> (s, t) di bidang, opsional dengan perspektif."""
    import math
    az = math.radians(60)
    e1 = (math.sin(az), math.cos(az))
    E0, N0, RL0 = 5000.0, 2000.0, 250.0
    uv = [(0.1, 0.1), (0.9, 0.12), (0.88, 0.9), (0.12, 0.85), (0.5, 0.5), (0.3, 0.6), (0.7, 0.3)][:n]
    pts = []
    for i, (u, v) in enumerate(uv):
        s, t = u * 20, (1 - v) * 16
        if persp:  # foto miring: bidang terlihat mengecil ke kanan (homografi)
            k = 1 + 0.4 * u
            s, t = s / k * 1.4, (t - 8) / k + 8
        pts.append({"name": f"G{i + 1}", "e": E0 + s * e1[0], "n": N0 + s * e1[1], "rl": RL0 + t, "uv": (u, v), "st": (s, t)})
    return pts


def test_georef_wall_and_floor_and_export(st):
    s, tmp = st
    pid = co.add_photo(s, str(_img(tmp, size=(1000, 800))), "Rina")["id"]
    co.update_photo(s, pid, {"desc:photo_type": "wall"}, "Rina")
    P = _wall_pts()
    pts = [{"name": p["name"], "u": p["uv"][0], "v": p["uv"][1], "e": p["e"], "n": p["n"], "rl": p["rl"]} for p in P]
    g = co.save_georef(s, pid, pts[:2], None, "Rina")["solution"]
    assert g["ok"] and "similaritas" in g["method"] and abs(g["dip"] - 90) < 1e-6 and g["warn"]
    assert abs(g["dip_dir"] - 150) < 1e-3 or abs(g["dip_dir"] - 330) < 1e-3
    g = co.save_georef(s, pid, pts[:3], None, "Rina")["solution"]
    assert "affine" in g["method"] and g["rms"] < 1e-3
    r = co.save_georef(s, pid, pts, None, "Rina")
    g = r["solution"]
    assert "homografi" in g["method"] and g["rms"] < 1e-3 and abs(g["m_per_px"] - 0.02) < 1e-6
    # vein lurus dari kiri-bawah ke kanan-atas dinding: panjang & apparent dip
    co.save_feature(s, pid, None, {"kind": "vein", "pts": [[0.1, 0.9], [0.6, 0.4]], "name": "V1", "attrs": {"au_ppm": 3.2}}, "Rina")
    co.save_feature(s, pid, None, {"kind": "zona_alt", "pts": [[0.1, 0.1], [0.6, 0.1], [0.6, 0.6], [0.1, 0.6]], "name": "Argilik"}, "Rina")
    co.save_feature(s, pid, None, {"kind": "skala", "pts": [[0.1, 0.95], [0.2, 0.95]], "attrs": {"length_m": 2}}, "Rina")
    m = co.georef_info(s, pid)["measure"]
    vals = list(m.values())
    ln = next(x for x in vals if "length_m" in x and "apparent_dip" in x and x["length_m"] > 12)
    assert abs(ln["length_m"] - (10 ** 2 + 8 ** 2) ** 0.5) < 0.01 and abs(ln["apparent_dip"] - 38.66) < 0.01
    area = next(x for x in vals if "area_m2" in x)
    assert abs(area["area_m2"] - 80) < 0.02
    # salah ketik satu RL 2 m -> galat terlihat
    bad = [dict(p) for p in pts]
    bad[4]["rl"] += 2
    g = co.save_georef(s, pid, bad, None, "Rina")["solution"]
    assert g["rms"] > 0.2 and max(r["err"] for r in g["residuals"]) == max(x["err"] for x in g["residuals"])
    co.save_georef(s, pid, pts, None, "Rina")
    # ekspor STR: urutan Y, X, Z; poligon tertutup; skala tidak ikut
    items, skipped = co.export_items(s, [pid])
    assert not skipped and {i["kind"] for i in items} == {"vein", "zona_alt"}
    txt = co.to_str(items, "uji").decode()
    lines = txt.strip().split("\r\n")
    assert lines[-1].endswith("END") and lines[1].startswith("0,")
    vein_no = next(k["string"] for k in co.kinds(s) if k["key"] == "vein")
    vl = [x for x in lines if x.startswith(f"{vein_no},")]
    sn, y, x, z = [float(t) for t in vl[0].split(",")[:4]]
    assert abs(x - P[0]["e"]) < 2.1 and abs(y - 2000) < 2 and "au=3.2" in vl[0] and "V1" in vl[0]
    zl = [x for x in lines if x.startswith(f"{next(k['string'] for k in co.kinds(s) if k['key'] == 'zona_alt')},")]
    assert len(zl) == 5 and zl[0].split(",")[1:4] == zl[-1].split(",")[1:4]
    dxf = co.to_dxf(items).decode()
    assert "AC1009" in dxf and dxf.count("POLYLINE") == 2 and "VEIN" in dxf and dxf.strip().endswith("EOF")
    # foto tanpa georef dilaporkan, tidak diekspor
    pid2 = co.add_photo(s, str(_img(tmp, "lain.jpg")), "Rina")["id"]
    items2, skipped2 = co.export_items(s, [pid, pid2])
    assert len(items2) == len(items) and len(skipped2) == 1 and "lain" in skipped2[0]


def test_georef_perspective_floor_and_errors(st):
    s, tmp = st
    pid = co.add_photo(s, str(_img(tmp, size=(1000, 800))), "Rina")["id"]
    P = _wall_pts(n=7, persp=True)
    pts = [{"name": p["name"], "u": p["uv"][0], "v": p["uv"][1], "e": p["e"], "n": p["n"], "rl": p["rl"]} for p in P]
    g = co.save_georef(s, pid, pts, "wall", "Rina")["solution"]
    assert g["ok"] and g["rms"] < 1e-3  # homografi menyerap perspektif sempurna
    g3 = co.save_georef(s, pid, pts[:3] + pts[4:5], "wall", "Rina")["solution"]
    assert g3["ok"]
    # lantai: RL hampir sama -> dip ~0
    fl = [{"name": f"F{i}", "u": u, "v": v, "e": 100 + u * 30, "n": 200 + (1 - v) * 24, "rl": 80.0}
          for i, (u, v) in enumerate([(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)])]
    g = co.save_georef(s, pid, fl, "floor", "Rina")["solution"]
    assert g["ok"] and g["dip"] < 1e-6 and abs(g["m_per_px"] - 0.03) < 1e-6
    g = co.save_georef(s, pid, fl, "wall", "Rina")["solution"]
    assert not g["ok"] or any("landai" in w for w in g["warn"])
    with pytest.raises(ValueError, match="kembar"):
        co.save_georef(s, pid, [fl[0], fl[0]], None, "Rina")
    with pytest.raises(ValueError, match="angka"):
        co.save_georef(s, pid, [{"name": "A", "u": 0.1, "v": 0.1, "e": "x", "n": 1, "rl": 1}], None, "Rina")
    g = co.save_georef(s, pid, [{"name": "A", "u": 0.1, "v": 0.1, "e": "", "n": 1, "rl": 1}, {"name": "B", "e": 1, "n": 2, "rl": 3}], None, "Rina")["solution"]
    assert not g["ok"] and "minimal 2" in g["msg"]
    seg = [{"name": f"S{i}", "u": 0.1 * i, "v": 0.5, "e": 10 * i, "n": 0, "rl": 5 * i} for i in range(1, 4)]
    g = co.save_georef(s, pid, seg, None, "Rina")["solution"]
    assert not g["ok"] and "segaris" in g["msg"]
    assert any(h["what"] == "georef" for h in co.history(s, pid))


def _zoned(tmp_path, name="zona.jpg"):
    """Foto fiktif: batuan abu-abu kehijauan dengan zona oksida coklat kemerahan di kanan atas dan lensa gelap di kiri bawah."""
    import numpy as np
    rng = np.random.default_rng(3)
    a = np.zeros((400, 600, 3)) + [128, 134, 126]
    yy, xx = np.mgrid[0:400, 0:600]
    a[(xx > 330) & (yy < 230 + 0.2 * (xx - 330))] = [168, 98, 52]
    a[((xx - 140) / 90) ** 2 + ((yy - 300) / 60) ** 2 < 1] = [60, 62, 58]
    a += rng.normal(0, 9, a.shape)
    f = tmp_path / "lapangan" / name
    f.parent.mkdir(exist_ok=True)
    Image.fromarray(np.clip(a, 0, 255).astype("uint8")).save(f)
    return f


def test_color_proposals_accept_reject_and_export(st):
    s, tmp = st
    pid = co.add_photo(s, str(_zoned(tmp)), "Rina")["id"]
    j = co.propose_color(s, pid, 3, by="Rina")
    drafts = [f for f in j["features"] if co.is_draft(f)]
    assert len(drafts) >= 2 and all(f["shape"] == "poly" for f in drafts)
    oks = [f for f in drafts if f["kind"] == "zona_oks"]
    assert len(oks) == 1 and ("merah" in oks[0]["name"] or "coklat" in oks[0]["name"])
    us = [u for u, _ in oks[0]["pts"]]
    vs = [v for _, v in oks[0]["pts"]]
    assert 0.5 < min(us) < 0.6 and max(us) > 0.98 and min(vs) < 0.02  # zona oksida di kanan atas
    dark = [f for f in drafts if f["kind"] == "zona_lito" and f["attrs"]["_pct"] < 20]
    assert dark and 0.05 < min(u for u, _ in dark[0]["pts"]) < 0.12
    # ulang: usulan warna lama diganti, tidak menumpuk; fitur manual tidak tersentuh
    co.save_feature(s, pid, None, {"kind": "vein", "pts": [[0.1, 0.1], [0.2, 0.3]]}, "Rina")
    j2 = co.propose_color(s, pid, 3, by="Rina")
    assert len([f for f in j2["features"] if co.is_draft(f)]) == len(drafts) and any(f["kind"] == "vein" for f in j2["features"])
    # draf tidak ikut ekspor; terima satu, buang sisanya
    co.save_georef(s, pid, [{"name": f"G{i}", "u": u, "v": v, "e": 100 + u * 30, "n": 500, "rl": 50 + (1 - v) * 20}
                            for i, (u, v) in enumerate([(0.05, 0.05), (0.95, 0.05), (0.95, 0.95), (0.05, 0.95)])], "wall", "Rina")
    items, _ = co.export_items(s, [pid])
    assert [i["kind"] for i in items] == ["vein"]
    ox = next(f for f in j2["features"] if co.is_draft(f) and f["kind"] == "zona_oks")
    feats = co.accept_drafts(s, pid, [ox["id"]], "Rina")
    acc = next(f for f in feats if f["id"] == ox["id"])
    assert not co.is_draft(acc) and "_pct" not in acc["attrs"]
    feats = co.reject_drafts(s, pid, None, "Rina")
    assert not any(co.is_draft(f) for f in feats) and {f["kind"] for f in feats} == {"vein", "zona_oks"}
    assert {i["kind"] for i in co.export_items(s, [pid])[0]} == {"vein", "zona_oks"}
    # foto seragam: tidak ada usulan
    pid2 = co.add_photo(s, str(_img(tmp, "rata.jpg")), "Rina")["id"]
    assert co.propose_color(s, pid2, 2)["made"] == []


def test_ai_delineation_parse(st, monkeypatch):
    s, tmp = st
    pid = co.add_photo(s, str(_zoned(tmp)), "Rina")["id"]
    sch = co.delin_schema(["vein", "sesar"])
    assert sch["properties"]["features"]["items"]["properties"]["kind"]["enum"] == ["vein", "sesar"]
    p = co.delin_prompt([k for k in co.kinds(s) if k["key"] not in co.AUTO_SKIP and k["shape"] != "point"], "fokus vein", {"lithology": "Tuf"})
    assert "0-1000" in p and "vein:" in p and "skala" not in p.split("Aturan")[0] and "Tuf" in p and "fokus vein" in p
    res = {"features": [{"kind": "vein", "name": "Vein kuarsa", "points": [[500, 0], [600, 1000]], "confidence": "tinggi"},
                        {"kind": "zona_oks", "points": [[550, 0], [1000, 0], [1000, 400], [550, 300]]},
                        {"kind": "skala", "points": [[0, 0], [100, 0]]},     # tidak boleh diusulkan AI
                        {"kind": "kekar", "points": [[10, 10]]}],            # titik kurang
           "notes": "zona oksida di kanan atas"}
    calls = []

    def fake_http(url, body, timeout=0):
        calls.append(body)
        return {"message": {"content": json.dumps(res)}}
    monkeypatch.setattr(co.core_io, "_http", fake_http)
    j = co.ai_delineate(s, pid, "http://x", "qwen3-vl:8b", max_px=300)
    assert len(j["made"]) == 2 and j["skipped"] == 2 and calls[0]["format"]["required"] == ["features"]
    v = next(f for f in j["features"] if f["kind"] == "vein")
    assert v["pts"] == [[0.5, 0.0], [0.6, 1.0]] and v["attrs"]["_draft"] == "ai:qwen3-vl:8b" and v["src"] == "ai:qwen3-vl:8b"
    # koordinat piksel gambar yang dikirim (gaya Qwen2.5-VL): dikenali dari nilai > 1000, dibagi ukuran gambar
    res = {"features": [{"kind": "sesar", "points": [[0, 0], [1600, 1066]]}]}
    j = co.apply_delin(s, pid, res, "qwen2.5vl", (1600, 1066))
    f = next(f for f in j["features"] if f["kind"] == "sesar")
    assert f["pts"][1] == [1.0, 1.0]
    assert not any(x["kind"] == "vein" for x in j["features"])  # usulan AI lama diganti
    assert any(h["what"] == "usulan delineasi AI" for h in co.history(s, pid))
