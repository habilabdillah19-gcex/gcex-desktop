"""Tema Core-Ex: palet editorial (kertas abu muda, pita navy, biru baja, judul biru tua) + font Inter / JetBrains Mono (OFL, dibundel)."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

LIGHT = dict(bg="#f2f2f0", pn="#ffffff", pn2="#eef0f3", bd="#d6d9de", bd2="#a9b0ba", ink="#232f45", tx="#2b2b2b", mu="#5d6773",
             hd="#1f4e8c", nv="#232f45", sb="#4a7499", ac="#4a7499", ac2="#1f4e8c", acs="#e3ebf3", ai="#e6eef6", sel="#d8e4f0",
             er="#a23b2a", ers="#f4e1dd", mk="#b4462f", half="#d08a1e", viewer="#0d1016")
DARK = dict(bg="#141a24", pn="#1b2331", pn2="#232f45", bd="#33405a", bd2="#4c5b78", ink="#e9edf3", tx="#e3e7ee", mu="#9aa4b2",
            hd="#a9c3dd", nv="#0f1520", sb="#4a7499", ac="#7fa4c7", ac2="#a9c3dd", acs="#26364f", ai="#22324a", sel="#2c4364",
            er="#e09a8c", ers="#3a2320", mk="#e07a62", half="#e0a24a", viewer="#0b0e14")
C = dict(LIGHT)  # palet aktif (dibaca widget saat menggambar)
SANS, MONO = "Inter", "JetBrains Mono"


def fonts_dir() -> Path:
    here = Path(__file__).resolve()
    for c in (Path(getattr(sys, "_MEIPASS", "")) / "fonts", here.parent / "fonts", here.parents[2] / "app-core" / "fonts"):
        if (c / "Inter-Variable.ttf").exists():
            return c
    return here.parent / "fonts"


def load_fonts() -> None:
    global SANS, MONO
    fams = {}
    for f in sorted(fonts_dir().glob("*.ttf")):
        i = QFontDatabase.addApplicationFont(str(f))
        if i >= 0:
            for fam in QFontDatabase.applicationFontFamilies(i):
                fams[fam.lower()] = fam
    SANS = next((v for k, v in fams.items() if k.startswith("inter")), "Segoe UI")
    MONO = next((v for k, v in fams.items() if k.startswith("jetbrains")), "Consolas")


def mono(size: float = 9.5, bold: bool = False) -> QFont:
    f = QFont(MONO)
    f.setPointSizeF(size)
    f.setBold(bold)
    return f


def qss(c: dict) -> str:
    return f"""
