/* a38: jendela besar "Laporan Grade × Tonnage" untuk Pit Schedule — kartu ringkasan, grafik per periode
   (batang bertumpuk ton per kelas + waste, garis kadar ore), tabel lengkap. Klik batang / baris = pindah ke periode itu di 3D. */
const GTR={W:'#a1887f'};
function gtBigWin(){if($('gtrw'))return;const st=document.createElement('style');st.textContent=
`#gtrw{position:fixed;left:300px;top:70px;width:900px;max-width:calc(100vw - 40px);max-height:calc(100vh - 90px);background:#fff;border:1px solid #9fb0cc;border-radius:7px;box-shadow:0 8px 28px rgba(20,32,58,.28);z-index:42;display:none;flex-direction:column;font:12px system-ui,Segoe UI,Arial,sans-serif}
#gtrh{display:flex;align-items:center;gap:8px;padding:5px 8px;background:linear-gradient(#1f3a5f,#152a47);color:#fff;cursor:move;user-select:none;border-radius:7px 7px 0 0}#gtrh button{background:#34527d;color:#fff;border:0;border-radius:4px;padding:2px 8px;cursor:pointer}#gtrh select{font-size:11px}#gtrh>*{white-space:nowrap;flex-shrink:0}#gtrh>b{flex-shrink:1;overflow:hidden;text-overflow:ellipsis}
#gtrb{overflow:auto;padding:8px 10px 10px}#gtrc{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:6px}#gtrc div{flex:1;min-width:110px;border:1px solid #dde3ee;border-radius:6px;padding:4px 8px;background:#f8f9fb}#gtrc small{display:block;color:#6c757d;font-size:10.5px}#gtrc b{font-size:15px;color:#1f3a5f}
#gtrg{border:1px solid #e3e7ef;border-radius:6px}#gtrg rect.b{cursor:pointer}#gtrl2{display:flex;flex-wrap:wrap;gap:4px 14px;margin:4px 2px;font-size:11px;color:#495057}#gtrl2 i{display:inline-block;width:10px;height:10px;margin-right:4px;vertical-align:-1px}
#gtrt{max-height:300px;overflow:auto;border:1px solid #e3e7ef;margin-top:6px}#gtrt table{border-collapse:collapse;width:100%;font-size:11.5px}#gtrt th,#gtrt td{border-bottom:1px solid #eef1f6;padding:3px 6px;text-align:right;white-space:nowrap}#gtrt th{position:sticky;top:0;background:#f1f3f7}#gtrt td:first-child,#gtrt th:first-child{text-align:left}#gtrt tr.tot td{font-weight:700;border-top:2px solid #9fb0cc}#gtrt tr[data-i]{cursor:pointer}#gtrt tr.on td{background:#fff3bf}#gtrd{font-size:11.5px;margin-top:5px;color:#343a40}`;
 document.head.appendChild(st);const w=document.createElement('div');w.id='gtrw';
 w.innerHTML='<div id="gtrh"><b>&#9878; Laporan Grade × Tonnage — <span id="gtrn"></span></b><span style="flex:1"></span>periode <select id="gtru2"></select><label><input type="checkbox" id="gtrf"> per fleet</label><button id="gtrmin" title="Ringkas: hanya grafik (agar 3D terlihat) / lengkap">&#9645; ringkas</button><button id="gtrcsv">&#8681; CSV</button><button id="gtrx">&#10005;</button></div>'+
  '<div id="gtrb"><div id="gtrc"></div><div id="gtrg"></div><div id="gtrl2"></div><div id="gtrd"></div><div id="gtrt"></div></div>';
 document.body.appendChild(w);let mv=null;$('gtrh').addEventListener('mousedown',e=>{if(/BUTTON|SELECT|INPUT|LABEL/.test(e.target.tagName))return;mv=[e.clientX,e.clientY,w.offsetLeft,w.offsetTop];e.preventDefault();});
 window.addEventListener('mousemove',e=>{if(!mv)return;w.style.left=Math.max(0,mv[2]+e.clientX-mv[0])+'px';w.style.top=Math.max(0,mv[3]+e.clientY-mv[1])+'px';});window.addEventListener('mouseup',()=>{mv=null;});
 w.addEventListener('mousedown',()=>{let m=40;document.querySelectorAll('.flw.win,#schw,#sayw,#bmw').forEach(x=>{const z=+getComputedStyle(x).zIndex||0;if(z>m&&z<60)m=z;});w.style.zIndex=Math.min(59,m+1);},true);
 $('gtrx').onclick=()=>gtBig(false);$('gtrmin').onclick=()=>gtBigMin(!GTR.min);$('gtrcsv').onclick=()=>gtCsv();
 $('gtru2').innerHTML=$('schun').innerHTML;$('gtru2').onchange=()=>{const s=$('schun');s.value=$('gtru2').value;s.dispatchEvent(new Event('change'));};
 $('gtrf').onchange=()=>{const c=$('gtfl');if(c){c.checked=$('gtrf').checked;c.dispatchEvent(new Event('change'));}};}
