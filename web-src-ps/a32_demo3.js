/* a32: Demo bab J — Pit Schedule: jalur gali per fleet (bench-by-bench), sump pojok utara, hauling DT (simulasi 19 Nov 2026).
   Memakai topografi & pit dua lantai FIKTIF dari bab I (dijalankan cepat bila belum ada). */
DMCH.push({id:'J',nm:'Pit Schedule — jadwal per fleet, grade × tonnage, desain face position',run:async()=>{
 const ok=()=>{try{return !!RES&&TP.some(t=>/topo_latihan_dua_lantai/.test(t.nm));}catch(_){return false;}};
 if(!ok()){await dmCap('J · Pit Schedule','Menyiapkan pit bab I','Bab J memakai topografi & pit dua lantai dari bab I — dijalankan cepat lebih dulu.');const I=DMCH.find(c=>c.id==='I'),sp=DMO.spd,cp=dmCap,sh=dmShot;DMO.spd=60;dmCap=async()=>{};dmShot=async()=>{};try{await I.run();}finally{DMO.spd=sp;dmCap=cp;dmShot=sh;}}
 const tz=p=>{const z=topoZ(p[0],p[1]);return [p[0],p[1],isFinite(z)?z:250];};
 const BND=[[600560,9200720],[600800,9200720],[600800,9200880],[600560,9200880]].map(tz),L1=[[600565,9200868],[600795,9200868]].map(tz),SU=[[600585,9200842],[600640,9200842]].map(tz),HR=[[600800,9200885],[600820,9201000],[600900,9201150],[600950,9201250]].map(tz);
 const lay=(re,on)=>{for(const l of document.querySelectorAll('#lay input[type=checkbox]'))if(re.test(l.parentElement.innerText)&&l.checked!==on)l.click();};
 dmWin();try{$('sayw').style.display='none';}catch(_){}schReset();lay(/Permukaan pit|Label RL|Garis potong/,false);
 await dmCap('J · Pit Schedule','Menu Pit Schedule','Simulasi penjadwalan gali seperti Minex: area dibagi blok tambang, jalur gali per fleet, kapasitas alat (unit, jam, PA, UA), lapis demi lapis.');
 await dmCam([600680,9200800,240,520,0.8],1400);await dmClick('#mbsch');{const w=$('schw');w.style.left='12px';w.style.top='78px';}await dW(400);
 await dmCap('J · 1 Blok tambang','Bench 10 × strip 20 × blok 40 m','Cukup isi ukuran blok tambang. Kotak hitung di dalamnya (5 × 5 m, lapis 2,5 m) dibuat otomatis oleh sistem dan pas ke batas fase.');await dmPoint('#mbbh');dmSet('mbbh',10);await dW(400);await dmPoint('#mbsw');dmSet('mbsw',20);await dW(400);await dmPoint('#mbbl');dmSet('mbbl',40);await dW(400);
 await dmCap('J · 2 Batas fase','Poligon batas fase','Poligon hanya membatasi — kotak hitung di luar batas tidak pernah digali. Penggalian dilakukan lewat tarik jalur gali.');
 await dmCam([600680,9200800,240,420,0],1200);await dmClick('#schap',{noFire:true});await dmDraw(BND,true,250);schPh().bnd=BND.map(q=>q.slice());dmDrawClear();schTasks();schDrawStatic();await dW(500);
 await dmCap('J · 3 Fleet A1','Jalur gali pertama (strip utara)','Tarik garis A→B; tiap lintasan menggali 1 flitch pada kotak hitung yang dilewati, lebar 4 blok (20 m).');
 await dmClick('#schal',{noFire:true});await dmDraw(L1,false,250);dmDrawClear();
 schAdd('line',L1,{nm:'Strip',alat:'ex200',pm2:'bkt',bkt:11,cyc:29,nu:2,fl:1,rep:8,nb:4,ord:'lapis',fm:'des',fd:'res',grp:'A1'});await dW(400);
 await dmCap('J · 3 Fleet A1','Alat & ketersediaan','2× Excavator kelas 200 t; jam jadwal 11 jam/shift, PA 90 %, UA 80 % → ±11.700 BCM/shift. Batas lantai ikut desain pit final.');
 await dmPoint('#sched [data-k=alat]');dmRip();await dW(500);await dmType('#sched [data-k=nu]',2);await dmPoint('#sched [data-k=pa]');await dW(300);await dmPoint('#sched [data-k=ua]');await dW(500);
 await dmCap('J · 3 Fleet A1','Hauling: DT 90 t + jalur angkut','Pilih alat angkut, lalu gambar jalur angkut ke dump. Kebutuhan DT dihitung ulang tiap jam dari jarak & posisi gali.');
 {const e=document.querySelector('#sched [data-k=hk]');await dmPoint(e);dmRip();e.value='r90';e.dispatchEvent(new Event('change'));await dW(500);}
 await dmCam([600800,9201000,250,620,0.5],1200);await dmClick('#sched [data-a=hr]',{noFire:true});await dmDraw(HR,false,250);dmDrawClear();for(const t of SCH.tasks)if(t.type==='line'&&t.grp==='A1')t.hr=HR.map(q=>q.slice());schTasks();schDrawStatic();await dW(400);
 await dmCap('J · 4 Salin sejajar','8 strip berdampingan','Lebar jalur diatur di "jalur baru: lebar … blok". Buka daftar Jalur gali, pilih jalur, Salin sejajar × 7 ke kanan: strip bergeser selebar jalur, arah bolak-balik — seperti face yang maju.');
 await dmCam([600680,9200800,240,420,0],1200);SCH.jOpen=true;schEdit();await dW(300);
 await dmClick('#schjl [data-l]');await dmType('#schpn',7);{const e=$('schps');e.value='1';}await dmClick('#sched [data-a=par]');await dW(600);
 await dmCap('J · 4 Salin sejajar','Urutan fleet: per lapis','Satu baris = satu fleet. Urutan "per lapis": semua jalur satu lintasan, lalu ulang — area turun merata flitch demi flitch (8 lintasan = 20 m).');SCH.jOpen=false;schEdit();await dmPoint('#sched [data-k=ord]');await dW(900);
 await dmCap('J · 5 Fleet A2','Sump di pojok utara','+ Fleet → Fleet A2 (Excavator kelas 120 t); tanda ◉ = fleet tujuan jalur baru. Jalur pendek di pojok utara, lebar 3 blok × 10 lintasan, mulai shift 5. Jejak semua fleet tampil di 3D.');
 await dmClick('#schfl');await dmClick('#schal',{noFire:true});await dmDraw(SU,false,250);dmDrawClear();
 schAdd('line',SU,{nm:'Sump utara',alat:'ex120',pm2:'bkt',bkt:6.7,cyc:27,nu:1,fl:1,rep:10,nb:3,start:5,grp:'A2',hl:true,hk:'r90',hp:91,hv:60,vl:22,ve:38,hr:HR.map(q=>q.slice())});await dW(600);
 await dmCap('J · 6 Pratinjau','Peta intensitas jalur','Sebelum dijalankan: blok diwarnai menurut jumlah flitch rencana — merah = paling sering dilewati (calon sump).');await dmCam([600680,9200800,240,380,0.75],1400);await dW(1200);
 await dmCap('J · 7 Jalankan','Simulasi per jam','Tiap jam: alat menggali blok sesuai kapasitas; kedalaman dihitung saat alat tiba di blok; lereng antar-blok 60° dijaga (blok tetangga ikut digali).');
 await dmClick('#schrun');await dW(800);
 await dmCap('J · 8 Hasil','Putar per shift','Slider & Putar: topografi tetap tampil, permukaan galian turun bench demi bench dengan kontur teras (garis tegas + label RL tiap bench). Desain acuan disembunyikan; excavator & DT ikut bergerak.');
 {const e=$('schun');e.value='s';e.dispatchEvent(new Event('change'));$('schspd').value='8';}schSet(-1);await dmCam([600680,9200800,232,340,0.8],1200);await dmClick('#schpl');
 for(let i=0;i<14&&SCH.play;i++)await dRaw(500);await dmCam([600640,9200830,232,260,0.9],1600);for(let i=0;i<20&&SCH.play;i++)await dRaw(500);schStop();schSet(SCH.bd.length-1);
 await dmCap('J · 8 Hasil','Periode per bench','Periode bisa per jam, shift, hari, minggu, bulan, flitch, atau bench — tabel volume & CSV ikut periode itu.');{const e=$('schun');await dmPoint(e);e.value='b';e.dispatchEvent(new Event('change'));}await dW(500);
 {const d=$('schtb').closest('details');if(d){d.open=true;}}await dmPoint('#schtb');await dW(1600);{const d=$('schtb').closest('details');if(d)d.open=false;}
 await dmCap('J · 9 Hauling','DT di jalur angkut','DT muat di excavator → angkut → dump (bak terangkat) → kembali. Kebutuhan DT tiap fleet tampil di ringkasan.');await dmCam([600760,9200990,245,520,0.7],1600);await dW(3500);
 if(window.__DMJK)return;
 await dmCap('J · 10 Sayatan','Penampang lewat sump','Sayatan N–S: topografi (hijau), pit final (biru), permukaan jadwal (jingga) — sump di pojok utara tertahan lantai desain.');
 await dmCam([600640,9200800,232,330,0.85],1200);try{window.__PS3.say.set([600610,9200715],[600610,9200885]);}catch(_){}await dW(3500);try{$('sayw').style.display='none';sayLine3D();}catch(_){}
 await dmCap('J · 11 Grade × Tonnage','Block model .mdl','Muat block model Surpac (.mdl): hanya blok di area jadwal yang dibaca. Cara Surpac — blok dihitung saat permukaan gali melewati titik pusatnya. Data demo fiktif.');
 gtMount();{const d=$('gtbox');d.open=true;const b=$('schbd');b.scrollTop=b.scrollHeight;}await dmPoint('#gtld');dmRip();await gtLoad(dmMdlFiktif());for(let i=0;i<120&&(GT.busy||!GT.res);i++)await dRaw(250);{const b=$('schbd');b.scrollTop=b.scrollHeight;}await dW(1200);
 await dmCap('J · 11 Grade × Tonnage','Laporan per periode','Per bench (atau jam / shift / hari …): ton @ g/t tiap kelas kadar, waste, SR, logam — kelas & tujuan memakai preset GC-Ex Block Model. Bisa dirinci per fleet, ekspor CSV.');await dmPoint('#gttb');await dW(1800);
 {const e=$('gtfl');await dmPoint(e);e.checked=true;e.dispatchEvent(new Event('change'));}for(let i=0;i<40&&GT.busy;i++)await dRaw(250);await dW(1600);{const e=$('gtfl');e.checked=false;e.dispatchEvent(new Event('change'));}
 await dmCap('J · 11 Grade × Tonnage','Warna kelas material','Permukaan galian diwarnai menurut kelas blok yang tergali: merah = HG, hijau = LG, cokelat = waste.');{const e=$('schcm');e.value='kls';e.dispatchEvent(new Event('change'));}schSet(SCH.bd.length-1);await dmCam([600680,9200800,232,330,0.85],1400);await dW(2600);{const e=$('schcm');e.value='rl';e.dispatchEvent(new Event('change'));}$('gtbox').open=false;
 await dmCap('J · 12 Desain','Desain dari face position','Dari permukaan akhir fase, sistem mencoba beberapa simulasi (batas digeser, lantai, pola jalan) dan merekomendasikan desain yang volumenya paling dekat dengan jadwal.');
 {const b=$('schbd');b.scrollTop=b.scrollHeight;}await dmClick('#schfd');for(let i=0;i<480&&SCHFD.busy;i++)await dRaw(250);{const b=$('schbd');b.scrollTop=b.scrollHeight;}await dmPoint('#schfdr');await dW(3000);
 await dmCap('J · 13 Fase','Kunci & lanjut fase','Setelah satu fase selesai, permukaan akhirnya menjadi topografi awal fase berikut — nomor shift & tanggal bersambung.');await dmPoint('#schph [data-a=nx]');await dW(1500);
 lay(/Permukaan pit|Label RL|Garis potong/,true);
 await dmCap('Selesai','Demo selesai','Semua desain di demo ini memenuhi empat tolok ukur kerapian; Pit Schedule mensimulasikan penggalian per fleet. Tekan Stop untuk mengembalikan pengaturan.');await dW(2500);}});
