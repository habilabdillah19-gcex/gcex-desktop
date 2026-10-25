"""Jalankan uji backend di GitHub Actions; baris galat ditulis sebagai anotasi (::error::)
agar penyebab kegagalan terbaca di ringkasan run tanpa membuka log lengkap."""
import subprocess
import sys

p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rf", "--tb=short", "backend/tests"],
                   capture_output=True, text=True)
out = p.stdout + p.stderr
print(out)
if p.returncode != 0:
    keep = [l for l in out.splitlines() if l.startswith(("FAILED", "ERROR", "E ")) or "Error" in l][:40]
    for l in keep:
        print("::error::" + l.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
sys.exit(p.returncode)
