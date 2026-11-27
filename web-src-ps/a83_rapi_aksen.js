/* a83 · Tanpa garis aksen + kontras & fokus (24 Nov 2026, pemilik: "untuk seluruh bar, tab, atau panel, hilangkan garis border
   atau aksen" — sama dengan Ore Works 0.33.1). Penanda aktif = warna latar, batas header = garis netral 1 px.
   Spesifisitas dinaikkan (#mbar#mbar, .flh.flh.flh.flh) karena aturan lama memakai !important.
   Warna = jangkar palet bawaan (a73), jadi ikut Palet warna. Dipasang di akhir <body> setelah semua modul memuat gayanya. */
(function(){const css=
`#mbar#mbar{border-bottom-color:transparent!important}
body.shx #mbar#mbar .shmt,body.shx #mbar#mbar .shmt:hover,body.shx #mbar#mbar .shm.op>.shmt{box-shadow:none!important;border-top:0!important}
#sbar#sbar{border-top-width:0!important}
html body .flw .flh.flh.flh.flh,html body #lgw#lgw .flh.flh.flh{border-bottom:1px solid #D3CDC1!important}
html body .shph>span{border-top-color:transparent!important}
html body #shtree .shn.act{box-shadow:none!important}
html body #agbar{border-left:1px solid #D3CDC1!important}
html body .mbb.on,html body #tabs button.on,html body #dkind button.on{border-bottom-color:transparent!important}
html body .sh{border-left-width:0!important}
:where(button,summary,select,input,.mbb,.tb,.shn,.cmenu .ci,[contenteditable]):focus-visible{outline:2px solid #2B5F9E!important;outline-offset:1px;box-shadow:0 0 0 1px #FFFFFF!important}
.shn.off .nm,.shn .bd,.shn .tw{color:#5A636B}
.shn .bd{font-size:11.5px}
.cmenu .hd{color:#5A636B!important}
.cmenu .ci.dis{color:#7B848C}
.info .ok{color:#15803D}.info .warn{color:#B45309}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important;animation:none!important}}`;
 setTimeout(()=>{const s=document.createElement('style');s.id='psRapiAksen';s.textContent=css;document.body.appendChild(s);},0);})();