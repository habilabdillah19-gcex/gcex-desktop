"""Tulis berkas VERSIONINFO untuk PyInstaller (--version-file) agar .exe membawa identitas lengkap (nama produk, versi,
pembuat, hak cipta, nama berkas asli). Exe tanpa identitas ini lebih sering ditandai heuristik antivirus — DB-Ex 0.46.0
ditandai Microsoft Defender sebagai "Trojan:Win32/Bearfoos.A!ml" (deteksi pembelajaran mesin, bukan tanda tangan virus).

Pemakaian:  python tools/rilis/versi_exe.py <keluaran.txt> <versi x.y.z> <NamaExe tanpa .exe> "<deskripsi>"
"""
from __future__ import annotations

import re
import sys

PEMBUAT = "Habil Abdillah"
HAK_CIPTA = "Copyright (c) 2026 Habil Abdillah"


def tulis(out: str, versi: str, nama: str, deskripsi: str) -> str:
    angka = [int(x) for x in re.findall(r"\d+", versi)[:3]]
    angka = (angka + [0, 0, 0])[:3] + [0]
    t = tuple(angka)

    def s(k: str, v: str) -> str:
        return f"StringStruct({k!r}, {v!r})"
    isi = f"""# dibuat oleh tools/rilis/versi_exe.py
VSVersionInfo(
  ffi=FixedFileInfo(filevers={t}, prodvers={t}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      {s('CompanyName', PEMBUAT)},
      {s('FileDescription', deskripsi)},
      {s('FileVersion', versi)},
      {s('InternalName', nama)},
      {s('LegalCopyright', HAK_CIPTA)},
      {s('OriginalFilename', nama + '.exe')},
      {s('ProductName', nama)},
      {s('ProductVersion', versi)}])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(isi)
    return isi


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    print(tulis(*sys.argv[1:5]))
