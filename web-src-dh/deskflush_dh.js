/* ================= GC-Ex Desktop (Drillhole): simpan sebelum jendela ditutup =================
   Dipanggil aplikasi desktop saat tombol x / File > Keluar: simpan ke komputer + folder proyek, lepas kunci,
   lalu izinkan penutupan. Bila gagal, aplikasi menampilkan pilihan "Tutup tanpa menyimpan / Batal". */
window.gcexFlush=async function(){var r={ok:true,folder:!!FP.dir,err:''},wait=function(ms){return new Promise(function(z){setTimeout(z,ms);});};
  try{if(window.SA&&SA.saveWork)await SA.saveWork();}catch(e){r.err='penyimpanan komputer: '+(e&&e.message||e);}
  try{if(FP.dir&&!FP.ro){for(var i=0;i<60&&FP.busy;i++)await wait(150);
      if(FP.pend||FP.unsync){if(FP.toast)FP.toast('Menyimpan ke folder proyek sebelum menutup&hellip;',false,4000);await FP.save(true,'saat menutup');for(i=0;i<60&&(FP.busy||FP.pend);i++)await wait(150);}
      if(FP.busy||FP.pend||FP.unsync){r.ok=false;r.err=FP.err||'perubahan belum masuk folder proyek';}else{try{await FP.lockRelease();}catch(e){}}}
    else if(!FP.dir&&FP._link&&FP.unsync){r.ok=false;r.err='folder proyek belum terhubung (izin folder) sehingga perubahan belum masuk folder';}}
  catch(e){r.ok=false;r.err=String(e&&e.message||e);}
  if(r.ok)FP._reloading=1;return r;};
