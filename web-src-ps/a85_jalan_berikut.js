/* a85: JALAN BERIKUTNYA per area (pemilik 25 Nov 2026: "dua jalan keluar dari satu lantai").
   Tiap area: jalan utama (Tarik arah jalan → a.rs / a.rv) + maks 2 jalan berikutnya a.rx[] = {rs, rv, flip}, nama A2, A3 …
   Dibuat dengan cara yang sama dengan jalan utama (rampsInit), tidak saling dihentikan aturan gabung (a19) bila satu area.
   Bawaan: tidak ada jalan berikutnya → desain sama persis dengan sebelumnya. Tersimpan di .pit.json (base.rx / extra[].rx). */
(function(){const b=$('rdrw');if(!b||$('rdrw2'))return;
 b.insertAdjacentHTML('afterend','<button id="rdrw2" title="Tambah jalan keluar lain dari area terdekat: klik titik 1 lalu titik 2 (sama seperti Tarik arah jalan). Maks 3 jalan per area. Jalan utama tidak berubah." style="margin-top:4px">&#10010; Jalan berikutnya (titik 1 &#8594; titik 2)</button><div id="rx2l" class="hint" style="margin-top:3px"></div>');
 $('rdrw2').onclick=()=>{if(!BASE){alert('Buat bentuk awal (langkah 2) dulu.');return;}$('rdrw2').classList.add('on');
  drvStart((a,c)=>{$('rdrw2').classList.remove('on');const ar=areas()[nearArea(a)];if(!ar)return;ar.rx=ar.rx||[];if(ar.rx.length>=2){alert('Maksimal 3 jalan per area (1 utama + 2 berikutnya). Hapus salah satu dulu.');return;}
   ar.rx.push({rs:a,rv:[c[0]-a[0],c[1]-a[1]]});if(RES)RES.stale=true;rPickDraw();},()=>BASE.z);};})();
function rx2List(){const el=$('rx2l');if(!el)return;const A=areas(),it=[];A.forEach((a,i)=>(a.rx||[]).forEach((x,k)=>it.push([i,k,String.fromCharCode(65+i)+(k+2),x])));
 if(!it.length){el.innerHTML=A.length?'Satu jalan per area. <b>Jalan berikutnya</b> menambah jalan keluar lain dari area yang sama.':'';return;}
 el.innerHTML='Jalan berikutnya: '+it.map(([i,k,nm,x])=>'<span style="white-space:nowrap;margin-right:8px"><b>'+nm+'</b> (area '+(i+1)+')'+(x.flip?' <span style="color:#B45309" title="Jalan ini berputar berlawanan dengan jalan utama, jadi kedua jalan pasti berpotongan di lereng (silang crest/jalan). Desain otomatis belum membuat simpang jalan: kembalikan arah putar (↻ balik lagi) atau pindahkan titik awal supaya searah.">⚠ berlawanan arah</span>':'')+' <a href="#" data-rxf="'+i+','+k+'" title="Balik arah putar jalan ini">&#8635; balik</a> <a href="#" data-rxd="'+i+','+k+'" title="Hapus jalan ini">&#10005;</a></span>').join('');
 el.querySelectorAll('[data-rxd]').forEach(q=>q.onclick=e=>{e.preventDefault();const [i,k]=q.dataset.rxd.split(',').map(Number),a=areas()[i];if(a&&a.rx){a.rx.splice(k,1);if(!a.rx.length)delete a.rx;}if(RES)RES.stale=true;rPickDraw();});
 el.querySelectorAll('[data-rxf]').forEach(q=>q.onclick=e=>{e.preventDefault();const [i,k]=q.dataset.rxf.split(',').map(Number),x=(areas()[i].rx||[])[k];if(x)x.flip=!x.flip;if(RES)RES.stale=true;rPickDraw();});}
{const _p=rPickDraw;rPickDraw=function(){const r=_p.apply(this,arguments);try{const g=G.ref.children.find(o=>o.userData.rs);if(g){let TS=null;if(BASE&&BASE.mode==='topo'&&BASE.src3){try{TS=topoStart();}catch(_){}}const zd=TS?TS.z:(BASE?BASE.z:0);
   for(const a of areas())for(const x of (a.rx||[]))if(x.rs&&x.rv)g.add(arrowObj(x.rs,[x.rs[0]+x.rv[0],x.rs[1]+x.rv[1]],zd+0.8));}
  const c=$('rclr');if(c){const f=c.onclick;c.onclick=ev=>{areas().forEach(a=>delete a.rx);f&&f(ev);};}rx2List();}catch(e){console.warn(e);}return r;};}
