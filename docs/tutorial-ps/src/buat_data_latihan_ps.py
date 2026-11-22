"""Data latihan FIKTIF Pit Studio: block model Surpac .mdl (Version 4.0) untuk laporan grade x tonnage.

  python docs/tutorial-ps/src/buat_data_latihan_ps.py [folder_keluaran]     (bawaan: docs/tutorial-ps/data)

Dua urat emas REKAAN arah timur-barat di area topografi latihan "dua lantai" (koordinat rekaan). Blok 5 x 5 x 2,5 m,
atribut au (g/t), sg, sxs dan atribut kalkulasi kelas = IIF(au<0.4,"WASTE",IIF(au<1,"LG","HG")).
Topografi pasangannya (PS_topo_latihan_dua_lantai.str) dibuat Pit Studio sendiri: Demo bab I."""
import struct,math,random,sys
random.seed(7)
def i32(v):return struct.pack('>i',v)
def f64(v):return struct.pack('>d',v)
L=7;bs=(5.0,5.0,2.5);O=(600480.0,9200480.0,100.0);RT=tuple(b*2**L for b in bs)
attrs=[('au',0.0),('sg',2.6),('sxs',0.0)]
calc=[('kelas',"IIF(au<0.4,\"WASTE\",IIF(au<1,\"LG\",\"HG\"))")]
H=[b'### Block Model ###\nVersion 4.0\n',b'\0',b'PS_blockmodel_fiktif_dua_lantai.mdl',b'\0',b'\0',bytes(12)]
for v in O+RT+RT:H.append(f64(v))
H.append(i32(0));H.append(i32(len(attrs)+len(calc)))
for n,d in attrs:H+= [n.encode(),b'\0',i32(0),i32(2),i32(2),f64(d),b'\0']
for n,e in calc:H+= [n.encode(),b'\0',i32(1),i32(2),e.encode('latin1'),b'\0']
H.append(i32(0))
out=bytearray(b''.join(H))
def au_at(x,y,z):
  # dua urat E-W fiktif (dip ke utara) + latar rendah
  g=0.05+0.04*random.random()
  for y0,dip,w,pk in [(9200790,0.35,9,3.2),(9200840,0.25,6,1.6)]:
    yc=y0+(250-z)*dip; d=abs(y-yc)
    if d<w*2: g+=pk*math.exp(-(d/w)**2)*(0.7+0.6*random.random())*(0.8+0.4*math.sin((x-600500)/60))
  return max(0.0,g)
n=0
xi0=int((600500-O[0])/bs[0]);xi1=int((601100-O[0])/bs[0]);yi0=int((9200680-O[1])/bs[1]);yi1=int((9200930-O[1])/bs[1]);zi0=int((195-O[2])/bs[2]);zi1=int((255-O[2])/bs[2])
for ix in range(xi0,xi1):
 for iy in range(yi0,yi1):
  for iz in range(zi0,zi1):
   dg=0;ixb=0;lo=0
   for l in range(1,L+1):
     b=L-l;d=(((ix>>b)&1)<<2)|(((iy>>b)&1)<<1)|((iz>>b)&1)
     if l<=3:dg|=d<<(3*(l-1))
     elif l<=9:ixb|=d<<(3*(l-4))
     else:lo|=d<<(3*(l-10))
   hi=(ixb<<14)|(dg<<5)|L
   x=O[0]+(ix+.5)*bs[0];y=O[1]+(iy+.5)*bs[1];z=O[2]+(iz+.5)*bs[2]
   a=au_at(x,y,z);sx=min(3.0,0.3+a*0.25+0.2*random.random())
   out+=struct.pack('>II',hi,lo)+f64(round(a,3))+f64(round(2.55+0.1*min(1,a/2),3))+f64(round(sx,3));n+=1
out+=b'\xff'*8+bytes(16)
from pathlib import Path
out_dir=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/"data"
out_dir.mkdir(parents=True,exist_ok=True)
(out_dir/"PS_blockmodel_fiktif_dua_lantai.mdl").write_bytes(bytes(out))
print(n,"blok",len(out),"byte ->",out_dir/"PS_blockmodel_fiktif_dua_lantai.mdl")
