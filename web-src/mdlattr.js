/* ============ Pembaca DAFTAR ATRIBUT block model Surpac .mdl (Version 4.0) — dipakai GC-Ex Block Model & Drillhole ============
   mdlAttrs(u, p, na) -> {A:[{name, calc, expr | type, def, w, rawType?}], p: posisi sesudah atribut terakhir}
   u = Uint8Array header (boleh terpotong: melempar Error dengan e.more=true bila butuh byte lebih banyak),
   p = posisi atribut pertama, na = jumlah atribut dari header.                                                     */
function mdlAttrs(u,p,na){var L=u.length,dv=new DataView(u.buffer,u.byteOffset,u.length),td=new TextDecoder('latin1');
  var more=function(){var e=new Error('header terpotong');e.more=true;throw e;};
  var str=function(p){var e=p;while(e<L&&u[e]!==0)e++;if(e>=L)more();return{s:td.decode(u.subarray(p,e)),p:e+1};};
  var i;
  /* Daftar atribut dibaca dengan VERIFIKASI (0.24.56). Dulu lebar nilai bawaan tiap atribut ditebak dari tipenya saja
     (real 8+1 byte, integer 4+1, karakter teks+1). Bila satu atribut di model pemilik tersimpan dengan lebar lain,
     pembacaan bergeser dan atribut BERIKUTNYA terbaca kacau -- 'Tipe atribut "" (24940) belum didukung' (24940 = huruf
     'al' dari nama atribut lain). Kini beberapa lebar dicoba, dan yang dipakai adalah yang membuat atribut berikutnya
     (nama teks + penanda kalkulasi 0/1) atau, untuk atribut terakhir, kunci blok pertama, terbaca sah. */
  /* Seluruh sisa daftar dicoba sampai kunci blok pertama (runut-balik): satu lebar yang 'kebetulan' membuat nama
     berikutnya tampak sah (mis. melewati satu huruf) tidak lolos bila atribut-atribut sesudahnya tidak terbaca. */
  var datOk=function(q){q+=4;if(q+8>L)more();var k=dv.getUint32(q);return (k&31)<=24;};
  /* 'd4'/'d8' = nilai 4/8 byte lalu TEKS DESKRIPSI atribut berakhiran 0; 'ds' = teks bawaan lalu teks deskripsi (Surpac yang
     mengisi kolom Description, mis. sg3 = "density"; 0.24.80 -- dulu deskripsi terbaca sebagai nama atribut berikutnya). */
  var cands=function(ty){return ty===1?[5,9,4,8,13,'d4','d8']:(ty===2||ty===4||ty===5)?[9,8,13,5,17,'d8','d4']:ty===3?['s1','s0','s5','s9','ds']:[9,5,'s1',8,4,13,17,'s0','s5','d8','d4','ds'];};
  var desk=function(q){var e=q;while(e<L&&e-q<128&&u[e]>=32&&u[e]<127)e++;if(e>=L)more();return (e-q<128&&u[e]===0)?{s:td.decode(u.subarray(q,e)),p:e+1}:null;};
  var KNOWN=function(ty){return ty===1||ty===2||ty===3||ty===4||ty===5;},langkah=0;
  var baca=function(p,i){if(++langkah>20000)return null;if(i===na)return datOk(p)?{p:p,A:[]}:null;
    var e=p;while(e<L&&e-p<96&&u[e]>=32&&u[e]<127)e++;if(e>=L)more();if(e===p||e-p>=96||u[e]!==0)return null;
    var nm=td.decode(u.subarray(p,e)),q=e+1;if(q+12>L)more();var calc=dv.getInt32(q);if(calc!==0&&calc!==1)return null;q+=8;var r;
    if(calc===1){var x=str(q);for(var k=0;k<2;k++){r=baca(x.p+k,i+1);if(r){r.A.unshift({name:nm,calc:true,expr:x.s});return r;}}var xd=desk(x.p);if(xd&&xd.s){r=baca(xd.p,i+1);if(r){r.A.unshift({name:nm,calc:true,expr:x.s,desc:xd.s});return r;}}return null;}
    if(q+28>L)more();var ty=dv.getInt32(q);q+=4;var C=cands(ty);
    for(var ci=0;ci<C.length;ci++){var w=C[ci],nq,dvl,ds=null;if(w==='ds'||w==='d4'||w==='d8'){var vq;if(w==='ds'){var d0=str(q);dvl=d0.s;vq=d0.p;}else{if(q+8>L)more();dvl=w==='d4'?dv.getInt32(q):dv.getFloat64(q);vq=q+(+w.slice(1));}ds=desk(vq);if(!ds||!ds.s)continue;r=baca(ds.p,i+1);if(r){var a1={name:nm,calc:false,type:ty,def:dvl,w:w,desc:ds.s};if(!KNOWN(ty)){a1.rawType=ty;a1.type=w==='ds'?3:w==='d4'?1:2;}r.A.unshift(a1);return r;}continue;}if(typeof w==='string'){var d=str(q);dvl=d.s;nq=d.p+(+w.slice(1));}else{dvl=(w===5||w===4)?dv.getInt32(q):dv.getFloat64(q);nq=q+w;}
      if(nq>L)more();/* byte ekor sesudah nilai (penanda) tidak boleh berupa huruf: kalau huruf, itu awal nama atribut berikutnya */var v0=typeof w==='string'?nq-(+w.slice(1)):q+((w===5||w===4)?4:8),bad=false;for(var z=v0;z<nq;z++)if(u[z]>=32&&u[z]<127){bad=true;break;}if(bad)continue;r=baca(nq,i+1);if(r){var a={name:nm,calc:false,type:ty,def:dvl,w:w};if(!KNOWN(ty)){a.rawType=ty;a.type=typeof w==='string'?3:(w===5||w===4)?1:2;}r.A.unshift(a);return r;}}
    return null;};
  var R=baca(p,0);
  if(!R){/* tidak ada susunan yang sah: laporkan atribut terakhir yang masih terbaca dengan tata letak baku */var ok=[],q0=p;try{for(i=0;i<na;i++){var s0=str(q0),c0=dv.getInt32(s0.p);if(c0===1){ok.push(s0.s);q0=str(s0.p+8).p;continue;}var t0=dv.getInt32(s0.p+8);if(!KNOWN(t0))throw new Error('Atribut ke-'+(i+1)+' sesudah "'+(ok[ok.length-1]||'-')+'" tidak terbaca (tipe '+t0+').');ok.push(s0.s);q0=t0===3?str(s0.p+12).p+1:s0.p+12+(t0===1?5:9);}}catch(er){if(er.more)throw er;throw new Error(er.message+' Kirim file .mdl ini ke admin GC-Ex.');}
    throw new Error('Daftar atribut .mdl tidak bisa dipastikan ('+ok.join(', ')+'). Kirim file .mdl ini ke admin GC-Ex.');}
  return R;
}
if(typeof window!=='undefined')window.mdlAttrs=mdlAttrs;
