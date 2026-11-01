"""Alat pengembang (CI manual): periksa & unduh kandidat model ONNX untuk DB-Ex dari Hugging Face.

Mencetak lisensi tiap repo, daftar file ONNX, ukuran, SHA256, serta nama/bentuk input-output (onnxruntime), lalu
menyalin file terpilih ke folder keluaran (untuk diunggah ke pre-release dev-wheels). Bukan bagian aplikasi.
Pemakaian: python tools/ai_models/probe_hf.py <folder_keluaran>
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

CANDIDATES = {
    # Segment Anything (ringan): MobileSAM / SlimSAM / SAM ViT-B ekspor ONNX
    "sam": ["Acly/MobileSAM", "Xenova/slimsam-77-uniform", "Xenova/slimsam-50-uniform", "onnx-community/sam-vit-base",
            "Xenova/sam-vit-base", "vietanhdev/segment-anything-onnx-models"],
    # Depth Anything V2 Small (Apache-2.0); Base/Large berlisensi non-komersial -> tidak dipakai
    "depth": ["onnx-community/depth-anything-v2-small", "Xenova/depth-anything-small-hf", "onnx-community/depth-anything-v2-base"],
}
MAX_MB = 450


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "dbex-probe"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read()


def main(out: Path) -> None:
    import onnxruntime as ort
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for group, repos in CANDIDATES.items():
        for repo in repos:
            try:
                info = json.loads(get(f"https://huggingface.co/api/models/{repo}?blobs=true"))
            except Exception as e:  # noqa: BLE001
                print(f"[{group}] {repo}: tidak ada ({e})")
                continue
            lic = (info.get("cardData") or {}).get("license") or [t for t in info.get("tags", []) if t.startswith("license:")]
            files = [(s["rfilename"], s.get("size") or 0) for s in info.get("siblings", []) if s["rfilename"].endswith(".onnx")
                     or s["rfilename"].endswith(".onnx_data")]
            print(f"[{group}] {repo}: lisensi={lic} sha={info.get('sha')}")
            for f, sz in files:
                print(f"    {f}  {sz / 1e6:.1f} MB")
            report[repo] = {"license": lic, "sha": info.get("sha"), "files": files}
            for f, sz in files:
                if not f.endswith(".onnx") or sz / 1e6 > MAX_MB:
                    continue
                if any(x in f for x in ("_fp16", "_q4", "_bnb4", "_int8", "_uint8")):
                    continue
                url = f"https://huggingface.co/{repo}/resolve/{info.get('sha')}/{f}"
                try:
                    b = get(url)
                except Exception as e:  # noqa: BLE001
                    print("      gagal unduh", f, e)
                    continue
                name = (repo.replace("/", "__") + "__" + f.replace("/", "__"))
                p = out / name
                p.write_bytes(b)
                h = hashlib.sha256(b).hexdigest()
                try:
                    s = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
                    io = {"in": [(i.name, i.shape, i.type) for i in s.get_inputs()], "out": [(o.name, o.shape, o.type) for o in s.get_outputs()]}
                except Exception as e:  # noqa: BLE001
                    io = {"error": str(e)[:300]}
                print(f"      OK {name} {len(b) / 1e6:.1f} MB sha256={h}\n        {io}")
                report[repo].setdefault("downloaded", []).append({"file": f, "name": name, "sha256": h, "bytes": len(b), "url": url, "io": io})
    (out / "model_report.json").write_text(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
