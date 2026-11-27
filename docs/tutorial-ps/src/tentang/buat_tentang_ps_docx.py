"""Versi Word (.docx) dari 'Tentang Pit Studio for Desktop'. Isinya SATU SUMBER dengan PDF: bagian isi buat_tentang_ps.py
dijalankan dengan pembantu perekam (P, L, fig, tbl, QA, kartu), lalu ditulis dengan python-docx.
Pemakaian: python buat_tentang_ps_docx.py <folder gambar> <berkas DOCX keluaran>"""
import sys, os, re, html
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

IMG, OUT = sys.argv[1], sys.argv[2]
SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "buat_tentang_ps.py"), encoding="utf-8").read()
VER, TGL = re.search(r'VER, TGL = "([^"]+)", "([^"]+)"', SRC).groups()
mm = 72 / 25.4
W = 595.2756 - 36 * mm                       # lebar isi (pt), sama dengan PDF
NV, GD, AC, MU = "1C2733", "B5893E", "2B5F9E", "6B7280"

# ---- perekam ----
def P(t, st="b"): return ("p", t, st)
def L(items, st="li"): return [("li", t) for t in items]
def fig(n, w=W, cap=None):
    out = [("img", os.path.join(IMG, n), w / W)]
    if cap: out.append(("p", cap, "cap"))
    return out
def tbl(rows, cw, head=True, zebra=True, fs=None): return ("tbl", rows, list(cw), head)
def QA(q, a, tip=None): return ("qa", q, a, tip)
def kartu(items, cols=3): return ("kartu", list(items), cols)
def Spacer(*a): return ("nop",)
def PageBreak(): return ("pb",)
def CondPageBreak(*a): return ("nop",)
def NextPageTemplate(*a): return ("nop",)

i0 = SRC.index('E = [NextPageTemplate("isi"), PageBreak()]'); i1 = SRC.index("doc.build(E)")
ns = dict(P=P, L=L, fig=fig, tbl=tbl, QA=QA, kartu=kartu, Spacer=Spacer, PageBreak=PageBreak, CondPageBreak=CondPageBreak,
          NextPageTemplate=NextPageTemplate, mm=mm, W=W, VER=VER, TGL=TGL)
exec(SRC[i0:i1], ns)
def flat(x):
    for e in x:
        if isinstance(e, list): yield from flat(e)
        else: yield e
E = [e for e in flat(ns["E"]) if e and e[0] != "nop"]

# ---- penulis ----
d = Document()
sec = d.sections[0]; sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.left_margin = sec.right_margin = Mm(18); sec.top_margin = sec.bottom_margin = Mm(20)
FONT = "Calibri"
def stfont(st, sz, bold=False, col=NV, before=0, after=5, keep=False):
    st.font.name = FONT; st.font.size = Pt(sz); st.font.bold = bold; st.font.color.rgb = RGBColor.from_string(col)
    rp = st.element.get_or_add_rPr(); rf = rp.find(qn("w:rFonts"))
    if rf is None: rf = OxmlElement("w:rFonts"); rp.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): rf.set(qn(a), FONT)
    st.paragraph_format.space_before = Pt(before); st.paragraph_format.space_after = Pt(after); st.paragraph_format.keep_with_next = keep
stfont(d.styles["Normal"], 10.5)
stfont(d.styles["Heading 1"], 18, True, NV, 4, 6, True)
stfont(d.styles["Heading 2"], 12.5, True, AC, 10, 4, True)
stfont(d.styles["List Bullet"], 10.5, after=2)

TOK = re.compile(r"(<br\s*/?>|</?b>|</?i>|<font[^>]*>|</font>|<super>|</super>|<sub>|</sub>)", re.I)
def runs(par, t, size=None, color=None, bold=None, italic=None):
    b = i = 0; col = [color]
    for tok in TOK.split(t):
        if not tok: continue
        lo = tok.lower()
        if lo.startswith("<br"): par.add_run().add_break(); continue
        if lo == "<b>": b += 1; continue
        if lo == "</b>": b = max(0, b - 1); continue
        if lo == "<i>": i += 1; continue
        if lo == "</i>": i = max(0, i - 1); continue
        if lo.startswith("<font"):
            m = re.search(r'color="?#?([0-9a-fA-F]{6})', tok); col.append(m.group(1) if m else col[-1]); continue
        if lo == "</font>":
            if len(col) > 1: col.pop()
            continue
        if lo in ("<super>", "</super>", "<sub>", "</sub>"): continue
        r = par.add_run(html.unescape(tok)); r.bold = True if (b or bold) else None; r.italic = True if (i or italic) else None
        if size: r.font.size = Pt(size)
        if col[-1]: r.font.color.rgb = RGBColor.from_string(col[-1].upper())
def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcol); tcPr.append(sh)
def borders(table, col="D3CDC1"):
    tblPr = table._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for k in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + k); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), col); b.append(e)
    tblPr.append(b)
def widths(table, cw):
    tot = sum(cw); CW = Mm(210 - 36)
    table.autofit = False
    tblPr = table._tbl.tblPr; tw = tblPr.find(qn("w:tblW"))
    if tw is None: tw = OxmlElement("w:tblW"); tblPr.append(tw)
    tw.set(qn("w:type"), "dxa"); tw.set(qn("w:w"), str(int(CW / 635)))
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    for k, col in enumerate(table.columns): col.width = int(CW * cw[k] / tot)
    for r in table.rows:
        for k, c in enumerate(r.cells): c.width = int(CW * cw[k] / tot)
