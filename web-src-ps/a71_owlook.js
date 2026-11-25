/* a71 · Menu & bilah alat CASCADE + panel Properti ala Ore Works (24 Nov 2026, pemilik:
   "Toolbar dan menu Pit Studio dibuat Cascade… panel kanan properti dibuat seperti Ore Works agar lebih mirip software tambang")
   1) Bar menu: tanda ▾; butir yang punya anak (Desain baru, Edit Otomatis, Edit Manual, Play-Doh) terbuka ke SAMPING (▸) saat kursor lewat.
   2) Bilah alat: ikon dikelompokkan jadi tombol tarik — Pandangan ▾ · String ▾ · Play-Doh ▾ (alat utama tetap satu klik).
   3) Properti: kepala bertab, judul objek + jenis, kisi "Umum" label | nilai, bagian datar bergaris (bukan kartu membulat). */
(function(){const st=document.createElement('style');st.textContent=`
body.shx .shmt::after{content:"▾";font-size:8px;margin-left:4px;opacity:.65}
body.shx .shmp .mbb.casc{position:relative;padding-right:22px!important;white-space:nowrap!important;overflow:visible!important}body.shx .shmp .mbb.casc::after{content:"▸";position:absolute;right:8px;top:50%;transform:translateY(-50%);color:#7a869a;font-size:11px;float:none!important}
body.shx .shmp .mbb.casc.on{font-weight:400!important;color:#1C2733!important;background:#dbe7fb!important;border-color:transparent!important}body.shx .shmp .mbb.casc.on::after{content:"▸"!important}
#ptb .tbg{display:inline-flex;flex:none;position:relative}#ptb .tbgb span::after{content:" ▾";font-size:8px;opacity:.7}
#ptb .tbdd{display:none;position:fixed;z-index:70;min-width:210px;max-height:70vh;overflow:auto;background:#fff;border:1px solid #a0a0a0;box-shadow:2px 3px 8px #00000030;padding:2px}
#ptb .tbg.op>.tbdd{display:block}
#ptb .tbdd button.tb{display:flex!important;width:100%!important;height:25px!important;justify-content:flex-start;gap:8px;padding:0 10px 0 6px!important;font-size:12px!important;border-radius:0!important}
#ptb .tbdd button.tb span{display:inline!important}#ptb .tbdd button.tb i{width:18px;flex:none}
#ptb .tbdd .ts{display:block;width:auto!important;height:1px!important;border:0!important;background:#e3e7ee;margin:2px 0!important;box-shadow:none}
/* ---- Properti ala Ore Works ---- */
body.shx #side>.shph{display:flex!important;align-items:stretch;height:26px;padding:0!important;background:#EDEBE6!important;border-bottom:1px solid #D3CDC1!important}
body.shx #side>.shph>span{display:flex;align-items:center;padding:0 12px;background:#F7F5F0;border-right:1px solid #D3CDC1;border-top:2px solid #2B5F9E;font-weight:700;font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:#1C2733}
body.shx #side>.shph>button{margin-left:auto;align-self:center}
body.shx #side>#pgw:not(#dock):not(#shpe):not(.shph):not(.x1){display:block!important;flex:none;border-bottom:1px solid #D3CDC1;background:#F7F5F0;font-size:12px}
#pgh{display:flex;align-items:baseline;gap:8px;padding:6px 10px 5px;cursor:pointer;user-select:none}#pgh b{font-size:13px;color:#1C2733;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#pgh span{margin-left:auto;color:#6c757d;font-size:11px;white-space:nowrap}
#pgw .pgs{background:#EDEBE6;border-top:1px solid #D3CDC1;border-bottom:1px solid #D3CDC1;padding:3px 10px;font-weight:700;font-size:11px;color:#1C2733}
#pgw .pgr{display:flex;border-bottom:1px solid #E7E3DA;min-height:22px;align-items:center}#pgw .pgr:last-child{border-bottom:0}
#pgw .pgr>span{flex:0 0 42%;padding:2px 6px 2px 10px;color:#495057;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#pgw .pgr>b{flex:1;font-weight:400;color:#1C2733;padding:2px 8px 2px 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#pgw.cl #pgb{display:none}#pgw.cl #pgh::before{content:"▸";color:#6c757d;font-size:10px}#pgw:not(.cl) #pgh::before{content:"▾";color:#6c757d;font-size:10px}
/* bagian datar bergaris */
body.shx #dock .uxs{border:0!important;border-bottom:1px solid #D3CDC1!important;border-radius:0!important;margin:0!important;background:#F7F5F0!important;box-shadow:none!important}
body.shx #dock .uxs>.uxh{background:#EDEBE6;border-radius:0!important;padding:4px 8px!important;border-top:1px solid #fff}
body.shx #dock .uxs.cur>.uxh{box-shadow:inset 3px 0 0 #B5893E}body.shx #dock .uxs>.uxh:hover{background:#E4E1DA}
body.shx #dock .uxn{flex:0 0 17px!important;height:17px!important;border-radius:2px!important;font-size:11px!important}
body.shx #dock .uxb{padding:4px 8px 8px!important}
body.shx #dock .step{border:0!important;border-bottom:1px solid #D3CDC1!important;border-radius:0!important;margin:0!important;box-shadow:none!important}
body.shx #dock .step>.sh{background:#EDEBE6!important;border-radius:0!important}
body.shx #dock input[type=number],body.shx #dock input[type=text],body.shx #dock select{border-radius:2px!important;border-color:#C9C3B6!important}
body.shx #dock .flw.win{border-radius:0!important;box-shadow:none!important}
`;document.head.appendChild(st);})();

