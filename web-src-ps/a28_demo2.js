/* a28: Demo bab I — pit dua lantai segi enam + jalan penghubung + 3 mulut jalan (simulasi 19 Nov 2026).
   Data FIKTIF: topografi dibuat dari rumus (lereng landai ±RL249–250 di sekitar pit, bukit RL505 di timur laut), tidak ada data proyek nyata.
   Juga: pilihan "Jalan tiap area berdiri sendiri" (= window.__NOJOIN) di langkah 3 Jalan. */
(function(){try{const r=$('rpat');const row=r&&(r.closest('.fl')||r.parentElement);if(row&&!$('rsolo')){row.insertAdjacentHTML('afterend','<div class="fl" title="Tiap area (lantai) punya jalan sendiri sampai permukaan; jalan yang bertemu tidak digabung. Dipakai untuk pit beberapa lantai dengan beberapa mulut jalan."><label><input type="checkbox" id="rsolo"> Jalan tiap area berdiri sendiri (tidak digabung)</label></div>');$('rsolo').onchange=()=>{window.__NOJOIN=$('rsolo').checked?1:0;};}}catch(e){console.warn('rsolo',e);}})();
function hxLayAll(){for(const l of document.querySelectorAll('#lay input[type=checkbox]'))if(!l.checked)l.click();}
const HX={X0:600000,Y0:9200000,XA:600650,XB:600950,Y:9200800,R:22,base:247};
function hxTopoText(){const X0=HX.X0,Y0=HX.Y0,b=HX.base,A=505.5-b-0.003*1850,Z=(x,y)=>{const d=Math.hypot(x-(X0+1850),y-(Y0+1850));return b+0.003*(x-X0)+A*Math.exp(-(d/420)*(d/420));};
 const L=['topo_latihan_dua_lantai,19/11/2026,,ssi_styles:survey.ssi','0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000'];const fx0=600200,fx1=601450,fy0=9200450,fy1=9201300;
 const add=(x,y)=>{L.push('1, '+y.toFixed(3)+', '+x.toFixed(3)+', '+Z(x,y).toFixed(3)+',');L.push('0, 0.000, 0.000, 0.000,');};
 for(let y=fy0;y<=fy1;y+=4)for(let x=fx0;x<=fx1;x+=4)add(x,y);
 for(let y=Y0;y<=Y0+2400;y+=20)for(let x=X0;x<=X0+2400;x+=20){if(x>=fx0-10&&x<=fx1+10&&y>=fy0-10&&y<=fy1+10)continue;add(x,y);}
 L.push('0, 0.000, 0.000, 0.000, END');return L.join('\n')+'\n';}
