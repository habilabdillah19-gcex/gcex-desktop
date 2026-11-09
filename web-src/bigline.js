/* ================= GC-Ex: pembaca garis berukuran jumbo (topografi / desain pit .str, .dxf, .csv/.xyz) =================
   Pembaca asli membaca seluruh file menjadi SATU teks lalu memecahnya per baris. Untuk file ±500 MB itu memakan
   memori 3-4 GB dan gagal total ("Invalid string length") bila teks melewati ±512 juta karakter (batas mesin JavaScript).
   Modul ini membaca file per potongan 8 MB dan memproses baris demi baris dengan aturan yang SAMA PERSIS
   (urutan baris, pemisah kolom, penanda segmen, pasangan kode DXF), sehingga hasilnya identik dengan pembaca asli.
   Untuk topografi & desain pit di layar Mulai, setiap segmen langsung disederhanakan (toleransi yang sama) begitu selesai
   dibaca, jadi titik mentah tidak pernah ditampung semuanya di memori. */
(function(){if(typeof readStr!=='function'||typeof readDxf!=='function'||typeof readXyz!=='function'||window.GCBL)return;
  var G={ch:8*1048576},str0=readStr,yieldUI=function(){return new Promise(function(r){setTimeout(r,0);});};
  /* setiap baris persis seperti teks.split(/\r?\n/) (termasuk potongan terakhir yang kosong bila file diakhiri baris baru) */
  async function eachLine(f,cb,prog){var dec=new TextDecoder('utf-8'),rest='',off=0,N=f.size;
    while(off<N){var end=Math.min(N,off+G.ch),buf=new Uint8Array(await f.slice(off,end).arrayBuffer());off=end;
      var t=rest+dec.decode(buf,{stream:true}),a=0,b;
      while((b=t.indexOf('\n',a))>=0){if(cb(t.slice(a,b>a&&t.charCodeAt(b-1)===13?b-1:b))===false)return;a=b+1;}
      rest=t.slice(a);if(prog)prog(off/N);await yieldUI();}
    rest+=dec.decode();cb(rest);}
  /* ---------- Surpac .str ---------- */
  async function readStrS(file,yx,emit,prog){var N=file.size,hd=new Uint8Array(await file.slice(0,Math.min(N,1048576)).arrayBuffer()),nl=0,ds=-1;
    for(var i=0;i<hd.length;i++){if(hd[i]===10){nl++;if(nl===2){ds=i+1;break;}}}
    if(ds<0&&N>hd.length){var S=await str0(file,yx);S.forEach(emit);return;}
    if(ds<0||ds>=N)throw new Error('format STR tidak dikenali');
    var c=hd[ds],cur=[],prev=null,csn=null,flush=function(){if(cur.length){cur.sn=csn;emit(cur);}cur=[];};
    if((c>=48&&c<=57)||c===32||c===45||c===13||c===10||c===9||c===43||c===46){
      await eachLine(file,function(L){var ln=L.replace(/\t/g,' ').trim();if(!ln)return;var a=ln.indexOf(',')>=0?ln.split(','):ln.split(/\s+/),sn=null,x,y,z,ok=false;a=a.map(function(v){return v.trim();});
        if(a.length>=4&&RXN.test(a[0])&&RXN.test(a[1])&&RXN.test(a[2])&&RXN.test(a[3])){sn=a[0];x=+a[1];y=+a[2];z=+a[3];ok=true;}
        else if(a.length===3&&RXN.test(a[0])&&RXN.test(a[1])&&RXN.test(a[2])){sn='1';x=+a[0];y=+a[1];z=+a[2];ok=true;}
        if(!ok)return;if(yx){var t=x;x=y;y=t;}
        if(x===0&&y===0&&z===0){flush();prev=null;return;}if(prev!==null&&sn!==prev)flush();prev=sn;csn=+sn;cur.push([x,y,z]);},prog);
      flush();return;}
    /* biner Surpac (big-endian): tiap rekaman = [1 byte flag 0x00][int32 nomor string][Y][X][Z] (29 byte) lalu DESKRIPSI sebagai
       TEKS berpanjang bebas (",2", ",9", ",Lensa A", … — dimulai koma, hanya karakter cetak) sampai byte awal rekaman berikutnya (0x00).
       Rekaman 29 byte nol = pemisah string. Sesudah header ada 4 byte awalan (nol). Akhir file: bantalan nol lalu "END".
       Dulu deskripsi dianggap 8 byte biner per kolom (rekaman tetap 29+8k) sehingga STR pit berdeskripsi teks (laporan pemilik
       9 Nov 2026: pit_z2_*.str) terbaca bergeser -> koordinat liar / kosong. Pembaca lama tetap jadi cadangan. */
    var tl=Math.min(N,67),tu=new Uint8Array(await file.slice(N-tl,N).arrayBuffer()),end=N;
    for(var k=N-3;k>=ds&&N-k<=64;k--){var q=k-(N-tl);if(tu[q]===69&&tu[q+1]===78&&tu[q+2]===68){end=k;break;}}
    var ok1=function(v){return isFinite(v)&&Math.abs(v)<1e8;},sane=function(dv,p){var y0=dv.getFloat64(p+5,false),x0=dv.getFloat64(p+13,false),z0=dv.getFloat64(p+21,false);return (x0===0&&y0===0&&z0===0)||(ok1(x0)&&ok1(y0)&&Math.abs(z0)<1e6&&(Math.abs(x0)>1e-3||Math.abs(y0)>1e-3));};
    var hb=new Uint8Array(await file.slice(ds,Math.min(end,ds+4096)).arrayBuffer()),hv=new DataView(hb.buffer),start=-1;
    for(var k0=0;k0<=16&&k0+58<=hb.length;k0++){if(hb[k0]!==0)continue;if(sane(hv,k0)){var nx=k0+29;while(nx<hb.length&&hb[nx]>=32&&hb[nx]<=126)nx++;if(nx+29>hb.length||(hb[nx]===0&&sane(hv,nx))){start=k0;break;}}}
    if(start<0){await strTetap(file,yx,emit,prog,ds,end,flush,function(P){cur=P.cur;csn=P.csn;});return;}
    var o=ds+start,pn=-1,nTot=0,nBad=0,carry=null,co=0;
    while(o<end){var e2=Math.min(end,o+G.ch),u=new Uint8Array(await file.slice(o,e2).arrayBuffer()),dv=new DataView(u.buffer),p=0,last=e2>=end,lim=u.length;
      while(p+29<=lim){
        if(!last&&lim-p<29+256)break;/* deskripsi bisa terpotong di batas potongan: sisakan untuk potongan berikutnya */
        var zero=true;for(var zq=0;zq<29;zq++){if(u[p+zq]!==0){zero=false;break;}}
        if(zero){flush();pn=-1;p+=29;continue;}
        if(u[p]!==0){p++;nBad++;continue;}/* bukan awal rekaman: geser 1 byte (sinkronisasi ulang) */
        var no=u[p+1]*16777216+(u[p+2]<<16|u[p+3]<<8|u[p+4]),Y=dv.getFloat64(p+5,false),X=dv.getFloat64(p+13,false),Z=dv.getFloat64(p+21,false);p+=29;
        while(p<lim&&u[p]>=32&&u[p]<=126)p++;/* deskripsi teks */
        if(!yx){var t2=X;X=Y;Y=t2;}nTot++;
        if(!(ok1(X)&&ok1(Y)&&Math.abs(Z)<1e6)){nBad++;continue;}
        if(X===0&&Y===0&&Z===0){flush();pn=-1;}else{if(pn>=0&&no!==pn)flush();pn=no;csn=no;cur.push([X,Y,Z]);}}
      o+=p;if(p===0)break;if(prog)prog(o/N);await yieldUI();}
    G.lastRecLen='teks';G.lastBad=nBad;
    if(nTot&&nBad>nTot/2){/* hampir semua rusak: coba pembaca rekaman tetap lama */cur=[];await strTetap(file,yx,emit,prog,ds,end,flush,function(P){cur=P.cur;csn=P.csn;});return;}
    flush();}
  /* cadangan: rekaman tetap 29 + 8 byte per kolom deskripsi biner (dideteksi), pembaca sebelum 9 Nov 2026 */
  async function strTetap(file,yx,emit,prog,ds,end,flush0,setCur){var N=file.size,cur=[],csn=null,pn=-1,flush=function(){if(cur.length){cur.sn=csn;emit(cur);}cur=[];};
    var RL=29,best=-1,ok1=function(v){return isFinite(v)&&Math.abs(v)<1e8;},smp=new Uint8Array(await file.slice(ds,Math.min(end,ds+8388608)).arrayBuffer()),sv=new DataView(smp.buffer);
    for(var rs=29;rs<=29+8*12;rs+=8){var o0=(end-ds)%rs,nr0=Math.floor((smp.length-o0)/rs),st0=Math.max(1,Math.floor(nr0/3000)),good=0,tot=0;
      for(var q0=0;q0<nr0;q0+=st0){var p0=o0+q0*rs,y0=sv.getFloat64(p0+5,false),x0=sv.getFloat64(p0+13,false),z0=sv.getFloat64(p0+21,false);tot++;
        if((x0===0&&y0===0&&z0===0)||(ok1(x0)&&ok1(y0)&&Math.abs(z0)<1e6&&(Math.abs(x0)>1e-3||Math.abs(y0)>1e-3)))good++;}
      var sc=tot?good/tot:0;if(sc>best+1e-9){best=sc;RL=rs;}if(sc===1)break;}
    smp=null;sv=null;G.lastRecLen=RL;
    var o=ds+((end-ds)%RL),R=RL*Math.max(1,Math.floor(G.ch/RL));
    while(o+RL<=end){var e2=Math.min(end,o+R),nr=Math.floor((e2-o)/RL);if(!nr)break;var u=new Uint8Array(await file.slice(o,o+nr*RL).arrayBuffer()),dv=new DataView(u.buffer);
      for(var r=0,p=0;r<nr;r++,p+=RL){var no=u[p+1]*16777216+(u[p+2]<<16|u[p+3]<<8|u[p+4]),Y=dv.getFloat64(p+5,false),X=dv.getFloat64(p+13,false),Z=dv.getFloat64(p+21,false);
        if(!yx){var t2=X;X=Y;Y=t2;}if(X===0&&Y===0&&Z===0){flush();pn=-1;}else{if(pn>=0&&no!==pn)flush();pn=no;csn=no;cur.push([X,Y,Z]);}}
      o+=nr*RL;if(prog)prog(o/N);await yieldUI();}
    flush();}
  /* ---------- DXF ASCII ---------- */
  async function readDxfS(file,emit,prog){var inE=false,ent=null,idx=0,codeL=null,bin=false;
    var close=function(){if(!ent)return;var t=ent.t,g=ent.g,num=function(c){for(var k=0;k<g.length;k++)if(g[k][0]===c)return +g[k][1];return 0;};
      if(t==='LINE')emit([[num(10),num(20),num(30)],[num(11),num(21),num(31)]]);
      else if(t==='POINT')emit([[num(10),num(20),num(30)]]);
      else if(t==='3DFACE'){var P=[[num(10),num(20),num(30)],[num(11),num(21),num(31)],[num(12),num(22),num(32)],[num(13),num(23),num(33)]];if(P[3][0]===P[2][0]&&P[3][1]===P[2][1]&&P[3][2]===P[2][2])P.pop();P.push(P[0]);emit(P);}
      else if(t==='LWPOLYLINE'){var el=num(38),P2=[],cx=null;g.forEach(function(p){if(p[0]===10)cx=+p[1];else if(p[0]===20&&cx!==null){P2.push([cx,+p[1],el]);cx=null;}});if(num(70)&1&&P2.length)P2.push(P2[0]);emit(P2);}
      else if(t==='POLYLINE'){ent.poly={P:[],closed:(num(70)&1)===1};SA._poly=ent.poly;}
      else if(t==='VERTEX'&&SA._poly){var fl=num(70);if(!(fl&128)||(fl&64))SA._poly.P.push([num(10),num(20),num(30)]);}
      else if(t==='SEQEND'&&SA._poly){var Q=SA._poly.P;if(SA._poly.closed&&Q.length)Q.push(Q[0]);emit(Q);SA._poly=null;}ent=null;};
    SA._poly=null;
    await eachLine(file,function(L){if(idx===0&&L.indexOf('AutoCAD Binary DXF')>=0){bin=true;return false;}
      if(idx++%2===0){codeL=L;return;}var code=parseInt(codeL,10),val=L.trim();if(!isFinite(code))return;
      if(code===0){if(val==='SECTION'){return;}if(val==='ENDSEC'){close();inE=false;return;}if(inE){close();ent={t:val,g:[]};}return;}
      if(code===2&&val==='ENTITIES'&&!ent){inE=true;return;}if(ent)ent.g.push([code,val]);},prog);
    if(bin)throw new Error('DXF binary belum didukung; simpan sebagai DXF ASCII');
    close();SA._poly=null;}
  /* ---------- CSV / XYZ titik (pemisah & tanda kutip seperti parseDelim) ---------- */
  async function readXyzS(file,emit,prog){var dec=new TextDecoder('utf-8'),off=0,N=file.size,first=true,best=',',row=[],cur='',q=false,carry='',head=[],ix,iy,iz,st=1,ready=false,ri=0;
    var decide=function(){var hdr=head[0]||[],T={h:hdr.map(txt),r:[]};ix=findCol(T,H.EAST,-1);iy=findCol(T,H.NORTH,-1);iz=findCol(T,H.RL,-1);st=1;
      if(ix<0||iy<0||iz<0){var nums=[];(head[0]||[]).forEach(function(v,i){if(numV(v)!==null)nums.push(i);});if(nums.length>=3){ix=nums[0];iy=nums[1];iz=nums[2];st=0;}else{var r1=head[1]||[];nums=[];r1.forEach(function(v,i){if(numV(v)!==null)nums.push(i);});ix=nums[0];iy=nums[1];iz=nums[2];}}
      if(ix==null||iy==null||iz==null)throw new Error('kolom X, Y, Z tidak ditemukan');ready=true;var H2=head;head=null;for(var k=st;k<H2.length;k++)use(H2[k]);};
    var use=function(r){var x=numV(r[ix]),y=numV(r[iy]),z=numV(r[iz]);if(x!==null&&y!==null&&z!==null)emit([[x,y,z]]);};
    var put=function(r){r=r.map(function(v){v=v.trim();return v===''?null:v;});ri++;if(ready){use(r);return;}head.push(r);if(head.length>=2)decide();};
    var run=function(t,last){var L=last?t.length:t.length-1,i=0;
      for(;i<L;i++){var ch=t.charAt(i);if(q){if(ch==='"'){if(t.charAt(i+1)==='"'){cur+='"';i++;}else q=false;}else cur+=ch;continue;}
        if(ch==='"'){q=true;continue;}if(ch===best){row.push(cur);cur='';continue;}if(ch==='\n'||ch==='\r'){if(ch==='\r'&&t.charAt(i+1)==='\n')i++;row.push(cur);put(row);row=[];cur='';continue;}cur+=ch;}
      return i<t.length?t.slice(i):'';};
    while(true){var last=off>=N,t;if(!last){var e=Math.min(N,off+G.ch),buf=new Uint8Array(await file.slice(off,e).arrayBuffer());off=e;t=carry+dec.decode(buf,{stream:true});}else t=carry+dec.decode();
      if(first&&!last&&t.length<4000){carry=t;continue;}
      if(first){first=false;t=t.replace(/^\uFEFF/,'');var f0=t.slice(0,4000).split(/\r?\n/)[0],bn=-1;[',',';','\t','|'].forEach(function(d){var n=f0.split(d).length;if(n>bn){bn=n;best=d;}});}
      carry=run(t,last);if(last)break;if(prog)prog(off/N);await yieldUI();}
    if(cur!==''||row.length){row.push(cur);put(row);}
    if(!ready)decide();}
  function readLinesS(s,emit,prog){var x=s.k;if(x==='str')return readStrS(s.f,E('strOrd')?E('strOrd').value==='yx':true,emit,prog);if(x==='dxf')return readDxfS(s.f,emit,prog);return readXyzS(s.f,emit,prog);}
  /* pembaca lama tetap tersedia dengan hasil yang sama (dipakai menu lain: DTM, boundary, titik pick-up, string model) */
  readStr=async function(file,yx){var S=[];await readStrS(file,yx,function(P){S.push(P);});return S;};
  readDxf=async function(file){var S=[];await readDxfS(file,function(P){S.push(P);});return S;};
  readXyz=async function(file){var S=[];await readXyzS(file,function(P){S.push(P);});return S;};
  /* baca + sederhanakan per segmen (sama dengan segsOut) + batas area; titik ditambahkan ke out hanya bila file terbaca utuh */
  /* titik berkoordinat tidak masuk akal (SA.koordOk) dibuang per titik & dihitung; > separuh rusak -> file ditolak */
  SA.readLinesInto=async function(s,out,tol,ab,prog){var o2=[],n0=0,n1=0,x0=1e18,x1=-1e18,y0=1e18,y1=-1e18,z0=1e18,z1=-1e18,bad=0,tot=0,okF=SA.koordOk||function(){return true;};G.lastRecLen=0;
    await readLinesS(s,function(P0){var P=[];for(var t=0;t<P0.length;t++){tot++;if(okF(P0[t][0],P0[t][1],P0[t][2]))P.push(P0[t]);else bad++;}if(P0.sn!=null)P.sn=P0.sn;if(P.length){var k=dpKeep(P,tol);for(var i=0;i<P.length;i++){n0++;if(k[i]){o2.push(P[i]);n1++;}}o2.push(null);}
      for(var j=0;j<P.length;j++){var p=P[j];if(p[0]<x0)x0=p[0];if(p[0]>x1)x1=p[0];if(p[1]<y0)y0=p[1];if(p[1]>y1)y1=p[1];if(isFinite(p[2])){if(p[2]<z0)z0=p[2];if(p[2]>z1)z1=p[2];}if(ab)ab(p[0],p[1],p[2]);}},prog);
    if(tot&&bad>tot*0.5)throw new Error(bad.toLocaleString()+' dari '+tot.toLocaleString()+' titik berkoordinat tidak masuk akal — file tidak terbaca benar. Bila ini STR biner Surpac, simpan ulang sebagai STR teks (ASCII) atau DXF lalu import lagi.');
    for(var m=0;m<o2.length;m++)out.push(o2[m]);return{nn:[n0,n1],x0:x0,x1:x1,y0:y0,y1:y1,z0:z0<1e17?z0:NaN,z1:z1>-1e17?z1:NaN,buang:bad,recLen:G.lastRecLen};};
  G.eachLine=eachLine;G.readLinesS=readLinesS;G.str0=str0;window.GCBL=G;
})();
