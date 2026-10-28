"""Ubah panduan Markdown sederhana menjadi satu file HTML mandiri (offline) untuk dibundel di installer.
Mendukung: judul #-####, paragraf, daftar - / 1., tabel |, blok kode ```, `kode`, **tebal**, [tautan](url).

Pemakaian: python docs/md2html.py docs/PANDUAN_CORE.md docs/PANDUAN_CORE.html
"""
import html
import re
import sys

CSS = """body{font:15px/1.55 "Segoe UI",system-ui,sans-serif;color:#141a26;background:#ecebe6;margin:0}
main{max-width:920px;margin:0 auto;padding:28px 34px 60px;background:#f6f5f1;min-height:100vh}
h1,h2,h3{font-family:Georgia,'Times New Roman',serif;color:#141a26}h1{border-bottom:1.5px solid #141a26;padding-bottom:8px}h2{margin-top:30px;color:#2a5ea8}h3{margin-top:22px}
table{border-collapse:collapse;margin:10px 0;width:100%}th,td{border:1px solid #c6c4bd;padding:6px 9px;text-align:left;vertical-align:top}
th{background:#141a26;color:#f6f5f1}code{background:#e4e3dd;border-radius:4px;padding:1px 5px;font-family:Consolas,monospace;font-size:13px}
pre{background:#141a26;color:#f6f5f1;padding:10px 14px;border-radius:6px;overflow:auto}pre code{background:none;color:inherit}a{color:#2a5ea8}"""


def inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t


def convert(md: str) -> str:
    out, lines, i = [], md.splitlines(), 0
    title = "Panduan"
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s.startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i].strip())
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
        elif re.match(r"^#{1,4} ", s):
            n = len(s) - len(s.lstrip("#"))
            if n == 1:
                title = s[2:]
            out.append(f"<h{n}>{inline(s[n + 1:])}</h{n}>")
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            i -= 1
            h = "<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr>"
            for r in rows[2:]:
                h += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
            out.append(h + "</table>")
        elif re.match(r"^(-|\d+\.) ", s):
            tag = "ol" if s[0].isdigit() else "ul"
            items = []
            while i < len(lines) and (re.match(r"^(-|\d+\.) ", lines[i].strip()) or (lines[i].startswith("   ") and lines[i].strip())):
                t = lines[i].strip()
                if re.match(r"^(-|\d+\.) ", t) and not lines[i].startswith("   "):
                    items.append([re.sub(r"^(-|\d+\.) ", "", t)])
                elif t.startswith("```"):  # blok kode di dalam butir
                    buf = []
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith("```"):
                        buf.append(lines[i].strip())
                        i += 1
                    items[-1].append("\0<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
                else:
                    items[-1].append(("\0<br>" if re.match(r"^(-|\d+\.) ", t) else "") + re.sub(r"^- ", "• ", t))
                i += 1
                while i < len(lines) and not lines[i].strip() and i + 1 < len(lines) and lines[i + 1].startswith("   "):
                    i += 1
            i -= 1
            li = "".join("<li>" + " ".join(x[1:] if x.startswith("\0") else inline(x) for x in it) + "</li>" for it in items)
            out.append(f"<{tag}>{li}</{tag}>")
        elif s:
            buf = [s]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|\||```|-|\d+\.) ?", lines[i + 1].strip()):
                i += 1
                buf.append(lines[i].strip())
            out.append("<p>" + inline(" ".join(buf)) + "</p>")
        i += 1
    return (f'<!DOCTYPE html><html lang="id"><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f"<style>{CSS}</style></head><body><main>" + "\n".join(out) + "</main></body></html>")


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        h = convert(f.read())
    with open(dst, "w", encoding="utf-8") as f:
        f.write(h)
    print("OK", dst, len(h), "byte")
