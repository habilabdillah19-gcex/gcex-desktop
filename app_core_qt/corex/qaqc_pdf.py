"""Laporan QAQC -> PDF (A4) dengan QTextDocument + QPdfWriter: HTML dari backend core_qaqc.report, grafik PNG sebagai resource,
nomor halaman & judul di kaki halaman."""
from __future__ import annotations

import base64

from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter, QTextDocument


def write_pdf(rep: dict, path: str, footer: str = "") -> int:
    """Tulis laporan ke PDF; kembalikan jumlah halaman."""
    pw = QPdfWriter(path)
    pw.setPageLayout(QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait, QMarginsF(16, 15, 16, 18), QPageLayout.Millimeter))
    pw.setResolution(144)
    pw.setTitle(rep.get("title") or "Laporan QAQC")
    pw.setCreator("DB-Ex")
    doc = QTextDocument()
    doc.setDocumentMargin(0)
    f = QFont("Segoe UI")
    f.setPointSizeF(9.5)
    doc.setDefaultFont(f)
    for name, b64 in (rep.get("images") or {}).items():
        im = QImage.fromData(base64.b64decode(b64), "PNG")
        doc.addResource(QTextDocument.ImageResource, QUrl("img:" + name), im)
    doc.setHtml(rep["html"])
    p = QPainter(pw)
    page = pw.pageLayout().paintRectPixels(pw.resolution())
    w, h = page.width(), page.height()
    foot_h = int(pw.resolution() * 0.35)
    body_h = h - foot_h
    # 1 px dokumen = 1 px perangkat; skala lebar teks ke lebar halaman
    scale = w / 700.0
    doc.setPageSize(QSizeF(700.0, body_h / scale))
    n = doc.pageCount()
    ff = QFont("Segoe UI")
    ff.setPointSizeF(7.5)
    for i in range(n):
        if i:
            pw.newPage()
        p.save()
        p.scale(scale, scale)
        p.translate(0, -i * body_h / scale)
        clip = QRectF(0, i * body_h / scale, 700.0, body_h / scale)
        doc.drawContents(p, clip)
        p.restore()
        p.setFont(ff)
        p.setPen(QColor("#5d6773"))
        p.drawLine(0, body_h + foot_h // 3, w, body_h + foot_h // 3)
        r = QRectF(0, body_h + foot_h // 3 + 4, w, foot_h)
        p.drawText(r, Qt.AlignLeft | Qt.AlignTop, footer or rep.get("title") or "")
        p.drawText(r, Qt.AlignRight | Qt.AlignTop, f"{i + 1} / {n}")
    p.end()
    return n
