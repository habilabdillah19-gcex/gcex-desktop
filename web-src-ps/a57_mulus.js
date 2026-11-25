/* a57: perpindahan halaman Properti mulus (23 Nov). Masalah: dalam kerangka (shell), saat membuka halaman lain di menu Tampilan,
   halaman lama ditutup dulu → sideAuto() (mode Edit) menyembunyikan panel samping → 30 ms kemudian resize → halaman baru dibuka →
   panel muncul lagi → resize lagi. Akibatnya 3D & panel melompat dua kali dan tersendat.
   Perbaikan: (1) dalam kerangka panel samping tidak disembunyikan otomatis (kerangka punya halaman kosong sendiri & tombol
   Tampilan → Panel Properti); (2) semua event resize dalam satu bingkai digabung jadi satu; (3) tata letak dock disesuaikan
   seketika saat jendela dibuka/ditutup, tidak menunggu pemindai berkala. */
{const _sa=sideAuto;sideAuto=function(){try{if(typeof SH!=='undefined'&&SH.on){const side=$('side');if(side&&side._auto){side._auto=false;side.classList.remove('hid');const sp=$('split');if(sp)sp.style.display='';}return;}}catch(_){}return _sa.apply(this,arguments);};}
{const _de=window.dispatchEvent.bind(window);let pend=0;window.dispatchEvent=function(ev){try{if(ev&&ev.type==='resize'&&!ev.isTrusted){if(pend)return true;pend=requestAnimationFrame(()=>{pend=0;_de(new Event('resize'));});return true;}}catch(_){}return _de(ev);};}
{const _w=winShow;winShow=function(){const r=_w.apply(this,arguments);try{if(SH.on){shEmpty();dkpGeom();}}catch(_){}return r;};}
try{sideAuto();}catch(_){}
