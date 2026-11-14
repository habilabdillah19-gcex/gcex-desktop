# Data latihan FIKTIF Ore Works (koordinat lokal, tanpa nama perusahaan / proyek nyata)
import math, random, os
random.seed(7)
D='data'
E0,N0=10000.0,20000.0
def topo(e,n): return 150+0.06*(e-E0)-0.03*(n-N0)+4*math.sin((e-E0)/35)+3*math.cos((n-N0)/45)
# bidang vein: strike 160, dip 70 ke 250
dd=math.radians(250);dip=math.radians(70)
nrm=(math.sin(dd)*math.sin(dip),math.cos(dd)*math.sin(dip),math.cos(dip))  # normal (upward-ish)
P0=(E0+100,N0+100,150)
def sd(e,n,z): return (e-P0[0])*nrm[0]+(n-P0[1])*nrm[1]+(z-P0[2])*nrm[2]
st=math.radians(160)
# topografi .str: garis tiap 5 m
L=['ZONA_LATIHAN,01-Nov-26,,topografi fiktif','0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000']
for i in range(0,41):
    n=N0+i*5
    for j in range(0,41):
        e=E0+j*5;L.append(f'1, {n:.3f}, {e:.3f}, {topo(e,n):.3f}, ')
    L.append('0, 0.000, 0.000, 0.000,')
L.append('0, 0.000, 0.000, 0.000, END');open(f'{D}/LTH_topografi.str','w').write('\r\n'.join(L)+'\r\n')
# jejak vein di topografi
def trace(s):
    bx=P0[0]+s*math.sin(st);by=P0[1]+s*math.cos(st);hx,hy=math.sin(dd),math.cos(dd)
    lo,hi=-60,60
    for _ in range(60):
        m=(lo+hi)/2;e,n=bx+hx*m,by+hy*m
        if sd(e,n,topo(e,n))>0: hi=m
        else: lo=m
    e,n=bx+hx*m,by+hy*m;return e,n,topo(e,n)
pk=[];k=1
for s in range(-30,31,5):
    e,n,z=trace(s+random.uniform(-.4,.4));pk.append((f'P{k:03d}',e,n,z,'VN'));k+=1
# kontak 14 m ke timur (sejajar strike)
for s in range(-30,31,10):
    e,n,z=trace(s);e+=14*math.sin(dd+math.pi);n+=14*math.cos(dd+math.pi);z=topo(e,n);pk.append((f'P{k:03d}',e,n,z,'KT'));k+=1
# jejak sesar memotong
for t in range(0,6):
    e=E0+60+t*14;n=N0+130-t*6;pk.append((f'P{k:03d}',e,n,topo(e,n),'SL'));k+=1
# channel memotong vein (tegak lurus strike), 9 titik tiap 1.5 m
e0,n0,_=trace(3);ux,uy=math.sin(dd),math.cos(dd)
for t in range(9):
    o=-6+t*1.5;e,n=e0+ux*o,n0+uy*o;pk.append((f'P{k:03d}',e,n,topo(e,n),'CH'));k+=1
# grab
for (de,dn) in [(-8,10),(5,-14),(12,6)]:
    e,n,_=trace(0);e+=de;n+=dn;pk.append((f'P{k:03d}',e,n,topo(e,n),'GB'));k+=1
