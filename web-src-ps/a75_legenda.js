/* a75 · (24 Nov 2026, pemilik)
   1) "Mengapa ada dua 'Play-Doh' di bilah alat?" → label bagian (.tl: Manual / Play-Doh / Edit+) disembunyikan; tinggal tombol tarik.
   2) "Kotak kuning itu mengatur apa?" → dijadikan tiga baris kisi berjudul "Jalur baru (yang ditarik berikutnya)":
      Lebar jalur (kotak) · Dalam gali (lapis per lintasan) · Jumlah lintasan.
   3) "Perlakukan Legenda seperti di Ore Works" → jendela kecil di pojok 3D: bisa diseret, – perkecil jadi strip, ✕ tutup,
      tombol Legenda di bilah alat untuk menampilkan lagi; posisi & keadaan diingat. Tombol tempel kiri/kanan/lepas dibuang. */
(function(){const st=document.createElement('style');st.textContent=`
body.shx #ptb .tl{display:none!important}
body.shx #dock .r.pgj{display:block!important;background:#FBF3D0!important;border:1px solid #E6D9A2;border-radius:2px!important;padding:0!important;margin:3px 0!important}
body.shx #dock .r.pgj>.pgjh{padding:3px 6px;font-size:11px;font-weight:700;color:#5b4a12;border-bottom:1px solid #E6D9A2}
body.shx #dock .r.pgj>.pgjh span{font-weight:400;color:#7a6a2f}
body.shx #dock .r.pgj>.pgjr{display:flex;align-items:center;gap:6px;min-height:25px;padding:1px 6px;border-bottom:1px solid #EFE4B8}
body.shx #dock .r.pgj>.pgjr:last-child{border-bottom:0}
body.shx #dock .r.pgj>.pgjr>span:first-child{flex:0 0 34%;color:#495057}body.shx #dock .r.pgj>.pgjr>input{flex:0 0 70px;width:70px!important}body.shx #dock .r.pgj>.pgjr>i{font-style:normal;color:#6c757d;font-size:11px}
/* Legenda ala Ore Works */
body.shx #lgw.lgx{position:absolute!important;width:214px!important;min-width:0!important;border:1px solid #D3CDC1!important;border-radius:2px!important;box-shadow:0 2px 8px #0000001f!important;background:#F7F5F0!important;z-index:9!important}
body.shx #lgw.lgx .flh{background:#EDEBE6!important;color:#1C2733!important;cursor:move!important;padding:3px 4px 3px 8px!important;display:flex!important;align-items:center;border-bottom:1px solid #D3CDC1;border-radius:0!important}
body.shx #lgw.lgx .flh b{color:#1C2733!important;font-size:11px;letter-spacing:.6px;text-transform:uppercase}
body.shx #lgw.lgx .flh>button:not(.lgk),body.shx #lgw.lgx .flh>span:not(.lgsp){display:none!important}
body.shx #lgw.lgx .flh .lgk{background:none!important;border:0!important;box-shadow:none!important;color:#5C6672!important;width:20px;height:18px;padding:0!important;margin:0!important;font-size:12px;cursor:pointer;min-width:0!important}
body.shx #lgw.lgx .flh .lgk:hover{background:#DDD9D0!important;color:#1C2733!important}
body.shx #lgw.lgx .flb{padding:5px 9px!important;max-height:46vh;overflow:auto;background:#F7F5F0!important}
body.shx #lgw.lgx.lgmin{width:auto!important}body.shx #lgw.lgx.lgmin .flb{display:none!important}body.shx #lgw.lgx.lgmin .flh{border-bottom:0}
body.shx #lgw.lgx.lgoff{display:none!important}
body.shx #lgw.lgx .flrz,body.shx #lgw.lgx .flrzr{display:none!important}
`;document.head.appendChild(st);})();

/* ---------- 2. kotak "jalur baru" → tiga baris ---------- */
function pgjFix(root){for(const i of root.querySelectorAll('.r input[data-k="nbN"]')){const r=i.closest('.r');if(!r||r.classList.contains('pgj'))continue;const a=r.querySelector('[data-k=nbN]'),b=r.querySelector('[data-k=flN]'),c=r.querySelector('[data-k=repN]');if(!a||!b||!c)continue;
  const row=(l,inp,u,tip)=>{const d=document.createElement('div');d.className='pgjr';d.title=tip;const s=document.createElement('span');s.textContent=l;const k=document.createElement('i');k.textContent=u;d.appendChild(s);d.appendChild(inp);d.appendChild(k);return d;};
  const h=document.createElement('div');h.className='pgjh';h.innerHTML='Jalur baru <span>— berlaku untuk jalur yang ditarik berikutnya</span>';
  const R=[row('Lebar jalur',a,'kotak hitung','Lebar galian jalur, dalam jumlah kotak hitung (bawaan = selebar strip)'),row('Dalam gali',b,'lapis per lintasan','Kedalaman yang digali setiap kali alat melintas, dalam lapis (bawaan = 1 bench)'),row('Jumlah lintasan',c,'× lewat','Berapa kali alat melintasi jalur yang sama; tiap lintasan turun sedalam isian di atas')];
  r.textContent='';r.removeAttribute('style');r.classList.remove('pgx');r.classList.add('pgj','pgn');r.appendChild(h);R.forEach(x=>r.appendChild(x));}}
{const _w=pgxWrap;pgxWrap=function(root){try{pgjFix(root);}catch(e){console.warn('pgj',e);}return _w.apply(this,arguments);};}

