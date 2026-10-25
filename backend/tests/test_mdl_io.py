"""Uji pembaca .mdl besar: cache kolom, potongan RL/XY, dan penulisan ulang .mdl mini (termasuk atribut kategori)."""
import io
import random
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gcex_backend import mdl_io as M  # noqa: E402

O, RT = (500000.0, 9000000.0, 100.0), (80.0, 80.0, 80.0)
ATTR = [("au", 2, -99.0), ("rock", 3, "WASTE"), ("pass", 1, 0), ("ox", 3, "")]


def _cstr(s):
    return s.encode("latin1") + b"\0"


def make_mdl(p: Path, n=3000, seed=1, tail=b"\xce\r\n!AA!\r\n"):
    """File .mdl sintetis versi 4: blok level 1-3 (ukuran 40/20/10 m), 2 atribut kategori."""
    rnd = random.Random(seed)
    h = b"### Block Model ###\nVersion 4.0\n" + _cstr("uji.mdl") + b"\0" + b"\0" * 12
    h += struct.pack(">9d", *O, *RT, 80.0, 80.0, 80.0) + struct.pack(">ii", 0, len(ATTR) + 1)
    for name, ty, d in ATTR:
        h += _cstr(name) + struct.pack(">i", 0) + b"\0" * 4 + struct.pack(">i", ty)
        h += struct.pack(">d", d) + b"\0" if ty == 2 else (_cstr(d) + b"\0" if ty == 3 else struct.pack(">i", d) + b"\0")
    h += _cstr("kelas") + struct.pack(">i", 1) + b"\0" * 4 + _cstr('IIF(au>=1,"HG","LG")')
    h += b"\0" * 4
    rocks, oxs = ["BX", "AND", "QV", "DAC"], ["OX", "TR", "SF"]
    seen_r, seen_o = {}, {}
    recs, blocks = [], []
    for _ in range(n):
        lv = rnd.randint(1, 3)
        dg = 0
        for l in range(1, lv + 1):
            dg |= rnd.randint(0, 7) << (3 * (l - 1))
        hi = (dg << 5) | lv
        au = rnd.random() * 3
        r, o = rnd.choice(rocks), rnd.choice(oxs)
        b = struct.pack(">IId", hi, 0, au)
        for val, seen, lst in ((r, seen_r, rocks), (None, None, None), (o, seen_o, oxs)):
            if val is None:
                b += struct.pack(">i", rnd.randint(0, 3))
                continue
            code = lst.index(val) + 1
            if code not in seen:
                seen[code] = 1
                b += struct.pack(">i", -code) + _cstr(val)
            else:
                b += struct.pack(">i", code)
        recs.append(b)
        # titik tengah yang diharapkan
        x = y = z = 0.0
        for l in range(1, lv + 1):
            d = (dg >> (3 * (l - 1))) & 7
            s = 2.0 ** -l
            x += RT[0] * s if d & 4 else 0
            y += RT[1] * s if d & 2 else 0
            z += RT[2] * s if d & 1 else 0
        hz = RT[2] * 2.0 ** -lv / 2
        blocks.append((O[2] + z + hz, hz, r, o, au))
    p.write_bytes(h + b"".join(recs) + M.END_MARK + tail)
    return blocks


@pytest.fixture
def cache_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GCEX_CACHE", str(tmp_path / "cache"))
    monkeypatch.setattr(M, "CHUNK", 777)  # paksa record & teks kategori terbelah di batas potongan
    return tmp_path


def test_roundtrip_identical_and_categories(cache_env):
    f = cache_env / "uji.mdl"
    blocks = make_mdl(f)
    meta = M.build_cache(f)
    assert meta["n"] == len(blocks)
    assert {k: sorted(v.values()) for k, v in meta["dicts"].items()} == {"1": ["AND", "BX", "DAC", "QV"], "3": ["OX", "SF", "TR"]}
    c, _ = M.open_cache(f)
    b = io.BytesIO()
    M.write_subset(c, M.select(c), b)
    assert b.getvalue() == f.read_bytes()  # tanpa filter = file asli byte demi byte


def test_subset_rl_is_valid_mdl_with_its_own_category_texts(cache_env):
    f = cache_env / "uji.mdl"
    blocks = make_mdl(f, n=5000, seed=7)
    M.build_cache(f)
    c, _ = M.open_cache(f)
    zlo, zhi = 130.0, 150.0
    idx = M.select(c, zlo, zhi)
    want = [i for i, (z, hz, *_r) in enumerate(blocks) if not (z + hz <= zlo or z - hz >= zhi)]
    assert idx.tolist() == want
    sub = cache_env / "sub.mdl"
    with open(sub, "wb") as fh:
        M.write_subset(c, idx, fh)
    # potongan dibaca lagi sebagai .mdl biasa: jumlah blok, kategori & kadar harus sama
    M.CHUNK = 1 << 20
    m2 = M.build_cache(sub)
    assert m2["n"] == len(want)
    c2, _ = M.open_cache(sub)
    au = c2.col("f0", "<f8")
    rock = c2.col("f1", "<i4")
    d1 = {int(k): v for k, v in m2["dicts"]["1"].items()}
    for j, i in enumerate(want[:500]):
        assert au[j] == blocks[i][4] and d1[int(rock[j])] == blocks[i][2]


def test_bbox_and_status(cache_env):
    f = cache_env / "uji.mdl"
    make_mdl(f, n=800)
    st = M.open_model(f)
    for _ in range(200):
        if st["state"] != "building":
            break
        __import__("time").sleep(0.05)
        st = M.open_model(f)
    assert st["state"] == "ready" and st["info"]["n"] == 800
    c, _ = M.open_cache(f)
    allx = M.select(c)
    part = M.select(c, bbox=[O[0], O[0] + 20, O[1], O[1] + 20])
    assert 0 < len(part) < len(allx)


def test_not_mdl_rejected(cache_env):
    f = cache_env / "bukan.mdl"
    f.write_bytes(b"X,Y,Z\n1,2,3\n")
    with pytest.raises(ValueError):
        M.read_header(f)


def test_select_by_center_with_open_sides(cache_env):
    f = cache_env / "uji.mdl"
    blocks = make_mdl(f, n=4000, seed=3)
    M.build_cache(f)
    c, _ = M.open_cache(f)
    idx = M.select(c, 120.0, 150.0, [None, O[0] + 40, None, None], center=True)
    x = c.col("x", "<f8")
    want = [i for i, (z, *_r) in enumerate(blocks) if 120.0 <= z <= 150.0 and x[i] <= O[0] + 40]
    assert idx.tolist() == want and 0 < len(want) < len(blocks)
