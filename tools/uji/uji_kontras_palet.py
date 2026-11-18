"""Uji kontras teks di semua palet warna (pemilik 18 Nov 2026: "sudah tidak ada warna yang menghalangi pembacaan tulisan?").
Setiap palet dipakai bergantian, tiga panel dibuka, lalu setiap teks yang tampil diukur kontrasnya terhadap latar efektif
(WCAG: 4,5:1 teks biasa, 3:1 teks besar / redup-disengaja). Pengecualian: palet Dasar Block Model (tampilan asli lama,
abu #64748B di panel = 4,24:1) dibiarkan apa adanya.
Pakai: python tools/uji/uji_kontras_palet.py app|app-dh
"""
import sys, json
app=sys.argv[1] if len(sys.argv)>1 else 'app'; sys.argv=['x',app]
from pathlib import Path
_U=Path(__file__).resolve().parent/'uji_palet.py'
exec(open(_U,encoding='utf-8').read().split('with sync_playwright() as pw:')[0])
AUD = r"""(function(){
 function rgba(s){var m=(s||'').match(/[\d.]+/g);if(!m)return null;return [+m[0],+m[1],+m[2],m.length>3?+m[3]:1];}
 function lum(c){return [0,1,2].map(function(i){var v=c[i]/255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);}).reduce(function(s,v,i){return s+v*[0.2126,0.7152,0.0722][i];},0);}
 function kon(a,b){var x=lum(a),y=lum(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);}
 function bgOf(e){var st=[];for(var p=e;p&&p.nodeType===1;p=p.parentElement){var cs=getComputedStyle(p);if(cs.backgroundImage&&cs.backgroundImage!=='none'&&/gradient/.test(cs.backgroundImage)){var m=(cs.backgroundImage.match(/rgba?\([^)]*\)/g)||[]).map(rgba).filter(function(c){return c[3]>=0.5;});if(m.length)return m[m.length-1];}var c=rgba(cs.backgroundColor);if(c&&c[3]>0.05){st.push(c);if(c[3]>=0.95)break;}}
   var r=[255,255,255];for(var i=st.length-1;i>=0;i--){var c=st[i],a=c[3];r=[c[0]*a+r[0]*(1-a),c[1]*a+r[1]*(1-a),c[2]*a+r[2]*(1-a)];}return r;}
 var out=[],seen={};
 document.querySelectorAll('body *').forEach(function(e){
  if(!e.offsetWidth||!e.offsetHeight)return;if(e.closest('.js-plotly-plot svg,.main-svg,canvas,#gxPal .sw'))return;
  var t=[].slice.call(e.childNodes).filter(function(n){return n.nodeType===3&&n.textContent.trim().length>1;}).map(function(n){return n.textContent.trim();}).join(' ');
  if(!t)return;var cs=getComputedStyle(e);if(cs.visibility==='hidden'||+cs.opacity<0.3)return;
  var r=e.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight||r.right<0||r.left>innerWidth)return;
  var fg=rgba(cs.color);if(!fg)return;var bg=bgOf(e);var k=kon(fg,bg);var fs=parseFloat(cs.fontSize),bold=+cs.fontWeight>=600;
  var batas=(fs>=18.66||(fs>=14&&bold))?3:4.5;
  if(e.disabled||e.closest('[disabled]')||/dis|mu|muted|hint|ph/.test(String(e.className)))batas=Math.min(batas,3);
  if(k<batas){var key=t.slice(0,30)+'|'+cs.color;if(seen[key])return;seen[key]=1;out.push([+k.toFixed(2),batas,t.slice(0,40),cs.color,'rgb('+bg.map(Math.round).join(',')+')',(e.id||'')+'.'+String(e.className).slice(0,25)]);}
 });out.sort(function(a,b){return a[0]-b[0];});return out;})()"""
with sync_playwright() as pw:
    b=pw.chromium.launch(args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"])
    srv,P=server(ROOT/app/'index.html'); pg=b.new_page(viewport={'width':1500,'height':860}); pg.on('dialog',lambda x:x.accept())
    muat(pg,P,TUNGGU)
    hasil={}
    for k in pg.evaluate("GXPAL.daftar().map(function(p){return p.k;})"):
        pg.evaluate("(k)=>GXPAL.pakai(k)",k); pg.wait_for_timeout(900)
        tot=[]
        for node in (['set.v','dig','bm'] if app=='app' else ['set.v','db','gm']):
            pg.evaluate("(id)=>{var el=document.querySelector('#ptree .ptr[data-id=\"'+id+'\"] .ptl');if(el)el.click();}",node); pg.wait_for_timeout(500)
            tot+=pg.evaluate(AUD)
        u={}
        for x in tot: u[(x[2],x[3])]=x
        hasil[k]=sorted(u.values())
    pg.evaluate("GXPAL.pakai('bawaan')")
    b.close(); srv.terminate()
gagal=0
for k,v in hasil.items():
    v=[x for x in v if not (app=='app' and k=='dasar' and x[0]>=4.2)]
    print('  %s %-10s %s'%('ok  ' if not v else 'GAGAL',k, '' if not v else [(x[0],x[2][:30],x[5]) for x in v[:5]]))
    gagal+=len(v)
print('LULUS' if not gagal else 'GAGAL (%d teks)'%gagal); sys.exit(1 if gagal else 0)
