/* a89 · Demo bab P — pembaruan 26 Nov 2026 (pemilik: "Update kembali tombol demonya").
   Isi: laporan block model dibatasi poligon (digit · di dalam / di luar · pilih string di 3D · blok mining dari berkas .str) ·
   kategori ore (Oxide / Sulfide dari atribut block model) · sayat horizontal di RL saat mendigit dasar pit.
   Gaya sama dengan bab O: angka diketik, kursor berjalan ke tiap tombol, kamera selalu bertransisi. Data seluruhnya fiktif. */
DMCH.push({id:'P',nm:'Laporan block model: batas poligon / string 3D / blok mining, kategori ore, sayat di RL',run:async()=>{
 const ok=()=>{try{return !!RES&&TP.some(t=>/topo_latihan_dua_lantai/.test(t.nm))&&!!GT.file;}catch(_){return false;}};
 if(!ok()){await dmCap('Laporan block model','Menyiapkan pit latihan','Memakai topografi & pit dua lantai fiktif dari bab I + block model fiktif — dijalankan cepat lebih dulu.');const sp=DMO.spd,cp0=dmCap,sh=dmShot;DMO.spd=60;dmCap=async()=>{};dmShot=async()=>{};try{await window.__PS3.demo.prepK();}finally{DMO.spd=sp;dmCap=cp0;dmShot=sh;}}
 let GK=0;const guard=async f=>{GK++;if(window.__PONLY&&!window.__PONLY.includes(GK))return;try{await f();}catch(e){if(e===DMO_STOP||e===DMO_SKIP)throw e;console.warn('demo P',e);}};
 const see=async e=>{try{if(typeof e==='string')e=document.querySelector(e);if(e){e.scrollIntoView({block:'center'});await dW(350);}}catch(x){if(x===DMO_STOP||x===DMO_SKIP)throw x;}};
 /* tunggu laporan selesai dihitung (waktu nyata, tidak ikut kecepatan demo) */
 const rep=async()=>{await dRaw(350);for(let k=0;k<120&&(GP.run||GT.busy);k++)await dRaw(250);await dRaw(450);};
 const win=()=>{const w=$('bmw');if(w&&!w.classList.contains('docked')&&!w.classList.contains('dkd')){if(!w._w0)w._w0=w.style.width||' ';w.style.width='440px';w.style.left=(innerWidth-460)+'px';w.style.top='250px';w.style.right='auto';}},winX=()=>{try{const w=$('bmw');return w&&w.style.display!=='none'?w.getBoundingClientRect().left-12:innerWidth;}catch(_){return innerWidth;}},winBack=()=>{try{const w=$('bmw');if(w&&w._w0){w.style.width=w._w0.trim();w._w0=null;}}catch(_){}};
 /* kamera: pit dibingkai di bagian kanvas yang TIDAK tertutup jendela Block model (jendela mengambang selalu di dalam kanvas) */
 const camL=async(c,ms)=>{await dmCam(c,ms);try{C.updateMatrixWorld();const r=cv.getBoundingClientRect(),sh=(r.left+r.width/2)-(r.left+Math.min(winX(),r.right))/2;if(sh>20){const R0=new THREE.Vector3().setFromMatrixColumn(C.matrixWorld,0),d=C.position.distanceTo(CT.target),wpp=C.isPerspectiveCamera?2*d*Math.tan(C.fov*Math.PI/360)/(r.height||800):1;await dmCam([c[0]+R0.x*sh*wpp,c[1]-R0.z*sh*wpp,c[2],c[3],c[4]],650);}}catch(e){if(e===DMO_STOP||e===DMO_SKIP)throw e;}};
 const to=async(E,N,ms)=>{const p=gpPx(E,N,gpZ(E,N));if(p)await dmMove(p[0],p[1],ms||650);return p;};
 const off=()=>{try{if(GP.on)gpEnd(false);gpPkEnd();GP.act=[];GP.set=[];GP.setNm='';GT.polyOut=false;gpSync(false);}catch(_){}};
 /* kotak pit latihan (dari string desain) → poligon contoh selalu jatuh di atas pit */
 const BB=(()=>{let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;try{for(const q of RES.S)for(const p of q.pts){if(p[0]<x0)x0=p[0];if(p[0]>x1)x1=p[0];if(p[1]<y0)y0=p[1];if(p[1]>y1)y1=p[1];}}catch(_){}if(!(x0<x1)){x0=600700;x1=601200;y0=9200700;y1=9201300;}return {x0,x1,y0,y1,w:x1-x0,h:y1-y0};})();
 try{schOpen(false);gtBig(false);$('mbw').style.display='none';}catch(_){}dmWin();try{cmClose();shClose();}catch(_){}
 if(MODE==='edit'){try{$('tabs').querySelector('[data-t="design"]').click();}catch(_){}await dW(500);}

 /* ---- 1. laporan desain + batas poligon digit ---- */
 await guard(async()=>{off();gtOpen(true);dmWin('bmw');win();await camL([600950,9200950,235,1750,0.6],1400);await dW(600);
  await dmCap('P · Laporan block model','Laporan desain','Jendela Block model → Laporan desain: ton & kadar per kelas, waste, SR per bench — untuk SELURUH desain yang dipilih.');
  await see('#gdgo');await dmClick('#gdgo');await rep();await see('#gdtb');await dW(1400);await dmShot('P01_laporan_desain',['#bmw']);
  await dmCap('P · Batas poligon','Digit poligon','Seperti constraint di Surpac: laporan dibatasi poligon yang didigit saat itu. Blok dihitung bila pusatnya di dalam poligon. Jendela jadi tembus-klik selama mendigit.');
  await see('#gpdg');await dmClick('#gpdg');await dW(500);
  for(const q of [[BB.x0+BB.w*.08,BB.y0+BB.h*.05],[BB.x0+BB.w*.42,BB.y0+BB.h*.05],[BB.x0+BB.w*.42,BB.y0+BB.h*.5],[BB.x0+BB.w*.08,BB.y0+BB.h*.5]]){await to(q[0],q[1],700);dmRip();GP.pts.push(q);gpDraw();gpUi();gpBar('dig');await dW(450);}
  await dmShot('P02_digit_poligon');await dmClick('#gpbok');await rep();win();await see('#gpst');await dW(1600);await dmShot('P03_laporan_dalam_poligon',['#bmw']);
  await dmCap('P · Batas poligon','Di dalam / di luar','Pilihan muncul begitu ada batas: "di luar" menghitung sisa desain di LUAR poligon (constraint OUTSIDE). Dalam + luar = seluruh desain.');
  const io=$('gpio');if(io){await dmPoint(io,650);dmRip();io.value='1';io.dispatchEvent(new Event('change'));await rep();await see('#gdsum');await dW(1700);await dmShot('P04_di_luar_poligon',['#bmw']);await dmPoint(io,400);dmRip();io.value='0';io.dispatchEvent(new Event('change'));await rep();}
  await dmClick('#gpdel');await rep();await dW(600);});

 /* ---- 2. pilih string yang tampil di 3D ---- */
 await guard(async()=>{off();gtOpen(true);dmWin('bmw');win();await camL([600950,9200950,232,1650,0.66],1300);
  await dmCap('P · Batas dari string','Pilih string di 3D','String yang sudah tampil — crest / toe, garis potong topo, blok tambang, pit impor — bisa langsung ditunjuk sebagai batas. Kursor menyorot kuning; Ctrl+klik menambah / melepas.');
  await see('#gppk');await dmClick('#gppk');await dW(500);let done=false;
  const S=(RES&&RES.S||[]).filter(s=>s.pts&&s.pts.length>12).sort((a,b)=>gpArea(b.pts)-gpArea(a.pts));
  for(const s of S.slice(1,8)){if(done)break;for(let i=0;i<s.pts.length&&!done;i+=Math.max(1,Math.floor(s.pts.length/9))){const p=s.pts[i],px=gpPx(p[0],p[1],p[2]);if(!px||px[0]>winX()||px[0]<300||px[1]<140)continue;let h=null;try{h=gpPick({clientX:px[0],clientY:px[1]});}catch(_){}
    if(h&&!h.bad&&h.lab==='string 3D'){await dmMove(px[0],px[1],900);GP.hov=h;gpHov();await dW(1300);await dmShot('P05_sorot_string');dmRip();gpTake(h,false);done=true;}}}
  await rep();await see('#gpst');await dW(1600);await dmShot('P06_laporan_dalam_string',['#bmw']);await dmClick('#gppk');await dW(400);await dmClick('#gpdel');await rep();});

 /* ---- 3. blok mining dari berkas .str ---- */
 await guard(async()=>{off();gtOpen(true);dmWin('bmw');win();await camL([600950,9200960,235,1800,0.6],1300);
  await dmCap('P · Blok mining','Impor poligon blok (.str / .dxf)','Berkas berisi banyak poligon (blok / strip mining) tampil di 3D berlabel nomor string. Klik DI DALAM blok yang mau dihitung sisa cadangannya; Ctrl+klik menambah blok.');
  const L=['blok_mining_fiktif, 26-Nov-26, , data latihan fiktif','0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000'],B=[];for(let i=0;i<4;i++){const sw=Math.round(BB.w/4),x0=Math.round(BB.x0)+i*sw,ya=Math.round(BB.y0-20),yb=Math.round(BB.y1+20),r=[[x0,ya],[x0+sw,ya],[x0+sw,yb],[x0,yb]];B.push(r);for(const p of r.concat([r[0]]))L.push((i+1)+', '+p[1].toFixed(3)+', '+p[0].toFixed(3)+', 100.000, ');L.push('0, 0.000, 0.000, 0.000,');}L.push('0, 0.000, 0.000, 0.000, END');
  await see('#gpimb');await dmPoint('#gpimb',700);dmRip();await gpImport(new File([L.join('\n')+'\n'],'blok_mining_fiktif.str'));await rep();await dW(1500);await dmShot('P07_blok_mining_tampil');
  const cen=r=>[r.reduce((a,p)=>a+p[0],0)/r.length,r.reduce((a,p)=>a+p[1],0)/r.length];
  for(const [i,add] of [[1,false],[2,true]]){const c=cen(B[i]);await to(c[0],c[1],850);const it=GP.set[i];GP.hov=it;gpHov();await dW(700);dmRip();gpTake(it,add);await rep();await dW(1100);}
  await see('#gpst');await dmShot('P08_blok_2_dan_3',['#bmw']);
  await dmCap('P · Blok mining','Semua · Kosongkan · Selesai','Bilah di atas kanvas: "Semua" memilih seluruh blok, "Kosongkan" melepas pilihan. Ringkasan otomatis di kiri atas tetap untuk seluruh desain.');
  if($('gpball')){await dmClick('#gpball');await rep();await dW(1300);}if($('gpbok')){await dmClick('#gpbok');await dW(400);}
  await dmClick('#gpdel');await rep();await dW(500);if($('gpdel')&&$('gpdel').style.display!=='none'){await dmClick('#gpdel');await dW(600);}});

 /* ---- 4. kategori ore ---- */
 await guard(async()=>{off();gtOpen(true);dmWin('bmw');win();
  await dmCap('P · Kategori ore','Oxide / Sulfide dari atribut block model','Pengganti centang "sulfida": pilih SATU atribut block model (unsur atau kode), tentukan rentang tiap kategori — semua laporan block model dan CSV dipecah per kategori.');
  const kd=$('gtkd');if(kd)kd.open=true;await see('#gtsfo');const cb=$('gtsfo');if(cb&&!cb.checked){await dmClick(cb);await rep();}await see('#gtct');await dW(900);
  await dmType('[data-ci="0"][data-k="hi"]','1');await rep();await see('#gtct');await dmType('[data-ci="1"][data-k="lo"]','1');await rep();await dW(700);await dmShot('P09_kategori_ore',['#gtct']);
  if(!GT.dres){await see('#gdgo');await dmClick('#gdgo');await rep();}await see('#gdtb');await dW(1900);await dmShot('P10_laporan_per_kategori',['#bmw']);
  await dmCap('P · Kategori ore','Baris ↳ per kategori','Di bawah tiap bench dan Total ada baris ↳ Oxide / ↳ Sulfide; jumlahnya selalu sama dengan baris induknya. Nilai di luar semua rentang masuk "tanpa kategori".');await dW(1600);
  try{GT.cats=[{nm:'Oxide',lo:'',hi:0.8},{nm:'Sulfide',lo:0.8,hi:''}];const c=$('gtsfo');if(c&&c.checked){c.checked=false;c.dispatchEvent(new Event('change'));}if(kd)kd.open=false;}catch(_){}await rep();});

 /* ---- 5. sayat horizontal di RL saat mendigit dasar pit ---- */
 await guard(async()=>{off();winBack();gtOpen(false);dmWin();await dmCam([600950,9200950,235,1050,0.62],1300);
  await dmCap('P · Dasar pit','Sayat di RL saat mendigit','Seperti di Surpac: saat mendigit poligon dasar, centang "Sayat di RL" — semua yang di atas elevasi dasar dipotong, block model terlihat sebagai irisan mendatar, titik digit jatuh tepat di RL itu.');
  let b3=false;try{b3Show(true);await b3Run();b3=true;const w=$('b3w');if(w)w.style.display='none';}catch(e){console.warn('demo P b3',e);}await dRaw(1200);
  const rl=$('srl'),v0=rl.value,base0=BASE?BASE.z:null;rl.value='220';digStart('poly');await dW(900);await dmShot('P11_digit_tanpa_sayat');
  await dmClick('#dgsl');await dW(1500);await dmCam([BB.x0+BB.w*.3,BB.y0+BB.h*.3,220,620,0.95],1600);await dW(900);await dmShot('P12_sayat_RL_220');
  for(const q of [[BB.x0+BB.w*.14,BB.y0+BB.h*.12],[BB.x0+BB.w*.30,BB.y0+BB.h*.26],[BB.x0+BB.w*.24,BB.y0+BB.h*.36],[BB.x0+BB.w*.08,BB.y0+BB.h*.22]]){const px=gpPx(q[0],q[1],220);if(px){await dmMove(px[0],px[1],650);dmRip();DG.pts.push([q[0],q[1],220]);digDraw();await dW(420);}}
  await dW(900);await dmShot('P13_digit_di_bidang_RL');rl.value='210';try{dslApply();}catch(_){}await dW(1600);await dmShot('P14_sayat_RL_210');
  digStop();DSL.on=false;rl.value=v0;if(BASE&&base0!==null)BASE.z=base0;try{if(b3){const c=$('b3on');if(c&&c.checked)c.click();b3Show(false);}}catch(_){}await dW(600);});

 off();winBack();try{gtOpen(false);}catch(_){}dmWin();await dmCam([600950,9200950,240,1300,0.55],1400);
 await dmCap('P · Selesai','Pembaruan 26 November','Laporan block model dibatasi poligon digit / string 3D / blok mining (.str) · di dalam / di luar · kategori ore · sayat di RL saat mendigit dasar pit.');await dW(2500);
}});