/* Bab K — TUTORIAL khusus Pit Schedule → Grade × Tonnage.
   Kasus 1: satu area diturunkan per selang elevasi (G × T × SR tiap penurunan). Kasus 2: jalur gali per fleet (bab J 1–9) + laporan rinci. */
DMCH.push({id:'K',nm:'Tutorial: Pit Schedule → Grade × Tonnage × SR (turun per bench, per fleet, cut-off)',run:async()=>{
 const ok=()=>{try{return !!RES&&TP.some(t=>/topo_latihan_dua_lantai/.test(t.nm));}catch(_){return false;}};
 if(!ok()){await dmCap('Tutorial','Menyiapkan pit latihan','Memakai topografi & pit dua lantai fiktif dari bab I — dijalankan cepat lebih dulu.');const I=DMCH.find(c=>c.id==='I'),sp=DMO.spd,cp0=dmCap,sh=dmShot;DMO.spd=60;dmCap=async()=>{};dmShot=async()=>{};try{await I.run();}finally{DMO.spd=sp;dmCap=cp0;dmShot=sh;}}
 const tz=p=>{const z=topoZ(p[0],p[1]);return [p[0],p[1],isFinite(z)?z:250];},BND=[[600560,9200720],[600800,9200720],[600800,9200880],[600560,9200880]].map(tz);
 const lay=(re,on)=>{for(const l of document.querySelectorAll('#lay input[type=checkbox]'))if(re.test(l.parentElement.innerText)&&l.checked!==on)l.click();};
 const wt=async n=>{for(let i=0;i<(n||160)&&(GT.busy||!GT.res);i++)await dRaw(250);},sb=()=>{const b=$('schbd');b.scrollTop=b.scrollHeight;},bigPos=()=>{const w=$('gtrw');w.style.left='590px';w.style.top='74px';w.style.width='838px';gtBigDraw();};
 const sum=()=>{const A=gtAgg({out:GT.res.out,B:gtBand(),np:GT.res.F.sim.np,TS:GT.res.F.sim.TS,fl:false}),K=A.K;let o=0,m=0;for(let k=0;k<K;k++){o+=A.tot.t[k];m+=A.tot.gt[k];}return {o,g:o>0?m/o:0,w:A.tot.t[K]};};
 const bars=async ms=>{const n=SCH.bd.length;for(let i=0;i<n;i++){const r=document.querySelector('#gtrg rect.b[data-i="'+i+'"]');if(!r)continue;await dmPoint(r,450);dmRip();schStop();schSet(i);await dW(ms);}};
 const S1='Kasus 1 · Turun per bench',S2='Kasus 2 · Jalur gali per fleet';
 /* tutorial: beri waktu baca tiap keterangan (± 35 ms per huruf) */
 const cap0=dmCap;dmCap=async(x,y,z)=>{await cap0(x,y,z);await dW(Math.min(5200,600+34*String(z||'').length));};try{
 /* ---------- Kasus 1 ---------- */
 dmWin();try{$('sayw').style.display='none';}catch(_){}try{gtBig(false);gtOpen(false);}catch(_){}schReset();lay(/Permukaan pit|Label RL|Garis potong/,false);
 await dmCap(S1,'Kasusnya','Mine plan diminta menjadwalkan satu area: setiap penurunan elevasi menghasilkan berapa ton, kadar dan stripping ratio? Buka menu Pit Schedule.');
 await dmCam([600680,9200800,240,520,0.8],1400);await dmClick('#mbsch');{const w=$('schw');w.style.left='12px';w.style.top='78px';}await dW(900);
 await dmCap(S1+' 1','Batas fase = area yang dijadwalkan','Gambar poligon area di 3D; di luar poligon tidak pernah digali. Blok tambang (bench × strip × blok) langsung dibuat otomatis.');
 await dmCam([600680,9200800,240,420,0],1200);await dmClick('#schap',{noFire:true});await dmDraw(BND,true,250);schPh().bnd=BND.map(q=>q.slice());dmDrawClear();schTasks();schDrawStatic();await dW(700);
 await dmCap(S1+' 2','Muat block model (.mdl)','Menu Impor → Block model. File Surpac dibaca seperti di GC-Ex; hanya blok di bawah topografi dan di area kerja yang dimuat. Kelas: LG 0,4–1 g/t, HG ≥ 1 g/t, sisanya waste. Data demo fiktif.');
 gtMount();gtOpen(true);{const w=$('bmw');w.style.left='590px';w.style.right='auto';w.style.top='78px';}await dW(500);await dmPoint('#gtld');dmRip();await gtLoad(dmMdlFiktif());await dW(1000);await dmPoint('#gttp');await dW(1000);$('gtkd').open=true;await dW(300);await dmPoint('#gtrl');await dW(2200);gtOpen(false);
 await dmCap(S1+' 3','Turun per bench 10 m','Tinggi bench di Blok tambang = selang penurunan. Tekan Turun per bench: seluruh area digali lapis demi lapis sampai lantai desain (lereng antar-blok dijaga), lalu dilaporkan per 10 m.');
 await dmCam([600680,9200800,236,360,0.85],1200);await dmType('#mbbh',10);dmSet('mbbh',10);await dmPoint('#schego');dmRip();await schElev();await wt();bigPos();await dW(1200);
 await dmCap(S1+' 4','Tiap penurunan: ton, kadar, SR','Satu baris = satu penurunan elevasi: ton @ g/t tiap kelas, waste, SR, logam. Kolom kanan = kumulatif (Σ ore, Σ kadar, Σ SR) dan kapan selang itu selesai menurut kapasitas alat.');
 await dmPoint('#gtrc');await dW(2600);await dmPoint('#gtrg');await dW(3000);await dmPoint('#gtrt');await dW(4500);
 await dmCap(S1+' 5','Lihat tiap elevasi di 3D','Klik batang / baris: permukaan area pada akhir penurunan itu. Warna = kelas material yang tergali (merah HG, hijau LG, cokelat waste) — seperti tampilan blok berwarna di Minex.');
 gtBigMin(true);{const w=$('gtrw');w.style.left='832px';w.style.top='74px';}await dmCam([600770,9200800,236,300,0.85],1300);await bars(2300);gtBigMin(false);bigPos();
 await dmCap(S1+' 6','Ubah bench: 5 m','Ganti tinggi bench lalu tekan lagi. Dengan 5 m terlihat lebih rinci di elevasi mana ore mulai muncul dan SR turun.');
 await dmType('#mbbh',5);dmSet('mbbh',5);await dmPoint('#schego');dmRip();GT.res=null;await schElev();await wt();bigPos();await dW(900);await dmPoint('#gtrg');await dW(2600);await dmPoint('#gtrt');await dW(3600);
 await dmCap(S1+' 7','Waktu mengikuti alat','Kolom "selesai" dihitung dari alat area ini (unit, jam, PA, UA). Ubah alat atau jumlah unit di kartu area → jadwal & laporan dihitung ulang. Tombol CSV mengekspor tabelnya.');
 await dmPoint('#schtl');await dW(2600);await dmPoint('#gtrcsv');await dW(1800);gtBig(false);dmSet('mbbh',10);
 /* ---------- Kasus 2: bab J langkah 1–9 ---------- */
 await dmCap(S2,'Bila urutan gali ditentukan per alat','Kasus kedua: arah & urutan gali ditentukan sendiri — tarik jalur gali untuk tiap fleet. Laporan yang sama lalu bisa dirinci per periode dan per fleet.');await dW(2600);
 {const e=$('schcm');e.value='rl';e.dispatchEvent(new Event('change'));}
 try{$('schbd').scrollTop=0;$('schw').style.width='';$('gtbox').open=false;schOpen(false);}catch(_){}
 window.__DMAUTOP=1;const J=DMCH.find(c=>c.id==='J'),cp=dmCap;window.__DMJK=1;dmCap=async(a,b,c)=>cp(String(a).replace(/^J · Pit Schedule$/,S2).replace(/^J · \d+ ?/,S2+' · '),b,c);
 try{await J.run();}finally{window.__DMJK=0;dmCap=cp;window.__DMAUTOP=0;}
 try{$('sayw').style.display='none';}catch(_){}
 await dmCap(S2+' · Laporan','Laporan & grafik per periode','Block model sudah dimuat, jadi laporan langsung dihitung setiap kali jadwal dijalankan. Buka "Laporan & grafik".');
 gtMount();{const d=$('gtbox');d.open=true;sb();}await wt();sb();await dmPoint('#gtsum');await dW(1800);await dmClick('#gtbigb');bigPos();await dW(600);await dmPoint('#gtrg');await dW(2800);
 await dmCap(S2+' · Laporan','Ganti periode','Per shift, per hari, per bench … tabel, grafik dan CSV ikut berubah — terlihat kapan ore mulai keluar.');
 for(const u of ['s','d','b']){const e=$('gtru2');await dmPoint(e);dmRip();e.value=u;e.dispatchEvent(new Event('change'));await dW(u==='b'?1800:3000);}
 await dmCap(S2+' · Laporan','Rincian per fleet','Centang "per fleet": tiap periode dipecah menurut fleet yang menggali blok itu — fleet mana membawa ore, mana mengupas waste.');
 {const e=$('gtrf');await dmPoint(e);dmRip();e.checked=true;e.dispatchEvent(new Event('change'));}await dW(600);await dmPoint('#gtrt');await dW(4200);{const e=$('gtrf');e.checked=false;e.dispatchEvent(new Event('change'));}
 await dmCap(S2+' · Jejak','Jejak jalur: tampil atau mati','Tiap jalur punya ikon mata di daftar Jalur gali; ada juga "tampil semua / sembunyikan semua / hanya terakhir" dan pilihan jejak semua fleet, fleet aktif, atau mati.');
 gtBig(false);{const e=$('schcm');e.value='rl';e.dispatchEvent(new Event('change'));}schSet(SCH.bd.length-1);await dmCam([600680,9200800,236,330,0.5],1200);
 SCH.sel='g:A1';SCH.jOpen=true;schTasks();schEdit();{const b=$('schbd');const j=$('schjl');if(j)b.scrollTop=Math.max(0,j.offsetTop-80);}await dW(900);
 for(const m of ['0','2','1']){const b=document.querySelector('#schjl [data-lva="'+m+'"]');if(b){await dmPoint(b);dmRip();b.click();{const bb=$('schbd'),j=$('schjl');if(j)bb.scrollTop=Math.max(0,j.offsetTop-80);}await dW(1900);}}
 {const b=document.querySelector('#schjl [data-lv]');if(b){await dmPoint(b);dmRip();b.click();await dW(1700);const b2=document.querySelector('#schjl [data-lv]');if(b2)b2.click();}}
 {const e=$('schtr');await dmPoint(e);dmRip();e.value='off';e.dispatchEvent(new Event('change'));await dW(1700);e.value='all';e.dispatchEvent(new Event('change'));await dW(900);}SCH.jOpen=false;schEdit();
 const s0=sum();await dmCap(S2+' · Cut-off','Uji cut-off','Cut-off LG 0,4 g/t: ore '+schF(s0.o)+' t @ '+s0.g.toFixed(2)+' g/t. Naikkan batas bawah LG ke 0,6 g/t — laporan langsung dihitung ulang.');
 gtBig(true);bigPos();gtOpen(true);{const w=$('bmw');w.style.left='60px';w.style.right='auto';w.style.top='120px';w.style.zIndex=58;}$('gtkd').open=true;await dW(500);await dmType('#gtrl input[data-k=lo][data-i="0"]',0.6);{const e=document.querySelector('#gtrl input[data-k=lo][data-i="0"]');e.value=0.6;e.dispatchEvent(new Event('change'));}await dRaw(300);await wt(80);gtOpen(false);
 const s1=sum();await dmCap(S2+' · Cut-off','Hasil cut-off 0,6 g/t','Ore turun menjadi '+schF(s1.o)+' t, kadar naik ke '+s1.g.toFixed(2)+' g/t; '+schF(s0.o-s1.o)+' t pindah ke waste. Setelah dicoba, dikembalikan ke 0,4 g/t.');
 await dmPoint('#gtrc');await dW(4200);GT.rules[0].lo=0.4;gtRules();await gtRun().catch(()=>{});await wt(80);
 const s2=sum();GT.rule='prop';try{$('gtru').value='prop';}catch(_){}await gtRun().catch(()=>{});await wt(80);const s3=sum();
 await dmCap(S2+' · Aturan blok','Cara Surpac vs proporsional','Pusat blok (cara Surpac): '+schF(s2.o)+' t @ '+s2.g.toFixed(2)+' g/t · proporsional: '+schF(s3.o)+' t @ '+s3.g.toFixed(2)+' g/t. Laporan resmi memakai cara Surpac agar cocok dengan GC-Ex.');
 await dmPoint('#gtrc');await dW(4500);GT.rule='pusat';try{$('gtru').value='pusat';}catch(_){}await gtRun().catch(()=>{});await wt(80);
 await dmCap(S2+' · Desain','Bandingkan dengan desain','Laporan desain (topografi → pit final, per bench) memakai block model & kelas yang sama: terlihat berapa bagian ore desain yang sudah terjadwal di fase ini.');
 gtBig(false);gtOpen(true);{const w=$('bmw');w.style.left='590px';w.style.right='auto';w.style.top='78px';}$('gtkd').open=false;try{$('gdds').value='res';}catch(_){}await dmClick('#gdgo');for(let i=0;i<200&&(GT.busy||!GT.dres);i++)await dRaw(250);{const b=$('bmwb');b.scrollTop=b.scrollHeight;}await dmPoint('#gdsum');await dW(2200);await dmPoint('#gdtb');await dW(3800);

 await dmCap('Selesai','Tutorial selesai','Kasus 1: Batas fase → Turun per bench → G × T × SR tiap bench. Kasus 2: jalur gali per fleet → laporan per periode / fleet. Tekan Stop untuk mengembalikan pengaturan.');gtOpen(false);$('gtbox').open=false;lay(/Permukaan pit|Label RL|Garis potong/,true);await dW(3000);}finally{dmCap=cap0;window.__DMJK=0;}}});
