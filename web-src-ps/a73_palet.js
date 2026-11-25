/* a73 · PALET WARNA (10 palet) — pola Ore Works 0.24.0 / web-src/palet.js GC-Ex (24 Nov 2026, pemilik:
   "Untuk tampilan ambil juga multiple color palet dari Ore Works").
   Teks asli tiap <style> bertema disimpan; tiap warna hex yang dekat ke warna jangkar palet bawaan digeser ke jangkar palet
   terpilih dengan selisih yang sama. #FFFFFF / #000000 tidak disentuh. Warna DATA (topografi, crest/toe, blok, kadar) ada di
   JS / WebGL, bukan di <style>, jadi tidak berubah. Letak: Tampilan → Palet warna ▸. Diingat per komputer (localStorage psPalet). */
(function(){
 const hx=h=>{h=h.replace('#','');return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)];};
 const th=a=>'#'+a.map(v=>{v=Math.round(Math.max(0,Math.min(255,v))).toString(16);return v.length<2?'0'+v:v;}).join('').toUpperCase();
 const mix=(a,b,t)=>{const A=hx(a),B=hx(b);return th(A.map((v,i)=>v+(B[i]-v)*t));};
 const lum=h=>hx(h).map(v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);}).reduce((s,v,i)=>s+v*[0.2126,0.7152,0.0722][i],0);
 const kontras=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);};
 const tombol=c=>{for(let k=0;k<30&&kontras(c,'#FFFFFF')<4.9;k++)c=mix(c,'#000000',0.06);return c;};
 /* jangkar = palet bawaan Pit Studio (kerangka a45: navy dof + panel hangat + aksen azurit) */
 const BASE={chrome:'#1C2733',chrome2:'#2D3D4F',chromeTx:'#E8ECF1',bar:'#EDEBE6',dock:'#F7F5F0',line:'#D3CDC1',accent:'#2B5F9E',accent2:'#B5893E',btn:'#1D5FD1',sel:'#DBE7FB',sub:'#6C757D'};
 const HANGAT=['#D9D6CC','#EDEBE5','#F8F6F1'];
 const PAL=[
  {k:'dasar',nm:'Dasar (palet pertama Pit Studio)',c:{chrome:'#14234A',chrome2:'#22346A',chromeTx:'#E9EEF5',bar:'#EEF1F5',dock:'#FFFFFF',line:'#D3D9E2',accent:'#1D5FD1',accent2:'#1D5FD1',btn:'#1D5FD1',sel:'#E8F0FD',sub:'#5D6878'},bg:['#DFE6F0','#EEF2F7','#FFFFFF']},
  {k:'malakit',nm:'Malakit',c:{chrome:'#14322F',chromeTx:'#E4EFEC',bar:'#F3F1EC',dock:'#FAF8F4',line:'#D5D0C6',accent:'#1E8C6E',accent2:'#B8692E',sel:'#D7EDE5',sub:'#5C6660'},vp:'#EEF1EE'},
  {k:'oksida',nm:'Oksida',c:{chrome:'#262321',chromeTx:'#F1ECE6',bar:'#F4F1ED',dock:'#FBF9F6',line:'#D8D1C8',accent:'#C4571E',accent2:'#3F7D74',sel:'#F5E1D3',sub:'#665E57'},vp:'#F1EFEC'},
  {k:'kuarsa',nm:'Kuarsa-Emas',c:{chrome:'#1F2328',chromeTx:'#ECEDEF',bar:'#F2F2F0',dock:'#FAFAF8',line:'#D3D3CF',accent:'#A88412',accent2:'#4A6B8A',sel:'#F1E7C4',sub:'#5D6168'},vp:'#EFF0F0'},
  {k:'azurit',nm:'Azurit',c:{chrome:'#16205A',chromeTx:'#E6E9F7',bar:'#F3F4F9',dock:'#FAFAFD',line:'#D2D5E4',accent:'#2F4BC4',accent2:'#1E8C6E',sel:'#DCE2FA',sub:'#5A5F75'},vp:'#EEF0F6'},
  {k:'garnierit',nm:'Garnierit',c:{chrome:'#1E3A2C',chromeTx:'#E8F1E6',bar:'#F4F3EB',dock:'#FBFAF4',line:'#D6D3C2',accent:'#4E9A3E',accent2:'#A8692A',sel:'#E0EED3',sub:'#5D6655'},vp:'#F0F2EC'},
  {k:'garmal',nm:'Garnierit-Malakit',c:{chrome:'#1B3A30',chromeTx:'#E6F0EA',bar:'#F4F3EC',dock:'#FBFAF5',line:'#D4D2C3',accent:'#17806B',accent2:'#A8692A',sel:'#D5ECE4',sub:'#5A645B'},vp:'#EFF2EE'},
  {k:'gcex',nm:'GC-Ex (seperti Drill Hole)',c:{chrome:'#1C2733',chrome2:'#2C3B57',chromeTx:'#E8ECF2',bar:'#EDEBE6',dock:'#F7F5F0',line:'#D3CDC1',accent:'#B5893E',accent2:'#2C3B57',btn:'#2C3B57',sel:'#F0E5CF',sub:'#5C6672'},bg:HANGAT},
  {k:'bawaan',nm:'Keluarga GC-Ex · aksen Pit Studio (bawaan)',bawaan:true,c:BASE,bg:HANGAT},
  {k:'hp',nm:'Hitam-putih',c:{chrome:'#141414',chrome2:'#2A2A2A',chromeTx:'#F2F2F2',bar:'#EEEEEE',dock:'#F8F8F8',line:'#CFCFCF',accent:'#2B2B2B',accent2:'#7A7A7A',sel:'#E1E1E1',sub:'#5E5E5E'},bg:['#D4D4D4','#E8E8E8','#FAFAFA']}];
 const ANK=Object.keys(BASE).map(k=>[k,hx(BASE[k])]);
 /* aksen lama (biru tombol / sorot dari lapisan sebelum kerangka) ikut jangkar yang sama */
 [['btn','#1F6FEB'],['btn','#164DB0'],['accent','#0067C0'],['sel','#CCE4F7'],['sel','#E8F0FD'],['sel','#D6E4F5'],['chrome','#1B2A4E'],['chrome','#101828'],['chrome','#14234A'],['line','#B8C4D6'],['bar','#E6EBF2'],['bar','#EEF1F5']].forEach(a=>ANK.push([a[0],hx(a[1]),hx(BASE[a[0]])]));
 function target(P){const c=Object.assign({},P.c);if(!c.chrome2)c.chrome2=mix(c.chrome,'#FFFFFF',0.12);if(!c.accent2)c.accent2=c.accent;c.btn=c.btn?c.btn:tombol(c.accent);return c;}
 function peta(P){const c=target(P),cache={};return h=>{const k=h.toUpperCase();if(cache[k])return cache[k];const v=hx(k);let best=null,bd=1e9;
   if(k!=='#FFFFFF'&&k!=='#000000')for(const a of ANK){const d=Math.hypot(v[0]-a[1][0],v[1]-a[1][1],v[2]-a[1][2]);if(d<bd){bd=d;best=a;}}
   let r=h;if(best&&bd<=(/^(accent|accent2|btn|sel)$/.test(best[0])?45:60)){const t=hx(c[best[0]]),a=best[1];r=th(v.map((x,i)=>t[i]+(x-a[i])));}
   cache[k]=r;return r;};}
 const ASLI=new WeakMap();
 const bertema=s=>{if(s.id==='psPalBg')return false;if(ASLI.has(s))return true;const t=s.textContent||'';if(/#[0-9a-fA-F]{6}/.test(t)){ASLI.set(s,t);return true;}return false;};
 let PK='bawaan',tunda=false;try{PK=localStorage.getItem('psPalet')||'bawaan';}catch(_){}
 function bgP(P){if(P.bg)return P.bg;const c=P.c,vp=P.vp||c.dock;return [mix(vp,c.line,0.55),mix(vp,c.line,0.2),mix(vp,'#FFFFFF',0.45)];}
 function latar(P){let s=document.getElementById('psPalBg');if(P.bawaan){if(s)s.remove();return;}const B=bgP(P);if(!s){s=document.createElement('style');s.id='psPalBg';}
  s.textContent='body.shx #cv{background:linear-gradient('+B[0]+','+B[1]+' 55%,'+B[2]+')!important}';document.body.appendChild(s);}
 function terapkan(k){const P=PAL.find(p=>p.k===k)||PAL.find(p=>p.bawaan);PK=P.k;try{localStorage.setItem('psPalet',PK);}catch(_){}
  tunda=true;const f=P.bawaan?null:peta(P);
  document.querySelectorAll('style').forEach(s=>{if(!bertema(s))return;const t=ASLI.get(s);const n=f?t.replace(/#[0-9a-fA-F]{6}(?=[0-9a-fA-F]{2}(?![0-9a-fA-F])|(?![0-9a-fA-F]))/g,m=>f(m)):t;if(s.textContent!==n)s.textContent=n;});
  tunda=false;document.body.dataset.palet=PK;latar(P);try{dispatchEvent(new Event('resize'));}catch(_){}}
 const mo=new MutationObserver(ms=>{if(tunda||PK==='bawaan')return;for(const m of ms)for(const n of m.addedNodes)if(n.tagName==='STYLE'&&n.id!=='psPalBg'&&bertema(n)){terapkan(PK);return;}});
 const menu=()=>[{hd:'Palet warna antarmuka'}].concat(PAL.map((p,i)=>{const c=target(p);return {t:(i+1)+'. '+p.nm,ic:'',on:()=>p.k===PK,fn:()=>terapkan(p.k),tip:'Bingkai '+c.chrome+' · aksen '+c.accent+' · panel '+c.dock};}),['-',{hd:'Warna data (topo, blok, kadar) tidak berubah'}]);
 function tombolMenu(){if(document.getElementById('mbpal'))return;const ms=[...document.querySelectorAll('.shm')].find(m=>/^Tampilan|^View|^Vista/.test(m.querySelector('.shmt').textContent.trim()));if(!ms)return;const p=ms.querySelector('.shmp');
  const b=document.createElement('button');b.id='mbpal';b.className='mbb';b.textContent='◐ Palet warna';b.title='Ganti palet warna antarmuka (10 pilihan) — warna data tidak berubah';b.onclick=()=>cmOpen(b,menu());
  const ref=[...p.children].find(e=>/Tata letak|Layout|Diseño/.test(e.textContent)&&e.classList.contains('shcap'));if(ref)p.insertBefore(b,ref);else p.appendChild(b);
  try{if(typeof CASC_ID!=='undefined'&&!CASC_ID.includes('mbpal'))CASC_ID.push('mbpal');}catch(_){}}
 window.__PS3=window.__PS3||{};window.__PS3.pal={list:()=>PAL.map(p=>({k:p.k,nm:p.nm,c:target(p)})),set:terapkan,get:()=>PK,kontras};
 const mulai=()=>{mo.observe(document.head,{childList:true});mo.observe(document.body,{childList:true});tombolMenu();if(PK!=='bawaan')terapkan(PK);};
 setTimeout(mulai,0);setInterval(tombolMenu,1500);
})();
