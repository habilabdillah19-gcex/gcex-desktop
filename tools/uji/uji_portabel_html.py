"""Uji GC-Ex versi portabel (.html tanpa instal; pemilik 26 Nov 2026: laptop kantor tidak boleh instal program).

Folder proyek di disk diakses lewat tiruan FileSystemDirectoryHandle yang membaca / menulis berkas SUNGGUHAN di disk
(page.expose_function), sehingga format berkas yang diuji persis sama dengan yang ditulis aplikasi (desktop maupun
browser memakai kode FP yang sama di index.html).

P1  file .html dibuka dari file:// (seperti dobel-klik): tanpa galat halaman, isSecureContext, showDirectoryPicker
    tersedia (pemilih folder proyek), IndexedDB jalan, Plotly termuat, tanpa jembatan desktop
P2  "proyek desktop": aplikasi (lewat http, data latihan) membuat proyek di folder disk, lalu folder diberi tambahan
    yang hanya dibuat aplikasi terpasang: gcex_proyek.db (SQLite, backend) dan export/<tanggal>/
P3  .html portabel (file://, profil browser baru — tanpa cache proyek) membuka folder itu: proyek terbuka, block model
    / data bor terbaca ulang dari folder, isi pekerjaan sama, tanpa galat
P4  berkas tambahan desktop tidak rusak / tidak terhapus; proyek bisa disimpan lagi ke folder dari .html
P5  semua simpul Project Tree yang tampil dibuka satu per satu di .html portabel tanpa galat halaman
Pakai: python tools/uji/uji_portabel_html.py [app|app-dh]   (tanpa argumen: keduanya)
"""
import sys, os, base64, hashlib, json, shutil, sqlite3, tempfile, time
from pathlib import Path
ARGS = [a for a in sys.argv[1:] if a in ('app', 'app-dh')] or ['app', 'app-dh']
sys.argv = ['x', 'app']
exec(open(Path(__file__).resolve().parent / 'uji_palet.py', encoding='utf-8').read().split('with sync_playwright() as pw:')[0])

SHIM = r"""(()=>{if(window.DiskDir)return;
function nf(n){return new DOMException('"'+n+'" tidak ada','NotFoundError');}
function b64(u8){var s='',C=0x8000;for(var i=0;i<u8.length;i+=C)s+=String.fromCharCode.apply(null,u8.subarray(i,i+C));return btoa(s);}
function unb(s){var b=atob(s),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u;}
async function toU8(d){if(d==null)return new Uint8Array(0);if(typeof d==='string')return new TextEncoder().encode(d);if(d instanceof Blob)return new Uint8Array(await d.arrayBuffer());
  if(d instanceof ArrayBuffer)return new Uint8Array(d);if(ArrayBuffer.isView(d))return new Uint8Array(d.buffer,d.byteOffset,d.byteLength);if(d.type==='write')return toU8(d.data);return new TextEncoder().encode(String(d));}
function FileH(p,n){this.kind='file';this.name=n;this._p=p;}
FileH.prototype.getFile=async function(){var r=await fsRead(this._p);if(r==null)throw nf(this.name);return new File([unb(r[0])],this.name,{lastModified:r[1]});};
FileH.prototype.createWritable=async function(){var p=this._p,parts=[];return{write:async function(d){parts.push(await toU8(d));},close:async function(){var n=0;parts.forEach(function(x){n+=x.length;});var u=new Uint8Array(n),o=0;parts.forEach(function(x){u.set(x,o);o+=x.length;});await fsWrite(p,b64(u));},abort:async function(){parts=[];}};};
FileH.prototype.queryPermission=async function(){return 'granted';};FileH.prototype.requestPermission=async function(){return 'granted';};
FileH.prototype.isSameEntry=async function(o){return !!o&&o._p===this._p;};
function DirH(p,n){this.kind='directory';this.name=n;this._p=p;}
DirH.prototype.getDirectoryHandle=async function(n,o){var q=this._p+'/'+n,k=await fsKind(q);if(k!=='directory'){if(o&&o.create&&!k)await fsMkdir(q);else throw nf(n);}return new DirH(q,n);};
DirH.prototype.getFileHandle=async function(n,o){var q=this._p+'/'+n,k=await fsKind(q);if(k!=='file'){if(o&&o.create&&!k)await fsWrite(q,'');else throw nf(n);}return new FileH(q,n);};
DirH.prototype.removeEntry=async function(n,o){var ok=await fsRm(this._p+'/'+n,!!(o&&o.recursive));if(!ok)throw nf(n);};
DirH.prototype.values=async function*(){var L=await fsList(this._p);for(var i=0;i<L.length;i++)yield L[i][1]==='directory'?new DirH(this._p+'/'+L[i][0],L[i][0]):new FileH(this._p+'/'+L[i][0],L[i][0]);};
DirH.prototype.entries=async function*(){for await(var e of this.values())yield [e.name,e];};
DirH.prototype.keys=async function*(){for await(var e of this.values())yield e.name;};
DirH.prototype[Symbol.asyncIterator]=DirH.prototype.entries;
DirH.prototype.queryPermission=async function(){return 'granted';};DirH.prototype.requestPermission=async function(){return 'granted';};
DirH.prototype.isSameEntry=async function(o){return !!o&&o._p===this._p;};
DirH.prototype.resolve=async function(c){return c&&c._p&&c._p.indexOf(this._p+'/')===0?c._p.slice(this._p.length+1).split('/'):null;};
window.DiskDir=function(p){return new DirH(p,p.split('/').pop());};
/* handle tiruan tidak bisa disimpan di IndexedDB (DataCloneError): lewati hanya untuk kunci fpDir */
var _ip=window.idbPut;if(typeof _ip==='function')window.idbPut=idbPut=function(k,v){if(k==='fpDir'&&v&&v._p)return Promise.resolve(true);return _ip.apply(this,arguments);};
})()"""