/* block model FIKTIF untuk demo (.mdl Surpac Version 4.0): kotak blok seragam + fungsi kadar rekaan */
function dmMdlBuat(o){const bs=o.bs,O=[Math.floor(o.x0/bs[0])*bs[0],Math.floor(o.y0/bs[1])*bs[1],Math.floor(o.z0/bs[2])*bs[2]],N=[Math.ceil((o.x1-O[0])/bs[0]),Math.ceil((o.y1-O[1])/bs[1]),Math.ceil((o.z1-O[2])/bs[2])],L=Math.max(1,Math.ceil(Math.log2(Math.max(...N)))),RT=bs.map(b=>b*2**L);
 const enc=t=>Uint8Array.from(t,ch=>ch.charCodeAt(0)),P=[];let seed=7;const rnd=()=>{seed=(seed*1103515245+12345)&0x7fffffff;return seed/0x7fffffff;};
 const i32=v=>{const b=new Uint8Array(4);new DataView(b.buffer).setInt32(0,v);return b;},f64=v=>{const b=new Uint8Array(8);new DataView(b.buffer).setFloat64(0,v);return b;},z1=new Uint8Array(1);
 P.push(enc('### Block Model ###\nVersion 4.0\n'),z1,enc(o.name+'.mdl'),z1,z1,new Uint8Array(12));for(const v of [...O,...RT,...RT])P.push(f64(v));P.push(i32(0),i32(4));
 for(const [n,d] of [['au',0],['sg',2.6],['sxs',0]])P.push(enc(n),z1,i32(0),i32(2),i32(2),f64(d),z1);P.push(enc('kelas'),z1,i32(1),i32(2),enc('IIF(au<0.4,"WASTE",IIF(au<1,"LG","HG"))'),z1,i32(0));
 const n=N[0]*N[1]*N[2],B=new Uint8Array(n*32+24),dv=new DataView(B.buffer);let q=0;
 for(let ix=0;ix<N[0];ix++)for(let iy=0;iy<N[1];iy++)for(let iz=0;iz<N[2];iz++){let dg=0,ib=0,lo=0;for(let l=1;l<=L;l++){const b=L-l,d=(((ix>>b)&1)<<2)|(((iy>>b)&1)<<1)|((iz>>b)&1);if(l<=3)dg|=d<<(3*(l-1));else if(l<=9)ib|=d<<(3*(l-4));else lo|=d<<(3*(l-10));}
  const x=O[0]+(ix+.5)*bs[0],y=O[1]+(iy+.5)*bs[1],z=O[2]+(iz+.5)*bs[2],g=Math.max(0,Math.round(o.au(x,y,z,rnd)*1000)/1000);
  dv.setUint32(q,((ib<<14)|(dg<<5)|L)>>>0);dv.setUint32(q+4,lo>>>0);dv.setFloat64(q+8,g);dv.setFloat64(q+16,Math.round((2.55+0.1*Math.min(1,g/2))*1000)/1000);dv.setFloat64(q+24,Math.round(Math.min(3,0.3+g*0.25+0.2*rnd())*1000)/1000);q+=32;}
 B.fill(255,q,q+8);P.push(B);return new File(P,o.name+'.mdl');}
