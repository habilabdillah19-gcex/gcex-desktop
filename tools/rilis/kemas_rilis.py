"""Kemas satu rilis GC-Ex lengkap untuk GitHub Release (dipanggil CI setelah ketiga installer dibangun).

Isi folder keluaran (semua diunggah ke Release v<versi>):
  GC-Ex-Setup-<v>.exe, GC-Ex-Drillhole-Setup-<v>.exe, DB-Ex-Setup-<v>.exe   installer (dipasang terpisah)
  GC-Ex-<v>_1_Dokumen.zip            README, panduan teknis, tutorial PDF (GC-Ex, DB-Ex, aktivasi lisensi)
  GC-Ex-<v>_2_Data-Latihan.zip       data dummy / simulasi (GC-Ex Drillhole & Block Model, DB-Ex) + generatornya
  GC-Ex-<v>_3_Lisensi-dan-Tentang.zip  TENTANG.txt, syarat penggunaan, lisensi pihak ketiga, penafian merek,
                                     alat pembuat lisensi untuk admin (TANPA kunci privat)
  GC-Ex-<v>_CATATAN_RILIS.md         isi rilis, daftar perubahan (commit) sejak rilis sebelumnya, SHA-256 tiap file
  SHA256SUMS.txt                     sidik jari semua file rilis
Kode sumber (zip / tar.gz) ditambahkan GitHub otomatis dari tag v<versi> (commit yang sama).

Pemakaian: python tools/rilis/kemas_rilis.py <versi> <folder_dist> <folder_keluaran> [folder_data_dummy_core]
           python tools/rilis/kemas_rilis.py --cek   (periksa kenaikan versi terhadap rilis sebelumnya, jalankan sebelum push)
"""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPS = [("GC-Ex-Setup", "GC-Ex Block Model"), ("GC-Ex-Drillhole-Setup", "GC-Ex Drillhole"), ("DB-Ex-Setup", "DB-Ex")]
KUNCI_PRIVAT = ("KUNCI_PRIVAT", "private", ".pem", ".key")


def git(*a):
    try:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout.strip()
    except Exception:
        return ""


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def zip_dir(out: Path, items: list[tuple[Path, str]]) -> list[str]:
    """items: (sumber file/folder, path di dalam zip). Hasil: daftar isi."""
    names = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for src, arc in items:
            if not src.exists():
                continue
            files = [src] if src.is_file() else sorted(p for p in src.rglob("*") if p.is_file())
            for f in files:
                low = f.name.lower()
                if any(k.lower() in low for k in KUNCI_PRIVAT) or "__pycache__" in f.parts:
                    continue
                a = arc if src.is_file() else f"{arc}/{f.relative_to(src).as_posix()}"
                z.write(f, a)
                names.append(a)
    return names


# ---- pengaman versi: nomor versi sebuah aplikasi hanya boleh naik bila ada berkas MILIK aplikasi itu yang berubah
# sejak rilis sebelumnya. Kejadian yang dicegah: Block Model ikut dinaikkan 0.24.16 -> 0.24.22 padahal isinya identik
# dengan 0.24.15 (perubahan hanya di Drill Hole), sehingga pengguna mengira ada pembaruan Block Model.
# Berkas bersama keluarga (README, PANDUAN_INSTALL, Tutorial Update / Petunjuk Teknis, alat rilis, CI) tidak dihitung
# milik aplikasi mana pun. Bila sebuah push HANYA mengubah berkas bersama, satu aplikasi boleh naik versi supaya
# perubahan itu tetap terbit di Release (aturan CLAUDE.md: setiap pembaruan harus masuk Release).
VERSI_APP = {
    "GC-Ex Block Model": ("package.json", ("version",)),
    "GC-Ex Drillhole": ("builder-dh.json", ("extraMetadata", "version")),
    "DB-Ex": ("builder-core.json", ("extraMetadata", "version")),
}
MILIK = {
    "GC-Ex Block Model": ["app/", "web-src/", "electron/", "backend/", "build/", "legal/", "package-lock.json",
                          "docs/tutorial-gcex/GCEx_Tutorial_Block_Model.pdf", "docs/tutorial-gcex/src/build_tutorial_bm.py",
                          "docs/tutorial-gcex/src/bm_bab.py", "docs/tutorial-gcex/src/tutorial_bm_shots.py",
                          "docs/tutorial-gcex/src/build_bm/", "docs/tutorial-gcex/data/SIM_BM_GC_kadar.csv", "docs/tutorial-gcex/tambah_unsur_bm.py"],
    "GC-Ex Drillhole": ["app-dh/", "web-src-dh/", "web-src/", "electron/", "backend/", "build/", "legal/", "package-lock.json",
                        "docs/tutorial-gcex/"],
    "DB-Ex": ["app-core/", "app_core_qt/", "electron/", "backend/", "build/", "legal/", "docs/tutorial-core/", "docs/referensi/",
              "docs/PANDUAN_CORE", "docs/DB-Ex_", "builder-core.json"],
}
# berkas Block Model di docs/tutorial-gcex/ tidak dihitung milik Drillhole
BUKAN_DH = ("docs/tutorial-gcex/GCEx_Tutorial_Block_Model.pdf", "docs/tutorial-gcex/src/build_tutorial_bm.py", "docs/tutorial-gcex/src/bm_bab.py",
            "docs/tutorial-gcex/src/tutorial_bm_shots.py", "docs/tutorial-gcex/src/build_bm/", "docs/tutorial-gcex/data/SIM_BM_GC_kadar.csv",
            "docs/tutorial-gcex/tambah_unsur_bm.py")


