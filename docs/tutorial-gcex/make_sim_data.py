"""Data simulasi tutorial GC-Ex Drillhole (SINTETIS, bukan data perusahaan).
Vein utama QV_Utama: sigmoidal, strike 45 deg, dip 70 deg ke tenggara (azimuth 135), tebal 1-3.2 m, ore shoot;
vein QV_HW1: sejajar, 22 m di sisi hangingwall, lebih tipis & pendek. Bor dari sisi HW (azimuth 315, dip -55..-65).
python make_sim_data.py [folder_output]   (default: ./data)"""
import numpy as np,os,sys,csv,math
OUTD=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'data')
os.makedirs(OUTD,exist_ok=True);rng=np.random.default_rng(42)
E0,N0=505000.0,9012000.0
s=np.array([math.sin(math.radians(45)),math.cos(math.radians(45)),0.0])           # strike
dh=np.array([math.sin(math.radians(135)),math.cos(math.radians(135)),0.0])         # arah dip (horizontal)
dip=math.radians(70);dd=math.cos(dip)*dh+np.array([0,0,-math.sin(dip)])            # turun searah dip, di bidang vein
n=np.cross(s,dd);n=n if n[2]>0 else -n                                            # normal ke sisi HW (atas)
def topo(x,y):return 318+0.035*(x-E0)-0.02*(y-N0)+2.5*np.sin((x-E0)/37.0)*np.cos((y-N0)/53.0)
C=np.array([E0,N0,0.0]);C[2]=topo(E0,N0)-3
VEINS={'QV_Utama':dict(off=0.0,a=(-105,105),b=(0,135),T0=1.0,T1=2.2,ac=10,bc=55,sa=75,sb=55,shoot=(-20,50,50,40),g=2.6),
       'QV_HW1':dict(off=22.0,a=(-60,70),b=(8,90),T0=0.8,T1=1.0,ac=5,bc=45,sa=40,sb=35,shoot=(10,40,35,30),g=1.6)}
def wmid(a,b,V):return V['off']+6.0*np.tanh((b-60)/25.0)+3.0*np.sin(2*np.pi*a/170.0)-V.get('k',0.0)*np.maximum(0.0,V.get('bj',0.0)-b)
def taper(a,b,V):
    a0,a1=V['a'];b0,b1=V['b'];e=np.minimum.reduce([np.clip((a-a0)/12,0,1),np.clip((a1-a)/12,0,1),np.clip((b-b0)/12,0,1),np.clip((b1-b)/12,0,1)]);return e
def thick(a,b,V):return (V['T0']+V['T1']*np.exp(-((a-V['ac'])/V['sa'])**2-((b-V['bc'])/V['sb'])**2))*taper(a,b,V)
def shoot(a,b,V):sa,sb,ra,rb=V['shoot'];return 0.35+1.65*np.exp(-((a-sa)/ra)**2-((b-sb)/rb)**2)
def frame(p):r=p-C;return r@s,r@dd,r@n
def inside(p,V):
    a,b,w=frame(p);T=thick(a,b,V);return (np.abs(w-wmid(a,b,V))<=T/2)&(T>0.3)
def dist(p,V):
    a,b,w=frame(p);T=thick(a,b,V);d=np.abs(w-wmid(a,b,V))-T/2;return np.where(T>0.3,d,99.0)
def vpt(a,b,V,side=0.0):return C+a*s+b*dd+(wmid(a,b,V)+side*thick(a,b,V)/2)*n
# ---------- lubang bor ----------
holes=[]
def mk_hole(hid,a,b,dipd,extra=12):
    az=math.radians(315);v=np.array([math.sin(az)*math.cos(math.radians(dipd)),math.cos(az)*math.cos(math.radians(dipd)),-math.sin(math.radians(dipd))])
    tgt=vpt(a,b,VEINS['QV_Utama']);t=10.0
    for _ in range(60):c=tgt-t*v;t+= (topo(c[0],c[1])-c[2])/max(-v[2],0.3)*0.7
    c=tgt-t*v;c[2]=topo(c[0],c[1]);depth=math.ceil(t+thick(a,b,VEINS['QV_Utama'])/max(abs(v@n),0.2)+extra)
    holes.append(dict(id=hid,c=c,v=v,dip=-dipd,az=315.0,depth=depth))
