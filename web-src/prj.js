/* ================= FILE PROYEK .prj (satu file untuk dikirim ke rekan) — GC-Ex Block Model & GC-Ex Drillhole =================
   .prj = arsip ZIP standar (bisa dibuka juga dengan 7-Zip / Windows Explorer bila diganti .zip) berisi:
     gcex_prj.json   manifest (aplikasi, nama proyek, pembuat, tanggal, daftar file)
     proyek.dh3d     seluruh proyek: data, pekerjaan (dig block, as-mined, sayatan, tampilan…), block model (≤ 1 juta blok), data referensi
     sumber/…        file sumber block model (.mdl / .csv) bila tersedia — wajib untuk block model > 1 juta blok
   Simpan: menu Proyek › "Simpan sebagai file .prj…". Buka: jendela awal / menu Proyek › "Buka file .prj…".
   Penulisan: JSON dikompresi (deflate), file sumber disimpan apa adanya (store) sehingga cepat walau ratusan MB. Batas 4 GB per arsip. */
(function(){if(SA.prjSave)return;
var PRJ=SA.PRJ={APP:(document.title||'').indexOf('Block Model')>=0?'GC-Ex Block Model':'GC-Ex Drillhole',MAXB:4290000000};
/* ---------- CRC32 ---------- */
var CT=(function(){var t=new Uint32Array(256);for(var n=0;n<256;n++){var c=n;for(var k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
function crcUp(c,u){for(var i=0;i<u.length;i++)c=CT[(c^u[i])&255]^(c>>>8);return c;}
async function crcBlob(b,prog){var r=b.stream().getReader(),c=0xFFFFFFFF,done=0,last=0;for(;;){var x=await r.read();if(x.done)break;c=crcUp(c,x.value);done+=x.value.length;if(prog&&Date.now()-last>250){last=Date.now();prog(done);}}return(c^0xFFFFFFFF)>>>0;}
async function deflate(b){var s=b.stream().pipeThrough(new CompressionStream('deflate-raw'));return await new Response(s).blob();}
async function inflate(b){var s=b.stream().pipeThrough(new DecompressionStream('deflate-raw'));return await new Response(s).blob();}
function dosTime(d){return{t:(d.getHours()<<11)|(d.getMinutes()<<5)|(d.getSeconds()>>1),d:((d.getFullYear()-1980)<<9)|((d.getMonth()+1)<<5)|d.getDate()};}
var enc=new TextEncoder();
/* ---------- tulis ZIP: entries [{name, blob, deflate}] -> Blob (bagian file asli tidak disalin ke memori) ---------- */
async function zipBlob(E,prog){var parts=[],cd=[],off=0,T=dosTime(new Date());
  for(var i=0;i<E.length;i++){var e=E[i],nm=enc.encode(e.name),raw=e.blob,usz=raw.size;if(prog)prog('Menghitung '+e.name+'…',i);
    var crc=await crcBlob(raw,prog?function(d){prog('Memeriksa '+e.name+': '+(usz?Math.round(d/usz*100):100)+'%',i);}:null),data=e.deflate?await deflate(raw):raw,csz=data.size,meth=e.deflate?8:0;
    if(off+csz+nm.length+30>PRJ.MAXB)throw new Error('Arsip melebihi 4 GB (file '+e.name+'). Jangan sertakan file sumber, atau bagikan lewat folder proyek.');
    var h=new DataView(new ArrayBuffer(30));h.setUint32(0,0x04034b50,true);h.setUint16(4,20,true);h.setUint16(6,0x0800,true);h.setUint16(8,meth,true);h.setUint16(10,T.t,true);h.setUint16(12,T.d,true);
    h.setUint32(14,crc,true);h.setUint32(18,csz,true);h.setUint32(22,usz,true);h.setUint16(26,nm.length,true);h.setUint16(28,0,true);parts.push(h.buffer,nm,data);
    var c=new DataView(new ArrayBuffer(46));c.setUint32(0,0x02014b50,true);c.setUint16(4,20,true);c.setUint16(6,20,true);c.setUint16(8,0x0800,true);c.setUint16(10,meth,true);c.setUint16(12,T.t,true);c.setUint16(14,T.d,true);
    c.setUint32(16,crc,true);c.setUint32(20,csz,true);c.setUint32(24,usz,true);c.setUint16(28,nm.length,true);c.setUint32(42,off,true);cd.push(c.buffer,nm);off+=30+nm.length+csz;}
  var cdSize=cd.reduce(function(s,p){return s+(p.byteLength||p.length);},0),z=new DataView(new ArrayBuffer(22));z.setUint32(0,0x06054b50,true);z.setUint16(8,E.length,true);z.setUint16(10,E.length,true);z.setUint32(12,cdSize,true);z.setUint32(16,off,true);
  return new Blob(parts.concat(cd,[z.buffer]),{type:'application/octet-stream'});}
/* ---------- baca ZIP ---------- */
async function zipRead(f){var n=f.size,tail=Math.min(n,66000),buf=new DataView(await f.slice(n-tail).arrayBuffer()),eo=-1;
  for(var i=tail-22;i>=0;i--)if(buf.getUint32(i,true)===0x06054b50){eo=i;break;}if(eo<0)throw new Error('bukan arsip .prj / zip yang valid');
  var cnt=buf.getUint16(eo+10,true),cs=buf.getUint32(eo+12,true),co=buf.getUint32(eo+16,true),C=new DataView(await f.slice(co,co+cs).arrayBuffer()),p=0,L=[],dec=new TextDecoder();
  for(var k=0;k<cnt;k++){if(C.getUint32(p,true)!==0x02014b50)throw new Error('direktori arsip rusak');var meth=C.getUint16(p+10,true),csz=C.getUint32(p+20,true),usz=C.getUint32(p+24,true),nl=C.getUint16(p+28,true),xl=C.getUint16(p+30,true),cl=C.getUint16(p+32,true),lo=C.getUint32(p+42,true);
    var name=dec.decode(new Uint8Array(C.buffer,C.byteOffset+p+46,nl));L.push({name:name,meth:meth,csz:csz,usz:usz,lo:lo});p+=46+nl+xl+cl;}
  var ent=async function(e){var h=new DataView(await f.slice(e.lo,e.lo+30).arrayBuffer());if(h.getUint32(0,true)!==0x04034b50)throw new Error('header file rusak: '+e.name);var ds=e.lo+30+h.getUint16(26,true)+h.getUint16(28,true),raw=f.slice(ds,ds+e.csz);
    if(e.meth===0)return raw;if(e.meth===8)return await inflate(raw);throw new Error('metode kompresi tidak didukung ('+e.meth+') untuk '+e.name);};
  return{list:L,get:function(nm){var e=L.filter(function(x){return x.name===nm;})[0];return e?ent(e):Promise.resolve(null);},ent:ent};}
/* ---------- UI kecil ---------- */
function say(t,bad,ms){if(window.FP&&FP.toast)FP.toast(t,bad,ms==null?0:ms);else if(window.msg)msg(t,bad);}
function slug(s){return String(s||'proyek').replace(/[^A-Za-z0-9_-]+/g,'_').replace(/^_+|_+$/g,'')||'proyek';}
function mb(b){return(b/1048576).toLocaleString('id-ID',{maximumFractionDigits:b<1048576*10?1:0})+' MB';}
async function saveBlob(b,name){
  /* Aplikasi terpasang punya dialog Simpan sendiri; dipakai lebih dulu supaya .prj ikut aturan
     yang sama dengan ekspor lain: selalu tanya lokasi & nama. */
  if(window.gxSimpan)return await gxSimpan(b,name);
  if(window.showSaveFilePicker){try{var h=await showSaveFilePicker({suggestedName:name,types:[{description:'Proyek GC-Ex (.prj)',accept:{'application/octet-stream':['.prj']}}]});var w=await h.createWritable();await w.write(b);await w.close();return h.name||name;}
    catch(e){if(e&&e.name==='AbortError')return null;console.warn(e);}}
  var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},1500);return name;}
async function projJson(){await SA.saveWork();var nm=SA.pname,r=await idbGet('proj:'+nm);if(!r)throw new Error('Proyek belum tersimpan di komputer ini.');var wk=await SA.loadWork(nm);
  return{name:r.name,text:JSON.stringify({format:'dh3d-project',version:1,name:r.name,date:r.date,data:r.data,work:wk},encTA),big:!!(wk&&((wk.bx&&wk.bx.big)||wk.bxBig))};}
async function srcFile(){var s=window.BX&&BX.m&&BX.m.src;if(!s||!s.name)return null;var f=SA.srcFiles&&SA.srcFiles[s.name];if(f)return f;
  try{if(window.FP&&FP.dir&&FP.findFile){var r=await FP.findFile(s.name,s.size);if(r)return r.f;}}catch(e){}return{missing:true,name:s.name,size:s.size};}
/* ---------- SIMPAN .prj ---------- */
SA.prjSave=async function(){var p=E('pjMenu');if(p)p.style.display='none';if(!SA.pname){alert('Belum ada proyek yang dibuka.');return;}
  if(typeof CompressionStream!=='function'){alert('Browser ini belum mendukung kompresi; gunakan GC-Ex Desktop / Chrome / Edge terbaru.');return;}
  try{say('Menyiapkan file .prj&hellip;');var P=await projJson(),S=await srcFile(),E2=[],inc=false;
    if(S&&!S.missing){var need=P.big;inc=need||confirm('Sertakan file sumber block model "'+S.name+'" ('+mb(S.size)+') di dalam .prj?\n\nOK = sertakan (rekan bisa membaca ulang / mengubah filter RL)\nBatal = tidak (block model tetap ikut di dalam proyek, file .prj lebih kecil)');
      if(need&&!inc)return;}
    else if(S&&S.missing&&P.big){if(!confirm('Block model "'+S.name+'" terlalu besar untuk disimpan di dalam proyek dan file sumbernya tidak tersedia di sesi ini.\n\nLanjutkan tanpa block model? (rekan harus import ulang file .mdl-nya)'))return;}
    var man={format:'gcex-prj',version:1,app:PRJ.APP,name:P.name,createdAt:new Date().toISOString(),createdBy:(window.FP&&FP.user&&FP.user())||'',files:['proyek.dh3d'],src:inc?{name:S.name,size:S.size}:null,
      note:'Buka di '+PRJ.APP+': jendela awal › Buka file proyek (.prj), atau menu Proyek › Buka file .prj.'};
    E2.push({name:'proyek.dh3d',blob:new Blob([P.text],{type:'application/json'}),deflate:true});if(inc){E2.push({name:'sumber/'+S.name,blob:S,deflate:false});man.files.push('sumber/'+S.name);}
    E2.unshift({name:'gcex_prj.json',blob:new Blob([JSON.stringify(man,null,1)],{type:'application/json'}),deflate:false});
    var z=await zipBlob(E2,function(t){say(t);}),fn=await saveBlob(z,slug(P.name)+'.prj');
    if(!fn){say('Penyimpanan .prj dibatalkan.',false,3000);return;}
    say('&#10003; <b>'+esc(fn)+'</b> tersimpan ('+mb(z.size)+(inc?', termasuk file sumber '+esc(S.name):'')+'). Kirim file ini ke rekan; buka dengan menu <b>Buka file proyek (.prj)</b>.',false,9000);}
  catch(e){console.error(e);say('Gagal membuat .prj: '+esc(e.message),true,9000);}};
/* ---------- BUKA .prj ---------- */
SA.prjOpen=async function(f){if(!f)return;if(typeof DecompressionStream!=='function'){alert('Browser ini belum mendukung dekompresi; gunakan GC-Ex Desktop / Chrome / Edge terbaru.');return;}
  try{var Z=await zipRead(f),mb0=await Z.get('gcex_prj.json'),man=mb0?JSON.parse(await mb0.text()):null;
    if(!man||man.format!=='gcex-prj')throw new Error('bukan file proyek GC-Ex (.prj)');
    if(man.app&&man.app!==PRJ.APP)throw new Error('file ini proyek '+man.app+'. Buka dengan aplikasi '+man.app+'.');
    var pb=await Z.get('proyek.dh3d');if(!pb)throw new Error('isi proyek (proyek.dh3d) tidak ada di arsip');
    /* file sumber: dipakai langsung dari arsip (tanpa salin) */
    SA.prjSrc=[];Z.list.filter(function(e){return /^sumber\//.test(e.name)&&e.usz>0;}).forEach(function(e){SA.prjSrc.push(e);});
    for(var i=0;i<SA.prjSrc.length;i++){var e=SA.prjSrc[i],b=await Z.ent(e),nm=e.name.replace(/^sumber\//,'');SA.srcFiles[nm]=new File([b],nm,{type:'application/octet-stream'});e.file=SA.srcFiles[nm];}
    var imp=E('imp');if(imp&&imp.classList.contains('off')&&SA.reopen){try{await SA.saveWork();}catch(e2){}SA.reopen();}
    await SA.openProjFile(new File([pb],slug(man.name)+'.dh3d',{type:'application/json'}));
    setTimeout(function(){var L=(SA.prjSrc||[]).map(function(e){return e.file.name;});
      say('&#10003; Proyek <b>'+esc(man.name)+'</b> dibuka dari .prj'+(man.createdBy?' (dibuat '+esc(man.createdBy)+', '+new Date(man.createdAt).toLocaleString('id-ID')+')':'')+'.'+(L.length?' File sumber '+esc(L.join(', '))+' tersedia: menu Proyek › <b>Simpan ke folder proyek</b> lalu <b>Salin file block model</b>, atau <b>Ekstrak file sumber</b>.':'')+
        (SA.bxBig&&SA.bxBig.big&&!(window.BX&&BX.m)?' &#9888; Block model besar tidak ikut tersimpan di proyek: ekstrak file sumber lalu import ulang lewat Block Model › Import BM.':''),false,12000);},1500);}
  catch(e){console.error(e);var t='Gagal membuka '+esc(f.name)+': '+esc(e.message);if(window.msg&&E('imp')&&!E('imp').classList.contains('off'))msg(t,true);else say(t,true,9000);}};
SA.prjExtract=async function(){var L=SA.prjSrc||[];if(!L.length)return;for(var i=0;i<L.length;i++){var f=L[i].file;if(!f)continue;var fn=null;
    if(window.gxSimpan){fn=await gxSimpan(f,f.name);}
    else if(window.showSaveFilePicker){try{var h=await showSaveFilePicker({suggestedName:f.name});var w=await h.createWritable();await w.write(f);await w.close();fn=h.name;}catch(e){if(e&&e.name==='AbortError')continue;}}
    if(!fn){var a=document.createElement('a');a.href=URL.createObjectURL(f);a.download=f.name;document.body.appendChild(a);a.click();setTimeout(function(){a.remove();},1500);fn=f.name;}
    say('&#10003; '+esc(fn)+' diekstrak.',false,5000);}};
/* jendela awal: tombol "Buka file proyek" menerima .prj dan .dh3d */
var _op=SA.openProjFile;SA.openProjFile=async function(f){if(f&&/\.prj$/i.test(f.name))return SA.prjOpen(f);return _op.apply(this,arguments);};
setTimeout(function(){document.querySelectorAll('input[type=file][accept=".dh3d,.json"]').forEach(function(i){i.accept='.prj,.dh3d,.json';var l=i.parentNode;if(l&&l.lastChild&&l.lastChild.nodeType===3)l.lastChild.nodeValue='Buka file proyek (.prj / .dh3d)';});},0);
/* menu Proyek */
if(window.FP&&FP.menu){var _m=FP.menu;FP.menu=async function(){var r=await _m.apply(this,arguments),m=E('pjMenu');if(!m)return r;var b=[].filter.call(m.querySelectorAll('button'),function(x){return /\.dh3d|Unduh file proyek/.test(x.textContent);})[0],d=document.createElement('div');
    d.innerHTML='<button onclick="SA.prjSave()" title="Satu file berisi proyek + file sumber block model, untuk dikirim ke rekan">&#128230; Simpan sebagai file .prj&hellip;</button><button onclick="this.nextSibling.click()">&#128194; Buka file .prj&hellip;</button><input type=file accept=".prj" style="display:none" onchange="SA.prjOpen(this.files[0]);this.value=\'\'">'+
      ((SA.prjSrc||[]).length?'<button onclick="SA.prjExtract()">&#8681; Ekstrak file sumber dari .prj ('+esc(SA.prjSrc.map(function(e){return e.name.replace(/^sumber\//,'');}).join(', '))+')</button>':'');
    var kids=[].slice.call(d.childNodes);kids.forEach(function(k){if(b)m.insertBefore(k,b);else m.appendChild(k);});return r;};}
})();
/* ================= .prj dibuka dengan klik dua kali (GC-Ex Desktop) ================= */
(function(){var D=window.gcexDesktop;if(!D||!D.prjPending)return;var say=function(t,bad,ms){if(window.FP&&FP.toast)FP.toast(t,bad,ms==null?0:ms);};
  var go=async function(o){if(!o)return;try{say('Membuka <b>'+esc(o.name)+'</b>&hellip;');var r=await fetch(o.url);if(!r.ok)throw new Error('file tidak bisa dibaca ('+r.status+')');var b=await r.blob();
      var wait=0;while((!window.Plotly||!SA.openProjFile)&&wait++<60)await new Promise(function(z){setTimeout(z,250);});
      await SA.prjOpen(new File([b],o.name,{type:'application/octet-stream'}));}catch(e){console.error(e);say('Gagal membuka '+esc(o.name)+': '+esc(e.message),true,9000);}};
  D.onPrj(go);setTimeout(async function(){try{go(await D.prjPending());}catch(e){}},1500);})();
