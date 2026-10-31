"""Lisensi GC-Ex (port Python dari electron/license.js, format & file sama -> lisensi lama tetap berlaku).

- ID Komputer = SHA-256('GC-Ex|guid:<MachineGuid>') (cadangan: nama komputer + CPU + MAC), base32 16 karakter XXXX-XXXX-XXXX-XXXX.
- Kunci = "GCEX1.<payload base64url>.<tanda tangan Ed25519 base64url>". Aplikasi hanya memegang kunci publik.
- File bersama ketiga aplikasi: %APPDATA%\\GC-Ex Lisensi\\lisensi.json  {key, at, last}.
Verifikasi Ed25519 ditulis di sini (RFC 8032, hanya verify) supaya tidak menambah dependensi.
"""
from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import json
import os
import platform
import re
import subprocess
import uuid
from pathlib import Path
from typing import Optional

PUBKEY_B64 = "MCowBQYDK2VwAyEA9r0X96ABXcPSrjl0edVsTn836jFZxwBDmFvX4aie0ug="  # SPKI DER, sama dengan license.js
APPS = {"bm": "GC-Ex Block Model", "dh": "GC-Ex Drillhole", "core": "DB-Ex"}
B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# ---------------------------------------------------------------- Ed25519 verify (RFC 8032)
_p = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _p - 2, _p) % _p
_I = pow(2, (_p - 1) // 4, _p)


def _inv(x: int) -> int:
    return pow(x, _p - 2, _p)


def _xrecover(y: int, sign: int) -> Optional[int]:
    xx = (y * y - 1) * _inv(_d * y * y + 1) % _p
    x = pow(xx, (_p + 3) // 8, _p)
    if (x * x - xx) % _p != 0:
        x = x * _I % _p
    if (x * x - xx) % _p != 0:
        return None
    if x & 1 != sign:
        x = _p - x
    if x == 0 and sign:
        return None
    return x


def _add(P, Q):
    (X1, Y1, Z1, T1), (X2, Y2, Z2, T2) = P, Q
    A = (Y1 - X1) * (Y2 - X2) % _p
    B = (Y1 + X1) * (Y2 + X2) % _p
    C = 2 * T1 * T2 * _d % _p
    D = 2 * Z1 * Z2 % _p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _p, G * H % _p, F * G % _p, E * H % _p)


def _mul(s: int, P):
    Q = (0, 1, 1, 0)
    while s:
        if s & 1:
            Q = _add(Q, P)
        P = _add(P, P)
        s >>= 1
    return Q


def _eq(P, Q) -> bool:
    return (P[0] * Q[2] - Q[0] * P[2]) % _p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % _p == 0


def _decode(b: bytes):
    if len(b) != 32:
        return None
    y = int.from_bytes(b, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    if y >= _p:
        return None
    x = _xrecover(y, sign)
    return None if x is None else (x, y, 1, x * y % _p)


_By = 4 * _inv(5) % _p
_B = (_xrecover(_By, 0), _By, 1, _xrecover(_By, 0) * _By % _p)


def ed25519_verify(pub: bytes, msg: bytes, sig: bytes) -> bool:
    if len(sig) != 64:
        return False
    A, R = _decode(pub), _decode(sig[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= _L:
        return False
    h = int.from_bytes(hashlib.sha512(sig[:32] + pub + msg).digest(), "little") % _L
    return _eq(_mul(s, _B), _add(R, _mul(h, A)))


def _pub_raw() -> bytes:
    return base64.b64decode(PUBKEY_B64)[-32:]


# ---------------------------------------------------------------- ID komputer
def _raw_machine() -> str:
    if os.name == "nt":
        try:
            out = subprocess.run(["reg", "query", r"HKLM\SOFTWARE\Microsoft\Cryptography", "/v", "MachineGuid"], capture_output=True, text=True,
                                 timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
            m = re.search(r"MachineGuid\s+REG_SZ\s+([0-9a-fA-F-]{20,})", out)
            if m:
                return "guid:" + m.group(1).lower()
        except Exception:  # noqa: BLE001
            pass
    mac = ":".join(f"{(uuid.getnode() >> s) & 0xff:02x}" for s in range(40, -1, -8))
    return "host:" + platform.node().lower() + "|" + (platform.processor() or "") + "|" + mac


_MID: Optional[str] = None


def machine_id() -> str:
    global _MID
    if _MID:
        return _MID
    h = hashlib.sha256(("GC-Ex|" + _raw_machine()).encode()).digest()
    bits = val = 0
    s = ""
    for byte in h:
        if len(s) >= 16:
            break
        val = ((val << 8) | byte) & 0xFFFFFFFF
        bits += 8
        while bits >= 5 and len(s) < 16:
            s += B32[(val >> (bits - 5)) & 31]
            bits -= 5
    _MID = "-".join(s[i:i + 4] for i in range(0, 16, 4))
    return _MID


# ---------------------------------------------------------------- kunci
def _unb64u(s: str) -> bytes:
    s = s.replace("-", "+").replace("_", "/")
    return base64.b64decode(s + "=" * (-len(s) % 4))


def _today() -> str:
    return _dt.datetime.now(_dt.timezone.utc).date().isoformat()


def parse_key(key: str) -> dict:
    k = re.sub(r"\s+", "", str(key or ""))
    p = k.split(".")
    if len(p) != 3 or p[0] != "GCEX1":
        return {"ok": False, "reason": 'Format kunci tidak dikenal. Kunci GC-Ex diawali "GCEX1."'}
    try:
        data = json.loads(_unb64u(p[1]).decode("utf-8"))
    except Exception:  # noqa: BLE001
        return {"ok": False, "reason": "Isi kunci rusak (salah salin?)."}
    try:
        good = ed25519_verify(_pub_raw(), (p[0] + "." + p[1]).encode(), _unb64u(p[2]))
    except Exception:  # noqa: BLE001
        good = False
    if not good:
        return {"ok": False, "reason": "Tanda tangan kunci tidak sah (kunci diubah, terpotong, atau bukan dari penerbit GC-Ex)."}
    return {"ok": True, "key": k, "data": data}


def verify(key: str, app: str, last_seen: Optional[str] = None, mid: Optional[str] = None) -> dict:
    r = parse_key(key)
    if not r["ok"]:
        return r
    d, mid = r["data"], (mid or machine_id())
    info = {k: d.get(k) or "" for k in ("id", "n", "o", "e", "i", "m")}
    info["a"] = d.get("a") if isinstance(d.get("a"), list) else []
    if str(d.get("m") or "").upper() != mid:
        return {"ok": False, "reason": f"Kunci ini untuk komputer lain (ID {d.get('m') or '?'}). ID komputer ini: {mid}.", "info": info}
    if not ("*" in info["a"] or app in info["a"]):
        names = ", ".join("semua aplikasi" if x == "*" else APPS.get(x, x) for x in info["a"])
        return {"ok": False, "reason": f"Kunci ini tidak berlaku untuk {APPS.get(app, app)} (berlaku: {names}).", "info": info}
    t = _today()
    if info["e"]:
        if last_seen and last_seen > info["e"] and t < last_seen:
            return {"ok": False, "expired": True, "info": info, "reason": f"Lisensi kedaluwarsa ({info['e']}); tanggal komputer lebih awal dari pemakaian terakhir ({last_seen}). Minta kunci baru ke penerbit GC-Ex."}
        if t > info["e"]:
            return {"ok": False, "expired": True, "info": info, "reason": f"Lisensi kedaluwarsa sejak {info['e']}. Minta kunci baru ke penerbit GC-Ex."}
    left = (_dt.date.fromisoformat(info["e"]) - _dt.date.fromisoformat(t)).days if info["e"] else None
    return {"ok": True, "key": r["key"], "info": info, "days_left": left}


class Store:
    def __init__(self, appdata: Optional[str] = None):
        base = Path(appdata or os.environ.get("APPDATA") or (Path.home() / ".config"))
        self.dir = base / "GC-Ex Lisensi"
        self.file = self.dir / "lisensi.json"

    def _read(self) -> dict:
        try:
            return json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}

    def _write(self, o: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(o, indent=1), encoding="utf-8")

    def check(self, app: str = "core") -> dict:
        st = self._read()
        if not st.get("key"):
            return {"ok": False, "none": True, "reason": "Belum ada lisensi di komputer ini."}
        prev, t = st.get("last"), _today()
        if not st.get("last") or t > st["last"]:
            st["last"] = t
            try:
                self._write(st)
            except OSError:
                pass
        return verify(st["key"], app, st["last"] if st["last"] > t else prev)

    def activate(self, key: str, app: str = "core") -> dict:
        st = self._read()
        r = verify(key, app, st.get("last"))
        if r["ok"]:
            self._write({"key": r["key"], "at": _dt.datetime.now(_dt.timezone.utc).isoformat(), "last": _today()})
        return r

    def remove(self) -> None:
        try:
            self.file.unlink()
        except OSError:
            pass
