"""0.24.65 (uji data nyata Zona 3): Model Estimation menyimpan ID² pembanding (atribut <unsur>_id2) dari sampel terpilih
kriging yang sama. Dipasang SESUDAH gm2_patch & mecls_patch karena titik sambungnya teks hasil kedua patch itu."""


def patch(s: str) -> str:
    def R(a, b):
        nonlocal s
        assert s.count(a) == 1, 'nyata_patch (%d x): %s' % (s.count(a), a[:90])
        s = s.replace(a, b)
    R("'ns','nh','dmin','spasi','type','date','run'];", "'ns','nh','dmin','spasi','type','date','run','idw'];")
    R("['x','y','z','est'].indexOf(k)>=0?Float64Array.from(a)", "['x','y','z','est','idw'].indexOf(k)>=0?Float64Array.from(a)")
    R("spasi:_sp.spasi,ex:meExEst(X,sel,r.w)};", "spasi:_sp.spasi,ex:meExEst(X,sel,r.w),idw:meIdw(mo,X,sel,x,y,z)};")
    R("if(res){B.est[row]=res.est;", "if(res){B.idw[row]=res.idw!=null?res.idw:-99;B.est[row]=res.est;")
    R("}else{B.est[row]=-99;", "}else{B.idw[row]=-99;B.est[row]=-99;")
    R("var EST=new Float64Array(n).fill(-99),PS=", "var IDW=new Float64Array(n).fill(-99),EST=new Float64Array(n).fill(-99),PS=")
    R("if(B.pass[j]>0){EST[idx]=B.est[j];", "if(B.pass[j]>0){EST[idx]=B.est[j];if(B.idw&&B.idw[j]!=null)IDW[idx]=B.idw[j];")
    R("m.num[A.est]=EST;m.num[A.fin]=FIN;", "m.num[A.est]=EST;m.num[A.idw]=IDW;m.num[A.fin]=FIN;")
    R("return{est:e+'_est',fin:e+'_final',", "return{est:e+'_est',idw:e+'_id2',fin:e+'_final',")
    return s
