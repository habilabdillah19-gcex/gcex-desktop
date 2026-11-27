/* a84: FILTER & KELAS PER UNSUR (pemilik 25 Nov 2026).
   Block model 3D dan blok tambang (strip) bisa diwarnai dan difilter dengan unsur apa pun di block model, tidak hanya kadar utama (Au):
   - Kelas kadar per unsur: unsur utama memakai kelas Laporan G×T (GT.rules); unsur lain punya kelas sendiri (UF.kls[unsur],
     disimpan di localStorage psUnsurKls; awal = kuantil P50 / P75 / P90 dari blok yang dimuat, bisa diubah).
   - Filter unsur: daftar baris (semua berlaku bersamaan / DAN), tiap baris = unsur + rentang (dari … s/d …) atau kelas tercentang.
   Semua filter KOSONG secara bawaan: tanpa filter, tampilan sama seperti sebelumnya. */
var UF={kls:{}};
try{const s=JSON.parse(localStorage.getItem('psUnsurKls')||'{}');if(s&&typeof s==='object')UF.kls=s;}catch(_){}
function ufSave(){try{localStorage.setItem('psUnsurKls',JSON.stringify(UF.kls));}catch(_){}}
function ufNames(){const m=GT.m;return m&&m.num?Object.keys(m.num):(GT.num||[]).slice();}
function ufAuto(a){const m=GT.m,A=m&&m.num&&m.num[a];let q=[0,0,0];if(A){const v=[],st=Math.max(1,Math.floor(A.length/20000));for(let i=0;i<A.length;i+=st){const x=A[i];if(x===x&&x>-1e29&&x<1e29)v.push(x);}v.sort((p,r)=>p-r);const Q=f=>v.length?v[Math.min(v.length-1,Math.floor(f*(v.length-1)))]:0;q=[Q(.5),Q(.75),Q(.9)];}
 const r=x=>+(+x).toPrecision(3);return [{lo:r(q[0]),hi:r(q[1]),c:'#9ccf6c',m:'Rendah'},{lo:r(q[1]),hi:r(q[2]),c:'#fcc419',m:'Sedang'},{lo:r(q[2]),hi:'',c:'#e03131',m:'Tinggi'}];}
function ufRules(a){if(!a||a===GT.attr)return GT.rules;if(!UF.kls[a]){UF.kls[a]=ufAuto(a);ufSave();}return UF.kls[a];}
function ufCls(a,v){if(!a||a===GT.attr)return gtCls(v);const R=ufRules(a);if(!(v===v)||v==null)return -1;for(let i=0;i<R.length;i++){const r=R[i];if(v>=+r.lo&&(r.hi===''||r.hi==null||v<+r.hi))return i;}return -1;}
function ufBawah(a){return !a||a===GT.attr?'Waste':'di bawah kelas';}
function ufLab(r){return esc(r.m)+' '+r.lo+(r.hi===''||r.hi==null?'+':'–'+r.hi);}
function ufAktif(F){return (F||[]).some(f=>f&&f.a&&(f.md==='kls'?Object.values(f.h||{}).some(Boolean):(f.lo!==''&&f.lo!=null)||(f.hi!==''&&f.hi!=null)));}
/* lolos semua filter? val(a) = nilai unsur a untuk objek ini (NaN bila tidak ada) */
function ufPass(F,val){for(const f of F||[]){if(!f||!f.a)continue;const v=val(f.a);
 if(f.md==='kls'){const k=ufCls(f.a,v),kk=k<0?'w':k;if(f.h&&f.h[kk])return false;}
 else{const lo=f.lo===''||f.lo==null?-Infinity:+f.lo,hi=f.hi===''||f.hi==null?Infinity:+f.hi;if(lo===-Infinity&&hi===Infinity)continue;if(!(v===v)||v==null||v<lo||v>hi)return false;}}return true;}
