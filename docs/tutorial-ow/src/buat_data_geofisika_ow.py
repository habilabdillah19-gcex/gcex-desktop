# -*- coding: utf-8 -*-
"""Data latihan FIKTIF georeferensi Ore Works: peta RTP magnetik (plan) dan penampang resistivity (vertikal) berupa PNG
tanpa world file, berbingkai, berlabel grid koordinat — sama dengan cakupan data latihan LTH (E 10.000–10.200, N 20.000–20.200).
Kunci (untuk memeriksa): peta 4 px/m, sudut kiri-atas area peta = piksel (100, 60) = E 10.000 N 20.200;
penampang 4 px/m, garis E 10.000 → 10.200 di N 20.100, RL 160 di piksel y 40, jarak 0 di piksel x 80."""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
OUT = (sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'data', 'Geofisika'))
os.makedirs(OUT, exist_ok=True)
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f12 = ImageFont.truetype(F, 12); f14 = ImageFont.truetype(F, 14)
def turbo(t):
    t = np.clip(t, 0, 1)
    r = 34.61 + t*(1172.33 - t*(10793.56 - t*(33300.12 - t*(38394.49 - t*14825.05))))
    g = 23.31 + t*(557.33 + t*(1225.33 - t*(3574.96 - t*(1073.77 + t*707.56))))
    b = 27.2 + t*(3211.1 - t*(15327.97 - t*(27814 - t*(22569.18 - t*6838.66))))
    return np.clip(np.stack([r, g, b], -1), 0, 255).astype(np.uint8)
# ---- peta RTP (plan) ----
W, H = 1000, 920; X0, Y0, S = 100, 60, 4.0
im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
E = 10000 + (np.arange(800) + 0.5) / S; N = 20200 - (np.arange(800) + 0.5) / S
EE, NN = np.meshgrid(E, N)
z = 1.2*np.exp(-(((EE-10075)*np.cos(0.35)+(NN-20110)*np.sin(0.35))**2/900 + ((NN-20110)*np.cos(0.35)-(EE-10075)*np.sin(0.35))**2/120)) \
    - 0.8*np.exp(-((EE-10150)**2+(NN-20050)**2)/700) + 0.15*np.sin(EE/9)*np.cos(NN/13)
rgb = turbo((z - z.min())/(z.max() - z.min()))
mask = ((EE-10100)**2/110**2 + (NN-20100)**2/95**2) < 1           # di luar area survei = putih
rgb[~mask] = 255
im.paste(Image.fromarray(rgb), (X0, Y0))
d.rectangle([X0, Y0, X0+800, Y0+800], outline='black', width=2)
for k in range(0, 201, 50):
    x = X0 + k*S; y = Y0 + k*S
    d.line([x, Y0, x, Y0+800], fill=(60, 60, 60), width=1); d.line([X0, y, X0+800, y], fill=(60, 60, 60), width=1)
    d.text((x-22, Y0+806), f'{10000+k:,}'.replace(',', '.'), font=f12, fill='black'); d.text((X0-92, y-7), f'{20200-k:,}'.replace(',', '.'), font=f12, fill='black')
d.text((X0, 18), 'RTP magnetik (nT) — DATA FIKTIF LATIHAN', font=f14, fill='black')
im.save(os.path.join(OUT, 'LTH_RTP_magnetik.png'))
# ---- penampang resistivity (vertikal) ----
W, H = 960, 500; X0, Y0 = 80, 40
im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
dd = (np.arange(800) + 0.5) / S; zz = 160 - (np.arange(400) + 0.5) / S
DD, ZZ = np.meshgrid(dd, zz)
rho = np.log10(80 + 900*np.exp(-((DD-100+(160-ZZ)*0.27)**2/40)) + 300*np.exp(-((DD-150)**2+(ZZ-100)**2)/300))
rgb = turbo((rho - rho.min())/(rho.max() - rho.min()))
top = 160 - 0.02*(DD-100)**2/10                                   # di atas topografi = putih
rgb[ZZ > top] = 255
im.paste(Image.fromarray(rgb), (X0, Y0)); d.rectangle([X0, Y0, X0+800, Y0+400], outline='black', width=2)
for k in range(0, 201, 25):
    x = X0 + k*S; d.line([x, Y0+400, x, Y0+406], fill='black'); d.text((x-10, Y0+408), str(k), font=f12, fill='black')
for rl in range(60, 161, 20):
    y = Y0 + (160-rl)*S; d.line([X0-6, y, X0, y], fill='black'); d.text((X0-42, y-7), str(rl), font=f12, fill='black')
d.text((X0, 12), 'Resistivity (Ohm.m) lintasan N 20.100, E 10.000 -> 10.200 — DATA FIKTIF LATIHAN', font=f14, fill='black')
d.text((X0+330, Y0+428), 'Jarak (m)', font=f12, fill='black')
im.save(os.path.join(OUT, 'LTH_resistivity_N20100.png'))
print('ok', OUT)
