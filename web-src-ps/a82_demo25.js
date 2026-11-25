/* a82 · Demo bab O — pembaruan 24 Nov 2026 (pemilik: "sesuaikan menu demo dengan seluruh pembaruan… sehumanize mungkin: angka diketik,
   transisi kamera halus"). Semua isian angka diketik (dmType), kamera selalu bertransisi (dmCam / oView), kursor berjalan ke tiap tombol.
   Isi: menu & bilah alat cascade · Properti (Umum, tab Data, lipat) · palet & ukuran tulisan · Legenda · isian adaptif · tombol Reset ·
   kartu fleet ringkas + Jalur baru · lapisan jadwal (Hanya permukaan, transparansi) · jadwal otomatis (SR maks wajib %) ·
   posisi sayatan di 3D (bidang, peta kunci, kursor, lihat di 3D). */
DMCH.push({id:'O',nm:'Antarmuka baru: cascade, Properti ala Ore Works, palet, lapisan jadwal, jadwal otomatis, sayatan di 3D',run:async()=>{
 const ok=()=>{try{return !!RES&&TP.some(t=>/topo_latihan_dua_lantai/.test(t.nm))&&!!GT.file;}catch(_){return false;}};
 if(!ok()){await dmCap('Antarmuka baru','Menyiapkan pit latihan','Memakai topografi & pit dua lantai fiktif dari bab I + block model fiktif — dijalankan cepat lebih dulu.');const sp=DMO.spd,cp0=dmCap,sh=dmShot;DMO.spd=60;dmCap=async()=>{};dmShot=async()=>{};try{await window.__PS3.demo.prepK();}finally{DMO.spd=sp;dmCap=cp0;dmShot=sh;}}
 let GK=0;const guard=async f=>{GK++;if(window.__OONLY&&!window.__OONLY.includes(GK))return;try{await f();}catch(e){if(e===DMO_STOP||e===DMO_SKIP)throw e;console.warn('demo O',e);}};
 const mBtn=nm=>[...document.querySelectorAll('.shmt')].find(b=>b.textContent.trim().indexOf(nm)===0);
 const openMenu=async nm=>{const mb=mBtn(nm);if(!mb)return null;await dmClick(mb,{noFire:true});mb.click();await dW(650);return mb;};
 const closeAll=()=>{try{cmClose();}catch(_){}try{shClose();}catch(_){}try{tbgClose();}catch(_){}};
 const fly=async(id,txt)=>{const b=$(id);if(!b)return;await dmPoint(b,700);await dW(150);if(!(CM&&CM._b===b))b.onclick();await dW(900);if(txt){const it=[...document.querySelectorAll('.cmenu .ci')].find(e=>e.innerText.indexOf(txt)>=0);if(it){await dmPoint(it,700);dmRip();await dW(200);it.click();}}await dW(500);};
 /* ganti arah pandang dengan transisi halus, pusat & jarak zoom dijaga */
 const oView=async(v,ms)=>{const D={plan:[0,1,0.0001],sw:[-0.62,0.62,0.48],ne:[0.62,0.62,-0.48],ew:[0,0.05,1],ns:[1,0.05,0]}[v];const t=CT.target.clone(),d=C.position.distanceTo(t),n1=new THREE.Vector3(...D).normalize(),n0=C.position.clone().sub(t).normalize();const T=(ms||1100);let k=0;
  while(k<1){k=Math.min(1,k+16*DMO.spd/T);const e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2,n=n0.clone().lerp(n1,e).normalize();C.position.copy(t).addScaledVector(n,d);C.up.set(0,1,0);CT.update();await dRaw(16);}};
 const see=async e=>{try{if(typeof e==='string')e=document.querySelector(e);if(e){e.scrollIntoView({block:'center'});await dW(350);}}catch(x){if(x===DMO_STOP||x===DMO_SKIP)throw x;}};
 const slide=async(el,to,ms)=>{if(!el)return;await dmPoint(el,600);dmRip();const a=+el.value,n=14;for(let i=1;i<=n;i++){el.value=Math.round(a+(to-a)*i/n);el.dispatchEvent(new Event('input'));await dW((ms||700)/n);}el.dispatchEvent(new Event('change'));await dW(300);};
 try{schOpen(false);gtBig(false);gtOpen(false);$('mbw').style.display='none';}catch(_){}dmWin();closeAll();
 if(MODE==='edit'){try{$('tabs').querySelector('[data-t="design"]').click();}catch(_){}await dW(500);}

 /* ---- 1. cascade ---- */
 await guard(async()=>{await dmCam([600950,9200950,235,1150,0.6],1400);
  await dmCap('O · Antarmuka','Menu cascade','Tiap judul menu bertanda ▾. Butir yang punya anak (▸) terbuka ke samping saat kursor lewat — menu induknya tetap terbuka.');
  await openMenu('Desain');await fly('mbds');await dW(1400);await dmShot('O01_menu_cascade',['.cmenu']);closeAll();await dW(300);
  await dmCap('O · Antarmuka','Bilah alat cascade & zoom terjaga','Pandangan ▾ berisi enam arah pandang. Ganti arah TIDAK lagi me-reset zoom: titik pusat dan jarak dijaga; hanya "Pas" yang membingkai ulang.');
  await dmCam([600800,9200800,225,430,0.7],1500);const g=document.querySelector('#ptb .tbg .tbgb');
  for(const [i,v] of [[1,'sw'],[2,'ne'],[0,'plan'],[1,'sw']]){if(g){await dmClick(g,{noFire:true});g.onclick({stopPropagation(){}});await dW(450);const it=document.querySelectorAll('#ptb .tbg.op .tbdd button.tb')[i];if(it){await dmPoint(it,500);dmRip();await dW(200);}tbgClose();}await oView(v,1200);await dW(500);}
  await dmShot('O02_bilah_cascade',['#ptb .tbg']);});

 /* ---- 2. Properti ---- */
 await guard(async()=>{await dmCam([600950,9200950,235,1150,0.6],1300);
  await dmCap('O · Properti','Gaya Ore Works: Umum · Data · lipat','Kepala bertab PROPERTI | DATA, judul objek + jenis, kisi Umum (label | nilai). Bar bagian diklik = dilipat. Tab DATA merangkum topografi, block model dan desain.');
  try{dsOpen(1);}catch(_){}await dW(800);const u=document.querySelector('#pgw .pgs');if(u){if(u.classList.contains('cl')){await dmClick(u);await dW(700);}await dmShot('O03_properti',['#pgw']);await dmClick(u);await dW(900);await dmClick(u);await dW(600);}
  const tb=document.querySelector('#side>.shph>.tabx');if(tb){await dmClick(tb);await dW(1800);await dmShot('O04_tab_data',['#pgd']);const t0=document.querySelector('#side>.shph>.tab0');await dmClick(t0);await dW(600);}});

 /* ---- 3. palet & ukuran tulisan ---- */
 await guard(async()=>{await dmCap('O · Tampilan','Palet warna & ukuran tulisan','Tampilan → Palet warna ▸ (10 palet seperti Ore Works; warna data tidak berubah) dan Ukuran tulisan ▸ (85–120 %; lebih kecil = ruang 3D lebih luas).');
  for(const nm of ['Malakit','Oksida','Hitam-putih']){await openMenu('Tampilan');await fly('mbpal',nm);closeAll();await dW(1500);}
  await dmShot('O05_palet');await openMenu('Tampilan');await fly('mbpal','aksen Pit Studio');closeAll();try{window.__PS3.pal.set('bawaan');}catch(_){}await dW(800);
  await openMenu('Tampilan');await fly('mbfz','85%');closeAll();await dW(1800);await dmShot('O06_ukuran_tulisan');await openMenu('Tampilan');await fly('mbfz','100%');closeAll();try{fzSet(100);}catch(_){}await dW(700);});

 /* ---- 4. Legenda ---- */
 await guard(async()=>{await dmCap('O · Tampilan','Legenda di pojok 3D','Seperti Ore Works: seret kepalanya untuk memindah, – memperkecil jadi strip, ✕ menutup; tombol Legenda di bilah alat menampilkannya lagi.');
  LGX.off=false;LGX.min=false;lgState();await dW(400);const w=$('lgw'),h=w&&w.querySelector('.flh b');if(h){await dmPoint(h,700);dmRip();const p=w.offsetParent,x0=w.offsetLeft,y0=w.offsetTop,x1=Math.max(20,x0-260),y1=Math.max(20,y0-200);for(let i=1;i<=20;i++){LGX.x=x0+(x1-x0)*i/20;LGX.y=y0+(y1-y0)*i/20;lgPlace();const r=h.getBoundingClientRect();DMO.cx=r.left+10;DMO.cy=r.top+6;$('dmoCur').style.left=DMO.cx+'px';$('dmoCur').style.top=DMO.cy+'px';await dW(40);}await dW(500);
   await dmClick('#lgw .lgk[data-k=min]');await dW(900);await dmClick('#lgw .lgk[data-k=min]');await dW(600);await dmClick('#lgw .lgk[data-k=x]');await dW(700);await dmClick('#ptbl');await dW(700);await dmShot('O07_legenda',['#lgw','#ptbl']);LGX.x=null;LGX.y=null;lgSave();lgPlace();}});

 /* ---- 5. isian adaptif + reset ---- */
 await guard(async()=>{await dmCap('O · Desain','Isian adaptif menurut mode','Yang tidak relevan tidak ditampilkan: Dasar pit → RL dasar + RL atas; Puncak pit → RL crest + RL bawah; Batas topo → RL bawah saja. "Buat jalan" mati → isian jalan hilang.');
  try{dsOpen(0);}catch(_){}await dW(900);for(const v of ['top','topo','bot']){await dmClick('#smode [data-v='+v+']');adApply();await dW(1500);}await dmShot('O08_adaptif',['#zmaxw^']);
  try{dsOpen(2);}catch(_){}await dW(800);await dmClick('#rOn');adApply();await dW(1400);await dmClick('#rOn');adApply();await dW(900);
  await dmCap('O · Antarmuka','Tombol Reset','Satu tombol di bilah alat, isinya menurut panel yang terbuka: hapus hasil desain, hapus hasil jadwal, kosongkan jadwal, atau batalkan semua edit.');
  await dmClick('#ptbr');await dW(1700);await dmShot('O09_reset',['#rsm']);const m=$('rsm');if(m)m.remove();});

 /* ---- 6. Pit Schedule: kartu fleet, Jalur baru, lapisan ---- */
 await guard(async()=>{dmWin();await dmCam([600950,9200950,235,1250,0.55],1400);
  await dmCap('O · Pit Schedule','Kartu fleet ringkas & "Jalur baru"','Kartu fleet tertutup bawaan (satu baris ringkasan). Di dalamnya, kotak "Jalur baru" mengatur jalur yang ditarik BERIKUTNYA: lebar (kotak hitung), dalam gali (lapis per lintasan), jumlah lintasan.');
  try{rsSchAll();}catch(_){}caraOpen();await dW(600);try{await mbCalc(true);}catch(_){}$('mbw').style.display='none';caraSet('jalur');await dW(900);
  const Ls=MB.R?MB.R.L:[];if(Ls.length){const s=Ls[Ls.length>>1].s,q=Ls.filter(o=>o.s===s).sort((a,b)=>a.b-b.b),G0=SCH.grid,cen=o=>{const w=schCorner(G0,(o.i0+o.i1+1)/2,(o.j0+o.j1+1)/2);return [w[0],w[1]];},a=cen(q[0]),c=cen(q[q.length-1]);
   await dmDraw([a,c],false);schAdd('line',[a,c],{});dmDrawClear();await dW(700);}
  const row=document.querySelector('#schtl .ti');if(row){await see(row);await dmClick(row);await dW(600);}await see('#sched');const sm=document.querySelector('#schedd>summary');if(sm){const d=$('schedd');if(d.open){d.open=false;await dW(300);}await dmShot('O10_kartu_fleet',['#sched']);await dmClick(sm);await dW(900);}
  await see('#sched .pgj');await dmType('#sched [data-k=nbN]',6);await dW(500);await dmType('#sched [data-k=flN]',2);await dW(500);await dmShot('O11_jalur_baru',['#sched .pgj']);
  await see('#schrun');await dmClick('#schrun');for(let i=0;i<80&&!SCH.sim;i++)await dRaw(200);await dW(1500);
  await dmCap('O · Pit Schedule','Lapisan jadwal: Hanya permukaan & transparansi','Kerangka blok sering menutupi topografi yang sudah turun. Tombol Permukaan menyembunyikan semua kerangka sekaligus; di panel Lapisan tiap lapisan punya centang dan ada penggeser transparansi blok.');
  await dmCam([600950,9200950,235,820,0.7],1500);await dmClick('#ptbs');await dW(1800);await dmShot('O12_hanya_permukaan',['#ptbs']);await dmClick('#ptbs');await dW(900);
  try{layRender();}catch(_){}await dW(300);await slide($('lyxo'),25,900);await dW(900);await slide($('lyxo'),100,700);
  const fr=[...document.querySelectorAll('#layb .lrow')].find(x=>/garis kerangka/.test(x.textContent));if(fr){const cb=fr.querySelector('input');await dmClick(cb);await dW(1300);await dmShot('O13_lapisan',['#lyxc']);await dmClick(fr.querySelector('input')||cb);await dW(600);}LYX.frame=true;LYX.op=100;LYX.solo=false;lyxSave();lyxApply();});

 /* ---- 7. jadwal otomatis ---- */
 await guard(async()=>{await dmCap('O · Pit Schedule','Jadwal otomatis: target rentang & SR wajib','Otomatis: blok atas habis dulu, kupas dulu supaya stok ore terbuka terjaga, SR diratakan. Isi SR maks dan persen periode yang wajib memenuhinya — bila tak mungkin lagi, jadwal berhenti dan memberi tahu.');
  await dmCam([600950,9200950,235,1250,0.55],1300);caraSet('auto');await dW(900);document.querySelectorAll('#plwb details').forEach(d=>d.open=true);await dW(400);
  const f=k=>document.querySelector('#plwb [data-ak="'+k+'"]');await see(f('tg.srmax'));if(f('tg.srmax')){await dmType(f('tg.srmax'),'1.2');await dW(400);}if(f('tg.srpct')){await dmType(f('tg.srpct'),'90');await dW(400);}await dmShot('O14_target_otomatis',['#plwb']);
  const rb=document.querySelector('#plwb [data-pa=run]');if(rb){await see(rb);await dmClick(rb);await dW(2200);}const sm=$('apsum');if(sm){try{sm.scrollIntoView({block:'center'});}catch(_){}await dW(600);await dmShot('O15_hasil_otomatis',['#apsum']);}await dW(2500);
  try{plStop();}catch(_){}const tl=$('pltl');if(tl)tl.style.display='none';});

 /* ---- 8. sayatan di 3D ---- */
 await guard(async()=>{try{rsSchAll();}catch(_){}try{schOpen(false);}catch(_){}dmWin();closeAll();await dmCam([600950,9200950,235,1100,0.62],1400);
  await dmCap('O · Sayatan','Di mana sayatan ini di 3D?','Empat pilihan di jendela Sayatan (semua mati bawaan): Bidang = tirai tegak A→B di 3D · Peta kunci = denah kecil di gambar (ikut PNG) · Kursor = penanda ikut di 3D · Lihat di 3D = kamera tegak lurus + model dipotong.');
  let a=[600620,9200650],b=[601280,9201250];try{const R0=curR();if(R0&&R0.foot&&R0.foot[0]){let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(const p of R0.foot[0]){x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}a=[x0-30,y0-30];b=[x1+30,y1+30];}}catch(_){}
  await dmDraw([a,b],false);saySet(a,b);dmDrawClear();const w=$('sayw');w.style.left='252px';w.style.right='auto';w.style.top='8px';w.style.bottom='auto';w.style.width='930px';w.style.height='296px';await dW(900);try{sayDraw();}catch(_){}await dW(600);
  LGX.off=true;lgState();await dmCam([600950,9200995,235,900,0.7],1300);
  await dmClick('#syxb [data-sx=plane]');await dW(1800);await dmShot('O16_bidang_sayatan',['#syxb']);await dmClick('#syxb [data-sx=key]');await dW(1700);await dmShot('O17_peta_kunci',['#saycv']);
  await dmClick('#syxb [data-sx=cur]');await dW(500);const cvs=$('saycv'),r=cvs.getBoundingClientRect();for(let i=0;i<=40;i++){const x=r.left+r.width*(0.2+0.55*i/40),y=r.top+r.height*(0.45+0.12*Math.sin(i/6));await dmMove(x,y,60);cvs.dispatchEvent(new MouseEvent('mousemove',{clientX:x,clientY:y,bubbles:true}));await dW(50);}await dmShot('O18_kursor_3d');await dW(600);
  await dmClick('#syxb [data-sx=cut]');await dW(3000);await dmShot('O19_lihat_di_3d');await dmClick('#syxb [data-sx=cut]');await dW(1200);
  for(const k of ['cur','key','plane'])if(SYX[k]){SYX[k]=false;}syxSave();syxPlane();syxCur(null);syxUi();const x=$('sayx');if(x)x.click();LGX.off=false;lgState();await dW(400);});
 closeAll();dmWin();await dmCam([600950,9200950,240,1300,0.55],1400);
 await dmCap('O · Selesai','Pembaruan 24 November','Cascade · Properti ala Ore Works · palet & ukuran tulisan · Legenda · isian adaptif · Reset · lapisan jadwal · jadwal otomatis · sayatan di 3D. Bahasa EN / ES / SU ikut diperbarui.');await dW(2500);
}});