/* daftar baris filter di dalam elemen el; F diubah langsung; onCh dipanggil bila hasil filter bisa berubah */
function ufFltUi(el,F,onCh){if(!el)return;const nm=ufNames(),opt=(v,l,c)=>'<option value="'+esc(v)+'"'+(v===c?' selected':'')+'>'+esc(l)+'</option>';let h='';
 F.forEach((f,i)=>{if(nm.length&&!nm.includes(f.a))f.a=nm.includes(GT.attr)?GT.attr:nm[0];const R=ufRules(f.a);
  h+='<div class="uff" data-i="'+i+'" style="border:1px solid #e3e7ef;border-radius:4px;padding:2px 5px;margin:3px 0"><div style="display:flex;flex-wrap:wrap;align-items:center;gap:3px 6px"><select data-f="a" title="Unsur">'+nm.map(n=>opt(n,n,f.a)).join('')+'</select><select data-f="md">'+opt('rng','rentang',f.md)+opt('kls','kelas',f.md)+'</select>'+
  (f.md==='kls'?'<a href="#" data-f="ed" title="Atur batas, nama dan warna kelas unsur ini">atur kelas</a>':'dari <input data-f="lo" type="number" step="any" style="width:58px" value="'+esc(f.lo==null?'':f.lo)+'"> s/d <input data-f="hi" type="number" step="any" style="width:58px" value="'+esc(f.hi==null?'':f.hi)+'">')+
  '<span style="flex:1"></span><button data-f="x" title="Hapus filter ini">&#10005;</button></div>';
  if(f.md==='kls')h+='<div style="display:flex;flex-wrap:wrap;gap:1px 9px;margin-top:2px">'+R.map((r,k)=>'<label><input type="checkbox" data-k="'+k+'"'+(f.h&&f.h[k]?'':' checked')+'><i style="display:inline-block;width:9px;height:9px;background:'+r.c+';margin:0 3px;vertical-align:-1px"></i>'+ufLab(r)+'</label>').join('')+'<label><input type="checkbox" data-k="w"'+(f.h&&f.h.w?'':' checked')+'> '+ufBawah(f.a)+'</label></div>';
  h+='</div>';});
 h+='<div style="display:flex;align-items:center;gap:6px;margin-top:2px"><button data-f="add">+ filter unsur</button><span style="font-size:11px;color:#6c757d">'+(F.length?'semua filter berlaku bersamaan':'belum ada filter: semua blok tampil')+'</span></div>';
 el.innerHTML=h;const again=()=>ufFltUi(el,F,onCh);
 el.querySelectorAll('.uff').forEach(row=>{const i=+row.dataset.i,f=F[i],q=s=>row.querySelector(s);
  q('[data-f=a]').onchange=e=>{f.a=e.target.value;f.h={};f.lo='';f.hi='';again();onCh();};
  q('[data-f=md]').onchange=e=>{f.md=e.target.value;f.h={};again();onCh();};
  for(const k of ['lo','hi']){const inp=q('[data-f='+k+']');if(inp)inp.onchange=()=>{f[k]=inp.value.trim();onCh();};}
  q('[data-f=x]').onclick=e=>{e.preventDefault();F.splice(i,1);again();onCh();};
  const ed=q('[data-f=ed]');if(ed)ed.onclick=e=>{e.preventDefault();ufKlsDlg(f.a,()=>{again();onCh();});};
  row.querySelectorAll('[data-k]').forEach(cb=>cb.onchange=()=>{f.h=f.h||{};f.h[cb.dataset.k]=!cb.checked;onCh();});});
 el.querySelector('[data-f=add]').onclick=e=>{e.preventDefault();F.push({a:nm.includes(GT.attr)?GT.attr:(nm[0]||''),md:'rng',lo:'',hi:'',h:{}});again();};}