/* bab J: dua urat E–W rekaan di area pit dua lantai */
function dmMdlFiktif(){return dmMdlBuat({name:'demo_fiktif_pit_schedule',bs:[5,5,2.5],x0:600540,x1:600820,y0:9200700,y1:9200900,z0:195,z1:255,au:(x,y,z,rnd)=>{let g=0.05+0.04*rnd();for(const [y0,dip,w,pk] of [[9200790,0.35,9,3.2],[9200840,0.25,6,1.6]]){const d=Math.abs(y-(y0+(250-z)*dip));if(d<w*2)g+=pk*Math.exp(-((d/w)**2))*(0.7+0.6*rnd())*(0.8+0.4*Math.sin((x-600500)/60));}return g;}});}
/* bab A–H: urat rekaan sepanjang garis urat demo (sumbu lokal u), miring ke arah +v */
function dmMdlUrat(){let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(const [u,v] of [[-460,-230],[460,-230],[460,230],[-460,230]]){const p=DP(u,v);x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}
 return dmMdlBuat({name:'demo_fiktif_urat',bs:[10,10,5],x0,x1,y0,y1,z0:225,z1:350,au:(x,y,z,rnd)=>{const du=(x-DCX)*DUX+(y-DCY)*DUY,dv=(x-DCX)*DPX+(y-DCY)*DPY;let g=0.04+0.05*rnd();if(Math.abs(du)<380){for(const [v0,dip,w,pk] of [[0,0.3,14,3.0],[55,0.2,9,1.4]]){const d=Math.abs(dv-(v0+(320-z)*dip));if(d<w*2)g+=pk*Math.exp(-((d/w)**2))*(0.7+0.6*rnd())*(0.75+0.35*Math.cos(du/120));}}return g;}});}
