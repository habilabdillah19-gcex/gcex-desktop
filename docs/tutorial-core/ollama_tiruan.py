"""Ollama tiruan untuk tangkapan layar tutorial DB-Ex (jawaban AI contoh, bukan model sungguhan).

Menjawab /api/version, /api/tags, /api/show dan /api/chat seperti Ollama 0.12.x dengan satu model vision qwen3-vl:8b.
Foto yang dikirim dicocokkan dengan thumbnail foto di paket data dummy, lalu jawabannya disusun dari tabel geologi
fiktif yang sama dengan generator data dummy, sehingga isian AI di tutorial konsisten dan masuk akal.

Pemakaian: python ollama_tiruan.py <folder Foto_Core> [port=11434]
"""
import base64
import io
import os
import time
import json
import random
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageOps

FOTO = Path(sys.argv[1])
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 11434

# tabel geologi fiktif (sama dengan buat_data_dummy.py): from, to, litologi, alterasi, oksidasi, warna, rekahan
GEO = {
    "LTH-101": [(0.0, 8.0, "AND", "Argilik", "OX", "Coklat kemerahan (Reddish Brown)", 0.8),
                (8.0, 21.5, "AND", "Propilitik", "FR", "Hijau keabuan (Greenish Grey)", 0.35),
                (21.5, 30.5, "AND", "Propilitik", "FR", "Hijau keabuan gelap (Dark Greenish Grey)", 0.3),
                (30.5, 36.8, "DAC", "Silisifikasi", "FR", "Abu-abu (Grey)", 0.45),
                (36.8, 41.2, "QV", "Silisifikasi kuat", "FR", "Abu-abu gelap (Dark Grey)", 0.25),
                (41.2, 50.0, "AND", "Propilitik", "FR", "Hijau keabuan (Greenish Grey)", 0.3)],
    "LTH-102": [(0.0, 6.0, "Andesit", "Argilik", "OX", "Coklat kekuningan (Yellowish Brown)", 0.85),
                (6.0, 19.0, "Andesit", "Propilitik", "FR", "Hijau keabuan (Greenish Grey)", 0.35),
                (19.0, 23.5, "Dasit", "Silisifikasi", "FR", "Abu-abu terang (Light Grey)", 0.5),
                (23.5, 50.0, "Andesit", "Propilitik lemah", "FR", "Hijau keabuan (Greenish Grey)", 0.3)],
}
WEA = {"OX": "W4 (Highly Weathered)", "FR": "W2 (Slightly Weathered)"}


def thumb(im: Image.Image) -> list:
    im = ImageOps.exif_transpose(im).convert("L").resize((24, 18))
    return list(im.get_flattened_data()) if hasattr(im, "get_flattened_data") else list(im.getdata())


REF = {}
for f in sorted(FOTO.rglob("*.jpg")):
    with Image.open(f) as im:
        REF[f.name] = thumb(im)


def match(img_b64: str) -> str:
    with Image.open(io.BytesIO(base64.b64decode(img_b64))) as im:
        t = thumb(im)
    return min(REF, key=lambda n: sum((a - b) ** 2 for a, b in zip(REF[n], t)))


def geo_at(hole: str, d: float):
    for g in GEO[hole]:
        if g[0] <= d < g[1]:
            return g
    return GEO[hole][-1]


def answer(name: str, rows: int = 4) -> dict:
    m = re.match(r"(LTH-\d+)_Box(\d+)_(\d+\.\d+)-(\d+\.\d+)", name)
    if m:
        hole, box, a, b = m.group(1), m.group(2), float(m.group(3)), float(m.group(4))
    else:  # IMG_0001: dibaca dari papan label
        hole, box, a, b = "LTH-101", "11", 36.30, 40.10
    rnd = random.Random(name)
    g = geo_at(hole, (a + b) / 2)
    frac = g[6]
    rqd = max(5, min(95, round(100 - frac * 85 + rnd.uniform(-6, 6))))
    rec = max(70, min(100, round(98 - frac * 18 + rnd.uniform(-3, 3))))
    segs = []
    L = (b - a) / rows
    for r in range(rows):
        d0 = a + r * L
        cuts = [0.0]
        for gg in GEO[hole]:  # batas geologi di baris ini
            t = (gg[0] - d0) / L
            if 0.05 < t < 0.95:
                cuts.append(round(t, 3))
        if len(cuts) == 1:
            cuts.append(round(rnd.uniform(0.4, 0.6), 3))
        cuts.append(1.0)
        for s0, s1 in zip(cuts, cuts[1:]):
            gs = geo_at(hole, d0 + L * (s0 + s1) / 2)
            fr = gs[6] + rnd.uniform(-0.1, 0.15)
            segs.append({"row": r + 1, "start": s0, "end": s1, "lithology": gs[2], "alteration": gs[3], "color": gs[5],
                         "weathering": WEA[gs[4]], "oxidation": gs[4], "rqd_pct": max(0, min(100, round(100 - fr * 90))),
                         "recovery_pct": max(60, min(100, round(99 - fr * 20))), "ff_per_m": round(2 + fr * 14, 1),
                         "gsi": "35-45" if fr > 0.6 else ("45-55" if fr > 0.4 else "55-65"), "rmr": round(70 - fr * 40),
                         "notes": "zona hancur" if fr > 0.75 else None})
    return {"hole_id": hole, "box_no": box, "from_m": a, "to_m": b, "drill_start": "05-03-25",
            "photo_date": "12-03-25" if hole == "LTH-101" else "20-03-25", "lithology": g[2], "color": g[5],
            "weathering": WEA[g[4]], "oxidation": g[4], "alteration": g[3], "condition": "WET", "recovery_pct": rec, "rqd_pct": rqd,
            "gsi": "35-45" if frac > 0.6 else ("45-55" if frac > 0.4 else "55-65"), "rmr": round(70 - frac * 40),
            "notes": ("Rekahan rapat, zona hancur di baris 1." if frac > 0.6 else
                      "Vein kuarsa banded dengan sulfida (pirit, kalkopirit) di baris 2-3." if g[2] == "QV" else
                      "Kekar terbuka jarang; core umumnya utuh."),
            "confidence": "sedang" if not m else "tinggi", "segments": segs}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, o):
        b = json.dumps(o).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/api/version"):
            return self._send({"version": "0.12.9"})
        return self._send({"models": [
            {"name": "qwen3-vl:8b", "size": 6100000000, "details": {"parameter_size": "8.8B", "families": ["qwen3vl"]}},
            {"name": "qwen3-vl:4b", "size": 3300000000, "details": {"parameter_size": "4.4B", "families": ["qwen3vl"]}},
            {"name": "llama3.2:3b", "size": 2000000000, "details": {"parameter_size": "3.2B", "families": ["llama"]}}]})

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        if self.path.startswith("/api/show"):
            return self._send({"capabilities": ["completion"] + (["vision"] if "vl" in body.get("model", "") else [])})
        msg = (body.get("messages") or [{}])[-1]
        imgs = msg.get("images") or []
        rows = int((re.search(r"Kotak berisi (\d+) baris", msg.get("content", "")) or [0, 4])[1])
        ans = answer(match(imgs[0]) if imgs else "", rows)
        time.sleep(float(os.environ.get("OLLAMA_DELAY", "0")))  # agar antrean AI sempat tertangkap kamera
        return self._send({"model": body.get("model"), "message": {"role": "assistant", "content": json.dumps(ans)}, "done": True})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
