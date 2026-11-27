/* a86: BUANG PIT YANG SEDANG DIEDIT (pemilik 26 Nov 2026: "setelah Pulihkan, pit tampil tetapi tidak ada tombol hapusnya").
   - Tombol Reset (bilah alat) di mode Edit pit mendapat butir "Tutup & buang pit ini": pit dikeluarkan dari layar, riwayat edit
     dikosongkan, dan salinan simpan-otomatis dihapus → tawaran "Pulihkan" tidak muncul lagi saat aplikasi dibuka berikutnya.
   - ✕ di baris "Pit impor" panel Lapisan dan tautan "Hapus pit impor" kini juga menghapus salinan simpan-otomatis itu
     (dulu pit hilang dari layar tetapi tawaran Pulihkan kembali muncul). Desain Pit final / Staging tidak tersentuh. */
function ebClean(){try{clearTimeout(ehSave.t);}catch(_){}try{EH.st.length=0;EH.i=-1;EH.next=null;EH_SAVED=null;}catch(_){}try{kvDel('edit');}catch(_){}
 try{const r=$('ehrest');if(r)r.hidden=true;}catch(_){}try{ehUI();}catch(_){}try{tbState();}catch(_){}try{SH.sig='';shTreeDraw();}catch(_){}try{layRender();}catch(_){}}
function ebBuang(){if(!ED)return;try{modeOff();}catch(_){}const _c=window.confirm;window.confirm=()=>true;try{const d=$('edel');if(d)d.click();}finally{window.confirm=_c;}
 if(ED){ED=null;try{edStopPick();clr(G.edit);for(const k of ['einfo','eseli','eres'])$(k).innerHTML='';pitRedraw();}catch(_){}}ebClean();}
{const _r=rsItems;rsItems=function(){const it=_r.apply(this,arguments);try{if(!rsSchOn()&&MODE==='edit')it.push({t:'Tutup & buang pit ini',s:'pit keluar dari layar · simpan-otomatis dihapus',dis:!ED,cf:'Buang pit yang sedang diedit beserta riwayat editnya? Simpan dulu (ikon disket) bila masih diperlukan.',fn:ebBuang});}catch(_){}return it;};}
/* jalur hapus lama (✕ Lapisan / tautan "Hapus pit impor"): bersihkan simpan-otomatis sesudahnya */
document.addEventListener('click',e=>{if(e.target&&e.target.closest&&e.target.closest('#edel')){const had=!!ED;setTimeout(()=>{if(had&&!ED)ebClean();},0);}},true);
try{window.__PS3.eb={buang:ebBuang};}catch(_){}