const hxHex=(cx,cy)=>{const o=[];for(let k=0;k<6;k++){const a=Math.PI/6+k*Math.PI/3;o.push([cx+HX.R*Math.cos(a),cy+HX.R*Math.sin(a)]);}return o;};
const hxRs=(cx,cy,deg,s)=>{const a=deg*Math.PI/180,ap=HX.R*Math.cos(Math.PI/6),p=[cx+ap*Math.cos(a),cy+ap*Math.sin(a)],t=[-Math.sin(a)*s,Math.cos(a)*s];return [p,[p[0]+10*t[0],p[1]+10*t[1]]];};
DMCH.push({id:'I',nm:'Pit dua lantai segi enam + 3 mulut jalan',run:async()=>{
 const CX=(HX.XA+HX.XB)/2,CY=HX.Y,ap=HX.R*Math.cos(Math.PI/6),LA=[HX.XA+ap,CY],LB=[HX.XB-ap,CY],hA=hxHex(HX.XA,CY),hB=hxHex(HX.XB,CY),sq=[[CX-5,CY-5],[CX+5,CY-5],[CX+5,CY+5],[CX-5,CY+5]];
 for(const l of document.querySelectorAll('#lay input[type=checkbox]'))if(!l.checked)l.click();const rA=hxRs(HX.XA,CY,30,1),rB=hxRs(HX.XB,CY,210,1),rC=[[CX,CY-5],[CX+10,CY-5]];
 await dmCap('I · Pit dua lantai','Project baru + topografi latihan','Dua lantai segi enam berjarak 300 m di RL200, jalan penghubung di tengah, tiga mulut jalan. Topografi fiktif.');dmWin();
 if(MODE==='edit'){try{$('tabs').querySelector('[data-t="design"]').click();}catch(_){}await dW(300);}try{pjReset();$('pjn').textContent='Pit dua lantai';}catch(_){}try{window.__PS3.ter.on(false);}catch(_){}dmTopoReset();await dmLoad('tpf','topo_latihan_dua_lantai.str',hxTopoText());/* semua lapisan tampil (bab sebelumnya bisa menyembunyikan sebagian) */for(const l of document.querySelectorAll('#lay input[type=checkbox]'))if(!l.checked)l.click();
 hxLayAll();await dmCam([600950,9200950,260,1300,0.35],1600);await dmShot('J01_topo');
 for(const[k,v]of Object.entries({pH:10,pA:70,pB:5,pN:1,pF:15,pFA:300,rW:12,rG:12,pss:8,psm:3,pZmin:'',pZmax:''}))dmSet(k,v);dmSet('vrnd',false);dmSet('rsolo',true);window.__NOJOIN=1;
 try{dkSet('new');}catch(_){}try{document.querySelector('#dkind [data-v=new]').click();}catch(_){}try{LNK.on=false;LNK.a=null;LNK.b=null;LNK.g=0;LNK.rc=null;}catch(_){}
 await dmCap('I · 1 Bentuk awal','Lantai A dan B: segi enam R 22 m','Mode Dasar pit; gambar segi enam pertama, lalu "Tambah area pit lain" untuk lantai kedua 300 m di timurnya.');
 dsOpen(0);dmWin('dsw1');await dmCam([CX,CY,230,520,0],1400);await dmClick('#smode [data-v=bot]');await dmClick('#dgp',{noFire:true});
 await dmDraw(hA,true,200);window.__PS.setBase(hA,200,'poly','bot');dmDrawClear();await dW(300);
 dsOpen(0);dmWin('dsw1');await dmClick('#dgadd');await dmDraw(hB,true,200);window.__PS.baseSet('poly',hB,200);document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));dmDrawClear();await dW(300);
 await dmCap('I · 1 Bentuk awal','Area C: simpang jalan di punggungan','Kotak 10 × 10 m di tengah jalan penghubung, RL dasar 210 — pangkal jalan ketiga.');
 dsOpen(0);dmWin('dsw1');await dmClick('#dgadd');await dmDraw(sq,true,210);window.__PS.baseSet('poly',sq,200);document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));dmDrawClear();await dW(300);
 dsOpen(0);dmWin('dsw1');await dmType('[data-az="2"]',210);hxLayAll();await dmShot('J02_bentuk_awal',['#smode','#dgadd','[data-az="2"]']);
 await dmCap('I · 2 Geoteknik','Geoteknik','Tinggi bench 10 m, muka 70°, berm 5 m tiap bench; sudut tajam.');dsOpen(1);dmWin('dsw2');for(const k of ['pH','pA','pB','pN'])await dmType('#'+k,{pH:10,pA:70,pB:5,pN:1}[k]);
 const cb=document.querySelector('#pcor [data-v=miter]');if(cb&&!cb.classList.contains('on'))await dmClick(cb);await dmShot('J03_geoteknik',['#pH^','#pA^','#pB^','#pN^','#pcor']);
 await dmCap('I · 3 Jalan','Jalan 12 m, 12 %, spiral, berdiri sendiri','Tiap lantai punya jalan sendiri sampai permukaan (tidak digabung) → tiga mulut jalan.');dsOpen(2);dmWin('dsw3');await dmType('#rW',12);await dmType('#rG',12);await dmClick('#rpat [data-v=spiral]');
 {const e=$('rsolo');if(e){if(!e.checked)await dmClick(e);else await dmPoint(e);}window.__NOJOIN=1;}await dmShot('J04_jalan',['#rW^','#rG^','#rpat','#rsolo^']);
 await dmCap('I · 3 Jalan','Arah awal jalan','A dan B berputar searah (A menyusuri dinding selatan, B dinding utara); pangkal jalan dijauhkan dari mulut jalan penghubung. C dari simpang ke timur.');
 dmWin();await dmCam([CX,CY,230,420,0],1200);hxLayAll();for(const [i,r] of [[0,rA],[1,rB],[2,rC]]){await dmDraw(r,false,200+(i===2?10:0));window.__PS.setRamp(i,r[0],r[1]);dmDrawClear();await dW(200);}await dmShot('J05_arah_jalan');
 await dmCap('I · 4 Jalan penghubung','Jalan penghubung dua lantai','Menu Desain baru → Jalan penghubung dua lantai: gambar dari tepi lantai A ke tepi lantai B; kemiringan 7,637 % supaya puncaknya tepat RL210.');
 const w=lnkWin();winShow(w,true);dmWin('lnkw');await dmClick('#lnkdig',{noFire:true});await dmDraw([LA,LB],false,200);lnkSet(LA,LB,200);dmDrawClear();await dmType('#lnkg',7.637);LNK.g=7.637;LNK.rc=null;try{lnkInfo();}catch(_){}
 await dmShot('J06_penghubung',['#lnkdig','#lnkg^','#lnkgo']);
 await dmCap('I · Buat pit','Buat pit','Bench dibangun dari kedua lantai ke atas sampai permukaan; jalan penghubung ikut digali.');$('res').innerHTML='';await dmClick('#lnkgo');await dmWaitRes();await dW(800);
 dmWin();await dmCam([CX,CY-10,230,520,0.9],1800);await dmCap('I · Hasil','Pit dua lantai, tiga mulut jalan','±1,49 juta m³, 6 bench RL200–260, jalan keluar di RL ±249–250 ke timur laut, barat laut, tenggara.');await dmShot('J07_hasil_3d');
 await dmCap('I · Kerapian','Tolok ukur ketat','Menggantung 0 · silang 0 · tidak dipatuhi 0 · bergelombang 0 (silang ruas penuh, berm negatif, tangga kecil ikut diperiksa).');{const t=$('tdw');if(t){t.style.display='block';t.style.zIndex=950;}}await dW(300);await dmShot('J08_kerapian',['#tdw']);dmWin();
 await dmCap('I · Hasil','Denah string','Topografi disembunyikan: crest (merah), toe (biru), jalan (jingga), simpang jalan RL210 di tengah.');dmTopoVis(false);await dmCam([CX,CY,230,560,0],1500);await dmShot('J09_denah');await dW(1200);dmTopoVis(true);
 await dmCam([HX.XA-20,CY,215,260,1.0],1600);await dW(900);await dmCam([HX.XB+20,CY-10,215,260,2.3],1800);await dW(900);await dmCam([CX,CY-10,230,560,0.9],1600);
 await dmCap('Selesai','Demo selesai','Semua desain di demo ini memenuhi empat tolok ukur kerapian. Tekan Stop untuk mengembalikan pengaturan.');await dW(2500);}});
/* penutup dipindah ke bab I */
try{const H=DMCH.find(c=>c.id==='H');if(H){const run0=H.run;H.run=async()=>{const _cap=dmCap;let skip=false;dmCap=async(a,b,c)=>{if(a==='Selesai'){skip=true;return;}return _cap(a,b,c);};const _w=dW;try{await run0();}finally{dmCap=_cap;}};}}catch(e){}
try{const w=$('dmoList');if(w){w.innerHTML=DMCH.map((c,i)=>'<div class="fl"><button class="sm" data-dmo="'+i+'">&#9654; '+c.id+'</button><span>&nbsp;'+esc(c.nm)+'</span></div>').join('');w.querySelectorAll('[data-dmo]').forEach(b=>b.onclick=()=>dmoPlay(+b.dataset.dmo,+b.dataset.dmo+1));}}catch(e){}