/* ---------- 1. menu: anak terbuka ke samping ---------- */
const CASC_ID=['mbds','mbea','mbmw','mbpd'];
{const _o=cmOpen;cmOpen=function(btn,items){const r=_o.apply(this,arguments);try{if(CM&&CM._b===btn&&btn.closest&&btn.closest('.shmp')){const b=btn.getBoundingClientRect(),w=CM.offsetWidth||240,h=CM.offsetHeight||200;CM.style.left=Math.max(4,(b.right+w>innerWidth-4?b.left-w+2:b.right-2))+'px';CM.style.top=Math.max(4,Math.min(b.top-2,innerHeight-h-6))+'px';}}catch(_){}return r;};}
function cascInit(){for(const id of CASC_ID){const b=$(id);if(!b||b._casc)continue;b._casc=1;b.classList.add('casc');
  for(const n of [...b.childNodes])if(n.nodeType===3&&/▾/.test(n.nodeValue))n.nodeValue=n.nodeValue.replace(/\s*▾\s*/,'');if(b._icv)b._icv=b.innerHTML;
  let tm=0;const inMenu=()=>!!b.closest('.shmp');
  b.addEventListener('mouseenter',()=>{if(!inMenu()||(typeof DMO!=='undefined'&&DMO.on))return;clearTimeout(tm);tm=setTimeout(()=>{if(!(CM&&CM._b===b)&&b.matches(':hover'))b.onclick&&b.onclick();},140);});
  b.addEventListener('mouseleave',()=>clearTimeout(tm));
  /* klik saat anak sudah terbuka: jangan menutup; menu induk tetap terbuka */
  b.parentNode&&b.addEventListener('click',e=>{if(inMenu())e.stopPropagation();});}
 /* butir lain di panel yang sama → tutup anak */
 for(const p of document.querySelectorAll('.shmp'))if(!p._casc){p._casc=1;p.addEventListener('mouseover',e=>{const x=e.target.closest('.mbb,.shi');if(x&&CM&&CM._b&&CM._b.closest('.shmp')===p&&x!==CM._b)cmClose();});}}
/* klik butir di menu anak → menu induk ikut tutup */
document.addEventListener('click',e=>{if(e.target.closest&&e.target.closest('.cmenu .ci'))try{shClose();}catch(_){}} ,true);
{const _c=shClose;shClose=function(){try{if(CM&&CM._b&&CM._b.closest('.shmp'))cmClose();}catch(_){}return _c.apply(this,arguments);};}

/* ---------- 2. bilah alat: kelompok tarik ---------- */
function tbgClose(){document.querySelectorAll('#ptb .tbg.op').forEach(g=>g.classList.remove('op'));}
function tbgMake(nm,ic,tip){const g=document.createElement('span');g.className='tbg';g.innerHTML='<button class="tb tbgb" title="'+tip+'"><i>'+ic+'</i><span>'+nm+'</span></button><div class="tbdd"></div>';const b=g.firstChild,d=g.lastChild;
 b.onclick=e=>{e.stopPropagation();const was=g.classList.contains('op');tbgClose();if(was)return;g.classList.add('op');const r=b.getBoundingClientRect(),z=(+document.body.dataset.fz||100)/100;d.style.left=Math.max(4,Math.min(r.left,innerWidth-230*z))/z+'px';d.style.top=(r.bottom+1)/z+'px';};
 d.addEventListener('click',e=>{if(e.target.closest('button.tb'))setTimeout(tbgClose,0);});return g;}
