"""Bangun Pit Studio: web-src-ps/*.js + app.css + body.html + pustaka -> app-ps/index.html (satu berkas HTML offline).

  python web-src-ps/bangun_ps.py            # tulis app-ps/index.html
  python web-src-ps/bangun_ps.py --cek      # gagal bila app-ps/index.html tidak sama dengan hasil bangun (dipakai CI)

- Versi = builder-ps.json extraMetadata.version, dicap sebagai window.GCEX_VER.
- Pembaca block model Surpac .mdl (a35) TIDAK disimpan di sini: dirakit dari sumber GC-Ex Block Model
  (web-src/mdlattr.js + web-src/gcex_base.html) setiap kali membangun, supaya hasil bacanya selalu sama.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "web-src-ps"
URUT = ["a1_core.js", "a2_ui.js", "a3_digit.js", "a4_param.js", "a5_gen.js", "a6_edit.js", "a7_out.js", "a8_stage.js", "a9_ramp.js",
        "a10_ui2.js", "a11_auto.js", "a12_plan.js", "a13_guide.js", "a14_manual.js", "a15_xroad.js", "a16_smooth.js", "a17_openedit.js",
        "a18_rampout.js", "a19_rampjoin.js", "a20_tools.js", "a21_fix.js", "a22_toptrim.js", "a23_terrace.js", "a24_data.js",
        "a24_demo.js", "a26_link.js", "a27_strict.js", "a28_demo2.js", "a30_sayatan.js", "a31_sched.js", "a32_demo3.js",
        "a34_review.js", "@mdl", "a36_gt.js", "a38_gtrep.js", "a39_elev.js", "a40_blok.js", "a29_i18n.js", "a33_i18n_sched.js", "a37_desktop.js"]
PUSTAKA = [P / "lib" / "three.min.js", P / "lib" / "OrbitControls.js", ROOT / "web-src" / "delaunator.min.js", P / "lib" / "clipper.js"]
IKON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 38 30%27%3E%3Crect x=%270.75%27 y=%270.75%27 "
        "width=%2736.5%27 height=%2728.5%27 rx=%274%27 fill=%27%23fff%27 stroke=%27%23c9d3e1%27 stroke-width=%271.5%27/%3E%3Cpath d=%27M3 8 H35 "
        "L31.5 13 H27.5 L25 18.5 H22 L20.5 24 H17.5 L16 18.5 H13 L10.5 13 H6.5 Z%27 fill=%27%231d5fd1%27/%3E%3C/svg%3E")


def baca(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def mdl() -> str:
    src = baca(ROOT / "web-src" / "gcex_base.html")
    a, b = src.index("SA.isMDL=function"), src.index("/* ================= permukaan grid dari string")
    kode = src[a:b].replace("/* @@MDLATTR@@ */", "")
    c = src.index("SA.surfAt=function")
    kode += src[c:src.index("\n", c)] + "\n"
    return ("/* a35: pembaca block model Surpac .mdl (Version 4.0) — dirakit APA ADANYA dari GC-Ex Block Model oleh bangun_ps.py\n"
            "   (web-src/mdlattr.js + web-src/gcex_base.html: SA.mdlHead / mdlParseHead / mdlDeps / readMDL / mdlExpr / surfAt). */\n"
            "const MDLSA=(function(){const SA={};\n" + baca(ROOT / "web-src" / "mdlattr.js") + "\n" + kode + "\nreturn SA;})();\n")


def bangun() -> str:
    ver = json.loads(baca(ROOT / "builder-ps.json"))["extraMetadata"]["version"]
    app = "\n".join(mdl() if f == "@mdl" else baca(P / f) for f in URUT)
    aman = lambda s: s.replace("</script", "<\\/script")
    return ('<!DOCTYPE html>\n<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Pit Studio</title><link rel="icon" href="' + IKON + '">\n<style>' + baca(P / "app.css") + "</style></head><body>\n"
            + baca(P / "body.html") + "\n<script>window.GCEX_VER='" + ver + "';</script>\n"
            + "".join("<script>" + aman(baca(l)) + "</script>\n" for l in PUSTAKA)
            + "<script>\n(function(){\n" + aman(app) + "\n})();\n</script></body></html>")


if __name__ == "__main__":
    h, out = bangun(), ROOT / "app-ps" / "index.html"
    if "--cek" in sys.argv:
        if not out.is_file() or baca(out) != h:
            raise SystemExit("app-ps/index.html tidak sama dengan sumber web-src-ps/ — jalankan: python web-src-ps/bangun_ps.py")
        print("Pit Studio: app-ps/index.html sesuai sumber")
    else:
        out.parent.mkdir(exist_ok=True)
        out.write_text(h, encoding="utf-8", newline="\n")
        print("Pit Studio", len(h), "byte ->", out.relative_to(ROOT))