sec=list(range(-100,101,20))
for k,a in enumerate(sec):
    for j,(b,dp) in enumerate([(22,55),(60,60),(102,65)]):
        mk_hole('SIM-S%02d-%d'%(k+1,j+1),a+rng.uniform(-1.5,1.5),b+rng.uniform(-4,4),dp+rng.uniform(-2,2))
infill=[]
for i,(a,b,dp) in enumerate([(-10,42,58),(10,78,62),(30,45,58),(-30,80,62)]):
    mk_hole('SIM-INF-%02d'%(i+1),a,b,dp);infill.append(holes.pop())
def samples(h,VE=None):
    VE=VE or VEINS
    rows=[];gl=[]
    for f in range(0,h['depth']):
        t=min(f+1,h['depth']);sub=np.array([h['c']+h['v']*(f+(t-f)*(q+0.5)/10) for q in range(10)])
        fr={k:inside(sub,V).mean() for k,V in VE.items()};dmin={k:dist(sub,V).min() for k,V in VE.items()}
        vk=max(fr,key=fr.get);fv=fr[vk];mid=h['c']+h['v']*(f+t)/2;a,b,w=frame(mid)
        gv=VE[vk]['g']*shoot(a,b,VE[vk])*math.exp(rng.normal(-0.32,0.8));dm=min(dmin.values())
        wall=(0.25*math.exp(rng.normal(0,0.5)) if dm<1.5 else 0.08*math.exp(rng.normal(0,0.6)) if dm<4 else 0.012*math.exp(rng.normal(0,0.7)))
        au=fv*gv+(1-fv)*wall;ag=max(0.2,au*2.8*math.exp(rng.normal(0,0.35)));sx=min(1.0,0.15+0.5*fv+abs(rng.normal(0,0.08)))
        lith='QV' if fv>=0.5 else 'AND';alt='SIL' if dm<2 else 'ARG' if dm<6 else 'PRO';ox='OX' if mid[2]>topo(mid[0],mid[1])-8 else 'FR'
        rows.append([h['id'],f,t,'%s_%03d'%(h['id'],f+1),round(au,3),round(ag,2),round(sx,3)]);gl.append([h['id'],f,t,lith,alt,ox])
    return rows,gl
def write(fn,head,rows):
    with open(os.path.join(OUTD,fn),'w',newline='') as f:w=csv.writer(f);w.writerow(head);w.writerows(rows)
def tables(H,pre,VE=None):
    col=[[h['id'],round(h['c'][0],3),round(h['c'][1],3),round(h['c'][2],3),h['depth']] for h in H]
    sv=[[h['id'],0,round(h['dip'],1),h['az']] for h in H]+[[h['id'],h['depth'],round(h['dip'],1),h['az']] for h in H]
    A=[];G=[]
    for h in H:r,g=samples(h,VE);A+=r;G+=g
    write(pre+'collar.csv',['Hole_ID','Easting','Northing','RL','Total_depth'],col);write(pre+'survey.csv',['Hole_ID','Depth','Dip','Azimuth'],sorted(sv))
    write(pre+'assay.csv',['Hole_ID','From','To','Sample_ID','Au','Ag','SxS'],A);write(pre+'geologi.csv',['Hole_ID','From','To','Lith','Alt','Ox'],G);return A
