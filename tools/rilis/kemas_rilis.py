"""Kemas satu rilis GC-Ex lengkap untuk GitHub Release (dipanggil CI setelah ketiga installer dibangun).

Isi folder keluaran (semua diunggah ke Release v<versi>):
  GC-Ex-Setup-<v>.exe, GC-Ex-Drillhole-Setup-<v>.exe, Core-Ex-Setup-<v>.exe   installer (dipasang terpisah)
  GC-Ex-<v>_1_Dokumen.zip            README, panduan teknis, tutorial PDF (GC-Ex, Core-Ex, aktivasi lisensi)
  GC-Ex-<v>_2_Data-Latihan.zip       data dummy / simulasi (GC-Ex Drillhole & Block Model, Core-Ex) + generatornya
  GC-Ex-<v>_3_Lisensi-dan-Tentang.zip  TENTANG.txt, syarat penggunaan, lisensi pihak ketiga, penafian merek,
                                     alat pembuat lisensi untuk admin (TANPA kunci privat)
  GC-Ex-<v>_CATATAN_RILIS.md         isi rilis, daftar perubahan (commit) sejak rilis sebelumnya, SHA-256 tiap file
  SHA256SUMS.txt                     sidik jari semua file rilis
Kode sumber (zip / tar.gz) ditambahkan GitHub otomatis dari tag v<versi> (commit yang sama).

Pemakaian: python tools/rilis/kemas_rilis.py <versi> <folder_dist> <folder_keluaran> [folder_data_dummy_core]
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
APPS = [("GC-Ex-Setup", "GC-Ex Block Model"), ("GC-Ex-Drillhole-Setup", "GC-Ex Drillhole"), ("Core-Ex-Setup", "Core-Ex")]
KUNCI_PRIVAT = ("KUNCI_PRIVAT", "private", ".pem", ".key")


def git(*a):
    try:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
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


def main():
    ver, dist, outd = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    core_dummy = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    tag = f"v{ver}"
    if outd.exists():
        shutil.rmtree(outd)
    outd.mkdir(parents=True)
    sha = os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD")
    run = os.environ.get("GITHUB_RUN_NUMBER", "lokal")
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M WIB")

    # ---- installer
    inst = []
    for stem, nm in APPS:
        f = dist / f"{stem}-{ver}.exe"
        if not f.exists():
            raise SystemExit(f"installer tidak ada: {f}")
        shutil.copy2(f, outd / f.name)
        inst.append((f.name, nm))

    D = ROOT / "docs"
    # ---- 1 dokumen
    dok = outd / f"GC-Ex-{ver}_1_Dokumen.zip"
    zip_dir(dok, [
        (ROOT / "README.md", "README.md"),
        (D / "PANDUAN_INSTALL.md", "Panduan_Teknis/PANDUAN_INSTALL.md"),
        (D / "PANDUAN_CORE.md", "Panduan_Teknis/PANDUAN_CORE.md"),
        (D / "PANDUAN_CORE.html", "Panduan_Teknis/PANDUAN_CORE.html"),
        (D / "tutorial-gcex" / "GCEx_Tutorial_Modelling_Estimasi.pdf", "Tutorial/GC-Ex_Tutorial_Modelling_Estimasi.pdf"),
        (D / "Core-Ex_Tutorial_Penggunaan.pdf", "Tutorial/Core-Ex_Tutorial_Penggunaan.pdf"),
        (D / "GC-Ex_Tutorial_Aktivasi_Lisensi.pdf", "Tutorial/GC-Ex_Tutorial_Aktivasi_Lisensi.pdf"),
        (D / "tutorial-core" / "README.md", "Tutorial/Core-Ex_tutorial_README.md"),
        (D / "tutorial-aktivasi" / "BACA_SAYA.md", "Tutorial/Aktivasi_tutorial_BACA_SAYA.md"),
    ])
    # ---- 2 data latihan
    dat = outd / f"GC-Ex-{ver}_2_Data-Latihan.zip"
    items = [
        (D / "tutorial-gcex" / "data", "GC-Ex_Drillhole_BlockModel_SIM"),
        (D / "tutorial-gcex" / "make_sim_data.py", "Generator/make_sim_data.py"),
        (D / "tutorial-core" / "buat_data_dummy.py", "Generator/buat_data_dummy_core.py"),
        (D / "referensi", "Core-Ex_Referensi"),
    ]
    if core_dummy and core_dummy.exists():
        items.append((core_dummy, "Core-Ex_Data_Dummy"))
    zip_dir(dat, items)
    # ---- 3 lisensi & tentang
    tentang = outd / "TENTANG.txt"
    pk = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    tentang.write_text(
        f"GC-Ex (Grade Control Excellence) {ver}\r\n"
        f"Aplikasi: GC-Ex Block Model, GC-Ex Drillhole, Core-Ex (dipasang terpisah)\r\n"
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
    log = git("log", rng, "--no-merges", "--pretty=format:- `%h` %ad %s", "--date=format:%Y-%m-%d %H:%M")
    if not prev:
        log = "\n".join(log.splitlines()[:40])
    files = sorted(p for p in outd.iterdir() if p.is_file())
    sums = [(sha256(p), p.name, p.stat().st_size) for p in files]
    L = [f"# GC-Ex {ver}", "",
         f"Commit `{sha[:7]}` · build GitHub Actions run {run} · {now}", "",
         "## Isi rilis", "",
         "| File | Isi | Ukuran |", "|---|---|---|"]
    desc = {n: f"Installer {a}" for n, a in inst}
    desc[dok.name] = "README, panduan teknis, tutorial PDF (GC-Ex Modelling & Estimasi, Core-Ex, aktivasi lisensi)"
    desc[dat.name] = "Data latihan dummy/simulasi (GC-Ex Drillhole & Block Model, Core-Ex) + generator"
    desc[lis.name] = "Tentang, syarat penggunaan, lisensi open source, penafian merek, alat pembuat lisensi admin (tanpa kunci privat)"
    for h, n, s in sums:
        L.append(f"| `{n}` | {desc.get(n, '')} | {s / 1048576:.1f} MB |")
    L += ["| Source code (zip / tar.gz) | Kode sumber commit ini (otomatis dari GitHub) | |", "",
          "Ketiga aplikasi dipasang satu per satu (installer terpisah). Aplikasi offline, tanpa pembaruan otomatis: "
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