def celltext(cell, v, size=9.5, color=None, bold=None):
    p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(2)
    if isinstance(v, tuple) and v and v[0] == "p": v = v[1]
    runs(p, v if isinstance(v, str) else str(v), size=size, color=color, bold=bold)

# sampul
for _ in range(5): d.add_paragraph()
p = d.add_paragraph(); runs(p, "TENTANG", size=13, color=GD, bold=True)
p = d.add_paragraph(); runs(p, "Pit Studio for Desktop", size=34, bold=True)
p = d.add_paragraph(); runs(p, "Apa itu, bagaimana bekerja, apa yang ditawarkan, kelebihan, status legal — dan cara menjawab pertanyaan ahli IT / programmer dan investor teknologi.", size=13, color=MU)
for _ in range(8): d.add_paragraph()
p = d.add_paragraph(); runs(p, "VERSI DOKUMEN", size=9, color=GD, bold=True)
p = d.add_paragraph(); runs(p, f"Pit Studio {VER} (Windows 64-bit) · {TGL}<br/>Keluarga GC-Ex · Copyright © 2026 Habil Abdillah")
p = d.add_paragraph(); runs(p, "Tangkapan layar memakai data latihan fiktif. Bagian legal adalah ringkasan fakta, bukan nasihat hukum. Angka teknis diambil dari kode sumber dan hasil uji pada tanggal dokumen ini.", size=8.5, color=MU)

# kepala & kaki halaman
hp = sec.header.paragraphs[0]; runs(hp, f"Tentang Pit Studio for Desktop  ·  versi {VER} · {TGL}", size=8, color=MU)
fp = sec.footer.paragraphs[0]; runs(fp, "© 2026 Habil Abdillah · keluarga GC-Ex  ·  halaman ", size=8, color=MU)
r = fp.add_run(); r.font.size = Pt(8)
for typ, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if typ: e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), typ)
    else: e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt
    r._r.append(e)

pend_break = True      # isi dimulai di halaman baru
def para(style=None):
    global pend_break
    p = d.add_paragraph(style=style)
    if pend_break: p.paragraph_format.page_break_before = True; pend_break = False
    return p
for e in E:
    k = e[0]
    if k == "pb": pend_break = True; continue
    if k == "p":
        st = e[2]
        if st == "h1": runs(para("Heading 1"), e[1])
        elif st == "h2": runs(para("Heading 2"), e[1])
        elif st == "cap":
            p = para(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(9); runs(p, e[1], size=8.5, color=MU)
        elif st == "s": runs(para(), e[1], size=9, color=MU)
        elif st == "pitch": runs(para(), e[1], size=12)
        else: runs(para(), e[1])
    elif k == "li": runs(para("List Bullet"), e[1])
    elif k == "img":
        p = para(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(e[1], width=Mm((210 - 36) * min(1.0, e[2])))
    elif k == "qa":
        p = para(); p.paragraph_format.keep_with_next = True; p.paragraph_format.space_before = Pt(7); p.paragraph_format.space_after = Pt(2); runs(p, e[1], bold=True)
        t = d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; widths(t, [1]); c = t.rows[0].cells[0]; shade(c, "F7F5F0"); celltext(c, e[2], size=10.5)
        if e[3]: p = d.add_paragraph(); runs(p, "Catatan untuk Anda: " + e[3], size=9, color=MU, italic=True)
        else: d.add_paragraph().paragraph_format.space_after = Pt(0)
    elif k == "kartu":
        items, cols = e[1], e[2]; nr = (len(items) + cols - 1) // cols
        if pend_break: para().paragraph_format.space_after = Pt(0)
        t = d.add_table(rows=nr, cols=cols); borders(t); widths(t, [1] * cols)
        for n, (a, b) in enumerate(items):
            c = t.rows[n // cols].cells[n % cols]; shade(c, "F7F5F0"); celltext(c, a, size=8, color=GD, bold=True)
            p2 = c.add_paragraph(); p2.paragraph_format.space_after = Pt(3); runs(p2, b, size=11.5, bold=True)
        d.add_paragraph().paragraph_format.space_after = Pt(2)
    elif k == "tbl":
        rows, cw, head = e[1], e[2], e[3]
        if pend_break: para().paragraph_format.space_after = Pt(0)
        t = d.add_table(rows=len(rows), cols=len(cw)); borders(t); widths(t, cw)
        for i, r in enumerate(rows):
            for j, v in enumerate(r[:len(cw)]):
                c = t.rows[i].cells[j]
                if head and i == 0: shade(c, NV); celltext(c, v, color="FFFFFF", bold=True)
                else:
                    if i % 2 == 0: shade(c, "FBFAF7")
                    celltext(c, v)
        if head:
            trPr = t.rows[0]._tr.get_or_add_trPr(); h = OxmlElement("w:tblHeader"); h.set(qn("w:val"), "true"); trPr.append(h)
        d.add_paragraph().paragraph_format.space_after = Pt(2)
d.core_properties.title = "Tentang Pit Studio for Desktop"; d.core_properties.author = "Habil Abdillah"
d.save(OUT); print("DOCX:", OUT, len(E), "elemen")