A=tables(holes,'SIM_');A2=tables(infill,'SIM_upsert_')
# ---------- topografi (titik XYZ, grid 5 m) ----------
xs=np.arange(E0-170,E0+171,5);ys=np.arange(N0-170,N0+171,5);T=[[round(x,2),round(y,2),round(float(topo(x,y)),2)] for x in xs for y in ys]
write('SIM_topo_xyz.csv',['X','Y','Z'],T)
# ---------- wireframe QV_Utama "dari Leapfrog" (OBJ tertutup) ----------
V=VEINS['QV_Utama'];na,nb=85,55;aa=np.linspace(V['a'][0]+1,V['a'][1]-1,na);bb=np.linspace(V['b'][0]+1,V['b'][1]-1,nb);verts=[];idx={}
def vid(i,j,side):
    k=(i,j,side)
    if k not in idx:
        T_=max(float(thick(aa[i],bb[j],V)),0.25);p=C+aa[i]*s+bb[j]*dd+(wmid(aa[i],bb[j],V)+(0.5 if side else -0.5)*T_)*n;idx[k]=len(verts)+1;verts.append(p)
    return idx[k]
F=[]
for i in range(na-1):
    for j in range(nb-1):
        a1,b1,c1,d1=vid(i,j,1),vid(i+1,j,1),vid(i+1,j+1,1),vid(i,j+1,1);F+=[(a1,b1,c1),(a1,c1,d1)]
        a2,b2,c2,d2=vid(i,j,0),vid(i+1,j,0),vid(i+1,j+1,0),vid(i,j+1,0);F+=[(a2,c2,b2),(a2,d2,c2)]
bd=[(i,0) for i in range(na-1)]+[(na-1,j) for j in range(nb-1)]+[(i,nb-1) for i in range(na-1,0,-1)]+[(0,j) for j in range(nb-1,0,-1)]
for k in range(len(bd)):
    p,q=bd[k],bd[(k+1)%len(bd)];u1,u2,l1,l2=vid(p[0],p[1],1),vid(q[0],q[1],1),vid(p[0],p[1],0),vid(q[0],q[1],0);F+=[(u1,l1,l2),(u1,l2,u2)]
with open(os.path.join(OUTD,'QV_Utama_Leapfrog.obj'),'w') as f:
    f.write('# QV_Utama - wireframe vein SIMULASI (contoh "dari Leapfrog", format OBJ)\n')
    for p in verts:f.write('v %.3f %.3f %.3f\n'%tuple(p))
    for t in F:f.write('f %d %d %d\n'%t)
# ---------- block model GC lama (CSV, blok 2.5 m di sekitar vein utama) ----------
bs=2.5;pts=[]
for a in np.arange(-110,111,2.0):
    for b in np.arange(-5,141,2.0):
        for w in np.arange(-14,15,2.0):pts.append(C+a*s+b*dd+(wmid(a,b,V)+w)*n)
P=np.array(pts);G=np.unique(np.floor((P-np.array([E0,N0,0]))/bs).astype(int),axis=0);cen=(G+0.5)*bs+np.array([E0,N0,0])
cen=cen[cen[:,2]<topo(cen[:,0],cen[:,1])];ins=inside(cen,V);a_,b_,_=frame(cen)
au=np.where(ins,V['g']*shoot(a_,b_,V)*0.75,np.where(dist(cen,V)<2,0.18,0.02));au=au*np.exp(rng.normal(0,0.25,len(au)))
dom=np.where(ins,'QV_UTAMA','WASTE')
write('SIM_BM_GC.csv',['X','Y','Z','XINC','YINC','ZINC','AU','SG','DOMAIN'],[[round(c[0],2),round(c[1],2),round(c[2],2),bs,bs,bs,round(float(g),3),2.6 if d=='WASTE' else 2.55,d] for c,g,d in zip(cen,au,dom)])
# ---------- infill tahap 2 (latihan koreksi model estimasi; dibuat paling akhir agar file lain tidak berubah) ----------
infill2=[]
for i,(a,b,dp) in enumerate([(70,50,58),(90,70,60)]):
    mk_hole('SIM-INF-%02d'%(i+5),a,b,dp);infill2.append(holes.pop())
