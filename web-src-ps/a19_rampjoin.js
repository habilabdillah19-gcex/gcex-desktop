/* a19 — jalan dua area bertemu (bawah→atas, beberapa area / urat).
   Setelah area-area menyatu, jalan tiap area naik sendiri-sendiri dan sering berjalan BERDAMPINGAN di jalur yang sama sampai ke atas
   (dua pita jalan bertumpuk → ujung menggantung & silang). Aturan: bila ujung dua jalan aktif berjarak < ½ lebar jalan setelah satu bench,
   kedua jalan dianggap bertemu; jalan yang lebih muda berhenti di titik temu itu, yang lebih tua meneruskan. Flag uji: __NOJOIN. */
{const _bst=benchStep;benchStep=function(st,ramps,o){const r=_bst(st,ramps,o);try{if(window.__NOJOIN||!st.up||!r||!r.ramps||r.ramps.length<2)return r;const W=(o&&o.rp?o.rp.W:RAMP().W)||12;
  const act=r.ramps.map((m,i)=>({m,i})).filter(q=>q.m&&q.m.on!==false&&q.m.act&&!q.m.ended&&!q.m.done&&q.m.pt);
  for(let a=0;a<act.length;a++)for(let b=a+1;b<act.length;b++){const A=act[a].m,B=act[b].m;if(B.ended||A.ended||B.done||A.done)continue;const d=Math.hypot(A.pt[0]-B.pt[0],A.pt[1]-B.pt[1]);if(d>=0.5*W)continue;
   /* yang lebih muda = urutan belakang (jalan area tambahan) */r.ramps[act[b].i]=Object.assign({},B,{on:false,ended:true,joined:A.nm});(r.warn=r.warn||[]).push('ℹ Jalan '+B.nm+' bertemu jalan '+A.nm+' di RL '+f1(st.z+(prmAt(st.z+0.01).H||5))+' — diteruskan sebagai satu jalan.');}}catch(e){console.warn(e);}return r;};}
/* Area tambahan yang lubangnya sudah MENYATU dengan pit area lain: sejak bench berikutnya jalan area itu tidak diteruskan
   (jalan area lama sudah melayani lubang gabungan). Mencegah dua jalan berjalan berdampingan / saling melintas di atas titik gabung. */
{const _bst2=benchStep;benchStep=function(st,ramps,o){try{if(!window.__NOJOIN&&st.up&&ramps&&ramps.length>1&&st.P&&st.P.length){const G=cOff(st.P,2).map(r=>ringOf(r)).filter(r=>r.length>2);
  const comp=pt=>{let best=-1,ba=1e18;G.forEach((R,i)=>{if(inFoot([R],pt[0],pt[1])){const a=Math.abs(cArea(toC(R)));if(a<ba){ba=a;best=i;}}});return best;};
  const live=ramps.map((m,i)=>({m,i,c:m&&m.on!==false&&m.act&&!m.ended&&m.pt?comp(m.pt):-1})).filter(q=>q.c>=0);let ch=false;const R2=ramps.slice();
  for(let a=0;a<live.length;a++)for(let b=a+1;b<live.length;b++){if(live[a].c!==live[b].c)continue;const A=live[a],Bq=live[b];/* yang diteruskan: jalan area dengan RL atas tertinggi (jalan area yang dibatasi RL atas lebih rendah toh terpotong di sana); seri → area lebih dulu */const AR=areas(),top=q=>{const t=AR[q.m.ai||0]?aTop(AR[q.m.ai||0]):NaN;return isFinite(t)?t:1e9;};const old=window.__JTOP?((top(A)>top(Bq)+0.01)||(Math.abs(top(A)-top(Bq))<=0.01&&(A.m.ai||0)<=(Bq.m.ai||0))?A:Bq):((A.m.ai||0)<=(Bq.m.ai||0)?A:Bq),young=old===A?Bq:A;/* bawaan: jalan area lebih dulu yang diteruskan (__JTOP: area RL atas tertinggi) */if(R2[young.i].on===false)continue;
   R2[young.i]=Object.assign({},young.m,{on:false,ended:true,joined:old.m.nm});ch=true;(window.__RJW=window.__RJW||[]).push('ℹ Lubang area '+young.m.nm+' menyatu dengan pit area '+old.m.nm+' di RL '+f1(st.z)+' — jalan '+young.m.nm+' berhenti di sana, jalan '+old.m.nm+' melayani pit gabungan.');}
  if(ch){const r=_bst2(st,R2,o);if(r&&window.__RJW){r.warn=(r.warn||[]).concat(window.__RJW);window.__RJW=[];}return r;}}}catch(e){console.warn(e);}return _bst2(st,ramps,o);};}
/* Cari pengaturan yang lebih rapi / Rekomendasi otomatis: kandidat tambahan pola jalan (lurus+switchback ↔ spiral) dan, untuk beberapa area,
   "tanpa jalan sendiri" bagi area tambahan (jalan area pertama melayani lubang gabungan). Kandidat ini boleh mengubah volume s.d. 40 %
   bila desain awal belum rapi (o.big). */
{const _ts=tidySet;tidySet=function(){const o=_ts();try{o.pat=($('rpat').querySelector('button.on')||{dataset:{}}).dataset.v;o.off=areas().map((a,i)=>a.noRamp?i:-1).filter(i=>i>=0);}catch(_){}return o;};}
{const _ta=tidyApply;tidyApply=function(o){_ta(o);try{if(o.pat){const b=$('rpat').querySelector('[data-v="'+o.pat+'"]');if(b&&!b.classList.contains('on'))b.click();}if(o.off){const AR=areas();AR.forEach((a,i)=>{a.noRamp=o.off.includes(i);});try{baseApply();}catch(_){}}}catch(e){console.warn(e);}};}
{const _tn=tidyNm;tidyNm=function(o){let t=_tn(o);if(o.patNm)t+=' · pola jalan '+o.patNm;if(o.offNm)t+=' · '+o.offNm;return t;};}
window.tidyMore=(C,o0)=>{if(!$('rOn').checked)return;for(const c of C){if(c.pat===undefined)c.pat=o0.pat;if(c.off===undefined)c.off=(o0.off||[]).slice();}
 const base=Object.assign({},o0,{off:(o0.off||[]).slice()});if(o0.pat==='zig'||o0.pat==='spiral'){const np=o0.pat==='zig'?'spiral':'zig';C.push(Object.assign({},base,{pat:np,patNm:np==='zig'?'lurus + switchback':'spiral',big:true}));}
 const AR=areas();if(AR.length>1){const offAll=AR.map((a,i)=>i).filter(i=>i>0);C.push(Object.assign({},base,{off:offAll,offNm:'area tambahan tanpa jalan sendiri',big:true}));if(o0.pat==='zig')C.push(Object.assign({},base,{off:offAll,pat:'spiral',patNm:'spiral',offNm:'area tambahan tanpa jalan sendiri',big:true}));}};
