'use strict';
/* Geo Pocket — Demo terpandu (Bantuan → Demo). Semua data fiktif dan dibangkitkan di sini; tidak ada file luar. */
const DM={i:-1,el:null,g:{}};
function dmZ(x,y){const u=(x-10000)/400,v=(y-20000)/300;return 150+22*Math.sin(u*2.6)*Math.cos(v*2.1)+14*u-9*v+6*Math.sin(u*7+v*5);}
function dmRand(seed){let s=seed;return ()=>{s=(s*1664525+1013904223)%4294967296;return s/4294967296;};}
function dmLayer(g,file,fold){g.file=file;g.base=g.name.replace(/[^A-Za-z0-9_]+/g,'_');g.fold=fold?fold.id:null;S.geoms.push(g);return g;}
function dmScan(){const c=document.createElement('canvas');c.width=900;c.height=640;const x=c.getContext('2d');x.fillStyle='#F6F2E7';x.fillRect(0,0,900,640);
 /* afin gambar: piksel 0,5 m, sedikit miring (peta pindaian), menutupi area demo */
 const th=4*Math.PI/180,s=0.5,A=s*Math.cos(th),B=s*Math.sin(th),D=s*Math.sin(th),E=-s*Math.cos(th),X0=9990,Y0=20318,W=(u,v)=>[X0+A*(u-0.5)+B*(v-0.5),Y0+D*(u-0.5)+E*(v-0.5)];
 const det=A*E-B*D,I=(X,Y)=>{const dx=X-X0,dy=Y-Y0;return [(E*dx-B*dy)/det+0.5,(-D*dx+A*dy)/det+0.5];};
 x.strokeStyle='#8E8672';x.lineWidth=1;x.font='12px Arial';x.fillStyle='#5B5546';
 for(let gx=10000;gx<=10400;gx+=100){const a=I(gx,19990),b=I(gx,20310);x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.stroke();x.fillText(gx+' E',a[0]+4,a[1]-6);}
 for(let gy=20000;gy<=20300;gy+=100){const a=I(9995,gy),b=I(10420,gy);x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.stroke();x.fillText(gy+' N',a[0]+6,a[1]-6);}
 x.strokeStyle='#7A3E2A';x.lineWidth=3;x.beginPath();[[10040,20060],[10110,20120],[10190,20150],[10270,20210],[10360,20250]].forEach((p,k)=>{const q=I(p[0],p[1]);k?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]);});x.stroke();
 x.fillStyle='rgba(181,137,62,.35)';x.strokeStyle='#B5893E';x.lineWidth=2;x.beginPath();[[10220,20040],[10330,20050],[10350,20120],[10250,20130]].forEach((p,k)=>{const q=I(p[0],p[1]);k?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]);});x.closePath();x.fill();x.stroke();
 x.fillStyle='#3A3528';x.font='700 16px Arial';x.fillText('PETA GEOLOGI LAMA (fiktif) · pindaian',20,26);x.font='12px Arial';x.fillText('garis cokelat = urat kuarsa · arsir = zona alterasi',20,46);
 return {cv:c,gcp:[[10000,20000],[10400,20000],[10400,20300],[10000,20300],[10200,20200]].map(p=>{const q=I(p[0],p[1]);return {c:q[0],r:q[1],x:String(p[0]),y:String(p[1])};})};}
