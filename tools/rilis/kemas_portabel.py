# -*- coding: utf-8 -*-
"""Paket GC-Ex PORTABEL (.html tanpa instal) — Block Model + Drillhole dalam satu ZIP.

Pemilik 26 Nov 2026: laptop kantor tidak boleh menginstal program (perlu hak admin), jadi GC-Ex dipakai sebagai file
.html yang dibuka di Microsoft Edge / Google Chrome, dengan folder proyek di drive D. Isi index.html sama persis dengan
yang ada di dalam installer; yang tidak tersedia hanya fitur yang butuh backend Python (lihat PETUNJUK_PORTABEL.txt).
Diuji: tools/uji/uji_portabel_html.py.

Pakai: python tools/rilis/kemas_portabel.py [folder_keluaran]   -> GC-Ex-Portabel_BM<v>_DH<v>.zip
"""
import json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def ver(f):
    d = json.load(open(ROOT / f, encoding='utf-8'))
    return (d.get('extraMetadata') or {}).get('version') or d.get('version')


def petunjuk(vbm, vdh):
    return f"""GC-Ex PORTABEL (tanpa instal) - Block Model {vbm} & Drillhole {vdh}
=====================================================================

Isi folder ini:
  GCEx_BlockModel.html   GC-Ex Block Model {vbm}
  GCEx_DrillHole.html    GC-Ex Drillhole {vdh}
  Proyek\\               tempat folder-folder proyek Anda (satu subfolder = satu proyek)
  Legal\\                syarat penggunaan & lisensi

Tidak ada yang diinstal dan tidak perlu hak administrator. Aplikasinya sama dengan yang ada di installer.


1. PASANG (sekali)
------------------
- Ekstrak ZIP ini ke drive D, misalnya:  D:\\GC-Ex\\
- Buka file .html dengan Microsoft Edge atau Google Chrome
  (klik kanan file -> Buka dengan -> Microsoft Edge). Boleh buat pintasan di Desktop.
- JANGAN pakai Firefox: Firefox tidak punya pemilih folder, jadi proyek tidak bisa disimpan ke folder.


2. MEMBUKA PROYEK LAMA DARI APLIKASI DESKTOP (laptop pribadi)
-------------------------------------------------------------
Format folder proyek desktop dan .html SAMA (kode penyimpanannya sama).
a. Di laptop pribadi, TUTUP dulu aplikasi GC-Ex (supaya kunci pemakai "gcex.lock" dilepas).
b. Salin SELURUH folder proyek (yang berisi gcex_project.json, gcex_data.json, sumber\\, backup\\, ...)
   ke  D:\\GC-Ex\\Proyek\\<nama proyek>\\  di laptop kantor.
   Folder "sumber\\" penting: di situ salinan file block model (.mdl / .csv) atau data bor yang dibaca ulang.
c. Buka GCEx_BlockModel.html (atau GCEx_DrillHole.html untuk proyek Drillhole).
d. Menu Proyek -> "Buka / pilih folder proyek" -> pilih folder proyek tadi -> klik "Lihat file" / "Izinkan"
   lalu "Simpan perubahan" / "Edit file" bila browser menanyakan izin edit.
e. Proyek terbuka dan setiap perubahan otomatis disimpan kembali ke folder itu (ditambah backup berversi).

Bila muncul pesan "Proyek sedang dipakai ... beralih ke hanya-baca": kunci dari laptop lain belum dilepas.
Tunggu 3 menit (kunci kedaluwarsa sendiri) lalu buka folder lagi, atau hapus file gcex.lock di folder proyek
bila Anda yakin aplikasi di laptop lain sudah ditutup.


3. PROYEK BARU
--------------
Buat subfolder kosong di D:\\GC-Ex\\Proyek\\ (mis. D:\\GC-Ex\\Proyek\\Z4_Nov2026\\), import data seperti biasa,
lalu Menu Proyek -> "Buka / pilih folder proyek" -> pilih subfolder itu. Proyek dibuat dan disimpan di sana.


4. SETIAP KALI MEMBUKA LAGI
---------------------------
Browser bisa meminta izin folder lagi setelah ditutup: klik "Hubungkan lagi" di menu Proyek lalu "Izinkan".
Selama belum terhubung, pekerjaan tetap tersimpan di browser dan disalin ke folder begitu terhubung lagi.
Jangan membuka proyek yang sama di dua tab / dua browser sekaligus.


5. YANG BERBEDA DARI APLIKASI TERPASANG
---------------------------------------
Tidak tersedia (butuh backend Python dari installer):
- Menulis register langsung ke workbook Excel yang sudah ada dan ke MS Access
  -> pakai export CSV / Excel lalu tempel ke register.
- Pembacaan .mdl besar lewat backend (cache kolom di disk). File .mdl tetap bisa dibuka, dibaca langsung oleh
  browser: lebih lambat untuk file sangat besar dan dibatasi memori laptop (pakai filter RL / pit saat import).
- Tombol data latihan otomatis (data latihan bisa di-import manual dari ZIP Data Latihan di Release).
- gcex_proyek.db (riwayat SQLite) tidak diperbarui oleh versi .html; berkasnya dibiarkan utuh.
Berbeda:
- Export (STR, DXF, PDF, CSV, MDL) memakai dialog Simpan / folder Download browser, dan salinannya ikut
  tersimpan di folder proyek\\export\\<tanggal>\\ seperti biasa.
- Lisensi per komputer hanya ada di aplikasi terpasang.

Bila kebijakan browser kantor memblokir akses folder (menu "Buka / pilih folder proyek" gagal), GC-Ex tetap
jalan dan menyimpan pekerjaan di browser; lakukan export secara berkala.

Copyright (c) Habil Abdillah 2026. Lihat Legal\\SYARAT_PENGGUNAAN.txt.
"""


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'dist-portabel'
    out.mkdir(parents=True, exist_ok=True)
    vbm, vdh = ver('package.json'), ver('builder-dh.json')
    z = out / f'GC-Ex-Portabel_BM{vbm}_DH{vdh}.zip'
    base = 'GC-Ex'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as Z:
        Z.write(ROOT / 'app' / 'index.html', f'{base}/GCEx_BlockModel.html')
        Z.write(ROOT / 'app-dh' / 'index.html', f'{base}/GCEx_DrillHole.html')
        Z.writestr(f'{base}/PETUNJUK_PORTABEL.txt', petunjuk(vbm, vdh).replace('\n', '\r\n'))
        Z.writestr(f'{base}/Proyek/BACA_SAYA.txt', ('Letakkan setiap folder proyek GC-Ex di sini (satu subfolder = satu proyek).\r\n'
                                                    'Lihat ..\\PETUNJUK_PORTABEL.txt.\r\n'))
        for p in sorted((ROOT / 'legal').rglob('*')):
            if p.is_file():
                Z.write(p, f'{base}/Legal/' + str(p.relative_to(ROOT / 'legal')).replace('\\', '/'))
    print('OK', z, z.stat().st_size, 'byte')
    return z


if __name__ == '__main__':
    main()
