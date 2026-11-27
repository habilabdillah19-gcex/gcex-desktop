"""Uji rotasi 3D tidak membalik utara (pemilik 27 Nov 2026: "arah utara sering berubah jadi ke bawah").
R1 mode putar scene = turntable; R2 tombol Orbital rotation tidak ada di modebar
R0 PENYEBAB: tanpa pengunci, mode bawaan Plotly = orbit (up tidak dikunci); dengan turntable up -> Z
R3 mode orbit dipaksa lalu digambar ulang -> kembali turntable; zoom/pan pilihan pengguna dipertahankan
R4 kamera up miring diminta (penampang miring) -> turntable menegakkan up ke Z; drag mouse tidak memiringkannya lagi
R5 setelah banyak putaran bolak-balik, up tetap Z (utara tidak ke bawah)
R6 penanda lantai nominal: AMK.nominal + kolom Status TSV
Pakai: python tools/uji/uji_rotasi_3d.py
"""
import sys
sys.argv = ['x', 'app']
from pathlib import Path
exec(open(Path(__file__).resolve().parent / 'uji_palet.py', encoding='utf-8').read().split('with sync_playwright() as pw:')[0])
gagal = []
def cek(nama, ok, info=''):
    print(('  ok   ' if ok else '  GAGAL ') + nama + ('  ' + str(info)[:250] if info else ''))
    if not ok: gagal.append(nama)
CAM = "(()=>{var c=document.getElementById('plotDiv')._fullLayout.scene.camera;return {e:c.eye,u:c.up}})()"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, P = server(ROOT / 'app' / 'index.html'); pg = b.new_page(viewport={'width': 1600, 'height': 900}); pg.on('dialog', lambda x: x.accept())
    err = []; pg.on('pageerror', lambda e: err.append(str(e)[:200]))
    muat(pg, P, TUNGGU); pg.wait_for_timeout(1500)
    pg.evaluate("if(window.VIEW2D)toggle2D();updatePlot();0"); pg.wait_for_timeout(1500)
    r0 = pg.evaluate("""(async()=>{var d=document.createElement('div');d.style.cssText='width:200px;height:200px;position:fixed;left:0;top:0;opacity:0';document.body.appendChild(d);var T=[{type:'scatter3d',x:[0,1],y:[0,1],z:[0,1]}],C={eye:{x:1.5,y:-1.5,z:1},up:{x:0.5,y:0.3,z:0.6}};
      await Plotly.newPlot(d,T,{scene:{camera:C}});var a=d._fullLayout.scene.dragmode;await Plotly.react(d,T,{scene:{dragmode:'turntable',camera:C}});var b=d.layout.scene.camera.up;d.remove();return [a,b.x,b.y,b.z]})()""")
    cek('R0 bawaan Plotly = orbit; turntable menegakkan up ke Z', r0 == ['orbit', 0, 0, 1], r0)
    dm = pg.evaluate("document.getElementById('plotDiv')._fullLayout.scene.dragmode")
    cek('R1 dragmode scene = turntable', dm == 'turntable', dm)
    cek('R2 tombol Orbital rotation tidak ada di modebar', pg.evaluate("!document.querySelector('#plotDiv .modebar [data-attr=\"scene.dragmode\"][data-val=\"orbit\"]')"))
    pg.evaluate("Plotly.relayout('plotDiv',{'scene.dragmode':'orbit'});0"); pg.wait_for_timeout(400)
    pg.evaluate("updatePlot();0"); pg.wait_for_timeout(1200)
    dm = pg.evaluate("document.getElementById('plotDiv')._fullLayout.scene.dragmode")
    pg.evaluate("Plotly.relayout('plotDiv',{'scene.dragmode':'pan'});0"); pg.wait_for_timeout(400)
    pg.evaluate("updatePlot();0"); pg.wait_for_timeout(1200)
    dp = pg.evaluate("document.getElementById('plotDiv')._fullLayout.scene.dragmode")
    pg.evaluate("Plotly.relayout('plotDiv',{'scene.dragmode':'turntable'});0"); pg.wait_for_timeout(300)
    cek('R3 orbit -> turntable setelah gambar ulang; pan dipertahankan', dm == 'turntable' and dp == 'pan', [dm, dp])
    pg.evaluate("setCam(1.5,-1.5,1,{x:0.5,y:0.3,z:0.6});0"); pg.wait_for_timeout(1500)
    c0 = pg.evaluate(CAM)
    bb = pg.evaluate("(()=>{var r=document.querySelector('#plotDiv .gl-container, #plotDiv .svg-container').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
    cek('R4a up miring yang diminta ditegakkan ke Z', abs(c0['u']['x']) < 0.05 and abs(c0['u']['y']) < 0.05 and c0['u']['z'] > 0.95, c0['u'])
    x, y = bb
    pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(x + 60, y + 20, steps=8); pg.mouse.up(); pg.wait_for_timeout(1200)
    c1 = pg.evaluate(CAM)
    cek('R4 setelah drag: up tetap Z', abs(c1['u']['x']) < 0.05 and abs(c1['u']['y']) < 0.05 and c1['u']['z'] > 0.95, c1['u'])
    for k in range(6):
        sg = 1 if k % 2 == 0 else -1
        pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(x + sg * 120, y + sg * 90, steps=10); pg.mouse.up(); pg.wait_for_timeout(300)
        pg.evaluate("setCam(%s,%s,%s);0" % (1.5 * sg, -1.5, 1 if sg > 0 else 0.4)) if k % 3 == 2 else None
        pg.wait_for_timeout(500)
    c2 = pg.evaluate(CAM)
    cek('R5 setelah putaran bolak-balik: up tetap Z', abs(c2['u']['x']) < 0.05 and abs(c2['u']['y']) < 0.05 and c2['u']['z'] > 0.95, c2['u'])
    r6 = pg.evaluate("(()=>{if(!window.AMK||!AMK.nominal)return 'tidak ada';return [AMK.nominal({calc:true,st:{fl:{none:1}}}),AMK.nominal({calc:true,st:{fl:{n:5}}}),AMK.nominal({calc:false,st:{fl:{none:1}}}),AMK.nominal({calc:true,st:{fl:null}})]})()")
    cek('R6 AMK.nominal: true hanya bila dihitung & lantai none', r6 == [True, False, False, False], r6)
    cek('R7 tanpa galat halaman', not err, err)
    b.close()
print('GAGAL: ' + ', '.join(gagal) if gagal else 'SEMUA LULUS'); sys.exit(1 if gagal else 0)