/* ---------- 3. Legenda ---------- */
const LGX={min:false,off:false,x:null,y:null};try{Object.assign(LGX,JSON.parse(localStorage.getItem('psLeg')||'{}'));}catch(_){}
function lgSave(){try{localStorage.setItem('psLeg',JSON.stringify(LGX));}catch(_){}}
function lgPlace(){const w=$('lgw');if(!w||!w.classList.contains('lgx'))return;const p=w.offsetParent||w.parentElement;if(!p)return;const W=p.clientWidth,H=p.clientHeight,ww=w.offsetWidth||214,wh=w.offsetHeight||60;
 let x=LGX.x==null?W-ww-10:LGX.x,y=LGX.y==null?H-wh-34:LGX.y;x=Math.max(2,Math.min(W-ww-2,x));y=Math.max(2,Math.min(H-wh-2,y));
 const S=(k,v)=>w.style.setProperty(k,v,'important');S('left',x+'px');S('top',y+'px');S('right','auto');S('bottom','auto');}
function lgState(){const w=$('lgw');if(!w)return;w.classList.toggle('lgmin',!!LGX.min);w.classList.toggle('lgoff',!!LGX.off);const m=w.querySelector('.lgk[data-k=min]');if(m){m.textContent=LGX.min?'▢':'–';m.title=LGX.min?'Buka legenda':'Perkecil jadi strip';}const b=$('ptbl');if(b)b.classList.toggle('on',!LGX.off);lgPlace();}
function lgInit(){const w=$('lgw');if(!w||w.classList.contains('lgx')||!document.body.classList.contains('shx'))return;try{if(w.classList.contains('dkd'))dkpSet('lgw','');}catch(_){}
 const cv=$('cv');if(cv&&w.parentElement!==cv&&!w.classList.contains('dkd'))cv.appendChild(w);w.classList.add('lgx');const h=w.querySelector('.flh');
 const sp=document.createElement('span');sp.className='lgsp';sp.style.flex='1';h.appendChild(sp);
 for(const [k,t] of [['min','–'],['x','✕']]){const b=document.createElement('button');b.className='lgk';b.dataset.k=k;b.textContent=t;if(k==='x')b.title='Tutup (tampilkan lagi: tombol Legenda di bilah alat)';h.appendChild(b);}
 h.addEventListener('click',e=>{const b=e.target.closest('.lgk');if(!b)return;e.stopPropagation();if(b.dataset.k==='min')LGX.min=!LGX.min;else LGX.off=true;lgSave();lgState();},true);
 h.addEventListener('dblclick',e=>{e.stopPropagation();e.preventDefault();LGX.min=!LGX.min;lgSave();lgState();},true);
 h.addEventListener('pointerdown',e=>{if(e.target.closest('.lgk')||e.button)return;e.stopPropagation();e.preventDefault();const p=w.offsetParent||w.parentElement,r=w.getBoundingClientRect(),pr=p.getBoundingClientRect(),dx=e.clientX-r.left,dy=e.clientY-r.top;
   const mv=ev=>{LGX.x=ev.clientX-pr.left-dx;LGX.y=ev.clientY-pr.top-dy;lgPlace();},up=()=>{removeEventListener('pointermove',mv,true);removeEventListener('pointerup',up,true);lgSave();};addEventListener('pointermove',mv,true);addEventListener('pointerup',up,true);},true);
 lgState();}
/* tombol Legenda di bilah alat (seperti Ore Works) */
{const _b=tbBuild;tbBuild=function(){_b();try{const T=$('ptb');if(T&&!$('ptbl')){const b=document.createElement('button');b.id='ptbl';b.className='tb';b.title='Tampilkan / sembunyikan Legenda di pojok 3D';b.innerHTML='<i>&#9776;</i><span>Legenda</span>';b.onclick=()=>{LGX.off=!LGX.off;if(!LGX.off)LGX.min=false;lgSave();lgState();};const r=$('ptbr');if(r&&r.previousElementSibling)T.insertBefore(b,r.previousElementSibling);else T.appendChild(b);}lgState();}catch(e){console.warn('lg',e);}};}
try{tbBuild();}catch(_){}
setInterval(()=>{try{lgInit();}catch(e){}},800);addEventListener('resize',()=>{try{lgPlace();}catch(_){}});
{const _l=legend;legend=function(){const r=_l.apply(this,arguments);setTimeout(()=>{try{lgPlace();}catch(_){}},30);return r;};}
try{window.__PS3.lg={st:()=>Object.assign({},LGX),set:o=>{Object.assign(LGX,o);lgSave();lgState();}};}catch(_){}