async function dmBmSiap(){gtWin();if(!GT.file||!GT.H||GT.H.name!=='demo_fiktif_urat'){await gtLoad(dmMdlUrat());}}
async function dmBmLap(id,cap1,cap2){try{if(!schDes().some(x=>x.id===id))return;await dmBmSiap();await dmCap(cap1,'Grade × Tonnage desain',cap2);gtOpen(true);{const w=$('bmw');w.style.left='12px';w.style.right='auto';w.style.top='78px';}$('gdds').value=id;await dW(400);await dmClick('#gdgo',{noFire:true});GT.dres=null;await gtDesign();await dmPoint('#gdtb');await dW(2600);{const b=$('bmwb');if(b)b.scrollTop=b.scrollHeight;}await dmShotL(id==='res'?'M02_laporan_pit_final':'M03_laporan_staging',cap1,'Grade × Tonnage desain',cap2);gtOpen(false);}catch(e){console.warn('demo GT',e);try{gtOpen(false);}catch(_){}}}
/* bab A: impor block model di awal; bab B & C: laporan grade × tonnage desain */
try{const A=DMCH.find(c=>c.id==='A'),B=DMCH.find(c=>c.id==='B'),C=DMCH.find(c=>c.id==='C');
 if(A){const r00=A.run;A.run=async()=>{try{if(typeof SH!=='undefined'&&SH.on){await dmCap('A · Kerangka','Menu, Project Tree, Properti','Bar menu tarik di atas; Project Tree di kiri berisi data, desain dan jadwal; halaman Properti di kanan menampilkan pengaturan; 3D selalu utuh di tengah; pesan muncul di status bar.');await dmPoint('#shbar');await dW(1200);await dmPoint('#shtree');await dW(1400);await dmPoint('#side .shph');await dW(1400);await dmPoint('#shmsg^');await dW(1100);}}catch(_){}await r00();};}
 if(A){const r0=A.run;A.run=async()=>{await r0();await dmCap('A · Block model','Impor block model (.mdl)','Menu Impor → Block model: file .mdl Surpac dibaca seperti di GC-Ex. Hanya blok di bawah topografi dan di area desain yang dimuat, sehingga model besar tetap ringan. Data demo fiktif.');
   gtOpen(true);{const w=$('bmw');w.style.left='12px';w.style.right='auto';w.style.top='78px';}await dmPoint('#gtld');dmRip();await gtLoad(dmMdlUrat());await dW(900);await dmPoint('#gttp');await dW(900);$('gtkd').open=true;await dmPoint('#gtrl');await dW(1500);await dmShotL('M01_impor_block_model','A · Block model','Impor block model (.mdl)','Menu Impor → Block model: file .mdl Surpac dibaca seperti di GC-Ex. Pilih atribut kadar & SG, aturan blok (cara Surpac = pusat blok), centang "hanya di bawah topografi", dan atur kelas kadar & tujuan (bisa impor preset GC-Ex). Data demo fiktif.');$('gtkd').open=false;gtOpen(false);};}
 if(B){const r0=B.run;B.run=async()=>{await r0();await dmBmLap('res','B · Laporan','Pit final vs topografi: ton @ g/t per kelas kadar, waste, SR dan logam tiap bench — cara Surpac (pusat blok). Kelas & tujuan memakai preset GC-Ex Block Model.');};}
 if(C){const r0=C.run;C.run=async()=>{await r0();await dmBmLap('stg','C · Laporan','Staging vs topografi: ore, waste dan SR tahap ini per bench — dasar untuk target ore bulanan.');};}}catch(e){console.warn(e);}
try{const I=DMCH.find(c=>c.id==='I');if(I){const run0=I.run;I.run=async()=>{const _cap=dmCap;dmCap=async(a,b,c)=>{if(a==='Selesai')return;return _cap(a,b,c);};try{await run0();}finally{dmCap=_cap;}};}}catch(e){}
try{const w=$('dmoList');if(w){w.innerHTML=DMCH.map((c,i)=>'<div class="fl"><button class="sm" data-dmo="'+i+'">&#9654; '+c.id+'</button><span>&nbsp;'+esc(c.nm)+'</span></div>').join('');w.querySelectorAll('[data-dmo]').forEach(b=>b.onclick=()=>dmoPlay(+b.dataset.dmo,+b.dataset.dmo+1));try{$('dmoAll').onclick=()=>dmoPlay(0,DMCH.findIndex(c=>c.id==='K'));}catch(_){}}}catch(e){}