A3=tables(infill2,'SIM_upsert2_')
with open(os.path.join(OUTD,'BACA_SAYA.txt'),'w') as f:f.write('\n'.join(['DATA SIMULASI TUTORIAL GC-Ex DRILLHOLE (SINTETIS, bukan data perusahaan)','',
 'SIM_collar/survey/assay/geologi.csv : %d lubang bor (11 section tegak lurus strike, 3 lubang per section), sampel 1 m'%len(holes),
 'SIM_upsert_*.csv                    : 4 lubang infill (SIM-INF-01..04) untuk latihan upsert',
 'SIM_upsert2_*.csv                   : 2 lubang infill tahap 2 (SIM-INF-05..06) untuk latihan koreksi Model Estimation','SIM_topo_xyz.csv                    : topografi titik XYZ grid 5 m',
 'SIM_topo_xyz_nov.csv                : topografi bulan berikutnya (area pit turun s/d 6 m) untuk latihan menu Data Spasial',
 'SIM_BM_GC.csv                       : block model GC lama 2.5 m (%d blok) di sekitar vein utama, atribut AU, SG, DOMAIN'%len(cen),
 'QV_Utama_Leapfrog.obj               : wireframe vein utama (contoh hasil Leapfrog, OBJ tertutup, %d segitiga)'%len(F),'',
 'Geometri: QV_Utama strike 045, dip 70 ke 135 (tenggara), bentuk sigmoidal, tebal 1-3.2 m, ore shoot di tengah;',
 'QV_HW1 sejajar 22 m di sisi hangingwall (lebih tipis). Bor dari sisi HW: azimuth 315, dip -55 s/d -65.',
 'Koordinat sekitar E %d, N %d. Dip survey negatif = ke bawah.'%(E0,N0),'Dibuat ulang: python make_sim_data.py']) +'\n')
print(len(holes),'hole',len(A),'assay',len(infill),'infill',len(A2),'assay infill',len(T),'topo',len(cen),'blok',len(verts),'v',len(F),'f')
au=np.array([r[4] for r in A]);print('Au mean %.3f max %.2f  >=0.5: %d'%(au.mean(),au.max(),(au>=0.5).sum()))
# ---------- topografi bulan berikutnya (latihan menu Data Spasial): area pit turun hingga 6 m ----------
T2=[[r[0],r[1],round(r[2]-6.0*max(0.0,1-((r[0]-E0)**2+(r[1]-N0)**2)/90.0**2),2)] for r in T]
write('SIM_topo_xyz_nov.csv',['X','Y','Z'],T2)

# ---------- DATA TERPISAH: vein bercabang (latihan domain induk) -- dibuat paling akhir, file lain tidak berubah ----------
# QVS_Utama (batang) + QVS_Cabang: cabang lepas dari sisi footwall batang di kedalaman ~65 m searah dip (titik percabangan)
# dan makin menjauh ke atas (0,32 m per m), sehingga bor dangkal menembus dua vein, bor dalam hanya satu (vein menyatu).
VS={'QVS_Utama':dict(VEINS['QV_Utama'],a=(-75,75)),
    'QVS_Cabang':dict(off=0.0,k=0.32,bj=66.0,a=(-58,58),b=(0,74),T0=0.7,T1=0.8,ac=0,bc=30,sa=45,sb=30,shoot=(0,30,40,30),g=1.9)}
spl=[]
for k,a in enumerate(range(-60,61,20)):
    for j,(b,dp) in enumerate([(18,52),(38,56),(62,60),(96,65)]):
        mk_hole('SPL-S%02d-%d'%(k+1,j+1),a+rng.uniform(-1.5,1.5),b+rng.uniform(-3,3),dp+rng.uniform(-2,2),extra=22);spl.append(holes.pop())
