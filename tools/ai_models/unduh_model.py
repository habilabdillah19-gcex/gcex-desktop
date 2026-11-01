"""Unduh model ONNX DB-Ex (tools/ai_models/models.json) ke folder tujuan dan periksa SHA256.

Dipakai CI sebelum PyInstaller (folder models/ ikut dibundel) dan oleh pengembang:
    python tools/ai_models/unduh_model.py models
File yang sudah ada dengan SHA256 benar tidak diunduh ulang. Gagal (jaringan / SHA256 salah) -> keluar dengan kode 1."""
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

M = json.loads((Path(__file__).resolve().parent / "models.json").read_text(encoding="utf-8"))


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    bad = 0
    for name, m in M.items():
        if name.startswith("_"):
            continue
        p = out / name
        if p.exists() and sha(p) == m["sha256"]:
            print("OK (sudah ada)", name)
            continue
        for i in range(3):
            try:
                req = urllib.request.Request(m["url"], headers={"User-Agent": "dbex-build"})
                with urllib.request.urlopen(req, timeout=600) as r, open(p, "wb") as f:
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        f.write(b)
                break
            except Exception as e:  # noqa: BLE001
                print(f"coba-{i + 1} gagal {name}: {e}")
                time.sleep(10)
        if not p.exists() or sha(p) != m["sha256"]:
            print("GAGAL / SHA256 salah:", name)
            bad += 1
        else:
            print("OK", name, p.stat().st_size)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "models")))