/* jendela kecil: kelas kadar satu unsur */
function ufKlsDlg(a,done){let w=$('ufkw');if(!w){w=document.createElement('div');w.id='ufkw';w.style.cssText='position:fixed;left:'+Math.max(8,Math.min(innerWidth-440,520))+'px;top:110px;width:420px;max-width:calc(100vw - 30px);background:#fff;border:1px solid #9fb0cc;border-radius:7px;box-shadow:0 8px 28px rgba(20,32,58,.28);z-index:300;font:12px system-ui,Segoe UI,Arial,sans-serif';document.body.appendChild(w);
  w.addEventListener('pointerdown',e=>{const h=e.target.closest('#ufkh');if(!h||e.target.closest('button'))return;e.preventDefault();const r=w.getBoundingClientRect(),dx=e.clientX-r.left,dy=e.clientY-r.top;const mv=ev=>{w.style.left=Math.max(0,Math.min(innerWidth-80,ev.clientX-dx))+'px';w.style.top=Math.max(0,Math.min(innerHeight-40,ev.clientY-dy))+'px';},up=()=>{removeEventListener('pointermove',mv);removeEventListener('pointerup',up);};addEventListener('pointermove',mv);addEventListener('pointerup',up);});}
 UF.cb=done;const isU=!a||a===GT.attr;let h='<div id="ufkh" title="Seret untuk memindahkan" style="display:flex;align-items:center;padding:5px 8px;background:#1f3a5f;color:#fff;border-radius:7px 7px 0 0;cursor:move;user-select:none"><b>Kelas kadar — '+esc(a||GT.attr)+'</b><span style="flex:1"></span><button id="ufkx" style="background:#34527d;color:#fff;border:0;border-radius:4px;padding:2px 8px;cursor:pointer">&#10005;</button></div><div style="padding:6px 8px 8px">';
 if(isU)h+='<div>Kelas unsur utama (<b>'+esc(GT.attr)+'</b>) adalah kelas Laporan Grade × Tonnage, juga dipakai untuk ton ore, waste dan tujuan.</div><div style="margin-top:6px"><button id="ufkgt">Buka pengaturan kelas G×T…</button></div>';
 else{const R=ufRules(a);h+='<div style="color:#6c757d;margin-bottom:4px">Batas bawah ≤ nilai &lt; batas atas. Kosongkan batas atas kelas terakhir = tanpa batas. Nilai di bawah kelas pertama = <i>di bawah kelas</i>.</div><table style="border-collapse:collapse;width:100%"><tr style="color:#6c757d"><td>nama</td><td>dari</td><td>s/d</td><td>warna</td><td></td></tr>'+
  R.map((r,k)=>'<tr data-k="'+k+'"><td><input data-c="m" value="'+esc(r.m)+'" style="width:80px"></td><td><input data-c="lo" type="number" step="any" value="'+esc(r.lo)+'" style="width:64px"></td><td><input data-c="hi" type="number" step="any" value="'+esc(r.hi==null?'':r.hi)+'" style="width:64px"></td><td><input data-c="c" type="color" value="'+esc(r.c)+'" style="width:30px;height:20px;padding:0;border:0"></td><td><button data-c="x" title="Hapus kelas">&#10005;</button></td></tr>').join('')+'</table>'+
  '<div style="margin-top:6px;display:flex;gap:6px"><button id="ufkad">+ kelas</button><button id="ufkau" title="Ganti dengan kelas kuantil P50 / P75 / P90 dari blok yang dimuat">Otomatis (kuantil)</button></div>';}
 h+='</div>';w.innerHTML=h;w.style.display='';
 const fin=()=>{ufSave();try{UF.cb&&UF.cb();}catch(e){console.error(e);}};
 $('ufkx').onclick=()=>{w.style.display='none';};
 if(isU){$('ufkgt').onclick=()=>{w.style.display='none';gtOpen(true);try{$('gtkd').open=true;}catch(_){}};return;}
 const R=UF.kls[a];w.querySelectorAll('tr[data-k]').forEach(tr=>{const r=R[+tr.dataset.k];tr.querySelectorAll('[data-c]').forEach(inp=>{if(inp.dataset.c==='x'){inp.onclick=()=>{R.splice(+tr.dataset.k,1);fin();ufKlsDlg(a,UF.cb);};return;}
  inp.onchange=()=>{const k=inp.dataset.c;r[k]=k==='m'||k==='c'?inp.value:(inp.value.trim()===''?'':+inp.value);fin();};});});
 $('ufkad').onclick=()=>{const L=R[R.length-1],lo=L?(L.hi!==''&&L.hi!=null?+L.hi:(+L.lo||0)*2||1):0;if(L&&(L.hi===''||L.hi==null))L.hi=lo;R.push({lo,hi:'',c:'#7048e8',m:'K'+(R.length+1)});fin();ufKlsDlg(a,UF.cb);};
 $('ufkau').onclick=()=>{UF.kls[a]=ufAuto(a);fin();ufKlsDlg(a,UF.cb);};}
