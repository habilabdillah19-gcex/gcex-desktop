"""Model Estimation merekam SPASI BOR & JUMLAH BOR per blok, lalu dipakai klasifikasi sumber daya.

Sebelumnya tiap blok hanya menyimpan est_pass, est_nsamp, est_sor, est_ke, est_kv. Jumlah komposit
(est_nsamp) bukan ukuran kerapatan bor: 20 komposit dari SATU lubang bor sangat berbeda artinya
dengan 20 komposit dari 6 lubang. Padahal justru kerapatan bor itulah yang dipakai Competent Person
untuk menetapkan Measured / Indicated / Inferred.

Tiga atribut baru per blok (ditulis saat estimasi, ikut ke block model & export):
  est_nhole  jumlah LUBANG BOR BERBEDA yang komposit-nya dipakai blok itu
  est_dmin   jarak (m) dari pusat blok ke komposit terdekat yang dipakai
  est_spasi  perkiraan SPASI BOR setempat (m): untuk tiap lubang bor yang dipakai diambil komposit
             terdekat ke blok, lalu dihitung rata-rata jarak mendatar tiap lubang ke lubang
             terdekat lainnya. Dengan kata lain: "bor di sekitar blok ini berjarak rata-rata sekian
             meter". Bernilai -99 bila lubang yang dipakai kurang dari dua.

Titik sambung (semuanya diperiksa harus muncul tepat satu kali) ada di gcex_dh_base.html.
"""


