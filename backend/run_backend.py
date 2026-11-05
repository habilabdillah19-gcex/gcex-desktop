"""Titik masuk backend GC-Ex (dipakai Electron & PyInstaller).
Contoh: python run_backend.py --port 8765
"""
import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    # wajib sebelum apa pun yang memakai multiprocessing (kriging membagi blok ke beberapa inti):
    # tanpa ini, versi terbungkus PyInstaller di Windows akan menjalankan ulang aplikasinya.
    import multiprocessing
    multiprocessing.freeze_support()
    ap = argparse.ArgumentParser(description="GC-Ex backend")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    log_dir = os.environ.get("GCEX_LOG_DIR")
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(Path(log_dir) / "backend.log", encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)
    import uvicorn
    from gcex_backend.server import app
    # hanya 127.0.0.1: backend tidak bisa diakses dari komputer lain
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
