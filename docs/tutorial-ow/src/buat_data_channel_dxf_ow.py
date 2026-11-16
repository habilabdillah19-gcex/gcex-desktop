"""Data latihan fiktif Ore Works: channel / trench (4 CSV) dan DXF pemetaan bergaya Global Mapper.
Koordinat grid lokal latihan (sama dengan LTH_*), nama dan angka seluruhnya karangan.
Jalankan:  python buat_data_channel_dxf_ow.py   (menulis ke ../data)"""
import math,os,random
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data')
rnd=random.Random(20261116)
# --- topografi latihan untuk elevasi ---
T={}
for ln in open(os.path.join(D,'LTH_topografi.str'),encoding='utf-8').read().splitlines()[2:]:
    f=[x.strip() for x in ln.split(',')]
    if len(f)>=4 and f[0] not in('0',''):
        y,x,z=float(f[1]),float(f[2]),float(f[3]);T[(round(x),round(y))]=z
def tz(x,y):
    gx,gy=math.floor(x/5)*5,math.floor(y/5)*5;fx,fy=(x-gx)/5,(y-gy)/5
    g=lambda a,b:T.get((a,b),T.get((round(a),round(b)),None))
    z00,z10,z01,z11=g(gx,gy),g(gx+5,gy),g(gx,gy+5),g(gx+5,gy+5)
    if None in(z00,z10,z01,z11):return min(T.values(),key=lambda v:0)  # tidak terjadi di area latihan
    return z00*(1-fx)*(1-fy)+z10*fx*(1-fy)+z01*(1-fx)*fy+z11*fx*fy
# --- jejak vein V2001 di permukaan (garis tengah wireframe latihan) ---
A=(10127.2,20035.4);B=(10079.3,20166.9)
def vein(t):return (A[0]+(B[0]-A[0])*t,A[1]+(B[1]-A[1])*t)
STK=math.degrees(math.atan2(B[0]-A[0],B[1]-A[1]))%360          # ±340°
NRM=(STK+90)%360                                                 # arah channel memotong vein (±70°)
# --- channel / trench ---
CH=[('LTH-TR-01',0.18,9),('LTH-TR-02',0.30,8),('LTH-TR-03',0.43,10),('LTH-CH-04',0.55,6),('LTH-CH-05',0.68,6),('LTH-TR-06',0.82,9)]
col=['Hole_ID,X,Y,Z,Max_Depth,Hole_Type'];sv=['Hole_ID,Depth,Dip,Azimuth'];asy=['Hole_ID,From,To,Sample_ID,Au_ppm,Ag_ppm,SxS_pct'];geo=['Hole_ID,From,To,Lith,Alt']
mids={}
for hid,t,L in CH:
    cx,cy=vein(t);az=math.radians(NRM);x0,y0=cx-math.sin(az)*L/2,cy-math.cos(az)*L/2
    col.append(f'{hid},{x0:.3f},{y0:.3f},{tz(x0,y0):.2f},{L},Channel');sv.append(f'{hid},0,-2,{NRM:.1f}');sv.append(f'{hid},{L},-2,{NRM:.1f}')
    w=2.0;n=int(L)
    for i in range(n):
        f,tt=i,i+1;m=(f+tt)/2;d=abs(m-L/2)
        inv=d<=w/2+0.25
        au=round((rnd.uniform(2.2,7.5) if inv else rnd.uniform(0.25,0.9) if d<2.5 else rnd.uniform(0.02,0.25))*(1.3 if t>0.5 else 1),2)
        ag=round(au*rnd.uniform(6,14),1);sx=round(rnd.uniform(0.05,0.6) if inv else rnd.uniform(0.2,1.4),2)
        sid=f'{hid.replace("-","")}-{i+1:02d}';asy.append(f'{hid},{f},{tt},{sid},{au},{ag},{sx}')
        geo.append(f'{hid},{f},{tt},{"QV" if inv else "AND"},{"SIL" if inv else ("ARG" if d<2.5 else "PRO")}')
        mx=x0+math.sin(az)*m;my=y0+math.cos(az)*m;mids.setdefault(hid,[]).append((mx,my,tz(mx,my),au,sid))
for nm,rows in (('collar',col),('survey',sv),('assay',asy),('geologi',geo)):
    open(os.path.join(D,f'LTH_channel_{nm}.csv'),'w',encoding='utf-8',newline='\n').write('\n'.join(rows)+'\n')
