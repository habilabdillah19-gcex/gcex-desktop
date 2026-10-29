const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://'+__dirname+'/aktivasi.html',{waitUntil:'networkidle'});
await p.pdf({path:__dirname+'/GC-Ex_Tutorial_Aktivasi_Lisensi.pdf',format:'A4',printBackground:true,displayHeaderFooter:true,headerTemplate:'<span></span>',
footerTemplate:'<div style="font-size:7pt;color:#5d6773;width:100%;padding:0 17mm;display:flex;justify-content:space-between;font-family:Arial"><span>Tutorial Aktivasi Lisensi GC-Ex · Copyright © Habil Abdillah 2026</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
margin:{top:'18mm',bottom:'20mm',left:'17mm',right:'17mm'}});await b.close();})();
