"""Samakan cap versi window.GCEX_VER di app-ow/index.html dengan builder-ow.json (extraMetadata.version)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ver = json.loads((ROOT / "builder-ow.json").read_text(encoding="utf-8"))["extraMetadata"]["version"]
p = ROOT / "app-ow" / "index.html"
s = p.read_text(encoding="utf-8")
s2, n = re.subn(r"window\.GCEX_VER='[^']*'", "window.GCEX_VER='%s'" % ver, s, count=1)
if n != 1:
    raise SystemExit("cap GCEX_VER tidak ditemukan di app-ow/index.html")
if s2 != s:
    p.write_text(s2, encoding="utf-8")
print("Ore Works cap versi =", ver)