def patch(s: str) -> str:
    def R(a, b):
        nonlocal s
        assert s.count(a) == 1, 'titik sambung mecls (%d x): %s' % (s.count(a), a[:90])
        s = s.replace(a, b)

    # 1. daftar kolom simpanan Model Estimation
    R("var MEF=['x','y','z','sx','sy','sz','dom','est','pass','sor','ke','kv','ns','type','date','run'];",
      "var MEF=['x','y','z','sx','sy','sz','dom','est','pass','sor','ke','kv','ns','nh','dmin','spasi','type','date','run'];")

    # 2. nama atribut
    R("return{est:e+'_est',fin:e+'_final',dom:'domain_est',pass:'est_pass',sor:'est_sor',ke:'est_ke',kv:'est_kv',ns:'est_nsamp',type:'est_type',date:'est_date',run:'est_run'};",
      "return{est:e+'_est',fin:e+'_final',dom:'domain_est',pass:'est_pass',sor:'est_sor',ke:'est_ke',kv:'est_kv',ns:'est_nsamp',"
      "nh:'est_nhole',dmin:'est_dmin',spasi:'est_spasi',type:'est_type',date:'est_date',run:'est_run'};")

    # 3. tipe larik saat disimpan ke proyek (dmin & spasi pecahan, nh bulat)
    R("['sx','sy','sz','sor','ke','kv'].indexOf(k)>=0?Float32Array.from(a)",
      "['sx','sy','sz','sor','ke','kv','dmin','spasi'].indexOf(k)>=0?Float32Array.from(a)")

    # 4. hitung saat estimasi: jumlah bor berbeda, jarak terdekat, spasi bor setempat
    R("var r=okKrige(mo,X.C,X.z,sel,x,y,z,dc.D,cbb);if(!r)continue;res={est:r.est,pass:p+1,sor:r.sor,ke:r.ke,kv:r.kv,ns:sel.length,ex:meExEst(X,sel,r.w)};",
      "var r=okKrige(mo,X.C,X.z,sel,x,y,z,dc.D,cbb);if(!r)continue;var _sp=meSpasi(X.C,sel,x,y,z);"
      "res={est:r.est,pass:p+1,sor:r.sor,ke:r.ke,kv:r.kv,ns:sel.length,nh:_sp.nh,dmin:_sp.dmin,spasi:_sp.spasi,ex:meExEst(X,sel,r.w)};")

    # fungsi bantu, disisipkan sebelum meStep
    R("function meStep(){",
      """/* Kerapatan bor di sekitar satu blok, dari komposit yang benar-benar dipakai kriging.
   nh    = jumlah lubang bor berbeda
   dmin  = jarak (m) ke komposit terdekat
   spasi = perkiraan spasi bor setempat: tiap lubang diwakili komposit terdekatnya ke blok, lalu
           dirata-ratakan jarak MENDATAR tiap lubang ke lubang terdekat lainnya. -99 bila < 2 lubang. */
function meSpasi(C,sel,x,y,z){var rep={},dmin=1e18,i,c,dx,dy,dz,d2;
  for(i=0;i<sel.length;i++){c=C[sel[i]];dx=c.x-x;dy=c.y-y;dz=c.z-z;d2=dx*dx+dy*dy+dz*dz;
    if(d2<dmin)dmin=d2;
    var r0=rep[c.id];if(!r0||d2<r0.d2)rep[c.id]={x:c.x,y:c.y,d2:d2};}
  var H=[];for(var k in rep)H.push(rep[k]);
  var out={nh:H.length,dmin:H.length?Math.sqrt(dmin):-99,spasi:-99};
  if(H.length>=2){var sum=0;
    for(i=0;i<H.length;i++){var best=1e18;
      for(var j=0;j<H.length;j++){if(j===i)continue;var ax=H[i].x-H[j].x,ay=H[i].y-H[j].y,a2=ax*ax+ay*ay;if(a2<best)best=a2;}
      sum+=Math.sqrt(best);}
    out.spasi=sum/H.length;}
  return out;}
function meStep(){""")

    # 5. tulis ke simpanan saat commit
    R("B.x[row]=it.x;B.y[row]=it.y;B.z[row]=it.z;B.sx[row]=it.sx;B.sy[row]=it.sy;B.sz[row]=it.sz;B.dom[row]=X.d.id;B.type[row]=it.type;B.date[row]=J.today;B.run[row]=J.runId;",
      "B.x[row]=it.x;B.y[row]=it.y;B.z[row]=it.z;B.sx[row]=it.sx;B.sy[row]=it.sy;B.sz[row]=it.sz;B.dom[row]=X.d.id;B.type[row]=it.type;B.date[row]=J.today;B.run[row]=J.runId;"
      "B.nh[row]=res?res.nh:0;B.dmin[row]=res?res.dmin:-99;B.spasi[row]=res?res.spasi:-99;")

    # 6. jadikan kolom block model
    R("var EST=new Float64Array(n).fill(-99),PS=new Float64Array(n),SR=new Float64Array(n).fill(-99),KE=new Float64Array(n).fill(-99),KV=new Float64Array(n).fill(-99),NS=new Float64Array(n),",
      "var EST=new Float64Array(n).fill(-99),PS=new Float64Array(n),SR=new Float64Array(n).fill(-99),KE=new Float64Array(n).fill(-99),KV=new Float64Array(n).fill(-99),NS=new Float64Array(n),"
      "NH=new Float64Array(n),DMI=new Float64Array(n).fill(-99),SPA=new Float64Array(n).fill(-99),")
    R("DC[idx]=dIx[dn];TY[idx]=B.type[j];PS[idx]=B.pass[j];NS[idx]=B.ns[j];DT[idx]=B.date[j];RN[idx]=B.run[j];IX[j]=idx;",
      "DC[idx]=dIx[dn];TY[idx]=B.type[j];PS[idx]=B.pass[j];NS[idx]=B.ns[j];NH[idx]=B.nh[j]||0;"
      "DMI[idx]=(B.dmin[j]==null?-99:B.dmin[j]);SPA[idx]=(B.spasi[j]==null?-99:B.spasi[j]);DT[idx]=B.date[j];RN[idx]=B.run[j];IX[j]=idx;")
    R("m.num[A.ns]=NS;m.num[A.type]=TY;m.num[A.date]=DT;m.num[A.run]=RN;m.cat[A.dom]={codes:DC,dict:dict,cnt:cnt};",
      "m.num[A.ns]=NS;m.num[A.nh]=NH;m.num[A.dmin]=DMI;m.num[A.spasi]=SPA;m.num[A.type]=TY;m.num[A.date]=DT;m.num[A.run]=RN;m.cat[A.dom]={codes:DC,dict:dict,cnt:cnt};")

    # 7. ikut ke file .mdl (Surpac) dengan jumlah desimal yang pantas
    R("if(m.mdl){var dec={};dec[A.est]=3;dec[A.fin]=3;dec[A.sor]=3;dec[A.ke]=3;dec[A.kv]=3;\n"
      "      m.mdl.add=[A.est,A.fin,A.pass,A.sor,A.ke,A.kv,A.ns,A.type,A.date,A.run]",
      "if(m.mdl){var dec={};dec[A.est]=3;dec[A.fin]=3;dec[A.sor]=3;dec[A.ke]=3;dec[A.kv]=3;dec[A.dmin]=2;dec[A.spasi]=2;\n"
      "      m.mdl.add=[A.est,A.fin,A.pass,A.sor,A.ke,A.kv,A.ns,A.nh,A.dmin,A.spasi,A.type,A.date,A.run]")
    R("def:/_est$|_sor$|_ke$|_kv$/.test(k)?-99:0};", "def:/_est$|_sor$|_ke$|_kv$|_dmin$|_spasi$/.test(k)?-99:0};")
    return s