A4=tables(spl,'SIM_split_',VS)
bs=2.5;pts=[]
for nm,V_ in VS.items():
    for a in np.arange(V_['a'][0]-6,V_['a'][1]+7,2.0):
        for b in np.arange(V_['b'][0]-6,V_['b'][1]+7,2.0):
            for w in np.arange(-10,11,2.0):pts.append(C+a*s+b*dd+(wmid(a,b,V_)+w)*n)
P=np.array(pts);G2=np.unique(np.floor((P-np.array([E0,N0,0]))/bs).astype(int),axis=0);cen2=(G2+0.5)*bs+np.array([E0,N0,0]);cen2=cen2[cen2[:,2]<topo(cen2[:,0],cen2[:,1])]
iU=inside(cen2,VS['QVS_Utama']);iC=inside(cen2,VS['QVS_Cabang']);a_,b_,_=frame(cen2)
au2=np.where(iU,2.6*shoot(a_,b_,VS['QVS_Utama'])*0.7,np.where(iC,1.9*shoot(a_,b_,VS['QVS_Cabang'])*0.7,0.03))*np.exp(rng.normal(0,0.25,len(cen2)))
dom2=np.where(iU|iC,'QVS','WASTE')
write('SIM_split_BM_GC.csv',['X','Y','Z','XINC','YINC','ZINC','AU','SG','DOMAIN'],[[round(c[0],2),round(c[1],2),round(c[2],2),bs,bs,bs,round(float(g),3),2.6 if d=='WASTE' else 2.55,d] for c,g,d in zip(cen2,au2,dom2)])
with open(os.path.join(OUTD,'BACA_SAYA.txt'),'a') as f:f.write('\n'.join(['','VEIN BERCABANG (latihan domain induk, proyek terpisah):',
 'SIM_split_collar/survey/assay/geologi.csv : %d lubang (7 section x 4 lubang, SPL-*); QVS_Utama + QVS_Cabang'%len(spl),
 'SIM_split_BM_GC.csv                        : block model GC 2.5 m (%d blok) di sekitar kedua vein'%len(cen2),
 'Geometri: QVS_Cabang lepas dari sisi footwall QVS_Utama pada ~66 m searah dip, menjauh 0,32 m per m ke atas.',
 'Bor baris 1-2 (dangkal) menembus dua vein (Utama dulu, Cabang di bawahnya); baris 3-4 hanya satu vein.'])+'\n')
print('split',len(spl),'hole',len(A4),'assay',len(cen2),'blok')

# ---------- DATA TERPISAH: struktur lapangan & pick-up survei (latihan menu Struktur & Map) -- paling akhir ----------
# jejak singkapan QV_Utama = titik di bidang tengah vein yang menembus topografi; struktur diukur di singkapan
V=VEINS['QV_Utama'];outc=[]
for a in np.arange(-96,97,6.0):
    lo,hi=-10.0,60.0
    for _ in range(40):
        m=(lo+hi)/2;p=vpt(a,m,V)
        if p[2]>topo(p[0],p[1]):lo=m
        else:hi=m
    outc.append((a,(lo+hi)/2))
def vnorm(a,b,V_):
    e=0.5;p0=vpt(a,b,V_);pa=vpt(a+e,b,V_);pb=vpt(a,b+e,V_);u=pa-p0;w=pb-p0;n_=np.cross(u,w);n_=n_/np.linalg.norm(n_);return n_ if n_[2]>0 else -n_
def dipaz(n_):d=math.degrees(math.acos(min(1,abs(n_[2]))));az=(math.degrees(math.atan2(n_[0],n_[1]))+360)%360;return d,az
S=[];k=1
for a,b in outc[::3]:
    p=vpt(a,b,V,1.0);n_=vnorm(a,b,V);d,az=dipaz(n_);S.append([k,round(p[0],2),round(p[1],2),round(float(topo(p[0],p[1])),2),round(d+rng.normal(0,2)),round((az+rng.normal(0,3))%360),'kontak HW QV_Utama']);k+=1