def pasang_fs(pg):
    def kind(p):
        return 'directory' if os.path.isdir(p) else ('file' if os.path.isfile(p) else None)
    def rd(p):
        if not os.path.isfile(p): return None
        return [base64.b64encode(open(p, 'rb').read()).decode(), int(os.path.getmtime(p) * 1000)]
    def wr(p, b):
        os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(base64.b64decode(b)); return True
    def mk(p):
        os.makedirs(p, exist_ok=True); return True
    def ls(p):
        return [[n, 'directory' if os.path.isdir(os.path.join(p, n)) else 'file'] for n in sorted(os.listdir(p))] if os.path.isdir(p) else []
    def rm(p, rec):
        if os.path.isfile(p): os.remove(p); return True
        if os.path.isdir(p): shutil.rmtree(p) if rec else os.rmdir(p); return True
        return False
    for n, f in [('fsKind', kind), ('fsRead', rd), ('fsWrite', wr), ('fsMkdir', mk), ('fsList', ls), ('fsRm', rm)]:
        pg.expose_function(n, f)

gagal = []
def cek(nama, ok, info=''):
    print(('  ok   ' if ok else '  GAGAL ') + nama + ('  ' + str(info)[:300] if info else ''))
    if not ok: gagal.append(nama)

def h(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
RINGKAS = {'app': """(()=>{var w=SA.collectWork?SA.collectWork():{};return {n:BX.m?BX.m.n:0,att:BX.m?Object.keys(BX.m.num||{}).length:0,src:BX.m&&BX.m.src?BX.m.src.name:'',
              pname:SA.pname||'',topo:!!(SA.D&&(SA.D.topo||SA.D.topos)),keys:Object.keys(w).sort().join(',')};})()""",
           'app-dh': """(()=>({holes:(window.collars||[]).length,assay:(window.assays||window.assay||[]).length,pname:SA.pname||window.PNAME||'',
              topo:!!(window.SA&&SA.D&&(SA.D.topo||SA.D.topos))}))()"""}

with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    tmp = Path(tempfile.mkdtemp(prefix='gcex_portabel_'))
    for app in ARGS:
        nm = {'app': 'GCEx_BlockModel.html', 'app-dh': 'GCEx_DrillHole.html'}[app]
        print('== %s (%s)' % (nm, app))
        (tmp / nm).write_bytes((ROOT / app / 'index.html').read_bytes())
        # ---- P1
        ctx = br.new_context(viewport={'width': 1500, 'height': 860}); pg = ctx.new_page(); err = []
        pg.on('pageerror', lambda e: err.append(str(e)[:200])); pg.on('dialog', lambda d: d.accept())
        pg.goto((tmp / nm).as_uri()); pg.wait_for_timeout(8000)
        r = pg.evaluate("""async()=>{var o={sec:isSecureContext,pick:typeof showDirectoryPicker==='function',plotly:!!window.Plotly,fp:!!(window.FP&&FP.ok&&FP.ok()),desk:!!window.gcexDesktop,idb:false};
            await new Promise(function(r){var q=indexedDB.open('uji');q.onsuccess=function(){o.idb=true;r();};q.onerror=function(){r();};});return o;}""")
        cek('P1 dibuka dari file:// tanpa galat; aman, pemilih folder, IndexedDB, Plotly', all([r['sec'], r['pick'], r['plotly'], r['fp'], r['idb'], not r['desk'], not err]), [r, err[:2]])
        ctx.close()
        # ---- P2: proyek dibuat di folder disk
        D = tmp / ('Proyek_' + app); D.mkdir()
        srv, P = server(ROOT / app / 'index.html')
        ctx = br.new_context(viewport={'width': 1500, 'height': 860}); pg = ctx.new_page(); err = []
        pg.on('pageerror', lambda e: err.append(str(e)[:200])); pg.on('dialog', lambda d: d.accept('Uji Desktop') if d.type == 'prompt' else d.accept())
        pasang_fs(pg)
        muat(pg, P, "window.BX && BX.m" if app == 'app' else "window.collars && collars.length > 0")
        pg.evaluate(SHIM)
        pg.evaluate("(d)=>FP.use(DiskDir(d))", str(D))
        for _ in range(60):
            if (D / 'gcex_project.json').exists() and (D / 'gcex_data.json').exists(): break
            pg.wait_for_timeout(1000)
        pg.wait_for_timeout(3000)
        A = pg.evaluate(RINGKAS[app])
        isi = sorted(os.listdir(D))
        cek('P2 proyek tersimpan di folder disk', (D / 'gcex_project.json').exists() and (D / 'gcex_data.json').exists() and not err, [isi, err[:2]])
        ctx.close(); srv.terminate()
        # aplikasi desktop ditutup normal -> kunci pemakai dilepas (Playwright tidak memicu beforeunload saat konteks ditutup)
        if (D / 'gcex.lock').exists(): (D / 'gcex.lock').unlink()
        # tambahan yang hanya dibuat aplikasi terpasang
        db = D / 'gcex_proyek.db'; c = sqlite3.connect(db); c.execute('create table riwayat(id integer primary key, waktu text, isi text)')
        c.execute("insert into riwayat(waktu,isi) values('2026-11-20T08:00','dibuat GC-Ex Desktop')"); c.commit(); c.close()
        (D / 'export' / '20261120').mkdir(parents=True); (D / 'export' / '20261120' / 'contoh.str').write_text('uji,20/11/2026,,ssi_styles:styles.ssi\n0, 0.000, 0.000, 0.000,\n')
        H0 = {str(p.relative_to(D)): h(p) for p in [db, D / 'export' / '20261120' / 'contoh.str']}
        print('    folder proyek:', ', '.join(isi), '+ gcex_proyek.db + export/')
        # ---- P3: .html portabel, profil baru, file://
        ctx = br.new_context(viewport={'width': 1500, 'height': 860}); pg = ctx.new_page(); err = []
        pg.on('pageerror', lambda e: err.append(str(e)[:200])); pg.on('dialog', lambda d: d.accept('Uji Kantor') if d.type == 'prompt' else d.accept())
        pasang_fs(pg)
        pg.goto((tmp / nm).as_uri()); pg.wait_for_timeout(8000)
        pg.evaluate(SHIM)
        pg.evaluate("(d)=>{FP.use(DiskDir(d));return 0;}", str(D))
        try:
            pg.wait_for_function("window.BX && BX.m" if app == 'app' else "window.collars && collars.length > 0", timeout=180000)
        except Exception as e:
            print('    (menunggu proyek terbuka habis waktu)', str(e)[:100])
        pg.wait_for_timeout(5000)
        B = pg.evaluate(RINGKAS[app])
        cek('P3 .html portabel membuka folder proyek desktop; isi sama', A == B and not err, {'desktop': A, 'portabel': B, 'galat': err[:3]})
        # ---- P4
        ok_save = pg.evaluate("async()=>{try{/* tunggu simpan otomatis yang sedang berjalan (FP.busy) selesai */for(var k=0;k<120&&(FP.busy||FP.pend);k++)await new Promise(function(r){setTimeout(r,250);});var r=await FP.save(true,'uji simpan dari html');return r===true?true:[r,FP.ro,FP.err,!!FP.conf,!!FP.dir];}catch(e){return String(e);}}")
        H1 = {k: h(D / k) for k in H0}
        cek('P4 berkas tambahan desktop utuh; simpan ulang dari .html berhasil', H0 == H1 and ok_save is True, [ok_save])
        # ---- P5: buka setiap simpul Project Tree / panel di .html portabel, catat galat
        err.clear()
        n = pg.evaluate("""async()=>{var L=[].slice.call(document.querySelectorAll('#ptree .ptr[data-id]')).map(function(r){return r.getAttribute('data-id');}),n=0;
            for(var i=0;i<L.length;i++){var el=document.querySelector('#ptree .ptr[data-id="'+L[i]+'"] .ptl');if(!el||!el.offsetParent)continue;try{el.click();n++;}catch(e){}await new Promise(function(r){setTimeout(r,250);});}return n;}""")
        pg.wait_for_timeout(2000)
        cek('P5 %d panel / simpul Project Tree dibuka tanpa galat' % n, n > 10 and not err, err[:3])
        ctx.close()
    br.close()
    shutil.rmtree(tmp, ignore_errors=True)
print('LULUS' if not gagal else 'GAGAL: %s' % gagal); sys.exit(1 if gagal else 0)