/* Bab L — Blok tambang (bench × strip × blok): arah strip dari garis 3D, cadangan per blok, jadwal dengan klik blok */
DMCH.push({id:'L',nm:'Blok tambang: bench × strip × blok, cadangan per blok, jadwal klik blok',run:async()=>{
 const ok=()=>{try{return !!RES&&TP.some(t=>/topo_latihan_dua_lantai/.test(t.nm));}catch(_){return false;}};
 if(!ok()){await dmCap('Blok tambang','Menyiapkan pit latihan','Memakai topografi & pit dua lantai fiktif dari bab I — dijalankan cepat lebih dulu.');const I=DMCH.find(c=>c.id==='I'),sp=DMO.spd,cp0=dmCap,sh=dmShot;DMO.spd=60;dmCap=async()=>{};dmShot=async()=>{};try{await I.run();}finally{DMO.spd=sp;dmCap=cp0;dmShot=sh;}}
 const tz=p=>{const z=topoZ(p[0],p[1]);return [p[0],p[1],isFinite(z)?z:250];},BND=[[600560,9200720],[600800,9200720],[600800,9200880],[600560,9200880]].map(tz),DIR=[[600590,9200765],[600770,9200831]].map(tz);
 const lay=(re,on)=>{for(const l of document.querySelectorAll('#lay input[type=checkbox]'))if(re.test(l.parentElement.innerText)&&l.checked!==on)l.click();},S='Blok tambang',az0=$('schaz').value;
 const cap0=dmCap;dmCap=async(x,y,z)=>{await cap0(x,y,z);await dW(Math.min(5200,600+34*String(z||'').length));};
 const clickB=async(s,b)=>{const R=MB.R,col=R.L.filter(o=>o.s===s&&o.b===b).sort((a,q)=>q.k-a.k);if(!col.length)return;const o=col[0],w=schCorner(SCH.grid,(o.i0+o.i1+1)/2,(o.j0+o.j1+1)/2),q=dmScr(w[0],w[1],o.zt);await dmMove(q[0],q[1],650);dmRip();mbClick(w[0],w[1]);await dW(700);};
 try{dmWin();try{$('sayw').style.display='none';gtBig(false);gtOpen(false);schOpen(false);}catch(_){}schReset();lay(/Permukaan pit|Label RL|Garis potong|String desain/,false);
 await dmCap(S,'Seperti Minex: bench × strip × blok','Area dibagi menjadi blok tambang bernama. Yang diatur hanya ukuran blok tambang dan arah strip; kotak hitung di dalamnya dibuat sistem.');
 await dmCam([600680,9200800,240,420,0],1200);await dmClick('#mbsch');{const w=$('schw');w.style.left='12px';w.style.top='78px';}await dW(500);
 await dmCap(S+' 1','Batas fase & block model','Gambar Batas fase, lalu muat block model (.mdl) dari menu Impor. Data demo fiktif.');
 await dmClick('#schap',{noFire:true});await dmDraw(BND,true,250);schPh().bnd=BND.map(q=>q.slice());dmDrawClear();schTasks();schDrawStatic();gtMount();await gtLoad(dmMdlFiktif());await dW(600);
 await dmCap(S+' 2','Arah strip = garis yang ditarik','Klik "Arah strip" lalu tarik garis A→B di 3D: strip dibuat sejajar garis itu. Bisa ditarik ulang kapan saja.');
 await dmClick('#mbdir',{noFire:true});await dmDraw(DIR,false,250);dmDrawClear();schAdd('dir',DIR);await dW(900);
 await dmCap(S+' 3','Ukuran blok & tabel Cadangan','Isi bench × strip × blok (10 × 20 × 40 m). Blok dibuat otomatis; tombol Cadangan membuka tabelnya. Tiap blok diberi nama, mis. B250-S4-02 = bench RL 250, strip 4, blok 2.');
 await dmPoint('#mbbh');await dW(700);await dmPoint('#mbsw');await dW(700);await dmPoint('#mbbl');await dW(700);await dmPoint('#mbtb');dmRip();await mbCalc();{const w=$('mbw');w.style.left='640px';w.style.top='74px';w.style.width='780px';}await dmCam([600660,9200800,240,330,0.8],1300);
 await dmCap(S+' 4','Basis data cadangan per blok','Tiap blok tambang: volume, ton @ g/t per kelas, waste, SR, logam — dihitung sekali dari block model dengan aturan Surpac. Klik judul kolom untuk mengurutkan; CSV untuk ekspor.');
 await dmPoint('#mbws');await dW(2200);await dmPoint('#mbwt');await dW(3200);{const t=document.querySelector('#mbwt th[data-s=g]');if(t){await dmPoint(t);dmRip();t.click();await dW(2600);}}
 await dmCap(S+' 5','Blok berwarna di 3D','Warna menurut kadar ore: terlihat strip mana yang kaya. Label = strip-blok · kadar.');$('mbw').style.display='none';MB.sort='nm';mbTable();await dW(2200);
 await dmCap(S+' 5','Warna SR dan kelas dominan','Ganti warna ke SR (biru rendah → merah tinggi) atau kelas dominan (merah HG, hijau LG, cokelat waste).');
 for(const v of ['sr','kls']){const e=$('mbcol');await dmPoint(e);dmRip();e.value=v;e.dispatchEvent(new Event('change'));await dW(2600);}
 await dmCap(S+' 5','Lihat bench di bawahnya','"Tampil" bisa dipindah ke bench tertentu untuk melihat isi bench yang belum terbuka.');
 {const e=$('mbvw'),o=[...e.options];for(const i of [2,4,0]){if(!o[i])continue;await dmPoint(e);dmRip();e.value=o[i].value;e.dispatchEvent(new Event('change'));await dW(i?2200:900);}}{const e=$('mbcol');e.value='kadar';e.dispatchEvent(new Event('change'));}
 await dmCap(S+' 6','Jadwalkan dengan klik blok','Aktifkan "Klik blok", lalu klik blok di 3D: masuk antrean fleet tujuan sesuai urutan klik. Klik lagi kolom yang sama = bench berikutnya.');
 await dmClick('#mbpk');for(const [s,b] of [[4,2],[4,3],[4,4],[5,2],[5,3],[4,2],[4,3]])await clickB(s,b);
 await dmCap(S+' 6','Fleet kedua','+ Fleet membuat Fleet A2; blok yang diklik berikutnya masuk ke fleet itu (warna garis = fleet).');
 await dmClick('#schfl');for(const [s,b] of [[6,3],[6,4],[7,3]])await clickB(s,b);{const e=$('mbcol');e.value='fleet';e.dispatchEvent(new Event('change'));}await dW(2200);mbPick(false);
 await dmCap(S+' 7','Jalankan','Mesin jadwal yang sama: tiap blok digali sampai dasar bench-nya menurut kapasitas alat; lereng antar-blok tetap dijaga.');
 await dmClick('#schrun');for(let i=0;i<160&&(GT.busy||!GT.res);i++)await dRaw(250);{const e=$('mbcol');e.value='kadar';e.dispatchEvent(new Event('change'));}{const b=$('schbd');b.scrollTop=b.scrollHeight;}
 schSet(-1);await dW(600);await dmClick('#schpl');for(let i=0;i<60&&SCH.play;i++)await dRaw(250);await dW(1200);
 await dmCap(S+' 8','Laporan per periode & per fleet','Laporan Grade × Tonnage dihitung dari jadwal blok itu: per shift, per bench, per fleet — cocok dengan cadangan tiap blok.');
 gtMount();$('gtbox').open=true;gtBig(true);{const w=$('gtrw');w.style.left='590px';w.style.top='74px';w.style.width='838px';}{const e=$('gtrf');e.checked=true;e.dispatchEvent(new Event('change'));}gtBigDraw();await dmPoint('#gtrg');await dW(2600);await dmPoint('#gtrt');await dW(3800);
 await dmCap('Selesai','Blok tambang selesai','Batas fase → Arah strip → Cadangan → klik blok per fleet → Jalankan → laporan. Jalur gali dan Turun per bench tetap bisa dipakai bersama.');{const e=$('gtrf');e.checked=false;e.dispatchEvent(new Event('change'));}gtBig(false);$('gtbox').open=false;lay(/Permukaan pit|Label RL|Garis potong|String desain/,true);await dW(3000);
 }finally{dmCap=cap0;try{$('schaz').value=az0;}catch(_){}}}});
