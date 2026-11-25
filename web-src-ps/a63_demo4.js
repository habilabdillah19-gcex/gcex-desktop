/* a63: DEMO diperbarui (24 Nov) — semua desain demo memakai geoteknik lebih kompleks + fitur 22–24 Nov:
   - Bab B (pit final) & bab I (pit dua lantai): langkah baru "Geoteknik per bench" (menu Desain → Geoteknik per bench / RL):
     bench oksida atas muka landai, catch berm, bench lapisan lemah memakai nilai zona sesar, bench dasar tanpa berm.
     dmFinalDesign (dipakai bab C–H) & staging bab C memakai tabel yang sama → semua pit final & staging demo ikut.
   - Bab M: langkah 3 memakai cara gali baru (Klik blok · Otomatis · Tarik jalur alat) + penurunan terkendali (blok yang sudah
     dipilih tidak bisa dipilih lagi sebelum ▶ Jalankan) + hasil rencana per periode.
   - Bab N (baru): warna & hillshade topografi, label adaptif, Block model 3D (warna kelas / gradasi, filter), Putus & Sambung instan. */
const DGB_B=[{z:335,A:55},{z:330,A:55},{z:300,bt:'catch'},{z:290,bt:'std'},{z:285,zn:'Zona 3 · Barat (zona sesar)'},{z:270,bt:'catch'},{z:240,bt:'none'}];
const DGB_I=[{z:250,A:60},{z:220,bt:'catch'}];
function dmGbApply(rows,H){H=H||PN().H;OVR=OVR.filter(o=>!o.bench);for(const r of rows){const o={z0:r.z,z1:r.z+H,A:isFinite(r.A)?r.A:NaN,B:NaN,N:NaN,bench:true,bt:r.bt||'',zn:r.zn||''};o.B=gbB(o);o.N=o.bt?1:NaN;OVR.push(o);}try{ovrDraw();prmUpd();}catch(_){}}
async function dmGbShow(rows,title,sub,txt){if(DMO.spd>=30){dmGbApply(rows,PN().H);return;}
 await dmCap(title,sub,txt);dmWin();
 const mb=[...document.querySelectorAll('.shmt')].find(b=>b.textContent==='Desain');if(mb){await dmClick(mb,{noFire:true});mb.click();await dW(500);const it=document.querySelector('[data-a=geob]');if(it){await dmClick(it,{noFire:true});it.click();}}else winShow($('ovw'),true);
 dmWin('ovw');winShow($('ovw'),true);gbDraw();await dW(500);
 await dmClick('#gbfill',{noFire:true});OVR=OVR.filter(o=>!o.bench);const R=gbRange();if(R){for(let z=R.zb;z<R.zt+R.H-1e-6;z+=R.H)OVR.push({z0:z,z1:z+R.H,A:NaN,B:NaN,N:NaN,bench:true,bt:'',zn:''});}gbDraw();prmUpd();await dW(700);
 const row=z=>[...document.querySelectorAll('#gbt tbody tr')].find(tr=>tr.firstChild&&tr.firstChild.textContent.startsWith(Math.round(z)+'–'));
 for(const r of rows){let tr=row(r.z);if(!tr){const o={z0:r.z,z1:r.z+PN().H,A:NaN,B:NaN,N:NaN,bench:true,bt:'',zn:''};OVR.push(o);gbDraw();tr=row(r.z);}if(!tr)continue;
  try{tr.scrollIntoView({block:'nearest'});}catch(_){}await dW(150);
  const set=async(sel,v)=>{const e=row(r.z)&&row(r.z).querySelector(sel);if(!e)return;await dmClick(e,{noFire:true});e.value=v;e.dispatchEvent(new Event('change'));await dW(420);};
  if(r.bt)await set('[data-g=bt]',r.bt);if(r.zn)await set('[data-g=zn]',r.zn);if(isFinite(r.A))await set('[data-g=A]',r.A);}
 await dW(500);await dmShot('GB_'+title.slice(0,1),['#gbw','#gbbs','#gbbc']);await dW(900);dmWin();}