for a,b in [(-40,90),(0,110),(40,95)]:  # struktur di kedalaman (dari core oriented)
    p=vpt(a,b,V,1.0);n_=vnorm(a,b,V);d,az=dipaz(n_);S.append([k,round(p[0],2),round(p[1],2),round(float(p[2]),2),round(d),round(az),'kontak HW (core oriented)']);k+=1
for i in range(5):
    x=E0+rng.uniform(-120,120);y=N0+rng.uniform(-120,120);S.append([k,round(x,2),round(y,2),round(float(topo(x,y)),2),round(rng.uniform(70,88)),round(rng.uniform(20,60)),'kekar']);k+=1
write('SIM_struktur.csv',['No','X','Y','Z','Dip','Dip_Azimuth','Keterangan'],S)
P=[];k=1
for a,b in outc:
    for side,code in [(1.0,'VEIN_HW'),(-1.0,'VEIN_FW')]:
        p=vpt(a,b,V,side);P.append(['P%03d'%k,round(p[0]+rng.normal(0,0.05),3),round(p[1]+rng.normal(0,0.05),3),round(float(topo(p[0],p[1])),3),code]);k+=1
P.sort(key=lambda r:(r[4],int(r[0][1:])))
for code,R in [('TOE',35.0),('CREST',47.0)]:
    for t in np.linspace(0,2*np.pi,25)[:-1]:
        x=E0-60+R*1.3*math.cos(t);y=N0+70+R*math.sin(t);P.append(['P%03d'%k,round(x,3),round(y,3),round(float(topo(x,y))-(6 if code=='TOE' else 0),3),code]);k+=1
write('SIM_pickup_survey.csv',['ID','East','North','RL','Code'],P)
with open(os.path.join(OUTD,'BACA_SAYA.txt'),'a') as f:f.write('\n'.join(['','STRUKTUR & PICK-UP (latihan menu Struktur & Map):',
 'SIM_struktur.csv        : %d titik struktur (No, X, Y, Z, Dip, Dip_Azimuth, Keterangan): kontak HW di singkapan, 3 dari core oriented, 5 kekar'%len(S),
 'SIM_pickup_survey.csv   : %d titik pick-up (ID, East, North, RL, Code): VEIN_HW / VEIN_FW singkapan QV_Utama, TOE / CREST pit kecil'%len(P)])+'\n')
print('struktur',len(S),'pickup',len(P))

# ---------- latihan validasi: salinan database dengan kesalahan sengaja ----------
import csv as _csv
_c=list(_csv.reader(open(os.path.join(OUTD,'SIM_collar.csv'))));_c.append(['SIM-X01','','9012000','300','50']);_c.append(_c[1][:])
with open(os.path.join(OUTD,'SIM_rusak_collar.csv'),'w',newline='') as f:_csv.writer(f).writerows(_c)
_a=list(_csv.reader(open(os.path.join(OUTD,'SIM_assay.csv'))));_h=_a[0];_b=_a[1:]
_b.append([_b[0][0],'5','5','X-001','0.10','1.0','0.20']);_b.append([_b[0][0],'10.5','11.5',_b[11][3],'0.30','1.0','0.20']);_b.append(['SIM-X99','0','1','X-002','0.2','1','0.1']);_b.append([_b[40][0],'40','41','X-003','-99','1','0.1'])
with open(os.path.join(OUTD,'SIM_rusak_assay.csv'),'w',newline='') as f:_csv.writer(f).writerows([_h]+_b)
with open(os.path.join(OUTD,'BACA_SAYA.txt'),'a') as f:f.write('SIM_rusak_collar.csv / SIM_rusak_assay.csv : database dengan kesalahan sengaja (latihan Validasi data bor)\n')