open(f'{D}/LTH_pickup.csv','w').write('ID,East,North,RL,Code\r\n'+''.join(f'{a},{b:.3f},{c:.3f},{d:.3f},{f}\r\n' for a,b,c,d,f in pk))
# assay channel (8 interval)
au=[0.08,0.21,0.62,3.85,7.12,1.48,0.33,0.05];ag=[1.2,2.0,4.5,22.0,41.0,9.5,3.1,0.8]
lith=['AND','AND','AND','QV','QV','QV','AND','AND'];alt=['PRO','ARG','ARG','SIL','SIL','ARG','ARG','PRO']
open(f'{D}/LTH_assay_channel.txt','w').write('Sample_ID\tAu_ppm\tAg_ppm\tLith\tAlt\tDeskripsi\n'+''.join(f'CH01-{i+1:03d}\t{au[i]}\t{ag[i]}\t{lith[i]}\t{alt[i]}\t{"Kuarsa berlapis" if lith[i]=="QV" else "Andesit"}\n' for i in range(8)))
# bor GC fiktif
col=['Hole_ID,X,Y,Z,Max_Depth,Hole_Purpose'];sv=['Hole_ID,Depth,Dip,Azimuth'];asy=['Hole_ID,From,To,Au_ppm,Ag_ppm,Cu_ppm,Pb_ppm,Zn_ppm,SxS_pct'];geo=['Hole_ID,From,To,Lith,Alt,Vein_Type']
R2=random.Random(11)  # RNG terpisah: nilai Au/Ag lama tetap sama
h=1
for i in range(7):
    for j in range(6):
        e=E0+55+i*14+random.uniform(-1,1);n=N0+55+j*18+random.uniform(-1,1);z=topo(e,n);hid=f'LTH_{h:03d}';h+=1;dep=40
        col.append(f'{hid},{e:.2f},{n:.2f},{z:.2f},{dep},{"Exploration" if i in (0,6) and j%2==0 else "GC"}');sv.append(f'{hid},0,-60,70');sv.append(f'{hid},{dep},-60,70')
        az=math.radians(70);dp=math.radians(60)
        for m in range(dep):
            c=m+0.5;x=e+math.sin(az)*math.cos(dp)*c;y=n+math.cos(az)*math.cos(dp)*c;zz=z-math.sin(dp)*c;d=abs(sd(x,y,zz))
            a=random.uniform(2.5,9) if d<1.2 else random.uniform(0.3,0.9) if d<3 else random.uniform(0.01,0.18)
            ag=a*6+random.uniform(0,2);v=d<1.2;dz=z-zz
            cu=(R2.uniform(150,900) if v else R2.uniform(20,120))*(0.4 if dz<6 else 1);pb=R2.uniform(300,2500) if v else R2.uniform(5,80);zn=pb*R2.uniform(1.2,2.4)
            sx=R2.uniform(0.1,0.7) if dz<6 else R2.uniform(0.8,1.0) if dz<9 else (R2.uniform(1.5,4.5) if v else R2.uniform(1.05,2.2))
            pbs='-' if pb<8 else f'{pb:.0f}'
            asy.append(f'{hid},{m},{m+1},{a:.3f},{ag:.2f},{cu:.0f},{pbs},{zn:.0f},{sx:.2f}')
            geo.append(f'{hid},{m},{m+1},{"QV" if v else "AND"},{"SIL" if v else "ARG" if d<3 else "PRO"},{("QV-B" if a>5 else "QV-C") if v else "-"}')
        h+=0
for nm,L in [('collar',col),('survey',sv),('assay',asy),('geologi',geo)]: open(f'{D}/LTH_{nm}.csv','w').write('\r\n'.join(L)+'\r\n')
# wireframe vein (.obj) tebal 2 m
V=[];F=[]
sx,sy=math.sin(st),math.cos(st);dx,dy,dz=math.sin(dd)*math.cos(dip),math.cos(dd)*math.cos(dip),-math.sin(dip)
for a in (-70,70):
    for b in (-10,90):
        for t in (-1,1):
            V.append((P0[0]+sx*a+dx*b+nrm[0]*t,P0[1]+sy*a+dy*b+nrm[1]*t,P0[2]+dz*b+nrm[2]*t))
idx=lambda a,b,t:a*4+b*2+t+1
for q in [(0,0,0),]: pass
faces=[(1,3,7,5),(2,6,8,4),(1,5,6,2),(3,4,8,7),(1,2,4,3),(5,7,8,6)]
o=['o V2001']+[f'v {x:.3f} {y:.3f} {z:.3f}' for x,y,z in V]+[f'f {a} {b} {c}\nf {a} {c} {d}' for a,b,c,d in faces]
open(f'{D}/LTH_V2001.obj','w').write('\n'.join(o)+'\n')
# titik struktur
sp=['ID,Kategori,Jenis,X,Y,Z,Dip,DipDirection,Tebal,Keterangan']
J=[('Geologi','Sesar',65,20),('Geologi','Kekar',80,115),('Geologi','Bedding',25,300),('Geologi','Foliasi',45,240),('Geologi','Shear zone',72,255),('Geologi','Kekar',85,30),('Vein','Vein',70,250),('Vein','Veinlet',62,245),('Vein','Stockwork',75,260),('Geologi','Lineasi / striasi',35,210)]
for i,(k2,j,dp2,d2) in enumerate(J):
    e,n,_=trace(-25+i*5.5);e+=random.uniform(-20,-6) if i%2 else random.uniform(6,20)
    sp.append(f'S-{i+1:03d},{k2},{j},{e:.2f},{n:.2f},,{dp2},{d2},{"0.6" if k2=="Vein" else ""},data latihan')
open(f'{D}/LTH_titik_struktur.csv','w').write('\r\n'.join(sp)+'\r\n')
print('ok',len(pk))