const DSTEP=[
 {t:'Data dari berbagai sumber, tersusun dalam folder',d:'Tiga lapisan fiktif dimuat ke Project Tree: string topografi (ala Surpac), titik sampel beratribut (ala tabel MapInfo), dan batas blok (ala DXF). Centang folder untuk menampilkan atau menyembunyikan isinya; seret untuk mengubah urutan.',
  run(){S.folders=[];S.geoms=[];S.sel=null;S.selF=null;S.selFold=null;S.undo=[];const f1=newFolder('Topografi',null,true),f2=newFolder('Sampel',null,true),f3=newFolder('Desain',null,true),R=dmRand(7);
   let gb=new GC.GB('Topografi (string)');for(let y=20000;y<=20300;y+=12){const id=[];for(let x=10000;x<=10400;x+=8)id.push(gb.add(x,y+3*Math.sin(x/40),dmZ(x,y)));gb.poly(id,false,[String(Math.round((y-20000)/12)+1)]);}
   const topo=gb.done('str',{cols:['STRING']});topo.color='#5A636B';M2.sty(topo).lw=0.8;
   gb=new GC.GB('Sampel permukaan');const lit=['Andesit','Tuf','Breksi','Urat kuarsa'];for(let k=0;k<70;k++){const x=10010+R()*380,y=20010+R()*280,near=Math.exp(-Math.pow((y-20000-(x-10000)*0.6-30)/35,2)),au=(0.02+near*R()*4.5).toFixed(2);gb.point(gb.add(x,y,dmZ(x,y)),['SP-'+String(k+1).padStart(3,'0'),lit[near>0.5?3:Math.floor(R()*3)],au]);}
   const smp=gb.done('tab',{cols:['Sample_ID','Litologi','Au_ppm']});smp.color='#2B5F9E';
   gb=new GC.GB('Batas blok');const blk=(n,P)=>gb.poly(P.map(p=>gb.add(p[0],p[1],dmZ(p[0],p[1]))),true,[n,'rencana']);blk('Blok A',[[10060,20050],[10170,20050],[10170,20130],[10060,20130]]);blk('Blok B',[[10170,20050],[10280,20050],[10280,20130],[10170,20130]]);
   const des=gb.done('dxf',{cols:['NAMA','KET']});des.color='#C2413B';M2.sty(des).lw=2;M2.sty(des).fill=0.12;M2.sty(des).label=0;
   S.geoms=[];dmLayer(des,'blok_rencana.dxf (fiktif)',f3);dmLayer(smp,'sampel_permukaan.tab (fiktif)',f2);dmLayer(topo,'topografi.str (fiktif)',f1);DM.g={topo,smp,des,f1,f2,f3};refreshAll();showTab('2d');setTool('pan');M2.fit();}},
 {t:'Topografi menjadi DEM dan kontur',d:'String topografi ditriangulasi (TIN, cara DTM Surpac) lalu dijadikan grid elevasi berwarna dan kontur 5 m. Di aplikasi: Analisis → Buat DEM dari topografi. Elevasi di bawah kursor tampil di status bar.',
  run(){const g=DM.g,tin=GC.buildTIN([g.topo],{step:2,factor:8}),dem=GC.tinToDEM(tin,1),d=GC.mk({name:'DEM topografi',src:'dem'});d.dem=dem;dem.cv=demCanvas(dem,'hyps');dmLayer(d,'(dari Topografi)',g.f1);
   const k=GC.contours(dem,5,'Kontur 5 m');k.color='#7A5A3A';M2.sty(k).lw=1;M2.sty(k).fill=0;const i=S.geoms.indexOf(g.topo);dmLayer(k,'(dari DEM)',g.f1);S.geoms.splice(S.geoms.indexOf(k),1);S.geoms.splice(i,0,k);g.topo.visible=false;g.dem=d;g.kon=k;refreshAll();select(d.id);M2.fit();}},
 {t:'Titik sampel diwarnai menurut kadar',d:'Titik diwarnai dari biru (rendah) ke merah (tinggi) menurut kolom Au_ppm dan diberi label. Klik sebuah titik untuk melihat semua atributnya di panel Properti. Di aplikasi: Properti → Gaya → Warna titik.',
  run(){const g=DM.g.smp,s=M2.sty(g);s.colorBy=2;s.pt=5;g._cb=null;let b=0;g.PA.forEach((a,k)=>{if(+a[2]>+g.PA[b][2])b=k;});S.sel=g.id;S.selF={g:g,type:'pt',i:b};select(g.id,true);M2.draw();}},
 {t:'Digitasi poligon, luas langsung terhitung',d:'Sebuah batas baru didigit mengikuti zona berkadar tinggi. Luas (m² dan hektare) dan keliling tampil di Properti, dan elevasi tiap sudut diambil dari DEM. Di aplikasi: tombol Poligon atau tekan P, klik sudut-sudutnya, Enter untuk selesai.',
  run(){const P=[[10085,20075],[10150,20105],[10215,20150],[10250,20195],[10215,20215],[10150,20175],[10075,20115]].map(p=>[p[0],p[1],dmZ(p[0],p[1])]);onDigit('poly',P);const g=S.geoms.find(x=>x.src==='digit');g.name='Zona target';g.P[0].attr=['Zona target','usulan bor'];g.color='#17806B';M2.sty(g).fill=0.25;M2.sty(g).label=0;g.fold=DM.g.f3.id;DM.g.dig=g;refreshAll();select(g.id,true);}},
 {t:'Georeferensi peta pindaian',d:'Gambar peta lama tanpa koordinat diberi 5 titik kontrol di perpotongan grid. Residu dan RMS menunjukkan ketelitiannya. Tekan Lanjut untuk menaruhnya di peta; hasilnya juga bisa diunduh sebagai GeoTIFF.',
  run(){const sc=dmScan();GR.img=sc.cv;GR.w=sc.cv.width;GR.h=sc.cv.height;GR.nm='peta_geologi_lama';GR.p=sc.gcp;GR.T=null;GR.sel=-1;dlgGeoref();},
  done(){const b=document.getElementById('grgo');if(b)b.click();const g=S.geoms.find(x=>x.src==='georef');if(g){g.opacity=0.75;g.fold=DM.g.f1.id;DM.g.geo=g;if(DM.g.dem)DM.g.dem.visible=false;refreshAll();M2.fit();}}},
 {t:'Tabel luas siap diunduh',d:'Setiap poligon punya panjang keliling dan luas, dengan total di atas tabel. Klik baris untuk menyorot fiturnya; klik ganda untuk memperbesar. Tombol Unduh CSV menyimpan tabelnya.',
  run(){if(DM.g.dem)DM.g.dem.visible=true;if(DM.g.geo)DM.g.geo.visible=false;S.view='pl';select(DM.g.des.id);showTab('tbl');}},
 {t:'Layout peta siap cetak',d:'Peta kerja disusun menjadi halaman A4 dengan skala, grid koordinat, arah utara, legenda, dan blok judul. Unduh sebagai PDF atau PNG. Di aplikasi: tombol Layout di atas peta.',
  run(){showTab('2d');M2.fit();LY.paper='A4';LY.land=true;LY.scale=0;LY.title='PETA ZONA TARGET (DEMO)';LY.sub='Data fiktif Geo Pocket';LY.no='DEMO-01';setTimeout(dlgLayout,150);},
  done(){const m=document.querySelector('.modal');if(m)m.remove();}},
 {t:'Konversi ke software lain',d:'Pilih tujuan (Leapfrog, Surpac, MapInfo, Global Mapper, Google Earth) dan format yang disarankan muncul. Di sini batas blok siap ditulis sebagai string Surpac. Demo selesai: data demo boleh dicoba-coba, atau dikosongkan.',
  run(){C.soft='Surpac';C.fmt='str';C.off=new Set(S.geoms.filter(g=>g!==DM.g.des&&g!==DM.g.dig).map(g=>g.id));showTab('conv');}}
];
function dmShow(){const st=DSTEP[DM.i],el=DM.el,last=DM.i===DSTEP.length-1;el.querySelector('.dmn').textContent='Demo · langkah '+(DM.i+1)+' dari '+DSTEP.length;el.querySelector('.dmt').textContent=st.t;el.querySelector('.dmd').textContent=st.d;
 el.querySelector('.dmbar i').style.width=((DM.i+1)/DSTEP.length*100)+'%';el.querySelector('#dmnext').textContent=last?'Selesai':'Lanjut';el.querySelector('#dmclr').style.display=last?'':'none';}