/* ---------- B & I: sisipkan langkah per bench sebelum langkah Jalan ---------- */
function dmGbHook(id,before,rows,cap){const C=DMCH.find(c=>c.id===id);if(!C)return;const run0=C.run;C.run=async()=>{const c0=dmCap;let done=false;
 dmCap=async(a,b,c)=>{if(!done&&a===before){done=true;dmCap=c0;try{await dmGbShow(rows,cap[0],cap[1],cap[2]);}finally{dmCap=wrap;}}return c0(a,b,c);};const wrap=dmCap;
 try{await run0();}finally{dmCap=c0;}};}
dmGbHook('B','B · 3 Jalan',DGB_B,['B · 2 Geoteknik','Geoteknik per bench / RL','Menu Desain → Geoteknik per bench: Isi daftar bench, lalu atur bench tertentu — 2 bench atas (oksida) muka 55°, catch berm 8 m di crest RL 275 & 305, berm standar di crest RL 295, bench RL 285 memakai nilai zona sesar di seluruh keliling, bench dasar tanpa berm. Kolom kosong tetap ikut zona poligon.']);
dmGbHook('I','I · 3 Jalan',DGB_I,['I · 2 Geoteknik','Geoteknik per bench','Bench teratas (oksida) muka 60°; catch berm di crest RL 230. Bench lain ikut parameter umum.']);
{const _f=dmFinalDesign;dmFinalDesign=async function(){dmGbApply(DGB_B,DGEO.pH);return _f.apply(this,arguments);};}
{const C=DMCH.find(c=>c.id==='C');if(C){const run0=C.run;C.run=async()=>{dmGbApply(DGB_B,DGEO.pH);const c0=dmCap;dmCap=async(a,b,c)=>c0(a,b,String(c||'').replace('Empat domain geoteknik bab B tetap berlaku untuk dinding staging.','Empat domain + tabel per bench bab B (oksida 55°, catch berm, bench zona sesar) tetap berlaku untuk dinding staging.'));try{await run0();}finally{dmCap=c0;}};}}
{const B=DMCH.find(c=>c.id==='B');if(B){const run0=B.run;B.run=async()=>{const c0=dmCap;dmCap=async(a,b,c)=>c0(a,b,a==='B · Hasil'&&b==='Pit final terbentuk'?'Ringkasan: bench, volume, kedalaman, lantai, jalan — dinding tiap domain mengikuti sudut & berm-nya sendiri; bench oksida lebih landai, catch berm lebih lebar, bench dasar tanpa berm.':c);try{await run0();}finally{dmCap=c0;}};}}
/* ---------- Bab N: fitur tampilan & edit baru ---------- */
DMCH.push({id:'N',nm:'Fitur baru: warna topografi & hillshade, Block model 3D, Putus & Sambung instan',run:async()=>{
 const ok=()=>{try{return !!RES&&TP.some(t=>/topo_latihan_dua_lantai/.test(t.nm))&&!!GT.file;}catch(_){return false;}};
 if(!ok()){await dmCap('Fitur baru','Menyiapkan pit latihan','Memakai topografi & pit dua lantai fiktif dari bab I + block model fiktif — dijalankan cepat lebih dulu.');const sp=DMO.spd,cp0=dmCap,sh=dmShot;DMO.spd=60;dmCap=async()=>{};dmShot=async()=>{};try{await window.__PS3.demo.prepK();}finally{DMO.spd=sp;dmCap=cp0;dmShot=sh;}}
 try{schOpen(false);gtBig(false);gtOpen(false);$('mbw').style.display='none';}catch(_){}dmWin();
 const menu=async(nm,sel)=>{const mb=[...document.querySelectorAll('.shmt')].find(b=>b.textContent===nm);if(!mb)return;await dmClick(mb,{noFire:true});mb.click();await dW(600);const it=document.querySelector(sel);if(it){await dmClick(it,{noFire:true});it.click();}await dW(500);};
 const cv=(x,y)=>{try{R.domElement.dispatchEvent(new PointerEvent('pointermove',{clientX:x,clientY:y,bubbles:true}));}catch(_){}};
 /* 1 warna topografi */
 await dmCam([600950,9200950,260,1250,0.55],1300);
 await dmCap('N · Tampilan','Warna & hillshade topografi','Tampilan → Kamera & tampilan 3D → Warna topografi: skema elevasi, hillshade (arah & tinggi matahari, kekuatan), garis kontur. Pilihan diingat.');
 await menu('Tampilan','[data-w=vw2]');dmWin('vw2');winShow($('vw2'),true);const tw=$('tpcw');if(tw){tw.open=true;await dmClick(tw.querySelector('summary'),{noFire:true});}await dW(500);
 const sel=async(id,v,ev)=>{const e=$(id);if(!e)return;await dmClick(e,{noFire:true});e.value=v;e.dispatchEvent(new Event(ev||'change'));await dW(1300);};
 await sel('tpcsk','spektrum');await sel('tpcsk','tanah');await sel('tpcaz','135','input');await sel('tpcaz','315','input');await sel('tpcsk','alami');await dmShot('N01_warna_topo',['#tpcw']);
 await dmCap('N · Tampilan','Label RL adaptif','Label RL, lantai dan simpang tanpa latar: ukurannya menyesuaikan zoom, label yang bertumpuk disembunyikan otomatis.');dmWin();
 await dmCam([600950,9200950,230,520,0.8],1500);await dW(900);await dmCam([600950,9200950,240,1500,0.6],1500);await dW(900);await dmCam([600800,9200800,230,700,0.75],1400);
 /* 2 block model 3D */
 await dmCap('N · Block model 3D','Tampilan → Block model 3D','Blok .mdl di dalam desain terpilih (Pit final, Staging, Pit hasil edit, Pit sedang diedit) — aturan sama dengan Laporan Grade × Tonnage desain: pusat blok di antara topografi dan desain.');
 await menu('Tampilan','[data-a=bm3d]');for(let i=0;i<60&&(B3.busy||!B3.sel);i++)await dRaw(200);dmWin('b3w');winShow($('b3w'),true);await dW(1600);await dmShot('N02_bm3d_kelas',['#b3b']);
 await dmCap('N · Block model 3D','Warna kelas · klik untuk sembunyikan','Klik kelas di legenda untuk menyembunyikan / menampilkan — di sini waste disembunyikan sehingga tinggal LG & HG.');
 {const w=document.querySelector('#b3b .lg[data-k="'+GT.rules.length+'"]');if(w){await dmClick(w,{noFire:true});B3.hide[GT.rules.length]=true;b3Save();await b3Run();}}await dW(1800);
 {const w=document.querySelector('#b3b .lg[data-k="'+GT.rules.length+'"]');if(w){await dmClick(w,{noFire:true});B3.hide[GT.rules.length]=false;b3Save();await b3Run();}}await dW(600);
 await dmCap('N · Block model 3D','Gradasi atribut & filter RL','Warna gradasi kadar (skema & batas bisa diatur). Filter RL s/d 230 = sayat horizontal; kursor di atas blok = isi blok.');
 {const r=document.querySelector('#b3b [name=b3m][value=grad]');if(r){await dmClick(r,{noFire:true});B3.mode='grad';b3Save();b3Draw();b3Ui();}}await dW(1500);
 {const d=document.querySelector('#b3b details:nth-of-type(2)');if(d)d.open=true;b3Ui();}{const e=$('b3zhi');if(e){await dmClick(e,{noFire:true});B3.zhi='230';b3Save();await b3Run();}}await dW(1200);
 if(B3.mesh&&B3.sel&&B3.sel.length){const m=GT.m,b=B3.sel[B3.sel.length>>1],q=dmScr(m.x[b],m.y[b],m.z[b]+m.sz[b]/2);await dmMove(q[0],q[1],900);for(let k=0;k<4;k++){cv(q[0]+k,q[1]);await dW(120);}await dW(2200);}
 await dmShot('N03_bm3d_gradasi',['#b3b']);B3.zhi='';B3.mode='kelas';b3Save();b3Off();dmWin();
 /* 3 putus & sambung instan */
 await dmCap('N · Edit manual','Putus instan','Tab Edit pit → pilih Pit final → tombol Putus: klik ruas string mana pun → langsung terputus (ruas di bawah kursor disorot merah). Kursor di atas string = sorot seluruh string + kedua ujungnya.');
 try{document.querySelector('#mode [data-m=edit]').click();}catch(_){}await dW(900);try{const b=document.querySelector('#epwb [data-ep=res]');if(b){await dmClick(b,{noFire:true});b.click();}}catch(_){}for(let i=0;i<30&&!ED;i++)await dRaw(200);await dW(800);dmWin();
 let si=-1,S=mwS();for(let i=0;i<S.length;i++)if(S[i].closed&&S[i].pts.length>30&&S[i].z<=232&&S[i].z>=218){si=i;break;}if(si<0)si=S.findIndex(s=>s.closed&&s.pts.length>20);
 if(si>=0){const s=S[si],i0=Math.floor(s.pts.length*0.3),a=s.pts[i0],b2=s.pts[i0+1],mx=(a[0]+b2[0])/2,my=(a[1]+b2[1])/2,mz=(a[2]+b2[2])/2;
  await dmCam([mx,my,mz,170,0.55],1500);{const q=dmScr(s.pts[i0+8][0],s.pts[i0+8][1],s.pts[i0+8][2]);await dmMove(q[0],q[1],800);for(let k=0;k<3;k++){cv(q[0]+k,q[1]);await dW(150);}await dW(1600);}
  const pb=[...document.querySelectorAll('button.tb')].find(x=>/Putus/.test(x.textContent));if(pb){await dmClick(pb,{noFire:true});putSet(true);}await dW(500);
  {const q=dmScr(mx,my,mz);await dmMove(q[0],q[1],900);PUT.k='';putHl({si,i:i0});await dW(900);dmRip();putHl(null);putCut({si,i:i0});await dW(1300);}putSet(false);
  const s2=mwS()[si];if(s2&&!s2.closed){const e0=s2.pts[0],e1=s2.pts[s2.pts.length-1];
   await dmCap('N · Edit manual','Sambung instan','Tombol Sambung tanpa pilihan = mode Sambung: klik ujung string pertama, lalu ujung string kedua (atau ujung lain string yang sama) → langsung tersambung lagi.');
   {const q=dmScr(e1[0],e1[1],e1[2]);await dmMove(q[0],q[1],700);for(let k=0;k<3;k++){cv(q[0]+k,q[1]);await dW(150);}await dW(1400);}
   const sb=[...document.querySelectorAll('button.tb')].find(x=>/Sambung/.test(x.textContent));if(sb){await dmClick(sb,{noFire:true});smbSet(true);}await dW(400);
   {const q=dmScr(e0[0],e0[1],e0[2]);await dmMove(q[0],q[1],800);dmRip();SMB.a={i:si,j:0};smbMark();await dW(1000);}
   {const q=dmScr(e1[0],e1[1],e1[2]);await dmMove(q[0],q[1],800);dmRip();const a=SMB.a;SMB.a=null;smbMark();try{smbJoin(a,{i:si,j:mwS()[si].pts.length-1});}catch(e){console.warn(e);}await dW(1500);}smbSet(false);}
  await dmShot('N04_putus_sambung');}
 try{hovClr();}catch(_){}try{document.querySelector('#mode [data-m=new]').click();}catch(_){}await dW(600);dmWin();await dmCam([600950,9200950,260,1250,0.55],1300);
 await dmCap('Selesai','Ringkasnya','Geoteknik per bench / RL, cara gali Klik blok terkendali, warna & hillshade topografi, label adaptif, Block model 3D, Putus & Sambung instan.');}});
try{const w=$('dmoList');if(w){w.innerHTML=DMCH.map((c,i)=>'<div class="fl"><button class="sm" data-dmo="'+i+'">&#9654; '+c.id+'</button><span>&nbsp;'+esc(c.nm)+'</span></div>').join('');w.querySelectorAll('[data-dmo]').forEach(b=>b.onclick=()=>dmoPlay(+b.dataset.dmo,+b.dataset.dmo+1));}}catch(e){}
try{window.__PS3.dgb={B:DGB_B,I:DGB_I};}catch(_){}
