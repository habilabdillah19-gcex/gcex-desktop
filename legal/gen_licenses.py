"""Kumpulkan teks lisensi Python + semua paket Python yang ikut dibundel di backend GC-Ex.
Dijalankan di CI (Windows) sesudah `pip install -r backend/requirements.txt pyinstaller`, di environment yang
sama dengan PyInstaller, sehingga daftar & versinya persis sama dengan isi installer.

Pemakaian: python legal/gen_licenses.py legal/LISENSI_PYTHON.txt
"""
import importlib.metadata as md
import os
import re
import sys

# alat uji / build yang tidak ikut di dalam aplikasi
SKIP = {'pip', 'setuptools', 'wheel', 'pytest', 'pluggy', 'iniconfig', 'packaging', 'httpx', 'httpcore', 'certifi',
        'altgraph', 'pefile', 'pywin32-ctypes', 'pyinstaller-hooks-contrib', 'pip-licenses', 'prettytable', 'wcwidth',
        'tomli', 'exceptiongroup', 'colorama-test'}
LIC_RE = re.compile(r'(^|/)(LICEN[CS]E|COPYING|NOTICE|AUTHORS)[^/]*$', re.I)


def lic_name(d):
    m = d.metadata
    e = m.get('License-Expression')
    if e:
        return e
    cls = [c.split('::')[-1].strip() for c in (m.get_all('Classifier') or []) if c.startswith('License ::')]
    if cls:
        return '; '.join(cls)
    l = (m.get('License') or '').strip()
    return l.splitlines()[0][:100] if l else 'lihat teks di bawah'


def texts(d):
    out = []
    for f in (d.files or []):
        if LIC_RE.search(str(f).replace('\\', '/')):
            try:
                t = f.locate().read_text(encoding='utf-8', errors='replace').strip()
            except Exception:
                continue
            if t:
                out.append((str(f).replace('\\', '/'), t))
    if not out:
        l = (d.metadata.get('License') or '').strip()
        if len(l) > 100:
            out.append(('metadata License', l))
    return out


def main(path):
    W = []
    W.append('GC-Ex — LISENSI PYTHON & PAKET PYTHON BACKEND / PYTHON AND BACKEND PACKAGE LICENSES')
    W.append('=' * 78)
    W.append('Dibuat otomatis saat build oleh legal/gen_licenses.py. Python %s.' % sys.version.split()[0])
    W.append('')
    # ---- Python (PSF License) ----
    for cand in [os.path.join(sys.base_prefix, 'LICENSE.txt'), os.path.join(sys.base_prefix, 'LICENSE'),
                 os.path.join(sys.base_prefix, 'lib', 'python%d.%d' % sys.version_info[:2], 'LICENSE.txt')]:
        if os.path.exists(cand):
            W.append('-' * 78)
            W.append('Python %s — Python Software Foundation License' % sys.version.split()[0])
            W.append('-' * 78)
            W.append(open(cand, encoding='utf-8', errors='replace').read().strip())
            W.append('')
            break
    else:
        W.append('Python %s — Python Software Foundation License (https://docs.python.org/3/license.html)' % sys.version.split()[0])
        W.append('')
    seen = {}
    for d in md.distributions():
        n = (d.metadata.get('Name') or '').strip()
        if n and n.lower() not in seen:
            seen[n.lower()] = d
    rows = []
    for k in sorted(seen):
        if k in SKIP:
            continue
        d = seen[k]
        rows.append((d.metadata['Name'], d.version, lic_name(d), texts(d)))
    W.append('DAFTAR PAKET / PACKAGE LIST')
    W.append('-' * 78)
    for n, v, l, _ in rows:
        W.append('  %-28s %-12s %s' % (n, v, l))
    W.append('')
    for n, v, l, T in rows:
        W.append('=' * 78)
        W.append('%s %s — %s' % (n, v, l))
        W.append('=' * 78)
        if not T:
            W.append('(teks lisensi tidak disertakan di paket; lihat halaman proyek paket ini)')
        for f, t in T:
            W.append('[%s]' % f)
            W.append(t)
            W.append('')
        W.append('')
    open(path, 'w', encoding='utf-8', newline='\r\n').write('\n'.join(W) + '\n')
    print('lisensi Python: %d paket -> %s' % (len(rows), path))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'LISENSI_PYTHON.txt')