function gtBig(on){gtBigWin();$('gtrw').style.display=on?'flex':'none';if(on)gtBigDraw();}
function gtBigMin(on){gtBigWin();GTR.min=!!on;const w=$('gtrw');for(const id of ['gtrc','gtrt','gtrd'])$(id).style.display=on?'none':'';if(on){GTR.w0=w.style.width;w.style.width='600px';}else w.style.width=GTR.w0||'';$('gtrmin').innerHTML=on?'&#9645; lengkap':'&#9645; ringkas';gtBigDraw();}
function gtNice(v){if(!(v>0))return 1;const e=Math.pow(10,Math.floor(Math.log10(v))),m=v/e;return (m<=1?1:m<=2?2:m<=2.5?2.5:m<=5?5:10)*e;}
function gtShort(v){return v>=1e6?schF(v/1e6,2)+' jt':v>=1e3?schF(v/1e3,v>=1e5?0:1)+' rb':schF(v);}
function gtBigDraw(){const w=$('gtrw');if(!w||w.style.display==='none')return;GTR.pi=SCH.pi;if(!GT.res||!SCH.sim){$('gtrc').innerHTML='<div><small>Belum ada laporan</small><b>Muat block model lalu Hitung laporan</b></div>';$('gtrg').innerHTML=$('gtrt').innerHTML=$('gtrd').innerHTML=$('gtrl2').innerHTML='';return;}
 $('gtrn').textContent=schPh().nm;$('gtru2').value=$('schun').value;$('gtrf').checked=!!GT.fleet;
 const X={out:GT.res.out,B:gtBand(),np:GT.res.F.sim.np,TS:GT.res.F.sim.TS,fl:false},A=gtAgg(X),{B,rows,tot,K}=A,n=B.length;
 const ore=a=>{let s=0;for(let k=0;k<K;k++)s+=a.t[k];return s;},met=a=>{let s=0;for(let k=0;k<K;k++)s+=a.gt[k];return s;},ot=ore(tot),om=met(tot);
 $('gtrc').innerHTML=[['Ore',gtShort(ot)+' t'],['Kadar ore',(ot>0?(om/ot).toFixed(2):'–')+' g/t'],['Logam',schF(om/31.1035)+' oz'],['Waste',gtShort(tot.t[K])+' t'],['Stripping ratio',ot>0?(tot.t[K]/ot).toFixed(2):'–'],['Blok terhitung',GT.res.nIn.toLocaleString('id-ID')+(GT.rule==='prop'?' · proporsional':' · pusat blok')]].map(c=>'<div><small>'+c[0]+'</small><b>'+c[1]+'</b></div>').join('');
 /* grafik */
 const W=878,H=250,L=58,R=48,T=14,Bm=n>14?58:34,pw=W-L-R,ph=H-T-Bm;let tm=0,gm=0;const R0=rows.map(r=>r[0]);
 R0.forEach(a=>{tm=Math.max(tm,ore(a)+a.t[K]);const o=ore(a);if(o>0)gm=Math.max(gm,met(a)/o);});tm=gtNice(tm);gm=gtNice(gm*1.1);
 const bw=Math.min(54,pw/Math.max(1,n)*0.72),xc=i=>L+(i+0.5)*pw/n,y=v=>T+ph-v/tm*ph,yg=g=>T+ph-g/gm*ph;let s='<svg viewBox="0 0 '+W+' '+H+'" width="100%" style="display:block">';
 for(let i=0;i<=4;i++){const v=tm*i/4,yy=y(v);s+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+yy+'" y2="'+yy+'" stroke="#e9ecef"/><text x="'+(L-5)+'" y="'+(yy+3.5)+'" text-anchor="end" font-size="10" fill="#6c757d">'+gtShort(v)+'</text><text x="'+(W-R+5)+'" y="'+(yy+3.5)+'" font-size="10" fill="#c2255c">'+(gm*i/4).toFixed(2)+'</text>';}
 s+='<text x="12" y="'+(T+ph/2)+'" font-size="10" fill="#6c757d" transform="rotate(-90 12 '+(T+ph/2)+')" text-anchor="middle">ton per periode</text><text x="'+(W-8)+'" y="'+(T+ph/2)+'" font-size="10" fill="#c2255c" transform="rotate(90 '+(W-8)+' '+(T+ph/2)+')" text-anchor="middle">kadar ore g/t</text>';
 const every=Math.max(1,Math.ceil(n/(n>14?30:14)));let path='';
 R0.forEach((a,i)=>{let acc=0;const x0=xc(i)-bw/2,seg=(t,c)=>{if(!(t>0))return;const y1=y(acc+t),hh=y(acc)-y1;s+='<rect class="b" data-i="'+i+'" x="'+x0.toFixed(1)+'" y="'+y1.toFixed(1)+'" width="'+bw.toFixed(1)+'" height="'+Math.max(0.5,hh).toFixed(1)+'" fill="'+c+'"><title>'+esc(B[i].lab)+'</title></rect>';acc+=t;};
  seg(a.t[K],GTR.W);for(let k=0;k<K;k++)seg(a.t[k],GT.rules[k].c);
  if(i===SCH.pi)s+='<rect x="'+(x0-3).toFixed(1)+'" y="'+T+'" width="'+(bw+6).toFixed(1)+'" height="'+ph+'" fill="none" stroke="#f08c00" stroke-width="1.6" stroke-dasharray="4 3"/>';
  const o=ore(a);if(o>0){const g=met(a)/o;path+=(path?'L':'M')+xc(i).toFixed(1)+' '+yg(g).toFixed(1);s+='<circle cx="'+xc(i).toFixed(1)+'" cy="'+yg(g).toFixed(1)+'" r="2.6" fill="#c2255c"/>'+(n<=16?'<text x="'+xc(i).toFixed(1)+'" y="'+(yg(g)-6).toFixed(1)+'" text-anchor="middle" font-size="9.5" fill="#c2255c">'+g.toFixed(2)+'</text>':'');}
  if(i%every===0){const lab=esc(String(B[i].lab).replace(/^Bench RL /,'RL '));s+=n>14?'<text x="'+xc(i).toFixed(1)+'" y="'+(T+ph+10)+'" font-size="9.5" fill="#495057" text-anchor="end" transform="rotate(-40 '+xc(i).toFixed(1)+' '+(T+ph+10)+')">'+lab+'</text>':'<text x="'+xc(i).toFixed(1)+'" y="'+(T+ph+14)+'" font-size="10" fill="#495057" text-anchor="middle">'+lab+'</text>';}});
 s+='<path d="'+path+'" fill="none" stroke="#c2255c" stroke-width="1.6"/><line x1="'+L+'" x2="'+(W-R)+'" y1="'+(T+ph)+'" y2="'+(T+ph)+'" stroke="#868e96"/></svg>';$('gtrg').innerHTML=s;
 $('gtrg').querySelectorAll('rect.b').forEach(r=>r.onclick=()=>{schStop();schSet(+r.dataset.i);});
 $('gtrl2').innerHTML=GT.rules.map(r=>'<span><i style="background:'+r.c+'"></i>'+esc(r.m)+' ('+r.lo+(r.hi===''?'+':'–'+r.hi)+' g/t)</span>').join('')+'<span><i style="background:'+GTR.W+'"></i>Waste</span><span><i style="background:#c2255c;height:3px;vertical-align:3px"></i>kadar ore (sumbu kanan)</span><span style="color:#868e96">klik batang / baris = lihat periode itu di 3D</span>';
 const H2=gtHtml(gtAgg(),'Total '+schPh().nm,'Periode');$('gtrt').innerHTML=H2.h;$('gtrd').innerHTML=H2.dest;
 /* kolom kumulatif (ore, kadar, SR) + kapan selesai — hanya tanpa rincian fleet */
 if(!GT.fleet){const tb=$('gtrt'),hr=tb.querySelector('thead tr');if(hr)hr.insertAdjacentHTML('beforeend','<th style="border-left:2px solid #dde3ee">Σ ore t</th><th>Σ g/t</th><th>Σ SR</th><th>selesai</th>');let co=0,cm=0,cw=0;const off=SCH.sim.off||0;
  R0.forEach((a,i)=>{co+=ore(a);cm+=met(a);cw+=a.t[K];const tr=tb.querySelector('tr[data-i="'+i+'"]');if(tr)tr.insertAdjacentHTML('beforeend','<td style="border-left:2px solid #dde3ee">'+schF(co)+'</td><td>'+(co>0?(cm/co).toFixed(2):'–')+'</td><td>'+(co>0?(cw/co).toFixed(2):'–')+'</td><td style="color:#6c757d">'+esc(schLab(B[i].b,0,off))+'</td>');});
  const tt=tb.querySelector('tr.tot');if(tt)tt.insertAdjacentHTML('beforeend','<td style="border-left:2px solid #dde3ee"></td><td></td><td></td><td></td>');}
 $('gtrt').querySelectorAll('tr[data-i]').forEach(tr=>{tr.onclick=()=>{schStop();schSet(+tr.dataset.i);};if(+tr.dataset.i===SCH.pi)tr.classList.add('on');});}
{const _t=gtTable;gtTable=function(){const r=_t.apply(this,arguments);try{gtBigDraw();}catch(e){console.error(e);}return r;};}
{const _h=gtHi;gtHi=function(){const r=_h.apply(this,arguments);try{const w=$('gtrw');if(w&&w.style.display!=='none'&&GTR.pi!==SCH.pi){GTR.pi=SCH.pi;gtBigDraw();}}catch(_){}return r;};}
{const _m=gtMount;gtMount=function(){const r=_m.apply(this,arguments);try{if($('gtcsv')&&!$('gtbigb')){const b=document.createElement('button');b.id='gtbigb';b.innerHTML='&#10530; Laporan &amp; grafik';b.title='Jendela besar: ringkasan, grafik ton & kadar per periode, tabel lengkap';b.onclick=()=>gtBig(true);$('gtcsv').after(b);}}catch(_){}return r;};}
{const _r=schReset;schReset=function(){const r=_r.apply(this,arguments);try{gtBigDraw();}catch(_){}return r;};}
try{window.__PS3.gt.big=on=>gtBig(on!==false);}catch(_){}
