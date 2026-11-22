/* a39: "Turun per elevasi" — kasus mine plan: satu area (batas fase) diturunkan per selang RL, tiap penurunan dilaporkan
   grade × tonnage × SR (+ kumulatif & kapan selesai menurut kapasitas fleet). Memakai mesin Pit Schedule (area gali penuh,
   lapis demi lapis, lereng antar-blok, lantai ikut desain) lalu periode "per bench" setinggi selang itu. */
(function(){const dg=$('schdg');if(!dg||$('schelv'))return;const d=document.createElement('div');d.className='r';d.id='schelv';
 d.innerHTML='<button id="schego" style="font-weight:700" title="Seluruh area di dalam Batas fase diturunkan lapis demi lapis sampai lantai desain; laporan grade × tonnage × SR tiap bench (tinggi bench = isian Blok tambang)">&#11015; Turun per bench</button>';
 dg.parentElement.insertAdjacentElement('afterend',d);$('schego').onclick=()=>{schElev().catch(e=>{schMsg(esc(e.message),1);console.error(e);});};})();
async function schElev(){const ph=schPh(),dz=Math.max(+$('schh2').value||2.5,+($('mbbh')||{}).value||10);if(!ph.bnd||ph.bnd.length<3){schMsg('Gambar <b>Batas fase</b> dulu (poligon area yang dijadwalkan), lalu tekan Hitung.',1);return false;}
 if(ph.lock)throw new Error(ph.nm+' sudah dikunci.');const D=schDes(),own=SCH.tasks.find(t=>t._elev),lines=SCH.tasks.filter(t=>t.on&&!t._elev);
 if(!lines.length){const o={nm:'Area fase (turun per elevasi)',_elev:1};if(D.length){o.fm='des';o.fd=(D.find(x=>x.id==='res')||D[0]).id;}else{o.fm='depth';o.fv=Math.max(dz,30);}
  if(own){own.pts=ph.bnd.map(q=>q.slice());own.on=true;}else schAdd('poly',ph.bnd.map(q=>[q[0],q[1],q[2]||0]),o);}
 else if(own)own.on=false;
 schRun();const u=$('schun');$('schhb').value=dz;SCH.hbSet=1;u.value='b';u.dispatchEvent(new Event('change'));GTR.cum=true;gtMount();
 if(GT.file){for(let i=0;i<400&&GT.busy;i++)await new Promise(r=>setTimeout(r,100));if(!GT.res)await gtRun();try{const e=$('schcm');e.value='kls';e.dispatchEvent(new Event('change'));}catch(_){}gtBig(true);
  schMsg('Turun per '+schF(dz,1)+' m: '+SCH.bd.length+' selang elevasi'+(lines.length?' (mengikuti jalur gali yang ada)':' (seluruh area, lapis demi lapis)')+'. Klik baris / batang untuk melihat permukaannya.');}
 else{gtOpen(true);schMsg('Volume per '+schF(dz,1)+' m sudah dihitung (tabel volume). Untuk <b>kadar, tonase ore & SR</b>: muat block model .mdl di jendela Block model — laporan langsung muncul.');}
 return true;}
/* setelah block model dimuat sementara jadwal per elevasi sudah ada → laporan besar langsung tampil */
{const _l=gtLoad;gtLoad=async function(){const r=await _l.apply(this,arguments);try{if(GTR.cum&&SCH.sim&&GT.file&&!GT.res){await gtRun();gtBig(true);}}catch(_){}return r;};}
try{window.__PS3.sch.elev=()=>schElev();}catch(_){}
