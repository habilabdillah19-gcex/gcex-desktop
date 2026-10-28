"""Tanda hak cipta GC-Ex pada file yang dihasilkan aplikasi (Excel)."""
COPYRIGHT = "Copyright © Habil Abdillah 2026"
NOTICE = ("Dibuat dengan GC-Ex. " + COPYRIGHT + ". Hasil adalah alat bantu dan wajib diperiksa orang yang kompeten; "
          "nilai geoteknik dari AI adalah perkiraan visual, bukan pengukuran.")


def mark_workbook(wb, app: str = "GC-Ex") -> None:
    """Footer cetak di setiap sheet + properti file (Pembuat / Judul / Keterangan). Data pengguna tidak diubah."""
    wb.properties.creator = app
    wb.properties.lastModifiedBy = app
    wb.properties.description = NOTICE
    wb.properties.keywords = "GC-Ex; " + COPYRIGHT
    for ws in wb.worksheets:
        for hf in (ws.oddFooter, ws.evenFooter, ws.firstFooter):
            hf.right.text = COPYRIGHT
            hf.right.size = 8
            hf.left.text = app + " · &D"
            hf.left.size = 8