try{const w=$('dmoList');if(w){w.innerHTML=DMCH.map((c,i)=>'<div class="fl"><button class="sm" data-dmo="'+i+'">&#9654; '+c.id+'</button><span>&nbsp;'+esc(c.nm)+'</span></div>').join('');w.querySelectorAll('[data-dmo]').forEach(b=>b.onclick=()=>dmoPlay(+b.dataset.dmo,+b.dataset.dmo+1));}}catch(e){}
/* Bab M — Scheduling berdiri sendiri dengan panel 4 langkah (data → blok tambang → alat & cara gali → hasil) */
DMCH.push({id:'M',nm:'Pit Schedule 4 langkah: data sendiri, batas dari desain, simpan / impor blok, klik blok berulang, laporan',run:async()=>{
 const ok=()=>{try{return !!RES&&TP.some(t=>/topo_latihan_dua_lantai/.test(t.nm));}catch(_){return false;}};
 if(!ok()){await dmCap('Pit Schedule','Menyiapkan pit latihan','Memakai topografi & pit dua lantai fiktif dari bab I — dijalankan cepat lebih dulu.');const I=DMCH.find(c=>c.id==='I'),sp=DMO.spd,cp0=dmCap,sh=dmShot;DMO.spd=60;dmCap=async()=>{};dmShot=async()=>{};try{await I.run();}finally{DMO.spd=sp;dmCap=cp0;dmShot=sh;}}
 const tz=p=>{const z=topoZ(p[0],p[1]);return [p[0],p[1],isFinite(z)?z:250];},BND=[[600560,9200720],[600800,9200720],[600800,9200880],[600560,9200880]].map(tz),DIR=[[600590,9200765],[600770,9200831]].map(tz),LN=[[600585,9200735],[600775,9200735]].map(tz);
 const lay=(re,on)=>{for(const l of document.querySelectorAll('#lay input[type=checkbox]'))if(re.test(l.parentElement.innerText)&&l.checked!==on)l.click();},az0=$('schaz').value;
 const cap0=dmCap;dmCap=async(x,y,z)=>{await cap0(x,y,z);await dW(Math.min(5200,600+34*String(z||'').length));};
 const clickB=async(s,b,ms)=>{const R=MB.R,col=R.L.filter(o=>o.s===s&&o.b===b).sort((a,q)=>q.k-a.k);if(!col.length)return;const o=col[0],w=schCorner(SCH.grid,(o.i0+o.i1+1)/2,(o.j0+o.j1+1)/2),q=dmScr(w[0],w[1],o.zt);await dmMove(q[0],q[1],600);dmRip();mbClick(w[0],w[1]);await dW(ms||700);};
 const step=async i=>{await dmClick('#uxs'+i+' .uxh',{noFire:true});UX.sel=i;uxSync(true);await dW(500);},wtR=async()=>{for(let i=0;i<60&&!MB.R;i++)await dRaw(200);};
 UX.keep=true;try{dmWin();try{$('sayw').style.display='none';gtBig(false);gtOpen(false);schOpen(false);$('mbw').style.display='none';}catch(_){}schReset();SCH.refId=null;lay(/Permukaan pit|Label RL|Garis potong|String desain|Bentuk awal/,false);
 await dmCap('Pit Schedule','Berdiri sendiri, 4 langkah','Pit Schedule tidak bergantung pada mode Pit final / Staging. Datanya sendiri: topografi, desain acuan, block model. Panelnya 4 langkah bernomor — judul tiap langkah memberi tahu apa yang harus dilakukan.');
 await dmCam([600950,9200950,250,1150,0.55],1300);await dmClick('#mbsch');{const w=$('schw');w.style.left='12px';w.style.top='78px';}uxSync(true);await dW(900);
 await dmCap('Langkah 1 · Data','Desain acuan & block model','Desain acuan dipilih dari daftar, atau diimpor (.str / .dxf) langsung di panel — menjadi lantai galian jadwal. Block model (.mdl) juga dimuat di sini. Data demo fiktif.');
 await dmPoint('#uxtp');await dW(900);await dmPoint('#uxdes');await dW(1100);await dmPoint('#uxdfb');await dW(1100);SCH.refId='res';uxSync(true);
 await dmClick('#uxbmb',{noFire:true});gtMount();await gtLoad(dmMdlFiktif());uxSync(true);await dW(1300);
 await dmCap('Langkah 1 · Area','Pakai batas desain — satu klik','Batas area bisa diambil langsung dari tapak galian desain acuan: blok tambang seluruh pit langsung dibuat dan diwarnai kadar (cokelat = tanpa ore).');
 await dmClick('#uxbd');await wtR();await dW(600);for(let i=0;i<40&&MB._rc;i++)await dRaw(150);await dmCam([600950,9200950,250,900,0.7],1300);await dW(2600);
 await dmCap('Langkah 1 · Area','Atau gambar sendiri area kerja','Untuk menjadwalkan sebagian saja: Batas fase, klik titik-titik di 3D, Enter. Selama menggambar, tampilan terkunci dari putaran (roda = zoom, seret kanan = geser) — petunjuknya di atas 3D.');
 await dmCam([600680,9200800,240,420,0],1300);await dmClick('#schap',{noFire:true});schDigStart('bnd');await dW(500);await dmDraw(BND,true,300);await dW(700);schDigEnd(false);schPh().bnd=BND.map(q=>q.slice());MB.R=null;dmDrawClear();schTasks();schDrawStatic();await wtR();await dW(900);
 await dmCap('Langkah 2 · Blok tambang','Ukuran & arah strip','Langkah 2 sudah terisi sendiri (✓). Buka bila ingin mengubah bench × strip × blok, atau menarik Arah strip di 3D — blok dihitung ulang otomatis.');
 await step(2);await dmPoint('#mbbh');await dW(600);await dmPoint('#mbbl');await dW(600);await dmClick('#mbdir',{noFire:true});schDigStart('dir');await dW(400);await dmDraw(DIR,false,300);await dW(600);schDigEnd(false);dmDrawClear();schAdd('dir',DIR);await dW(300);MB.R=null;mbAutoCalc();await wtR();await dmCam([600660,9200800,240,330,0.8],1300);await dW(900);
 await dmCap('Langkah 2 · Blok tambang','Simpan & impor blok','Simpan blok (.str) menyimpan batas, ukuran bench × strip × blok dan arah strip. Di proyek / laptop lain: Impor blok / batas — nama blok persis sama. Poligon batas dari Surpac juga bisa diimpor.');
 await dmPoint('#mbsv');await dW(1500);await dmPoint('#mbim');await dW(1500);{const e=$('mbcol');await dmPoint(e);dmRip();e.value='kadarb';e.dispatchEvent(new Event('change'));await dW(1500);e.value='sr';e.dispatchEvent(new Event('change'));await dW(1500);e.value='kadar';e.dispatchEvent(new Event('change'));await dW(700);}
 await dmCap('Langkah 3 · Cara gali','Tiga cara, boleh digabung','Turun per bench (seluruh area), Klik blok (pilih blok satu per satu), atau Jalur gali (tarik garis arah gali). Alat tiap fleet diatur di kartu fleet.');
 await step(3);await dmPoint('#schego');await dW(900);await dmPoint('#mbpk');await dW(900);await dmPoint('#schal');await dW(900);
 await dmCap('Langkah 3 · Klik blok','Blok yang sama diklik berulang = lebih dalam','Klik blok memasukkannya ke antrean fleet. Klik blok yang sama lagi = bench berikutnya di kolom itu (Shift + klik = batal): di sini satu blok diturunkan 3 bench, tetangganya 1 bench.');
 await dmClick('#mbpk');for(const [s,b] of [[5,3],[5,3],[5,3],[5,2],[4,3],[4,2]])await clickB(s,b,900);await dW(900);
 await dmCap('Langkah 3 · Fleet kedua','+ Fleet, lalu klik blok lain','Blok berikutnya masuk ke Fleet A2. Warna garis blok = fleet; angka = urutan gali.');
 await dmClick('#schfl');for(const [s,b] of [[6,4],[6,4],[7,3],[7,4]])await clickB(s,b,800);{const e=$('mbcol');e.value='fleet';e.dispatchEvent(new Event('change'));}await dW(2000);mbPick(false);
 await dmCap('Langkah 3 · Alat','Kartu fleet','Klik baris fleet untuk mengatur alat, jumlah unit, jam kerja, PA dan UA — menentukan kapan tiap blok selesai. Lalu tekan Jalankan.');
 SCH.sel='g:A1';schTasks();schEdit();{const b=$('schbd');b.scrollTop=b.scrollHeight;}await dmPoint('#schtl');await dW(1800);await dmPoint('#sched');await dW(1800);
 await dmClick('#schrun');for(let i=0;i<160&&(GT.busy||!GT.res);i++)await dRaw(250);uxSync(true);await dW(600);
 await dmCap('Langkah 4 · Hasil','Putar jadwal','Langkah 4 terbuka sendiri. Putar: blok yang digali berulang turun paling dalam; lereng antar-blok dijaga otomatis.');
 {const e=$('mbcol');e.value='kadar';e.dispatchEvent(new Event('change'));}schSet(-1);await dW(500);await dmClick('#schpl');for(let i=0;i<80&&SCH.play;i++)await dRaw(250);await dW(1000);
 await dmCap('Langkah 4 · Laporan','Grade × Tonnage × SR','Laporan & grafik: per bench, per shift, per fleet; kolom kumulatif dan kapan selesai. CSV untuk ekspor.');
 gtMount();$('gtbox').open=true;{const u=$('schun');u.value='b';u.dispatchEvent(new Event('change'));}gtBig(true);{const w=$('gtrw');w.style.left='590px';w.style.top='74px';w.style.width='838px';}gtBigDraw();await dmPoint('#gtrg');await dW(2600);{const e=$('gtrf');await dmPoint(e);dmRip();e.checked=true;e.dispatchEvent(new Event('change'));}await dmPoint('#gtrt');await dW(3600);
 await dmCap('Selesai','Ringkasnya','1 Data & area → 2 Blok tambang (otomatis) → 3 Alat & cara gali → Jalankan → 4 Hasil & laporan.');{const e=$('gtrf');e.checked=false;e.dispatchEvent(new Event('change'));}await dW(2600);gtBig(false);$('gtbox').open=false;lay(/Permukaan pit|Label RL|Garis potong|String desain|Bentuk awal/,true);
 }finally{dmCap=cap0;UX.keep=false;try{$('schaz').value=az0;uxSync(true);}catch(_){}}}});
