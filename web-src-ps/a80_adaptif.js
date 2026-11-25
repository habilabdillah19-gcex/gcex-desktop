/* a80 · Isian ADAPTIF menurut mode (24 Nov 2026, pemilik: "jika suatu tombol tidak relevan dalam suatu mode, tidak perlu tampil")
   Aturan (isian yang sudah berisi nilai TIDAK disembunyikan, supaya batas yang aktif tidak hilang dari pandangan):
   Desain 1 · Dasar pit   : RL dasar + RL atas galian          (RL bawah galian disembunyikan — lantai = RL dasar)
            · Puncak pit  : RL crest atas + RL bawah galian    (RL atas galian disembunyikan — puncak = crest)
            · Batas topo  : RL bawah galian                    (RL acuan bench otomatis & RL atas disembunyikan)
            daftar area   : kolom "atas" / "bawah" per area mengikuti aturan yang sama
   Desain 3 · "Buat jalan" mati → semua isian jalan disembunyikan
   Snap ke string topografi mati → jarak snap disembunyikan
   Edit 4   · "Buat jalan ke dalam sump" mati → "lantai min" disembunyikan
   Edit 6   · "Dinding runcing" mati → sudut muka / izin / berm disembunyikan
   Catatan penjelas kotak RL diganti satu kalimat sesuai mode. */
(function(){const st=document.createElement('style');st.textContent='.adh,body.shx #dock .adh.adh.adh,body.shx #side .adh.adh.adh{display:none!important}';document.head.appendChild(st);})();
function adShow(el,on){if(el)el.classList.toggle('adh',!on);}
function adVal(id){const e=$(id);return !!(e&&String(e.value).trim()!=='');}
function adAfter(el,on){/* saudara setelah el di induk yang sama */for(let n=el.nextElementSibling;n;n=n.nextElementSibling)adShow(n,on);}
function adApply(){try{let m='bot';try{m=smode();}catch(_){}
  adShow($('zmaxw'),m==='bot'||adVal('pZmax'));adShow($('zminw'),m!=='bot'||adVal('pZmin'));
  const sr=$('srl')&&$('srl').closest('.fl');adShow(sr,m!=='topo');
  const box=$('zmaxw')&&$('zmaxw').parentElement;if(box){const h=box.querySelector(':scope > .hint');if(h){const t={bot:'Lantai pit = <b>RL dasar</b>. RL atas galian opsional (kosong = sampai topografi).',top:'Crest teratas di <b>RL crest atas</b>; bench dibangun turun sampai <b>RL bawah galian</b> (kosong = lantai minimum).',topo:'Batas digambar di permukaan topografi; bench turun sampai <b>RL bawah galian</b> (kosong = lantai minimum).'}[m];if(h.dataset.adm!==m){h.dataset.adm=m;h.innerHTML=t;}}box.title='';}
  /* daftar area: atas / bawah */
  for(const s of document.querySelectorAll('.rlp')){if(!s.dataset.adw){s.dataset.adw='1';const a=document.createElement('span'),b=document.createElement('span');a.className='rla';b.className='rlb';let cur=a;for(const n of [...s.childNodes]){if(n.nodeType===3&&/bawah/.test(n.nodeValue)){const i=n.nodeValue.indexOf('bawah');if(i>0)a.appendChild(document.createTextNode(n.nodeValue.slice(0,i)));cur=b;b.appendChild(document.createTextNode(n.nodeValue.slice(Math.max(0,i))));n.remove();continue;}cur.appendChild(n);}s.appendChild(a);s.appendChild(b);}
   const a=s.querySelector('.rla'),b=s.querySelector('.rlb'),ia=a&&a.querySelector('input'),ib=b&&b.querySelector('input');adShow(a,m==='bot'||!!(ia&&ia.value!==''));adShow(b,m!=='bot'||!!(ib&&ib.value!==''));}
  /* jalan */
  const ro=$('rOn');if(ro){const l=ro.closest('label');if(l&&l.parentElement)for(const n of l.parentElement.children)if(n!==l)adShow(n,ro.checked);}
  const sn=$('dgsn'),sd=$('dgsnd');if(sn&&sd){adShow(sd,sn.checked);adShow(sd.nextElementSibling,sn.checked);}
  const ez=$('edzr');if(ez){const l=ez.closest('label');if(l)adAfter(l,ez.checked);}
  /* Edit 2: jarak snap (px) hanya bila snap aktif · Edit 3: tombol pilih titik jalan hanya bila "Lanjutkan jalan" dicentang */
  const es=$('esnp'),ex=$('esnpx');if(es&&ex){adShow(ex,es.checked);adShow(ex.nextElementSibling,es.checked);}
  const er=$('erOn'),ep=$('erpk');if(er&&ep)adShow(ep,er.checked);
  /* Edit Manual · proyeksi: isian RL hanya untuk "RL tetap" */
  const pm=$('mwpm'),pr=$('mwprl');if(pm&&pr)adShow(pr,pm.selectedIndex===0);
  /* Staging: angka jarak tangkap di penjelasan mengikuti isian */
  try{const sf=$('sfsnap'),w=$('fbw'),h=w&&w.querySelector('.flb > .hint b');if(sf&&h&&/\d/.test(h.textContent)){const t=h.textContent.replace(/[\d.,]+/,String(sf.value||10));if(h.textContent!==t)h.textContent=t;}}catch(_){}
  const ew=$('epwOn');if(ew){const l=ew.closest('label');if(l&&l.nextElementSibling)adShow(l.nextElementSibling,ew.checked);}
 }catch(e){console.warn('adaptif',e);}}
document.addEventListener('change',()=>setTimeout(adApply,0),true);document.addEventListener('click',e=>{if(e.target.closest&&e.target.closest('#smode,#tabs,#dkind,.shmp,.cmenu,#ptb'))setTimeout(adApply,30);},true);
setInterval(adApply,1200);setTimeout(adApply,300);
try{window.__PS3.ad={apply:adApply,hidden:()=>[...document.querySelectorAll('.adh')].map(e=>e.id||(e.textContent||'').trim().slice(0,24)||e.tagName)};}catch(_){}
