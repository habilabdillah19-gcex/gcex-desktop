"""Mode Transkrip borang (DB-Ex 0.45): AI hanya MENYALIN tulisan di kertas menjadi teks baris per baris; pengguna merapikan
teks itu, memilih pemisah sel, dan menentukan kolom teks mana masuk ke isian mana. Program lalu menyusun baris, validasi,
ringkasan dan pivot persis seperti hasil baca langsung (apply_ai). Usul pemilik: untuk borang padat (Daily Drilling Report
40 kegiatan) model 2b sering menggeser kolom / menyalin contoh; dengan transkrip, kesalahan terlihat dan diputuskan manusia.

Alur:  /transkrip (AI -> teks, disimpan di docs.teks)  ->  /transkrip/pratinjau (teks + pemisah -> kisi + usulan pemetaan)
       ->  /transkrip/terapkan (kisi + pemetaan -> header, baris, tabel tambahan; pemetaan disimpan per jenis borang).
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
from pathlib import Path
from typing import Any, Optional

from . import core_io
from . import core_forms as F

SEPS = {"|": "|", "tab": "\t", ",": ",", ";": ";"}
MAP_FILE = "transkrip_map.json"
_LABEL = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 _./()\-]{1,40}?)\s*[:=]\s*(.+?)\s*$")


# ---------------------------------------------------------------- prompt & AI
def prompt(ftype: str, extra: str = "") -> str:
    t = F.TYPES[ftype]
    cols = [lbl for _k, lbl, _t in F.ai_rows(t)]
    tabs = [f"{tt['name']}: " + ", ".join(lbl for _k, lbl, _t in tt["rows"]) for tt in (t.get("tables") or {}).values()]
    lines = ["Anda petugas data entry. SALIN semua tulisan pada formulir di gambar menjadi teks, baris per baris, urut dari atas ke bawah.",
             "Isian tunggal di kop (tanggal, shift, nama, unit, dll.) ditulis satu per baris: Label: nilai",
             "Baris tabel: sel dipisah ' | ' dalam urutan kolom di kertas; sel kosong ditulis - (jangan dilewati). "
             "Tulis judul kolom SEKALI pada baris pertama tabel. Satu baris tabel = satu baris teks; tulisan lanjutan di bawah "
             "sebuah sel digabung ke baris itu.",
             f"Kolom tabel yang biasanya ada di borang '{t['name']}': " + ", ".join(cols) + ".",
             *([f"Tabel lain pada borang: " + "; ".join(tabs)] if tabs else []),
             "Salin angka, kode dan tulisan PERSIS seperti tertulis (jangan diterjemahkan / dirapikan / dilengkapi). "
             "Tulisan yang tidak jelas: tebakan terbaik diakhiri '?'. Tanda ulang (\" 〃 ,,) ditulis 〃.",
             "Baca SEMUA baris yang terisi sampai baris terakhir. JANGAN mengulang baris, JANGAN menulis penjelasan, "
             "JANGAN mengarang baris yang tidak ada di kertas."]
    if extra and extra.strip():
        lines.append(f"Catatan pengguna: {extra.strip()}")
    lines.append("/no_think")
    return "\n".join(lines)


def _teks_path(s: F.Store, did: int) -> Path:
    p = s.root / "ai_mentah"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{did}_teks.txt"


def clean(txt: str) -> str:
    """Rapikan jawaban model: buang pagar kode / markdown, baris penjelasan Inggris, baris kembar berturut-turut, garis tabel."""
    out: list[str] = []
    for ln in (txt or "").replace("\r", "").split("\n"):
        ln = re.sub(r"^```\w*|```$", "", ln).replace("**", "").strip()
        ln = re.sub(r"^(?:[-*•]\s+|\d+[.)]\s+(?=[A-Za-z]))", "", ln)
        if not ln or re.fullmatch(r"[|\s:\-=–—]+", ln):  # garis pemisah tabel markdown
            continue
        if (len(ln) > 60 and ln.count(" ") > 8 and re.search(r"\b(the|here|this|image|form|I |we |shows|contains)\b", ln)) or \
                re.match(r"^(here|this|the|below|sure|okay|note)\b.*:?$", ln, re.I) and "|" not in ln and not _LABEL.match(ln):
            continue  # kalimat pengantar model ("Here is the transcription:"), bukan isi borang
        ln = ln.strip("|").strip() if ln.startswith("|") and ln.endswith("|") else ln
        if out and re.sub(r"\s+", "", ln.lower()) == re.sub(r"\s+", "", out[-1].lower()):
            continue
        out.append(ln)
    return "\n".join(out)


def ai_transcribe(s: F.Store, did: int, host: str, model: str, extra: str = "", max_px: int = 1600, by: str = "",
                  timeout: float = 900, trim: bool = True) -> dict:
    """AI menyalin kertas -> teks; disimpan di docs.teks (+ berkas ai_mentah/<id>_teks.txt). Tidak mengubah baris yang ada."""
    d = F.doc(s, did)
    host = (host or core_io.DEFAULT_HOST).rstrip("/")
    p = prompt(d["type"], extra)
    img, size = F._image_b64(s, d, max_px, trim)
    body = {"model": model, "messages": [{"role": "user", "content": p, "images": [img]}], "stream": False, "keep_alive": "30m",
            "options": {"temperature": 0, "num_ctx": F.ctx_for(size, p), "num_predict": F.N_PREDICT, "repeat_penalty": 1.1, "repeat_last_n": 160}}
    if F._can_think(host, model):
        body["think"] = False
    t0 = time.time()
    try:
        try:
            j = core_io._http(host + "/api/chat", body, timeout=timeout)
        except urllib.error.HTTPError as e:
            if "think" in body and e.code == 400:
                body.pop("think")
                F._THINK[(host, model)] = False
                j = core_io._http(host + "/api/chat", body, timeout=timeout)
            elif e.code >= 500:
                time.sleep(5)
                img, size = F._image_b64(s, d, min(1280, max(960, int(max(size) * 0.8))), trim)
                body["messages"] = [dict(body["messages"][0], images=[img])]
                body["options"] = dict(body["options"], num_ctx=F.ctx_for(size, p))
                j = core_io._http(host + "/api/chat", body, timeout=timeout)
            else:
                raise ValueError(F.ollama_why(e)) from e
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        raise ValueError(F.ollama_why(e)) from e
    except urllib.error.HTTPError as e:
        raise ValueError(F.ollama_why(e)) from e
    if j.get("error"):
        raise RuntimeError("Ollama: " + str(j["error"]))
    msg = j.get("message") or {}
    raw = str(msg.get("content") or "")
    teks = clean(raw)
    if not teks.strip():
        raise ValueError("AI tidak menyalin apa pun: " + F._why_empty(j))
    try:
        _teks_path(s, did).write_text(raw, encoding="utf-8")
    except OSError:
        pass
    secs = round(time.time() - t0, 1)
    with s.lock, s.conn() as c:
        c.execute("UPDATE docs SET teks=?, ai_model=?, ai_at=?, ai_secs=?, error=NULL WHERE id=?", (teks, model, core_io.now(), secs, did))
        F._hist(c, did, "AI menyalin teks", None, f"{teks.count(chr(10)) + 1} baris", "ai:" + model, by or "AI")
    ev = j.get("eval_count") or 0
    return {"teks": teks, "perf": {"secs": secs, "tokens": ev, "px": max(size),
                                   "tok_s": round(ev / (j["eval_duration"] / 1e9), 1) if j.get("eval_duration") else None}}


def save_teks(s: F.Store, did: int, teks: str, by: str) -> None:
    with s.lock, s.conn() as c:
        c.execute("UPDATE docs SET teks=? WHERE id=?", (teks or "", did))
        F._hist(c, did, "teks transkrip diedit", None, f"{len(teks or '')} karakter", "edit", by)


def get_teks(s: F.Store, did: int) -> str:
    with s.conn() as c:
        r = c.execute("SELECT teks FROM docs WHERE id=?", (did,)).fetchone()
    return (r[0] if r else "") or ""


# ---------------------------------------------------------------- teks -> kisi
def guess_sep(txt: str) -> str:
    """Pemisah yang paling konsisten muncul (>= 1 kali) pada baris terbanyak."""
    best, bn = "|", -1
    for name, ch in SEPS.items():
        n = sum(1 for ln in txt.split("\n") if ln.count(ch) >= 1)
        if n > bn:
            best, bn = name, n
    return best


def grid(txt: str, sep: str = "auto") -> dict:
    """Teks -> {sep, hdr: [[label, nilai]], rows: [[sel…]], raw: [baris asli untuk kisi]}. Baris 'Label: nilai' tanpa pemisah =
    isian kop; baris berpemisah = baris tabel. Baris tanpa pemisah & tanpa ':' = lanjutan sel terakhir baris tabel sebelumnya."""
    txt = clean(txt)
    if sep == "auto" or sep not in SEPS:
        sep = guess_sep(txt)
    ch = SEPS[sep]
    hdr: list[list[str]] = []
    rows: list[list[str]] = []
    for ln in txt.split("\n"):
        if ch in ln and ln.count(ch) >= 1 and not (ch != "|" and _LABEL.match(ln) and ln.count(ch) == 1 and ch == ","):
            cells = [c.strip() for c in ln.split(ch)]
            cells = ["" if F._JUNK.fullmatch(c) and "〃" not in c else c for c in cells]
            if any(cells):
                rows.append(cells)
            continue
        m = _LABEL.match(ln)
        if m and not rows:
            hdr.append([m.group(1).strip(), m.group(2).strip()])
        elif m:
            hdr.append([m.group(1).strip(), m.group(2).strip()])
        elif rows and ln.strip():
            rows[-1][-1] = (rows[-1][-1] + " " + ln.strip()).strip()
    n = max((len(r) for r in rows), default=0)
    rows = [r + [""] * (n - len(r)) for r in rows]
    return {"sep": sep, "hdr": hdr, "rows": rows, "ncol": n}


def _norm(x: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(x or "").lower())


def options(ftype: str) -> list[dict]:
    """Tujuan yang bisa dipilih per kolom: kolom baris (termasuk kolom AI, mis. 'jam' DDR) + tabel tambahan (awalan 'tabel:')."""
    t = F.TYPES[ftype]
    out, seen = [{"key": "", "label": "— abaikan —"}], set()
    for k, lbl, _tt in list(F.ai_rows(t)) + list(t["rows"]):
        if k not in seen:
            seen.add(k)
            out.append({"key": k, "label": lbl})
    for tb, tt in (t.get("tables") or {}).items():
        for k, lbl, _tt in tt["rows"]:
            out.append({"key": f"{tb}:{k}", "label": f"{tt['name']} · {lbl}"})
    return out


def hdr_options(ftype: str) -> list[dict]:
    return [{"key": "", "label": "— abaikan —"}] + [{"key": k, "label": lbl} for k, lbl, _t in F.TYPES[ftype]["header"]]


def _alias(ftype: str) -> dict[str, str]:
    t = F.TYPES[ftype]
    al: dict[str, str] = {}
    for k, lbl, _tt in list(t["rows"]) + list(F.ai_rows(t)):
        for x in (k, lbl, re.sub(r"\s*\(.*?\)", "", lbl)):
            al.setdefault(_norm(x), k)
    for tb, tt in (t.get("tables") or {}).items():
        for k, lbl, _tt in tt["rows"]:
            for x in (k, lbl, re.sub(r"\s*\(.*?\)", "", lbl)):
                al.setdefault(_norm(x), f"{tb}:{k}")
    al.update({"from": al.get("from", "from_m"), "to": al.get("to", "to_m"), "time": "jam", "jam": "jam", "waktu": "jam",
               "holeid": al.get("holeid", "hole_id"), "az": al.get("az", "az"), "azimuth": al.get("azimuth", "az"),
               "description": al.get("description", "aktivitas"), "uraian": al.get("uraian", "aktivitas"), "kegiatan": al.get("kegiatan", "aktivitas")})
    return {k: v for k, v in al.items() if k}


def suggest(ftype: str, g: dict, saved: Optional[dict]) -> dict:
    """Usulan pemetaan: (1) pemetaan tersimpan untuk jenis ini bila jumlah kolom cocok; (2) baris judul kolom di teks;
    (3) urutan kolom AI bawaan. hdr: label kop -> kunci header (padanan nama)."""
    n = g["ncol"]
    cols: list[str] = [""] * n
    title_row = -1
    al = _alias(ftype)
    def look(c: str) -> str:
        nc = _norm(c)
        if not nc:
            return ""
        if nc in al:
            return al[nc]
        cand = [k for k in al if len(k) >= 4 and len(nc) >= 4 and (k.startswith(nc) or nc.startswith(k) or (len(nc) >= 6 and nc in k))]
        return al[max(cand, key=len)] if cand else ""
    for i, r in enumerate(g["rows"][:3]):
        hit = [look(c) for c in r]
        if n >= 2 and sum(1 for h in hit if h) >= max(2, int(0.6 * len([c for c in r if c]))):
            cols, title_row = [h for h in hit] + [""] * (n - len(hit)), i
            break
    if title_row < 0:
        if saved and len(saved.get("cols") or []) == n:
            cols = list(saved["cols"])
        else:
            ai = [k for k, _l, _t in F.ai_rows(F.TYPES[ftype])]
            cols = (ai + [""] * n)[:n]
    hk = {_norm(x): k for k, lbl, _t in F.TYPES[ftype]["header"] for x in (k, lbl, re.sub(r"\s*\(.*?\)", "", lbl))}
    hk.update({"date": "tanggal", "tanggal": "tanggal", "shift": "shift", "rig": "rig", "drillrig": "rig", "client": "client",
               "driller": "driller", "geologist": "geologist", "lokasi": "lokasi", "location": "lokasi", "pit": "lokasi"})
    hdr = []
    for lbl, _v in g["hdr"]:
        nl = _norm(lbl)
        k = hk.get(nl) or next((v for kk, v in hk.items() if kk and (kk in nl or nl in kk) and len(kk) >= 3), "")
        if saved and (saved.get("hdr") or {}).get(nl):
            k = saved["hdr"][nl]
        hdr.append(k)
    return {"cols": cols, "hdr": hdr, "title_row": title_row}


def _map_path(s: F.Store) -> Path:
    return s.root / MAP_FILE


def load_map(s: F.Store) -> dict:
    try:
        return json.loads(_map_path(s).read_text(encoding="utf-8")) if _map_path(s).exists() else {}
    except (OSError, ValueError):
        return {}


def save_map(s: F.Store, ftype: str, sep: str, cols: list[str], hdr_pairs: list[tuple[str, str]]) -> None:
    m = load_map(s)
    cur = m.get(ftype) or {}
    hd = dict(cur.get("hdr") or {})
    hd.update({_norm(lbl): k for lbl, k in hdr_pairs if k})
    m[ftype] = {"sep": sep, "cols": list(cols), "hdr": hd}
    try:
        _map_path(s).write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def preview(s: F.Store, did: int, teks: Optional[str], sep: str) -> dict:
    d = F.doc(s, did)
    txt = teks if teks is not None else get_teks(s, did)
    saved = (load_map(s).get(d["type"]) or None)
    if sep == "auto" and saved and saved.get("sep") in SEPS:
        g = grid(txt, saved["sep"])
    else:
        g = grid(txt, sep)
    sg = suggest(d["type"], g, saved)
    return {"teks": txt, **g, "map": sg, "options": options(d["type"]), "hdr_options": hdr_options(d["type"]),
            "type": d["type"], "type_name": F.TYPES[d["type"]]["name"]}


# ---------------------------------------------------------------- kisi + pemetaan -> baris borang
def build(ftype: str, g: dict, cols: list[str], hdr_keys: list[str], skip_rows: Optional[list[int]] = None) -> dict:
    """{header, rows, <tabel>…} dalam bentuk yang diterima apply_ai. Sel diakhiri '?' -> ragu. Baris yang seluruh selnya
    kosong atau berisi nama kolom dibuang. Satu baris teks boleh mengisi baris utama DAN tabel tambahan sekaligus
    (Daily Drilling Report: lubang + kegiatan sebaris)."""
    t = F.TYPES[ftype]
    skip = set(skip_rows or [])
    names = {_norm(x) for k, lbl, _tt in list(t["rows"]) + list(F.ai_rows(t)) for x in (k, lbl)}
    names |= {_norm(x) for tt in (t.get("tables") or {}).values() for k, lbl, _tt in tt["rows"] for x in (k, lbl)}
    out: dict[str, Any] = {"header": {"ragu": []}, "rows": [], "catatan": ""}
    for tt in (t.get("tables") or {}).values():
        out[tt["ai"]] = []
    tbl_ai = {tb: tt["ai"] for tb, tt in (t.get("tables") or {}).items()}
    for (lbl, val), k in zip(g["hdr"], hdr_keys + [""] * len(g["hdr"])):
        if k and val and not F._JUNK.fullmatch(val):
            if val.endswith("?"):
                val = val[:-1].strip()
                out["header"]["ragu"].append(k)
            out["header"][k] = val
    for i, r in enumerate(g["rows"]):
        if i in skip:
            continue
        main: dict[str, Any] = {"ragu": []}
        extra: dict[str, dict[str, Any]] = {}
        for c, k in zip(r, cols + [""] * len(r)):
            if not k:
                continue
            v = str(c or "").strip()
            if F._JUNK.fullmatch(v) and "〃" not in v:
                v = ""
            ragu = v.endswith("?")
            if ragu:
                v = v[:-1].strip()
            if ":" in k:
                tb, kk = k.split(":", 1)
                x = extra.setdefault(tb, {"ragu": []})
                if kk in x and x[kk]:
                    x[kk] = (x[kk] + " " + v).strip()
                else:
                    x[kk] = v
                if ragu:
                    x["ragu"].append(kk)
            else:
                main[k] = (main[k] + " " + v).strip() if main.get(k) else v
                if ragu:
                    main["ragu"].append(k)
        filled = [v for k, v in main.items() if k != "ragu" and v]
        if filled and sum(1 for v in filled if _norm(v) in names) < max(1, len(filled) // 2 + 1):
            out["rows"].append(main)
        for tb, x in extra.items():
            f2 = [v for k, v in x.items() if k != "ragu" and v]
            if f2 and sum(1 for v in f2 if _norm(v) in names) < max(1, len(f2) // 2 + 1) and tb in tbl_ai:
                out[tbl_ai[tb]].append(x)
    return out


def apply(s: F.Store, did: int, teks: str, sep: str, cols: list[str], hdr: list[str], by: str, skip_rows: Optional[list[int]] = None,
          save: bool = True) -> dict:
    d = F.doc(s, did)
    g = grid(teks, sep)
    if not g["rows"] and not g["hdr"]:
        raise ValueError("Teks belum berisi baris tabel (pisahkan sel dengan pemisah yang dipilih) atau isian 'Label: nilai'.")
    if len(cols) != g["ncol"]:
        cols = (list(cols) + [""] * g["ncol"])[:g["ncol"]]
    res = build(d["type"], g, cols, hdr, skip_rows)
    n_rows = len(res["rows"]) + sum(len(v) for k, v in res.items() if isinstance(v, list) and k != "rows")
    if not n_rows and not any(v for k, v in res["header"].items() if k != "ragu"):
        raise ValueError("Tidak ada kolom yang dipetakan ke isian borang: pilih tujuan kolom pada kisi pratinjau.")
    save_teks(s, did, teks, by)
    model = (d.get("ai_model") or "transkrip")
    out = F.apply_ai(s, did, res, "transkrip/" + model, 0.0, by)
    if save:
        save_map(s, d["type"], g["sep"], cols, list(zip([h for h, _v in g["hdr"]], hdr)))
    return out


# ---------------------------------------------------------------- API
class TrBody(F.FBody):
    id: int
    host: str = ""
    model: str = ""
    extra: str = ""
    max_px: int = 1600
    trim: bool = True


class TeksBody(F.FBody):
    id: int
    teks: Optional[str] = None
    sep: str = "auto"


class TerapBody(F.FBody):
    id: int
    teks: str
    sep: str = "|"
    cols: list[str] = []
    hdr: list[str] = []
    skip_rows: list[int] = []
    save_map: bool = True


@F.router.post("/transkrip")
def api_transkrip(b: TrBody) -> dict:
    s = F.store(b.folder)
    r = ai_transcribe(s, b.id, b.host, b.model, b.extra, b.max_px, b.by, trim=b.trim)
    return {"ok": True, **r, **preview(s, b.id, r["teks"], "auto")}


@F.router.post("/transkrip/simpan")
def api_transkrip_simpan(b: TeksBody) -> dict:
    s = F.store(b.folder)
    save_teks(s, b.id, b.teks or "", b.by)
    return {"ok": True}


@F.router.post("/transkrip/pratinjau")
def api_transkrip_pratinjau(b: TeksBody) -> dict:
    return {"ok": True, **preview(F.store(b.folder), b.id, b.teks, b.sep)}


@F.router.post("/transkrip/terapkan")
def api_transkrip_terapkan(b: TerapBody) -> dict:
    s = F.store(b.folder)
    apply(s, b.id, b.teks, b.sep, b.cols, b.hdr, b.by, b.skip_rows, b.save_map)
    return {"ok": True, **F._full(s, b.id)}