def _ver_di(ref, app):
    f, keys = VERSI_APP[app]
    try:
        o = json.loads(git("show", f"{ref}:{f}") or "{}")
        for k in keys:
            o = o.get(k, {}) if isinstance(o, dict) else {}
        return o if isinstance(o, str) and o else None
    except Exception:
        return None


def _vt(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return ()


def _milik(app, path):
    if app == "GC-Ex Drillhole" and path.startswith(BUKAN_DH):
        return False
    if app == "DB-Ex" and path == "builder-core.json":
        return False          # baris versinya sendiri tidak dihitung; isi DB-Ex ada di folder di atas
    return any(path == p or path.startswith(p) for p in MILIK[app])


def cek_versi(prev, sha):
    """Kembalikan daftar pelanggaran (kosong = aman). prev = tag rilis sebelumnya."""
    if not prev:
        return []
    ubah = [p for p in git("diff", "--name-only", f"{prev}..{sha}").splitlines() if p]
    naik = []
    for app in VERSI_APP:
        a, b = _ver_di(prev, app), _ver_di(sha, app)
        if a and b and _vt(b) > _vt(a):
            naik.append((app, a, b))
    punya = {app: [p for p in ubah if _milik(app, p)] for app in VERSI_APP}
    if not any(punya.values()):
        # hanya berkas bersama yang berubah: satu aplikasi boleh naik agar perubahan itu terbit
        return [] if len(naik) <= 1 else [f"{app} {a} -> {b}: hanya berkas bersama keluarga GC-Ex yang berubah; naikkan SATU aplikasi saja"
                                           for app, a, b in naik[1:]]
    return [f"{app} {a} -> {b}: tidak ada berkas {app} yang berubah sejak {prev} (kembalikan versinya ke {a})"
            for app, a, b in naik if not punya[app]]


def _tag_sebelum(sha, tag=None):
    tags = [t for t in git("tag", "--list", "v*", "--sort=-v:refname").splitlines() if t and t != tag]
    return next((t for t in tags if subprocess.run(["git", "merge-base", "--is-ancestor", t, sha], cwd=ROOT).returncode == 0), "")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cek":
        sha = git("rev-parse", "HEAD"); prev = _tag_sebelum(sha)
        bad = cek_versi(prev, sha)
        print(f"cek versi terhadap {prev or '(belum ada tag)'}: " + ("aman" if not bad else "DITOLAK"))
        for b in bad:
            print("  - " + b)
        raise SystemExit(1 if bad else 0)
    ver, dist, outd = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    _sha = os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD")
    _bad = cek_versi(_tag_sebelum(_sha, f"v{ver}"), _sha)
    if _bad:
        raise SystemExit("Pengaman versi menolak rilis ini:\n  - " + "\n  - ".join(_bad) +
                         "\nNomor versi aplikasi hanya boleh naik bila berkas aplikasi itu berubah (lihat CLAUDE.md).")
    core_dummy = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    tag = f"v{ver}"
    if outd.exists():
        shutil.rmtree(outd)
    outd.mkdir(parents=True)
    sha = os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD")
    run = os.environ.get("GITHUB_RUN_NUMBER", "lokal")
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M WIB")

    # ---- installer
    # Setiap rilis memuat installer KETIGA aplikasi pada versinya masing-masing. CI memang membangun
    # ketiganya di tiap run, jadi tidak ada gunanya membuang yang nomor versinya kebetulan bukan yang
    # tertinggi: dulu perbaikan GC-Ex tidak pernah sampai ke pengguna selama DB-Ex terus naik versi.
    # Tag rilis tetap memakai versi tertinggi; versi tiap aplikasi disebut di catatan rilis.
    inst = []
    for stem, nm in APPS:
        f = dist / f"{stem}-{ver}.exe"
        if not f.exists():                       # versinya tidak naik -> pakai yang ada di folder dist
            kand = sorted(dist.glob(f"{stem}-*.exe"), key=lambda q: q.stat().st_mtime)
            f = kand[-1] if kand else None
        if f is not None and f.exists():
            shutil.copy2(f, outd / f.name)
            v_app = f.stem[len(stem) + 1:] or "?"
            inst.append((f.name, nm, v_app))
    if not inst:
        raise SystemExit(f"tidak ada installer satu pun di {dist}")
    has_core = any(n.startswith("DB-Ex") for n, _, _ in inst)
    has_gcex = any(n.startswith("GC-Ex") for n, _, _ in inst)

    D = ROOT / "docs"
    # ---- 1 dokumen
    dok = outd / f"GC-Ex-{ver}_1_Dokumen.zip"
    zip_dir(dok, [
        (ROOT / "README.md", "README.md"),
        (D / "PANDUAN_INSTALL.md", "Panduan_Teknis/PANDUAN_INSTALL.md"),
        (D / "GC-Ex_Tutorial_Aktivasi_Lisensi.pdf", "Tutorial/GC-Ex_Tutorial_Aktivasi_Lisensi.pdf"),
        (D / "tutorial-aktivasi" / "BACA_SAYA.md", "Tutorial/Aktivasi_tutorial_BACA_SAYA.md"),
    ] + ([(D / "tutorial-gcex" / "GCEx_Tutorial_Modelling_Estimasi.pdf", "Tutorial/GC-Ex_Tutorial_Modelling_Estimasi.pdf"), (D / "tutorial-gcex" / "GCEx_Tutorial_Block_Model.pdf", "Tutorial/GC-Ex_Tutorial_Block_Model.pdf"), (D / "GCEx_Tutorial_Update.pdf", "Tutorial/GC-Ex_Tutorial_Update.pdf"), (D / "GCEx_Petunjuk_Teknis.pdf", "Panduan_Teknis/GC-Ex_Petunjuk_Teknis.pdf")] if has_gcex else [])
      + ([(D / "PANDUAN_CORE.md", "Panduan_Teknis/PANDUAN_CORE.md"), (D / "PANDUAN_CORE.html", "Panduan_Teknis/PANDUAN_CORE.html"),
          (D / "DB-Ex_Tutorial_Penggunaan.pdf", "Tutorial/DB-Ex_Tutorial_Penggunaan.pdf"),
          (D / "DB-Ex_Panduan_Teknis.pdf", "Panduan_Teknis/DB-Ex_Panduan_Teknis.pdf"),
          (D / "tutorial-core" / "README.md", "Tutorial/DB-Ex_tutorial_README.md")] if has_core else []))
    # ---- 2 data latihan
    dat = outd / f"GC-Ex-{ver}_2_Data-Latihan.zip"
    items = []
    if has_gcex:
        items += [(D / "tutorial-gcex" / "data", "GC-Ex_Drillhole_BlockModel_SIM"), (D / "tutorial-gcex" / "make_sim_data.py", "Generator/make_sim_data.py"), (D / "tutorial-gcex" / "make_sim_laterit.py", "Generator/make_sim_laterit.py"), (D / "tutorial-gcex" / "tambah_unsur_bm.py", "Generator/tambah_unsur_bm.py")]
    if has_core:
        items += [(D / "tutorial-core" / "buat_data_dummy.py", "Generator/buat_data_dummy_core.py"), (D / "referensi", "DB-Ex_Referensi")]
        if core_dummy and core_dummy.exists():
            items.append((core_dummy, "DB-Ex_Data_Dummy"))
    zip_dir(dat, items)
    # ---- 3 lisensi & tentang
    tentang = outd / "TENTANG.txt"
    pk = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    tentang.write_text(
        f"GC-Ex (Grade Control Excellence) {ver}\r\n"
        f"Aplikasi: GC-Ex Block Model, GC-Ex Drillhole, DB-Ex (dipasang terpisah)\r\n"
        f"Commit sumber: {sha}\r\nBuild GitHub Actions run: {run}\r\nTanggal build: {now}\r\n"
        f"Electron {pk.get('devDependencies', {}).get('electron', '?')}\r\n"
        f"Offline: aplikasi tidak memeriksa / memasang pembaruan lewat internet. Versi baru diminta ke admin.\r\n"
        f"Lisensi: kunci lisensi terikat komputer (lihat Tutorial Aktivasi Lisensi).\r\n", encoding="utf-8")
    lis = outd / f"GC-Ex-{ver}_3_Lisensi-dan-Tentang.zip"
    zip_dir(lis, [
        (tentang, "TENTANG.txt"),
        (ROOT / "legal", "Legal"),
        (ROOT / "tools" / "lisensi", "Alat_Admin_Lisensi"),
    ])
    tentang.unlink()

    # ---- catatan rilis
    tags = [t for t in git("tag", "--list", "v*", "--sort=-v:refname").splitlines() if t and t != tag]
    prev = next((t for t in tags if subprocess.run(["git", "merge-base", "--is-ancestor", t, sha], cwd=ROOT).returncode == 0), "")
    rng = f"{prev}..{sha}" if prev else sha
    WIB = datetime.timezone(datetime.timedelta(hours=7))
    rows = []
    for ln in git("-c", "i18n.logOutputEncoding=UTF-8", "log", rng, "--no-merges", "--pretty=format:%h\x1f%cI\x1f%s").splitlines():
        h, d, m = (ln.split("\x1f") + ["", ""])[:3]
        try:
            d = datetime.datetime.fromisoformat(d).astimezone(WIB).strftime("%Y-%m-%d %H:%M WIB")
        except ValueError:
            pass
        rows.append(f"- `{h}` {d} {m}")
    log = "\n".join(rows)
    if not prev:
        log = "\n".join(log.splitlines()[:40])
    files = sorted(p for p in outd.iterdir() if p.is_file())
    sums = [(sha256(p), p.name, p.stat().st_size) for p in files]
    L = [f"# GC-Ex {ver}", "",
         f"Commit `{sha[:7]}` · build GitHub Actions run {run} · {now}", "",
         "## Isi rilis", "",
         "| File | Isi | Ukuran |", "|---|---|---|"]
    desc = {n: f"Installer {a} {v}" for n, a, v in inst}
    desc[dok.name] = "README, panduan teknis, tutorial PDF (GC-Ex Modelling & Estimasi, DB-Ex, aktivasi lisensi)"
    desc[dat.name] = "Data latihan dummy/simulasi (" + ", ".join(nm for _, nm, _ in inst) + ") + generator"
    desc[lis.name] = "Tentang, syarat penggunaan, lisensi open source, penafian merek, alat pembuat lisensi admin (tanpa kunci privat)"
    for h, n, s in sums:
        L.append(f"| `{n}` | {desc.get(n, '')} | {s / 1048576:.1f} MB |")
    L += ["| Source code (zip / tar.gz) | Kode sumber commit ini (otomatis dari GitHub) | |", "",
          "Versi tiap aplikasi di rilis ini: " + ", ".join(f"{nm} {v}" for _, nm, v in inst) + ". "
          + ("Aplikasi yang tidak ada installernya di sini tetap memakai rilis sebelumnya. " if len(inst) < len(APPS) else "")
          + "Aplikasi dipasang satu per satu (installer terpisah). Aplikasi offline, tanpa pembaruan otomatis: "
          "pelanggan meminta versi baru ke admin.", "",
          f"## Perubahan sejak {prev or 'awal'}", "", log or "- (tidak ada commit baru)", "",
          "## SHA-256", "", "```"] + [f"{h}  {n}" for h, n, _ in sums] + ["```", ""]
    notes = outd / f"GC-Ex-{ver}_CATATAN_RILIS.md"
    notes.write_text("\n".join(L), encoding="utf-8")
    (outd / "SHA256SUMS.txt").write_text("".join(f"{h}  {n}\n" for h, n, _ in sums) +
                                         f"{sha256(notes)}  {notes.name}\n", encoding="utf-8")
    for p in sorted(outd.iterdir()):
        print(f"{p.stat().st_size:>12}  {p.name}")


if __name__ == "__main__":
    main()