function tbgPut(g,b){const d=g.lastChild;if(b.tagName==='BUTTON'){let s=b.querySelector('span');const t=((b._it&&b._it.t)||b.title||'').replace('…','');if(!s){s=document.createElement('span');b.appendChild(s);}if(!s.textContent.trim()||s.textContent.length<t.length)s.textContent=/^(RL tetap|Topografi|Permukaan pit)$/.test(t)?'Proyeksikan ke '+(t==='RL tetap'?t:t.charAt(0).toLowerCase()+t.slice(1)):t;}d.appendChild(b);}
function tbGroup(){const T=$('ptb');if(!T||T.querySelector('.tbg'))return;
 const vw=[...T.querySelectorAll(':scope > button.tb.vw')];if(vw.length){const g=tbgMake('Pandangan','&#9634;','Arah pandang kamera: Plan, SW, NE, Timur, Selatan, Pas');vw[0].before(g);vw.forEach(b=>tbgPut(g,b));}
 const E=$('ptbe');if(E){const PRI=/^(Pilih|Sambung|Putus|Perbaiki|Offset|Dorong|Tarik)$/;let sec='',gS=null,gP=null;
  for(const n of [...E.children]){if(n.classList.contains('tl')){sec=n.textContent.trim();continue;}if(n.tagName!=='BUTTON'||!n.classList.contains('tb')||!sec)continue;const s=n.querySelector('span');if(s&&PRI.test(s.textContent.trim()))continue;
   if(sec==='Manual'){if(!gS){gS=tbgMake('String','&#8767;','Alat string lain: lepas pilihan, snap, poligon, kurangi titik, luruskan, geser, hapus, sorot ujung lepas');n.before(gS);}tbgPut(gS,n);}
   else{if(!gP){gP=tbgMake('Play-Doh','&#128396;','Alat Play-Doh lain: kuas, potong, perapat, haluskan, proyeksi RL / topo / pit, salin, balik, pindah titik, trim, overcut');n.before(gP);}tbgPut(gP,n);}}
  /* kelompok diletakkan setelah alat utama bagiannya */
  const lastPri=(from)=>{let x=from,l=null;while(x&&!(x.classList&&x.classList.contains('ts'))){if(x.tagName==='BUTTON')l=x;x=x.nextElementSibling;}return l;};
  for(const g of [gS,gP])if(g){const l=lastPri(g.nextElementSibling);if(l)l.after(g);}}
 }
{const _b=tbBuild;tbBuild=function(){_b();try{tbGroup();}catch(e){console.warn('tbg',e);}try{tbState();}catch(_){}};}
{const _s=tbState;tbState=function(){_s();try{for(const g of document.querySelectorAll('#ptb .tbg')){const on=!!g.querySelector('.tbdd button.tb.on');g.firstChild.classList.toggle('on',on);}}catch(_){}};}
document.addEventListener('pointerdown',e=>{if(!e.target.closest||!e.target.closest('#ptb .tbg'))tbgClose();},true);
/* demo: sasaran di dalam kelompok → kelompoknya dibuka dulu */
{const _e=dmEl;dmEl=function(s){const e=_e.apply(this,arguments);try{const d=e&&e.closest&&e.closest('#ptb .tbdd');if(d&&!d.parentElement.classList.contains('op'))d.parentElement.firstChild.onclick({stopPropagation(){}});else if(!d&&typeof DMO!=='undefined'&&DMO.on)tbgClose();}catch(_){}return e;};}