try{const w=$('dmoList');if(w){w.innerHTML=DMCH.map((c,i)=>'<div class="fl"><button class="sm" data-dmo="'+i+'">&#9654; '+c.id+'</button><span>&nbsp;'+esc(c.nm)+'</span></div>').join('');w.querySelectorAll('[data-dmo]').forEach(b=>b.onclick=()=>dmoPlay(+b.dataset.dmo,+b.dataset.dmo+1));}}catch(e){}
/* kait uji: siapkan pit bab I + batas fase + block model fiktif (tanpa animasi) */
try{window.__PS3.demo.prepK=async()=>{const I=DMCH.find(c=>c.id==='I'),sp=DMO.spd,cp0=dmCap,sh=dmShot;DMO.spd=60;dmCap=async()=>{};dmShot=async()=>{};try{await I.run();}finally{DMO.spd=sp;dmCap=cp0;dmShot=sh;}
 const tz=p=>{const z=topoZ(p[0],p[1]);return [p[0],p[1],isFinite(z)?z:250];};schReset();schOpen(true);schPh().bnd=[[600560,9200720],[600800,9200720],[600800,9200880],[600560,9200880]].map(tz);schTasks();schDrawStatic();gtMount();await gtLoad(dmMdlFiktif());return true;};window.__PS3.demo.cam=async f=>{const sp=DMO.spd;DMO.spd=60;try{await dmCam(f,60);}finally{DMO.spd=sp;}};}catch(_){}

/* PDF tutorial: langkah bab J / K / L dipotret otomatis saat keterangan berikutnya muncul — hanya bila perekam memasang __DMSHOT */
async function dmShotL(nm,sec,ti,tx){if(!window.__DMSHOT)return;(window.__DMLOG=window.__DMLOG||[]).push({nm,sec,ti,tx});await dmShot(nm);}
function dmAutoShot(pre){if(!window.__DMSHOT||window.__DMAUTO)return {end:async()=>{}};window.__DMAUTO=1;const c0=dmCap;let cur=null,n=0;
 const flush=async()=>{if(!cur)return;const q=cur;cur=null;if(window.__DMAUTOP)return;await dmShotL(pre+String(++n).padStart(2,'0'),q[0],q[1],q[2]);};
 dmCap=async(a,b,c)=>{await flush();cur=(a==='Selesai'||/Menyiapkan pit/.test(b)||window.__DMAUTOP)?null:[a,b,c];return c0(a,b,c);};
 return {end:async()=>{try{await flush();}finally{dmCap=c0;window.__DMAUTO=0;}}};}
for(const [id,pre] of [['J','S'],['K','T'],['L','U']]){const C=DMCH.find(c=>c.id===id);if(C){const r0=C.run;C.run=async()=>{const a=dmAutoShot(pre);try{await r0();}finally{await a.end();}};}}