function dmGo(){const prev=DSTEP[DM.i];try{if(prev&&prev.done)prev.done();}catch(e){msg('Demo: '+e.message,'w');}
 DM.i++;if(DM.i>=DSTEP.length){dmStop(false);return;}dmShow();try{DSTEP[DM.i].run();}catch(e){msg('Demo langkah '+(DM.i+1)+': '+e.message,'e');}}
function dmStop(clear){const m=document.querySelector('.modal');if(m)m.remove();if(DM.el){DM.el.remove();DM.el=null;}DM.i=-1;if(clear){clearAll();showTab('2d');}else msg('Demo selesai. Data demo (fiktif) masih terbuka; kosongkan lewat Berkas → Kosongkan semua.');}
function startDemo(){if(DM.el)return;if(S.geoms.length&&!confirm('Demo memakai data fiktif dan akan mengosongkan lapisan yang sedang terbuka. Lanjutkan?'))return;
 const el=document.createElement('div');el.id='demo';el.innerHTML='<div class="dmbar"><i></i></div><div class="dmb"><div class="dmn"></div><div class="dmt"></div><div class="dmd"></div><div class="dmr"><button class="btn" id="dmnext">Lanjut</button><button class="btn2" id="dmclr" style="display:none">Selesai &amp; kosongkan data demo</button><span style="flex:1"></span><button class="btn2" id="dmstop">Hentikan demo</button></div></div>';
 document.body.append(el);DM.el=el;el.querySelector('#dmnext').onclick=dmGo;el.querySelector('#dmstop').onclick=()=>dmStop(false);el.querySelector('#dmclr').onclick=()=>dmStop(true);DM.i=-1;DM.g={};dmGo();}
