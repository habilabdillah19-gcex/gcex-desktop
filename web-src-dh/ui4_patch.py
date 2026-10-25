# -*- coding: utf-8 -*-
"""GC-Ex Drillhole 0.12: Peta (Mapping) & Layout terpisah, layer peta terperinci, titik struktur di peta.
Dipanggil dari build_dh.py sesudah gm3_patch: s = ui4_patch.patch(s)."""
import re


def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, 'ui4_patch: pola ditemukan %d kali (harus %d): %s' % (c, n, a[:90])
    return s.replace(a, b)


def patch(s):
    # ---- panel Map: layer terperinci + bagian Titik struktur ----
    m = re.search(r"  h\+='<h4>Layer</h4><div class=g2>'.*?ck\('lab','Label'\)\+'</div>';\n", s)
    assert m, 'ui4_patch: bagian Layer mapPanel tidak ditemukan'
    s = s[:m.start()] + "  h+=mapLayerHtml(ck,hasT,hasO);\n" + s[m.end():]
    s = rep(s, "  h+='<h4>Layout peta</h4>", "  h+=mapStHtml();\n  h+='<h4>Layout peta</h4>'+mapLoHtml()+'")
    s = rep(s, "uiSecTabs($('mapBody'),'map',['Layer','Pick-up','Digitasi','Layout']);",
            "uiSecTabs($('mapBody'),'map',['Layer peta','Pick-up','Digitasi','Titik struktur','Layout']);")
    # ---- isi peta: sembunyikan per sumber / kelompok (hanya di peta) ----
    s = rep(s, "GM.doms.forEach(function(d){if(!d.vis)return;var X=[],Y=[];gmRuns(d.id)",
            "GM.doms.forEach(function(d){if(!d.vis||MAP.hid['dom:'+d.id])return;var X=[],Y=[];gmRuns(d.id)")
    s = rep(s, "MAP.F.forEach(function(f){if(f.vis===false||!f.pts.length)return;var st=",
            "MAP.F.forEach(function(f){if(f.vis===false||!f.pts.length||mapHidF(f))return;var st=")
    s = rep(s, "var P=STR.P.filter(stOn);T.push({type:'scatter',mode:'markers',x:P.map(function(p){return p.x;})",
            "var P=STR.P.filter(function(p){return stOn(p)&&!MAP.hid['stf:'+p.fid];});T.push({type:'scatter',mode:'markers',x:P.map(function(p){return p.x;})")
    s = rep(s, "STR.P.forEach(function(p){if(!stOn(p))return;var V=stVec(p),x=p.x,y=p.y",
            "STR.P.forEach(function(p){if(!stOn(p)||MAP.hid['stf:'+p.fid])return;var V=stVec(p),x=p.x,y=p.y")
    s = rep(s, "MAP.PF.forEach(function(f){if(!f.on)return;var by={};",
            "MAP.PF.forEach(function(f){if(!f.on||MAP.hid['pf:'+f.id])return;var by={};")
    s = rep(s, "Object.keys(by).forEach(function(cd){var col=MAPPAL[",
            "Object.keys(by).forEach(function(cd){if(MAP.hid['pfc:'+cd])return;var col=MAPPAL[")
    # ---- mode titik struktur di peta ----
    s = rep(s, "if(MAP.mode==='dig'){down=[e.clientX,e.clientY];return;}",
            "if(MAP.mode==='dig'||MAP.mode==='stpt'){down=[e.clientX,e.clientY];return;}")
    s = rep(s, "if(MAP.mode!=='dig'||!down)return;var mv=",
            "if((MAP.mode!=='dig'&&MAP.mode!=='stpt')||!down)return;var mv=")
    s = rep(s, "var P=pos(e);if(!P||!P.in)return;var s=mapSnap(P.A,P.px,P.py);MAP.cur.push(",
            "var P=pos(e);if(!P||!P.in)return;if(MAP.mode==='stpt'){mapStAdd(P.w);return;}var s=mapSnap(P.A,P.px,P.py);MAP.cur.push(")
    s = rep(s, "else if(e.key==='Escape'&&MAP.sel){",
            "else if(e.key==='Escape'&&MAP.mode==='stpt'){MAP.mode=null;mapPanel();}else if(e.key==='Escape'&&MAP.sel){")
    # ---- layout: elemen opsional ----
    s = rep(s, "gridcolor:'#e9ecef'", "gridcolor:MAP.lo&&MAP.lo.grid===false?'rgba(0,0,0,0)':'#e9ecef',showgrid:!(MAP.lo&&MAP.lo.grid===false)", 2)
    s = rep(s, "      /* skala dari rentang sumbu */\n", "      /* skala dari rentang sumbu */\n      if(!MAP.lo||MAP.lo.sc!==false){\n")
    s = rep(s, "      /* panah utara */\n", "      }\n      /* panah utara */\n      if(!MAP.lo||MAP.lo.na!==false){\n")
    s = rep(s, "      /* legenda */\n", "      }\n      /* legenda */\n      if(!MAP.lo||MAP.lo.leg!==false){\n")
    s = rep(s, "      /* kotak judul */\n", "      }\n      /* kotak judul */\n")
    return s
