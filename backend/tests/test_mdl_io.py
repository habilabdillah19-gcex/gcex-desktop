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


def test_rl_index_out_of_core_matches_argsort(cache_env, monkeypatch):
    import numpy as np
    monkeypatch.setattr(M, "ZS_STEP", 333)  # banyak potongan
    p = cache_env / "a.mdl"
    make_mdl(p, n=4000, seed=5)
    m = M.build_cache(p)
    c, _ = M.open_cache(p)
    z = np.asarray(c.col("z", "<f8"))
    ref = np.argsort(z, kind="stable")
    od = "<i4" if m["ord_dtype"] == "int32" else "<i8"
    assert np.array_equal(np.asarray(c.col("zord", od)), ref)
    assert np.array_equal(np.asarray(c.col("zs", "<f8")), z[ref])


def test_rl_index_fallback_when_off_grid(tmp_path):
    import numpy as np
    z = np.array([5.0, 1.0, 1.0000001, 3.0, 1.0, 2.5], "<f8")
    z.tofile(tmp_path / "z.bin")
    M._zsort(tmp_path, len(z), float(z.min()), float(z.max()), 1.0, np.int32)
    o = np.fromfile(tmp_path / "zord.bin", "<i4")
    assert np.array_equal(o, np.argsort(z, kind="stable"))
    assert np.all(np.diff(np.fromfile(tmp_path / "zs.bin", "<f8")) >= 0)


def test_fit_window_caps_block_count_from_top(cache_env):
    p = cache_env / "a.mdl"
    make_mdl(p, n=3000, seed=2)
    M.build_cache(p)
    c, m = M.open_cache(p)
    z0, z1, cap, tot = M.fit_window(c, None, None, 10 ** 6)
    assert not cap and tot == c.n and z0 is None
    z0, z1, cap, tot = M.fit_window(c, None, None, 1000)
    assert cap and tot == c.n and z1 is None
    idx = M.select(c, z0, z1)
    assert 0 < len(idx) <= 1000
    dz = m["root"][2] * 2.0 ** -m["maxL"]
    assert abs((z0 - m["origin"][2]) / dz - round((z0 - m["origin"][2]) / dz)) < 1e-6


def test_header_attribute_description_is_skipped():
    """Atribut berdeskripsi (kolom Description Surpac, mis. sg3 = "density") tidak boleh menggeser daftar atribut.
    Header SINTETIS; laporan pemilik 12 Nov 2026: 'Tipe atribut "" (24940) belum didukung'."""
    i32 = lambda v: struct.pack(">i", v)
    f64 = lambda v: struct.pack(">d", v)
    H = b"### Block Model ###\nVersion 4.0\n\x00uji.mdl\x00\x00" + b"\x00" * 12
    H += b"".join(f64(v) for v in (1000, 2000, 0, 12, 12, 6, 1200, 1200, 300)) + i32(0) + i32(4)
    H += b"au\x00" + i32(0) + i32(2) + i32(2) + f64(0) + b"\x00"                    # tanpa deskripsi
    H += b"sg3\x00" + i32(0) + i32(2) + i32(2) + f64(2.5) + b"density\x00"          # real berdeskripsi
    H += b"rock\x00" + i32(0) + i32(0) + i32(3) + b"BLANK\x00" + b"rock type\x00"   # karakter berdeskripsi
    H += b"n\x00" + i32(0) + i32(0) + i32(1) + i32(-9) + b"nomor\x00"                # integer berdeskripsi
    H += i32(0) + b"\x00" * 64
    h = M._parse_head(H, len(H), "uji.mdl")
    got = [(a["name"], a["def"], a.get("desc")) for a in h["attrs"]]
    assert got == [("au", 0.0, ""), ("sg3", 2.5, "density"), ("rock", "BLANK", "rock type"), ("n", -9, "nomor")]


def test_cache_root_can_be_moved_and_old_cache_removed(cache_env, tmp_path):
    """14 Nov 2026 (pemilik): cache .mdl 10,7 GB tidak muat di C: -> folder cache bisa dipindah (mis. drive D:)."""
    f = tmp_path / "a.mdl"
    make_mdl(f, n=500)
    M.build_cache(f)
    old = M.cache_root()
    info = M.cache_info()
    assert len(info["items"]) == 1 and info["used"] > 0 and not info["custom"]
    baru = tmp_path / "D_cache"
    r = M.set_cache_root(str(baru), hapus_lama=True)
    sub = baru / M.CUSTOM_SUB
    assert Path(r["root"]) == sub and r["custom"] and r["removed_old"] == 1
    assert M.cache_root() == sub and not any(d.is_dir() for d in old.iterdir())
    m = M.build_cache(f)  # dibangun ulang di folder baru
    assert m["n"] == 500 and M.cache_dir(f).parent == sub
    lain = sub / "folder_pengguna"  # folder lain di dalamnya TIDAK boleh ikut terhapus
    lain.mkdir()
    (lain / "penting.txt").write_text("x")
    assert M.clear_cache() == 1 and (lain / "penting.txt").exists()
    r = M.set_cache_root(None)
    assert not r["custom"] and M.cache_root() == old
    with pytest.raises(ValueError):
        M.set_cache_root(str(f / "bukan_folder"))
