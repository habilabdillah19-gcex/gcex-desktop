"""Tulis baris register ke workbook Excel yang SUDAH ADA tanpa menyimpan ulang workbook.

Mengapa tidak openpyxl.save()? openpyxl membangun ulang seluruh file: grafik, gambar, slicer, pivot
dan sebagian link ke workbook lain bisa hilang atau rusak. Modul ini hanya menyunting sel-sel tujuan
di XML sheet (bagian lain file disalin apa adanya, byte demi byte), sehingga rumus, link eksternal,
format bersyarat, grafik dan makro VBA (.xlsm) tetap utuh.

Aturan penulisan:
- kolom dicocokkan dengan NAMA header (bukan posisi);
- hanya kolom INPUT yang ditulis: kolom yang berisi rumus di baris data tidak pernah ditimpa;
- baris baru ditaruh setelah baris terakhir yang kolom kuncinya terisi;
- kode yang sudah ada dilewati (mode "skip") atau kolom inputnya diperbarui (mode "update");
- salinan cadangan dibuat sebelum file diganti; file diganti secara atomik (tulis ke file sementara dulu).
"""
from __future__ import annotations

import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from lxml import etree

M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
XMLNS = "http://www.w3.org/XML/1998/namespace"
q = lambda t: f"{{{M}}}{t}"  # noqa: E731


class WorkbookLocked(RuntimeError):
    pass


def _norm(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s or "").lower())


def col_idx(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch.upper()) - 64)
    return n


def col_letter(i: int) -> str:
    s = ""
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def _split_ref(ref: str) -> tuple[int, int]:
    m = re.match(r"^\$?([A-Z]+)\$?(\d+)$", ref.upper())
    return col_idx(m.group(1)), int(m.group(2))