/* ---------- 3. Properti: judul objek + kisi Umum ---------- */
const PGX={sig:'',cl:false};try{PGX.cl=localStorage.getItem('psPgCl')==='1';}catch(_){}
function pgData(){const rows=[];let nm='Project',ty='Proyek';const add=(a,b)=>{if(b!=null&&b!=='')rows.push([a,String(b)]);};
 const chip=id=>{const e=$(id);return e&&e.offsetParent!==null?e.textContent.replace(/^[^:]*:\s*/,'').trim():'';};
 let sch=false;try{sch=caraSchOn();}catch(_){}
 try{const p=$('pjnm')||document.querySelector('#pjn,.pjn');if(p)add('Project',p.textContent.trim());}catch(_){}
 if(sch){const ph=schPh();nm='Pit Schedule';ty='Jadwal';add('Fase',(ph.nm||'Fase 1')+(ph.lock?' (terkunci)':''));add('Batas area',ph.bnd&&ph.bnd.length>=3?ph.bnd.length+' titik':'belum ada');
  try{add('Cara gali',{klik:'Klik blok',auto:'Otomatis',jalur:'Tarik jalur alat'}[CARA.v]||CARA.v);}catch(_){}
  try{if(MB.R)add('Blok tambang',MB.R.L.length+' blok');}catch(_){}
  try{const F=schFleets();let n=0;for(const v of F.values())n+=v.length;add('Fleet / jalur',F.size+' fleet · '+n+' jalur');}catch(_){}
  try{if(PL.on)add('Urutan blok',PL.q.length+' blok'+(PL.q.length>PL.qN?' · '+(PL.q.length-(PL.qN|0))+' menunggu Jalankan':''));}catch(_){}
  add('Hasil',SCH.sim?gtShort(SCH.sim.vtot||0)+' BCM terjadwal':(PL.res?'rencana sudah dihitung':'belum dijalankan'));}
 else{const ed=MODE==='edit',stg=MODE==='stage';nm=ed?'Edit pit':stg?'Staging':'Pit final';ty=ed?'Edit':'Desain';
  add('Topografi',chip('chT'));if(stg)add('Batas final',chip('chF'));add('Geoteknik',chip('chG')||(()=>{try{const p=PN();return p.H+' m · '+p.A+'° · berm '+p.B+' m';}catch(_){return '';}})());
  let R0=null;try{R0=curR();}catch(_){}
  if(R0&&R0.B){let zs=R0.B.map(b=>b.zc);if(!zs.length&&R0.S)for(const q of R0.S)for(const p of q.pts)zs.push(p[2]);add('Jumlah bench',R0.B.length||'');if(R0.vol&&R0.vol.tot)add('Volume',nf(R0.vol.tot)+' m³');
   if(zs.length)add('RL dasar – atas',f1(R0.zmin)+' – '+f1(Math.max(...zs)));if(R0.kpi&&R0.kpi.rl)add('Panjang jalan',nf(R0.kpi.rl)+' m');if(R0.S)add('String',R0.S.length);}
  else if(ed&&ED&&ED.base&&ED.base.S){add('Pit sumber',ED.nm||'');add('String',ED.base.S.length);}
  else add('Hasil','belum ada desain');
  if(ed){try{add('Riwayat edit',EH.st.length?(EH.i+1)+' / '+EH.st.length:'kosong');}catch(_){}}}
 return {nm,ty,rows};}
function pgDraw(){if(!document.body.classList.contains('shx'))return;const side=$('side');if(!side)return;let w=$('pgw');if(!w){const ph=side.querySelector(':scope > .shph');if(!ph)return;w=document.createElement('div');w.id='pgw';w.innerHTML='<div id="pgh" title="Klik: buka / tutup ringkasan"><b></b><span></span></div><div id="pgb"></div>';ph.after(w);w.classList.toggle('cl',PGX.cl);
   w.firstChild.onclick=()=>{PGX.cl=!PGX.cl;w.classList.toggle('cl',PGX.cl);try{localStorage.setItem('psPgCl',PGX.cl?'1':'0');}catch(_){}dispatchEvent(new Event('resize'));};}
 let d;try{d=pgData();}catch(e){return;}const sg=JSON.stringify(d);if(sg===PGX.sig)return;PGX.sig=sg;
 w.querySelector('#pgh b').textContent=d.nm;w.querySelector('#pgh span').textContent=d.ty;
 $('pgb').innerHTML='<div class="pgs">Umum</div>'+d.rows.map(r=>'<div class="pgr"><span>'+esc(r[0])+'</span><b title="'+esc(r[1])+'">'+esc(r[1])+'</b></div>').join('');}
setInterval(()=>{try{cascInit();pgDraw();}catch(_){}},700);
try{tbBuild();cascInit();pgDraw();}catch(e){console.warn('owlook',e);}
try{window.__PS3.ow={pg:()=>pgData(),groups:()=>[...document.querySelectorAll('#ptb .tbg')].map(g=>[g.firstChild.textContent.trim(),g.lastChild.children.length])};}catch(_){}
