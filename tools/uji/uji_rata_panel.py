"""Uji perataan panel PROPERTI yang adaptif (BM 0.24.116; pemilik 27 Nov 2026: "panel tidak allign ... harusnya bisa adaptif").
Semua node Project Tree dibuka satu per satu pada lebar panel 262 / 310 / 360 / 460 px, lalu diperiksa:
  A  baris grid 2-4 kolom yang tidak penuh (isian sendirian setengah baris)
  B  isian sebaris tidak sejajar (> 3 px) karena label beda tinggi
  C  pilihan (select) / tulisan tombol di sel grid yang terpotong / terlipat padahal sel belum selebar baris
  E  elemen melewati tepi kanan panel (tabel harus bisa digeser)
  F  deretan tombol patah baris dengan baris yang menggantung (sisa ruang > 25 %)
Lulus bila tidak ada satu temuan pun. Pakai: python tools/uji/uji_rata_panel.py [--lebar 360]"""
import sys, json
sys.argv = ['x', 'app'] + sys.argv[1:]
from pathlib import Path
exec(open(Path(__file__).resolve().parent / 'uji_palet.py', encoding='utf-8').read().split('with sync_playwright() as pw:')[0])
LEBAR = [int(sys.argv[sys.argv.index('--lebar') + 1])] if '--lebar' in sys.argv else [262, 310, 360, 460]
SEED = r"""(()=>{try{var m=BX.m,L=lyU();var xs=[],ys=[];for(var i=0;i<m.n;i+=7){xs.push(m.x[i]);ys.push(m.y[i]);}xs.sort((a,b)=>a-b);ys.sort((a,b)=>a-b);
var cx=xs[xs.length>>1],cy=ys[ys.length>>1];var D=amD();D.bnd=D.bnd||[];D.bnd.push({id:'u1',name:'UJI',key:'u1',pts:[[cx-30,cy-30],[cx+30,cy-30],[cx+30,cy+30],[cx-30,cy+30]],top:L.top,bot:L.bot,on:true,d:'ORE',no:1});
D.pts=[];D.ptsR=[];for(var a=-20;a<=20;a+=10)for(var b=-20;b<=20;b+=10){D.pts.push({x:cx+a,y:cy+b,z:L.bot+0.1,id:'',c:'FLR'});D.ptsR.push({x:cx+a,y:cy+b,z:L.top-0.2,id:'',c:'ROOF'});}
return 'ok'}catch(e){return String(e)}})()"""
AUDIT = r"""(()=>{
var side=document.getElementById('side'),out=[],sr=side.getBoundingClientRect(),cv=document.createElement('canvas').getContext('2d');
var SKIP='#ptree,#ptHdr,#ptPH,#gxNolOv';
function vis(e){var r=e.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none'}
function nm(e){var t=(e.closest('[id]')||{}).id||'';var h=e.closest('.amset,.box,fieldset,section');var hd=h?(h.querySelector('b,h3,h4,legend')||{}).textContent||'':'';return (t?'#'+t:'')+(hd?' «'+hd.trim().slice(0,34)+'»':'')}
function tx(e){return (e.textContent||'').trim().replace(/\s+/g,' ').slice(0,40)}
function tw(e,t){var cs=getComputedStyle(e);cv.font=cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily;return cv.measureText(t).width}
function span(c,cols){var cs=getComputedStyle(c),m=/span (\d+)/.exec(cs.gridColumnEnd)||/span (\d+)/.exec(cs.gridColumnStart);if(m)return Math.min(cols,+m[1]);if(cs.gridColumnEnd==='-1')return cols;var a=parseInt(cs.gridColumnStart),b=parseInt(cs.gridColumnEnd);return a>0&&b>a?b-a:1}
function rows(ch){var R=[];ch.forEach(c=>{var t=Math.round(c.getBoundingClientRect().top),r=R.filter(x=>Math.abs(x.t-t)<4)[0];if(!r)R.push(r={t:t,c:[]});r.c.push(c)});return R}
var els=[...side.querySelectorAll('*')].filter(e=>!e.closest(SKIP)&&vis(e));
els.forEach(function(e){var cs=getComputedStyle(e);
 if(cs.display==='grid'&&!e.closest('table')){var cols=cs.gridTemplateColumns.split(' ').filter(Boolean).length,ch=[...e.children].filter(vis);
  if(cols>1&&cols<=4&&ch.length){rows(ch).forEach(r=>{var used=r.c.reduce((s,c)=>s+span(c,cols),0);if(used<cols)out.push({k:'A',w:nm(e),d:'baris '+cols+' kolom terisi '+used+' ('+tx(r.c[0])+')'});
   var L=r.c.map(c=>{var l=c.firstElementChild,k=c.querySelector('select,input:not([type=checkbox]):not([type=radio]):not([type=color]),textarea');return l&&l.tagName==='LABEL'&&k?k:null});
   if(r.c.length>1&&L.every(Boolean)){var tp=L.map(k=>k.getBoundingClientRect().top),d=Math.max(...tp)-Math.min(...tp);if(d>3)out.push({k:'B',w:nm(e),d:'tidak sejajar '+Math.round(d)+' px ('+r.c.map(tx).join(' | ')+')'})}
   r.c.forEach(c=>{if(span(c,cols)>=cols)return;[...c.querySelectorAll('select'),...(c.tagName==='SELECT'?[c]:[])].forEach(s=>{if(s.selectedIndex<0)return;var sc=getComputedStyle(s),ru=s.clientWidth-parseFloat(sc.paddingLeft)-parseFloat(sc.paddingRight)-16,t=s.options[s.selectedIndex].text;if(tw(s,t)>ru+1)out.push({k:'C',w:nm(e),d:'pilihan terpotong "'+t.slice(0,40)+'"'})});
     [...c.querySelectorAll('button,label.mdbtn'),...(c.matches('button,label.mdbtn')?[c]:[])].forEach(b=>{var t=(b.textContent||'').trim();if(t.length<4)return;var bc=getComputedStyle(b),ru=b.clientWidth-parseFloat(bc.paddingLeft)-parseFloat(bc.paddingRight);if(tw(b,t)>ru+1||b.scrollHeight>b.clientHeight+2)out.push({k:'C',w:nm(e),d:'tombol terlipat "'+t.slice(0,40)+'"'})})})})}}
 if(cs.display==='flex'&&cs.flexWrap==='wrap'){var ch=[...e.children].filter(vis),bt=ch.filter(c=>c.tagName==='BUTTON');if(bt.length>=2&&bt.length>=ch.length-1){var R=rows(ch);if(R.length>1){var er=e.getBoundingClientRect();R.forEach(r=>{var right=Math.max(...r.c.map(c=>c.getBoundingClientRect().right));if(er.right-right>er.width*0.25)out.push({k:'F',w:nm(e),d:'deretan tombol menggantung ('+r.c.map(tx).join(' | ').slice(0,70)+')'})})}}}
 var r=e.getBoundingClientRect();if(r.right>sr.right+1&&!e.closest('.rataGeser')){var p=e.parentElement,ok=false;while(p&&p!==side){var o=getComputedStyle(p).overflowX;if(o==='auto'||o==='scroll'||o==='hidden'){if(p.getBoundingClientRect().right<=sr.right+1){ok=true;break}}p=p.parentElement}if(!ok)out.push({k:'E',w:nm(e),d:e.tagName.toLowerCase()+' lewat tepi kanan '+Math.round(r.right-sr.right)+' px'})}
});
var seen={};return out.filter(o=>{var k=o.k+o.w+o.d;if(seen[k])return false;seen[k]=1;return true});})()"""
hasil = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, P = server(ROOT / 'app' / 'index.html'); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); pg.on('dialog', lambda x: x.accept())
    err = []; pg.on('pageerror', lambda e: err.append(str(e)[:200]))
    muat(pg, P, TUNGGU); pg.wait_for_timeout(1200); pg.evaluate(SEED)
    ids = pg.evaluate("[].map.call(document.querySelectorAll('#ptree .ptr[data-id]'),e=>e.getAttribute('data-id'))")
    pg.add_style_tag(content="#ptCol{width:var(--auw,310px)!important;flex:0 0 var(--auw,310px)!important}")
    for w in LEBAR:
        pg.evaluate("document.documentElement.style.setProperty('--auw','%dpx')" % w)
        for i in ids:
            try:
                pg.evaluate("PT.select(%s);0" % json.dumps(i)); pg.wait_for_timeout(350)
                for o in pg.evaluate(AUDIT):
                    hasil.setdefault((o['k'], i, o['w'], o['d']), []).append(w)
            except Exception as ex: print('  err', i, str(ex)[:100])
    b.close(); srv.terminate()
for (k, i, wh, d), L in sorted(hasil.items()):
    print('  %s %-10s %-42s %s  @%s' % (k, i, wh[:42], d[:90], ','.join(map(str, sorted(set(L))))))
print('temuan:', len(hasil), ' galat:', err[:2])
print('LULUS' if not hasil and not err else 'GAGAL'); sys.exit(1 if hasil or err else 0)