# --- DXF pemetaan bergaya Global Mapper: BLOCK + INSERT + ATTRIB ---
out=['0','SECTION','2','HEADER','9','$ACADVER','1','AC1009','999','Data latihan Ore Works (fiktif)','0','ENDSEC','0','SECTION','2','TABLES','0','ENDSEC','0','SECTION','2','BLOCKS']
ins=[];nb=[0]
def block(lay,ents,att=None):
    k=f'BLK{nb[0]}';nb[0]+=1
    out.extend(['0','BLOCK','8',lay,'70','2','2',k,'3',k,'10','0.0','20','0.0']);out.extend(ents);out.extend(['0','ENDBLK'])
    ins.extend(['0','INSERT','8',lay,'2',k,'41','1','42','1','43','1','50','0','10','0','20','0','30','0']+(['66','1'] if att else []))
    if att:
        for tag,val,(x,y) in att: ins.extend(['0','ATTRIB','8',lay,'70','1','1',str(val),'2',tag,'10',f'{x:.3f}','20',f'{y:.3f}','40','1.0'])
        ins.extend(['0','SEQEND'])
def pline(lay,pts,z3=True):
    e=['0','POLYLINE','8',lay,'66','1','70','8' if z3 else '0']
    for p in pts:e.extend(['0','VERTEX','8',lay,'70','32' if z3 else '0','10',f'{p[0]:.3f}','20',f'{p[1]:.3f}']+(['30',f'{p[2]:.3f}'] if z3 else []))
    return e+['0','SEQEND','8',lay]
def point(lay,x,y,z,txt):
    e=['0','POINT','8',lay,'10',f'{x:.3f}','20',f'{y:.3f}']+(['30',f'{z:.3f}'] if z is not None else [])
    return e+['0','TEXT','8',lay,'1',txt,'40','1.0','10',f'{x:.3f}','20',f'{y:.3f}']
# vein: dua ruas 3D + satu ruas 2D (elevasi diisi dari topografi saat impor)
for a,b,z3 in ((0.05,0.40,True),(0.40,0.70,True),(0.70,0.96,False)):
    pts=[];n=8
    for i in range(n+1):
        t=a+(b-a)*i/n;x,y=vein(t);x+=rnd.uniform(-0.6,0.6);pts.append((x,y,tz(x,y)))
    block('Qz-Vein V2001',pline('Qz-Vein V2001',pts,z3))
# kontak litologi dan sesar
k=[(10060.0,20060.0),(10085.0,20095.0),(10102.0,20130.0),(10112.0,20150.0)];block('Kontak AND-DAC',pline('Kontak AND-DAC',[(x,y,0) for x,y in k],False))
s=[(10070.0,20140.0),(10100.0,20112.0),(10132.0,20086.0)];block('Sesar F1',pline('Sesar F1',[(x,y,tz(x,y)) for x,y in s],True))
# titik sampel: 2 sama dengan interval channel (kadar & lokasi sama), sisanya grab baru
gs=[]
for hid,i in (('LTH-TR-03',4),('LTH-CH-05',2)):
    mx,my,mz,au,sid=mids[hid][i];gs.append((mx,my,mz,f'Au: {au} ppm'))
for t,off,au,zn in ((0.10,1.5,4.12,'0.31%'),(0.25,-3.0,0.46,'850 ppm'),(0.37,0.4,6.05,'1.12%'),(0.62,2.2,1.38,None),(0.76,-0.6,3.27,'0.24%'),(0.90,4.0,0.18,None)):
    x,y=vein(t);a=math.radians(NRM);x+=math.sin(a)*off;y+=math.cos(a)*off
    gs.append((x,y,tz(x,y) if t<0.7 else None,f'Au: {au} ppm'+(f' | Zn: {zn}' if zn else '')))
for x,y,z,tx in gs:
    lay=tx.replace(':','_').replace('|','_');block(lay,point(lay,x,y,z,tx),[('ELEVATION',f'{z:.3f} m',(x,y))] if z is not None else None)
x,y=vein(0.5);block('LTH-GB-09',point('LTH-GB-09',x+6,y-2,None,'LTH-GB-09'))
# strike / dip (atribut DIP, DIP_AZI, STRIKE_AZI) — tanpa elevasi
for t,off,dip,dd in ((0.15,0.3,72,248),(0.35,-0.2,68,252),(0.52,0.1,75,245),(0.66,0.4,70,250),(0.88,-0.3,66,255)):
    x,y=vein(t);a=math.radians(NRM);x+=math.sin(a)*off;y+=math.cos(a)*off
    block(str(dip),point(str(dip),x,y,None,str(dip)),[('DIP',dip,(x,y)),('DIP_AZI',dd,(x,y)),('STRIKE_AZI',(dd-90)%360,(x,y))])
for x,y,dip,dd in ((10098.0,20111.0,58,25),(10120.0,20090.0,62,30)):
    block(str(dip),point(str(dip),x,y,None,str(dip)),[('DIP',dip,(x,y)),('DIP_AZI',dd,(x,y)),('STRIKE_AZI',(dd-90)%360,(x,y))])
out.extend(['0','ENDSEC','0','SECTION','2','ENTITIES']+ins+['0','ENDSEC','0','EOF'])
open(os.path.join(D,'LTH_pemetaan.dxf'),'w',encoding='utf-8',newline='\n').write('\n'.join(out)+'\n')
print('channel',len(CH),'interval',len(asy)-1,'· strike vein',round(STK,1),'· DXF titik sampel',len(gs))