* {{ font-family: "{SANS}"; font-size: 9.75pt; color: {c['tx']}; }}
QMainWindow, QDialog, #central {{ background: {c['bg']}; }}
QToolTip {{ background: {c['ink']}; color: {c['pn']}; border: 0; padding: 4px 7px; }}
#top {{ background: {c['pn']}; border-bottom: 3px solid {c['nv']}; }}
#kick {{ font-size: 7.8pt; font-weight: 600; letter-spacing: 2px; color: {c['mu']}; }}
#brand {{ font-size: 17pt; font-weight: 800; color: {c['ink']}; }}
#prj {{ font-size: 8.3pt; color: {c['mu']}; }}
#fbar {{ background: {c['bg']}; border-bottom: 1px solid {c['bd']}; }}
#fbar QLabel {{ font-size: 7.8pt; letter-spacing: 2px; color: {c['mu']}; }}
QPushButton, QToolButton {{ background: {c['pn']}; color: {c['ink']}; border: 1px solid {c['ink']}; border-radius: 4px; padding: 5px 11px; font-weight: 500; }}
QPushButton:hover, QToolButton:hover {{ background: {c['acs']}; border-color: {c['ac2']}; }}
QPushButton:disabled, QToolButton:disabled {{ color: {c['bd2']}; border-color: {c['bd2']}; }}
QPushButton[pri="true"] {{ background: {c['ink']}; color: {c['pn']}; font-weight: 700; }}
QPushButton[pri="true"]:hover {{ background: {c['ac2']}; border-color: {c['ac2']}; }}
QPushButton[ok="true"] {{ background: {c['ac']}; border-color: {c['ac']}; color: #ffffff; font-weight: 700; }}
QPushButton[sm="true"] {{ padding: 2px 8px; font-size: 8.6pt; }}
QPushButton:checked {{ background: {c['ink']}; color: {c['pn']}; border-color: {c['ink']}; font-weight: 700; }}
QPushButton#pill {{ border-radius: 12px; border-color: {c['bd2']}; padding: 4px 11px; }}
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QPlainTextEdit, QTextEdit {{ background: {c['pn']}; border: 1px solid {c['bd2']}; border-radius: 4px; padding: 3px 6px; selection-background-color: {c['ac']}; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {c['ac']}; }}
QComboBox QAbstractItemView {{ background: {c['pn']}; selection-background-color: {c['sel']}; selection-color: {c['ink']}; }}
QTableView {{ background: {c['pn']}; alternate-background-color: {c['bg']}; gridline-color: {c['bd']}; border: 1px solid {c['bd']};
              selection-background-color: {c['sel']}; selection-color: {c['ink']}; }}
QHeaderView::section {{ background: {c['pn2']}; color: {c['ink']}; border: 0; border-right: 1px solid {c['bd']}; border-bottom: 1px solid {c['bd2']};
                        padding: 4px 6px; font-weight: 700; font-size: 8.4pt; }}
QSplitter::handle {{ background: {c['bd']}; }}
QSplitter::handle:hover {{ background: {c['ac']}; }}
QStatusBar {{ background: {c['pn']}; border-top: 1px solid {c['bd']}; color: {c['mu']}; }}
QStatusBar QLabel {{ color: {c['mu']}; }}
#wmark {{ color: {c['mu']}; font-weight: 600; font-size: 8.2pt; padding: 0 8px; }}
QProgressBar {{ border: 1px solid {c['bd2']}; border-radius: 3px; background: {c['pn2']}; height: 10px; text-align: center; font-size: 7pt; }}
QProgressBar::chunk {{ background: {c['ac']}; }}
QScrollArea, #card {{ background: {c['pn']}; border: 0; }}
#cardTitle {{ font-size: 14pt; font-weight: 800; color: {c['ink']}; }}
#sect {{ font-size: 11pt; font-weight: 800; color: {c['hd']}; border-bottom: 2px solid {c['nv']}; padding-bottom: 1px; margin-top: 6px; }}
QFrame#fld {{ background: {c['pn']}; border: 1px solid {c['bd']}; border-radius: 6px; }}
QFrame#fld[ai="true"] {{ background: {c['ai']}; border-color: #b7c9e6; }}
QFrame#fld[lg="true"] {{ border-color: {c['ink']}; }}
QFrame#fld QLabel#fl {{ font-size: 7.4pt; letter-spacing: 2px; color: {c['mu']}; }}
QFrame#fld QLineEdit, QFrame#fld QPlainTextEdit {{ border: 0; background: transparent; font-weight: 700; padding: 0; }}
QLabel#tag {{ font-size: 7pt; border-radius: 3px; padding: 0 5px; }}
QLabel#tag[k="ai"] {{ background: {c['ac']}; color: #ffffff; }}
QLabel#tag[k="ed"] {{ border: 1px solid {c['ink']}; color: {c['ink']}; }}
QLabel#tag[k="fn"] {{ background: {c['pn2']}; color: {c['ink']}; border: 1px dashed {c['bd2']}; }}
QLabel#tag[k="lgt"] {{ background: {c['ink']}; color: {c['pn']}; }}
QLabel#tag[k="mk"] {{ background: {c['mk']}; color: #ffffff; }}
#note {{ color: {c['mu']}; font-size: 8.6pt; }}
#err {{ color: {c['er']}; }}
QLabel#box {{ background: {c['pn2']}; border: 1px solid {c['bd']}; border-left: 4px solid {c['sb']}; border-radius: 4px; padding: 8px 10px; }}
QLabel#box[k="er"] {{ border-left-color: {c['er']}; background: {c['ers']}; }}
QLabel#box[k="ok"] {{ border-left-color: {c['ac2']}; }}
#dlgHead {{ background: {c['nv']}; border-left: 12px solid {c['sb']}; }}
#dlgHead QLabel {{ color: #ffffff; font-size: 12.5pt; font-weight: 800; }}
#vtools QToolButton {{ background: rgba(246,245,241,0.94); color: #141a26; border: 1px solid #141a26; border-radius: 4px; padding: 2px 6px;
                       min-width: 18px; font-family: "{MONO}"; font-size: 10pt; font-weight: 700; }}
#vtools QToolButton:hover {{ background: #dbe5f3; }}
#vtools QToolButton:checked {{ background: #dbe5f3; }}
#qres {{ background: {c['pn']}; border: 1px solid {c['bd2']}; }}
#start {{ background: {c['bg']}; }}
#startCard {{ background: {c['pn']}; border: 1px solid {c['bd']}; border-top: 4px solid {c['nv']}; }}
#startH {{ font-size: 19pt; font-weight: 800; color: {c['ink']}; }}
"""


def apply(app: QApplication, dark: bool = False) -> None:
    C.clear()
    C.update(DARK if dark else LIGHT)
    pal = app.palette()
    for role, key in ((QPalette.Window, "bg"), (QPalette.Base, "pn"), (QPalette.AlternateBase, "bg"), (QPalette.Text, "tx"),
                      (QPalette.WindowText, "tx"), (QPalette.Button, "pn"), (QPalette.ButtonText, "ink"), (QPalette.Highlight, "ac"),
                      (QPalette.HighlightedText, "pn"), (QPalette.ToolTipBase, "ink"), (QPalette.ToolTipText, "pn"), (QPalette.PlaceholderText, "mu")):
        pal.setColor(role, QColor(C[key]))
    app.setPalette(pal)
    app.setStyleSheet(qss(C))


def repolish(w) -> None:
    w.style().unpolish(w)
    w.style().polish(w)