def _resolve(base: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    parts = (base.rsplit("/", 1)[0] + "/" + target).split("/") if "/" in base else target.split("/")
    out: list[str] = []
    for p in parts:
        if p == "..":
            out.pop()
        elif p and p != ".":
            out.append(p)
    return "/".join(out)


def _rels(z: zipfile.ZipFile, part: str) -> dict[str, tuple[str, str]]:
    d, f = part.rsplit("/", 1) if "/" in part else ("", part)
    rp = (d + "/" if d else "") + "_rels/" + f + ".rels"
    if rp not in z.namelist():
        return {}
    root = etree.fromstring(z.read(rp))
    return {e.get("Id"): (e.get("Type", "").rsplit("/", 1)[-1], _resolve(part, e.get("Target")))
            for e in root.findall(f"{{{PR}}}Relationship") if e.get("TargetMode") != "External"}


def check_unlocked(p: Path) -> None:
    """Excel mengunci file yang sedang dibuka; ia juga membuat file '~$nama.xlsx' di folder yang sama."""
    msg = (f"Workbook '{p.name}' sedang dibuka di Excel. Simpan & tutup dulu di Excel, lalu kirim lagi "
           "(GC-Ex tidak menulis ke file yang sedang dibuka supaya perubahan Anda di Excel tidak hilang).")
    try:
        with open(p, "r+b"):
            pass
    except PermissionError as e:
        raise WorkbookLocked(msg) from e


def _replace_retry(src: str, dst: Path, tries: int = 8) -> None:
    """Ganti file secara atomik. Di Windows, OneDrive / antivirus / indexer kadang memegang file sebentar:
    coba lagi beberapa kali sebelum menyerah dengan pesan yang jelas."""
    import time
    for k in range(tries):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if k == tries - 1:
                raise WorkbookLocked(f"Workbook '{dst.name}' sedang dipakai program lain (Excel, OneDrive, antivirus). "
                                     "Tutup workbook / tunggu sinkronisasi selesai, lalu kirim lagi. File asli tidak berubah.")
            time.sleep(0.25 * (k + 1))


class _Book:
    def __init__(self, path: Path):
        self.path = path
        self.z = zipfile.ZipFile(path)
        names = set(self.z.namelist())
        if "xl/workbook.xml" not in names:
            raise ValueError("Bukan workbook Excel .xlsx/.xlsm (format .xls lama tidak didukung; simpan ulang sebagai .xlsx di Excel).")
        wb = etree.fromstring(self.z.read("xl/workbook.xml"))
        rels = _rels(self.z, "xl/workbook.xml")
        self.sheets: dict[str, str] = {}
        for s in wb.iter(q("sheet")):
            rid = s.get(f"{{{R}}}id")
            if rid in rels and rels[rid][0] == "worksheet":
                self.sheets[s.get("name")] = rels[rid][1]
        self.sst: list[str] = []
        sp = next((t for k, (ty, t) in rels.items() if ty == "sharedStrings"), None)
        if sp and sp in names:
            for si in etree.fromstring(self.z.read(sp)).iter(q("si")):
                self.sst.append("".join(t.text or "" for t in si.iter(q("t")) if t.getparent().tag != q("rPh")))
        self._trees: dict[str, etree._ElementTree] = {}

    def tree(self, part: str):
        if part not in self._trees:
            parser = etree.XMLParser(huge_tree=True, remove_blank_text=False)
            self._trees[part] = etree.ElementTree(etree.fromstring(self.z.read(part), parser))
        return self._trees[part]

    def text(self, c) -> Optional[str]:
        t = c.get("t")
        if t == "inlineStr":
            return "".join(x.text or "" for x in c.iter(q("t")))
        v = c.find(q("v"))
        if v is None or v.text is None:
            return None
        if t == "s":
            try:
                return self.sst[int(v.text)]
            except (ValueError, IndexError):
                return None
        return v.text


def _scan(book: _Book, part: str, headers: list[str], max_scan: int = 30):
    want = {_norm(h): h for h in headers if _norm(h)}
    sd = book.tree(part).getroot().find(q("sheetData"))
    best = (0, {})
    for row in sd.iterfind(q("row")):
        r = int(row.get("r"))
        if r > max_scan:
            break
        found: dict[str, int] = {}
        for c in row.iterfind(q("c")):
            k = _norm(book.text(c))
            if k in want and k not in found:
                found[k] = _split_ref(c.get("r"))[0]
        if len(found) > len(best[1]):
            best = (r, found)
    return best


def _set_cell(c, v: Any) -> None:
    for ch in list(c):
        c.remove(ch)
    if "t" in c.attrib:
        del c.attrib["t"]
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return
    if isinstance(v, bool):
        c.set("t", "b")
        etree.SubElement(c, q("v")).text = "1" if v else "0"
    elif isinstance(v, (int, float)):
        etree.SubElement(c, q("v")).text = repr(float(v)) if isinstance(v, float) and not float(v).is_integer() else str(int(v)) if float(v).is_integer() else repr(v)
    else:
        c.set("t", "inlineStr")
        t = etree.SubElement(etree.SubElement(c, q("is")), q("t"))
        s = str(v)
        t.text = s
        if s != s.strip():
            t.set(f"{{{XMLNS}}}space", "preserve")


def write_register(path: str | Path, headers: list[str], rows: list[list[Any]], sheet: Optional[str] = None,
                   key_header: Optional[str] = None, mode: str = "skip", dry_run: bool = False,
                   backup: bool = True) -> dict:
    """Rencanakan (dry_run) atau tulis baris register ke workbook yang sudah ada. Lihat docstring modul."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {p}")
    if p.suffix.lower() not in (".xlsx", ".xlsm"):
        raise ValueError("Hanya file .xlsx / .xlsm yang bisa ditulisi GC-Ex.")
    if not dry_run:
        check_unlocked(p)
    book = _Book(p)
    try:
        cands = [sheet] if sheet else list(book.sheets)
        if sheet and sheet not in book.sheets:
            raise ValueError(f"Sheet '{sheet}' tidak ada. Sheet tersedia: {', '.join(book.sheets)}")
        scored = [(s, _scan(book, book.sheets[s], headers)) for s in cands]
        sname, (hrow, colmap) = max(scored, key=lambda t: len(t[1][1]))
        if len(colmap) < 2:
            raise ValueError("Header register (mis. 'Kode Poligon GC') tidak ditemukan di sheet mana pun.")
        part = book.sheets[sname]
        tree = book.tree(part)
        sd = tree.getroot().find(q("sheetData"))
        key_h = key_header if key_header in headers else headers[0]
        key_col = colmap.get(_norm(key_h))
        if not key_col:
            raise ValueError(f"Kolom kunci '{key_h}' tidak ada di sheet '{sname}'.")

        rows_el: dict[int, Any] = {}
        formula_cols: set[int] = set()
        formula_last = 0
        existing: dict[str, int] = {}
        last_key = hrow
        for row in sd.iterfind(q("row")):
            r = int(row.get("r"))
            rows_el[r] = row
            if r <= hrow:
                continue
            for c in row.iterfind(q("c")):
                ci = _split_ref(c.get("r"))[0]
                if c.find(q("f")) is not None:
                    formula_cols.add(ci)
                    formula_last = max(formula_last, r)
                elif ci == key_col:
                    v = book.text(c)
                    if v not in (None, ""):
                        existing.setdefault(str(v).strip().upper(), r)
                        last_key = max(last_key, r)

        mapping = []
        write_cols: list[tuple[int, int]] = []  # (indeks di headers, kolom)
        for i, h in enumerate(headers):
            ci = colmap.get(_norm(h))
            if ci is None:
                mapping.append({"header": h, "column": None, "status": "tidak ada di sheet"})
            elif ci in formula_cols:
                mapping.append({"header": h, "column": col_letter(ci), "status": "rumus (tidak ditimpa)"})
            else:
                mapping.append({"header": h, "column": col_letter(ci), "status": "ditulis"})
                write_cols.append((i, ci))
        ki = headers.index(key_h)

        plan, skipped, seen = [], [], set()
        nxt = last_key + 1
        for r in rows:
            k = str(r[ki] if ki < len(r) else "").strip()
            if not k:
                continue
            ku = k.upper()
            if ku in seen:
                skipped.append({"code": k, "reason": "ganda di kiriman GC-Ex"})
                continue
            seen.add(ku)
            if ku in existing:
                if mode == "update":
                    plan.append({"code": k, "row": existing[ku], "action": "perbarui", "values": r})
                else:
                    skipped.append({"code": k, "reason": f"sudah ada di baris {existing[ku]}"})
                continue
            plan.append({"code": k, "row": nxt, "action": "baru", "values": r})
            nxt += 1

        warnings = []
        if formula_cols and any(x["row"] > formula_last for x in plan):
            warnings.append(f"Rumus di sheet hanya sampai baris {formula_last}; baris setelahnya akan berisi input tanpa rumus. "
                            f"Tarik (fill down) rumus di Excel sampai baris {max(x['row'] for x in plan)}.")
        result = {"file": str(p), "sheet": sname, "header_row": hrow, "key_column": col_letter(key_col),
                  "mapping": mapping, "rows": [{k: v for k, v in x.items() if k != "values"} for x in plan],
                  "added": sum(1 for x in plan if x["action"] == "baru"),
                  "updated": sum(1 for x in plan if x["action"] == "perbarui"),
                  "skipped_existing": [s["code"] for s in skipped], "skipped": skipped,
                  "missing_columns": [m["header"] for m in mapping if m["column"] is None],
                  "formula_columns_kept": [m["header"] for m in mapping if m["status"].startswith("rumus")],
                  "warnings": warnings, "dry_run": dry_run, "backup": None}
        if dry_run or not plan:
            return result

        # ---- terapkan ke XML sheet ----
        all_r = sorted(rows_el)
        for x in plan:
            r = x["row"]
            row = rows_el.get(r)
            if row is None:
                row = etree.Element(q("row"), r=str(r))
                after = [n for n in all_r if n < r]
                if after:
                    rows_el[after[-1]].addnext(row)
                else:
                    sd.insert(0, row)
                rows_el[r] = row
                all_r = sorted(rows_el)
            above = rows_el.get(r - 1)
            for i, ci in write_cols:
                ref = f"{col_letter(ci)}{r}"
                cells = list(row.iterfind(q("c")))
                c = next((e for e in cells if e.get("r") == ref), None)
                if c is None:
                    c = etree.Element(q("c"), r=ref)
                    if above is not None:  # ikut format sel di atasnya
                        a = next((e for e in above.iterfind(q("c")) if e.get("r") == f"{col_letter(ci)}{r - 1}"), None)
                        if a is not None and a.get("s"):
                            c.set("s", a.get("s"))
                    later = [e for e in cells if _split_ref(e.get("r"))[0] > ci]
                    if later:
                        later[0].addprevious(c)
                    else:
                        row.append(c)
                elif c.find(q("f")) is not None:
                    continue  # pengaman: sel rumus tidak pernah ditimpa
                _set_cell(c, x["values"][i] if i < len(x["values"]) else None)
            if row.get("spans"):
                del row.attrib["spans"]  # opsional; dihapus agar tidak salah bila kolom bertambah

        last_row = max(x["row"] for x in plan)
        dim = tree.getroot().find(q("dimension"))
        if dim is not None and ":" in dim.get("ref", ""):
            a, b = dim.get("ref").split(":")
            bc, br = _split_ref(b)
            if last_row > br:
                dim.set("ref", f"{a}:{col_letter(bc)}{last_row}")
        changed = {part: tree}

        # perpanjang tabel Excel (ListObject) yang header-nya di baris header register
        srels = _rels(book.z, part)
        for rid, (ty, tp) in srels.items():
            if ty != "table" or tp not in book.z.namelist():
                continue
            tt = book.tree(tp)
            t = tt.getroot()
            c1, r1 = _split_ref(t.get("ref").split(":")[0])
            c2, r2 = _split_ref(t.get("ref").split(":")[1])
            if r1 == hrow and last_row > r2:
                nref = f"{col_letter(c1)}{r1}:{col_letter(c2)}{last_row}"
                t.set("ref", nref)
                af = t.find(q("autoFilter"))
                if af is not None:
                    af.set("ref", nref)
                changed[tp] = tt

        # minta Excel menghitung ulang semua rumus saat file dibuka (nilai tersimpan baris baru masih kosong)
        wbt = book.tree("xl/workbook.xml")
        cp = wbt.getroot().find(q("calcPr"))
        if cp is None:
            cp = etree.SubElement(wbt.getroot(), q("calcPr"))
        cp.set("fullCalcOnLoad", "1")
        changed["xl/workbook.xml"] = wbt

        fd, tmp = tempfile.mkstemp(prefix=".gcex-", suffix=p.suffix, dir=str(p.parent))
        os.close(fd)
        try:
            with zipfile.ZipFile(tmp, "w") as zo:
                for info in book.z.infolist():
                    if info.filename in changed:
                        data = etree.tostring(changed[info.filename], xml_declaration=True, encoding="UTF-8", standalone=True)
                        zo.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
                    else:
                        zo.writestr(info, book.z.read(info.filename))
            book.z.close()
            if backup:
                bdir = p.parent / "_backup_gcex"
                bdir.mkdir(exist_ok=True)
                bak = bdir / f"{p.stem}_{datetime.now():%Y%m%d-%H%M%S}{p.suffix}"
                shutil.copy2(p, bak)
                result["backup"] = str(bak)
                olds = sorted(bdir.glob(f"{p.stem}_*{p.suffix}"))
                for o in olds[:-30]:  # simpan 30 cadangan terakhir
                    try:
                        o.unlink()
                    except OSError:
                        pass
            check_unlocked(p)
            _replace_retry(tmp, p)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        result["first_row"] = min(x["row"] for x in plan)
        result["last_row"] = last_row
        return result
    finally:
        try:
            book.z.close()
        except Exception:
            pass
