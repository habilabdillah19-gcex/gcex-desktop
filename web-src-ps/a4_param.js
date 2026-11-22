/* ================= Langkah 3: parameter geoteknik ================= */
const PN=()=>({H:+$('pH').value||5,A:+$('pA').value||68,B:Math.max(0,+$('pB').value||0),N:Math.max(1,Math.round(+$('pN').value||1)),F:+$('pF').value||0,O:+$('pO').value||90});
let OVR=[];/* {z0,z1,A,B,N} */
function prmAt(z){const p=PN();for(const o of OVR){if(isFinite(o.z0)&&isFinite(o.z1)&&z>=Math.min(o.z0,o.z1)-1e-6&&z<Math.max(o.z0,o.z1)-1e-6){if(isFinite(o.A)&&o.A>0)p.A=o.A;if(isFinite(o.B)&&o.B>=0)p.B=o.B;if(isFinite(o.N)&&o.N>=1)p.N=Math.round(o.N);}}p.a=p.H/Math.tan(Math.min(p.A,88.9)*Math.PI/180);return p;}
function ovrDraw(){const tb=$('ovb');tb.innerHTML='';OVR.forEach((o,i)=>{const tr=document.createElement('tr');tr.innerHTML=['z0','z1','A','B','N'].map(k=>'<td><input data-k="'+k+'" type="number" step="any" value="'+(isFinite(o[k])?o[k]:'')+'"></td>').join('')+'<td><button title="Hapus">&#10005;</button></td>';
 tr.querySelectorAll('input').forEach(inp=>inp.onchange=()=>{o[inp.dataset.k]=inp.value===''?NaN:+inp.value;prmUpd();});tr.querySelector('button').onclick=()=>{OVR.splice(i,1);
ovrDraw();prmUpd();};tb.appendChild(tr);});
 $('ovr').innerHTML='&#9881; Beda parameter per RL'+(OVR.length?' ('+OVR.length+' baris aktif)':' (mis. zona oksida)')+'…';}
$('ova').onclick=()=>{const z=BASE?BASE.z:NaN;OVR.push({z0:z,z1:isFinite(z)?z+30:NaN,A:55,B:NaN,N:NaN});ovrDraw();prmUpd();};
/* sketsa penampang */
function sketch(){const p=prmAt(-1e9),a=p.a,sv=$('sk'),nb=Math.max(4,p.N+2),Wt=nb*a+Math.floor((nb-1)/p.N)*p.B,Ht=nb*p.H,k=Math.min(220/Math.max(Wt,1),88/Ht),x0=36,y0=108;
 let x=x0,y=y0,d='M'+(x0-24)+' '+y0+' L'+x+' '+y;const lab=[];
 for(let i=0;i<nb;i++){x+=a*k;y-=p.H*k;d+=' L'+x.toFixed(1)+' '+y.toFixed(1);if(i===0)lab.push('<text x="'+(x+3)+'" y="'+(y+p.H*k/2+4)+'" class="k">'+p.H+' m</text><text x="'+(x-a*k-2)+'" y="'+(y0-3)+'" class="k" text-anchor="end">'+p.A+'°</text>');
  if((i+1)%p.N===0&&i<nb-1&&p.B>0){const xb=x+p.B*k;if(!lab.some(t=>/berm/.test(t)))lab.push('<text x="'+((x+xb)/2)+'" y="'+(y-4)+'" class="k" text-anchor="middle">berm '+p.B+' m</text>');x=xb;d+=' L'+x.toFixed(1)+' '+y.toFixed(1);}}
 d+=' L'+(x+20)+' '+y.toFixed(1);const ov=Math.atan2(Ht,Wt)*180/Math.PI;
 sv.innerHTML='<style>.k{font:10px Inter,Arial;fill:#1b2a4e}.m{font:9px Inter,Arial;fill:#667085}</style><path d="'+d+' L'+(x+20)+' 118 L'+(x0-24)+' 118 Z" fill="#e9ddc8" stroke="#8a6d3b" stroke-width="1.4"/>'+
  '<line x1="'+x0+'" y1="'+y0+'" x2="'+x+'" y2="'+y+'" stroke="#c92a2a" stroke-dasharray="4 3" stroke-width="1.2"/><text x="'+((x0+x)/2-6)+'" y="'+((y0+y)/2-6)+'" class="k" fill="#c92a2a" style="fill:#c92a2a" text-anchor="end">overall '+ov.toFixed(1)+'°</text>'+lab.join('')+
  '<text x="'+(x0-22)+'" y="'+(y0-4)+'" class="m">lantai</text>';return ov;}
function prmUpd(){const p=prmAt(-1e9),ov=sketch(),rw=+$('rW').value||0,nb=p.N,ir=Math.atan2(nb*p.H,nb*p.a+p.B+rw)*180/Math.PI;
 let h='Overall slope (tanpa jalan): <b>'+ov.toFixed(1)+'°</b>'+(ov>p.O+0.05?' <span class="bad">&gt; batas '+p.O+'°</span>':' <span class="ok">≤ '+p.O+'°</span>')+'<br>Bila jalan memotong '+nb+' bench: '+ir.toFixed(1)+'° · offset horizontal per bench '+f1(p.a)+' m';
 if(p.A>80)h+='<br><span class="warn">Muka bench &gt; 80° jarang aman di batuan teralterasi.</span>';if(p.B>0&&p.B<3)h+='<br><span class="warn">Berm &lt; 3 m kurang efektif menahan runtuhan.</span>';
 $('slopeinfo').innerHTML=h;stepSt('s3',p.H+' m · '+p.A+'° · berm '+p.B+'/'+p.N+(OVR.length?' · +'+OVR.length+' RL':'')+(window.SECT&&SECT.length?' · '+SECT.length+' zona':''),true);if(RES)RES.stale=true;if(BASE&&BASE.kind==='line')baseApply();}
['pH','pA','pB','pN','pF','pO','rW'].forEach(id=>$(id).addEventListener('input',prmUpd));
ovrDraw();prmUpd();stepSt('s4',$('rW').value+' m · '+$('rG').value+'%',true);
/* berm: bench yang crest-nya pada level ini diberi berm */
function isBerm(zc,zref,p){const k=Math.round((zc-zref)/p.H);return p.B>0&&k!==0&&k%p.N===0;}

$('ovr').onclick=()=>winShow($('ovw'));

/* sudut bench Tajam/Bulat (dulu tidak terpasang: kode ini tersisip di tombol hapus override) */
const pcor=segOf('pcor',v=>{CORNER=v;/* Bulat = sudut dibulatkan dengan radius penghalusan; nilai kecil (≤1 m) hampir tak terlihat → naikkan otomatis ke 8 m */const ps=$('psm');if(v==='round'&&(+ps.value||0)<6)ps.value=8;else if(v==='miter'&&+ps.value===8)ps.value=1;prmUpd();if(BASE)baseApply();
 /* hasil yang sudah ada langsung dibuat ulang supaya perubahan terlihat */if(BASE&&(MODE==='new'||MODE==='stage')&&!window.IB&&(MODE==='stage'?STG:RES)&&typeof gmode==='function'&&gmode()!=='bench')setTimeout(()=>{try{$('go').click();}catch(e){}},30);});
