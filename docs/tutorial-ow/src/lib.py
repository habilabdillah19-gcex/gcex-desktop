import asyncio, json
from PIL import Image, ImageDraw, ImageFont
APP='file:///home/claude/gcex-desktop/app-ow/index.html'
D='/home/claude/tut/data/'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
async def boxes(pg,sels):
    out=[]
    for s in sels:
        b=await pg.evaluate("""(s)=>{let e;if(s.startsWith('text=')){const t=s.slice(5);e=[...document.querySelectorAll('button,label,.subh,h2,b,span,div,summary')].filter(x=>x.offsetParent&&x.textContent.trim()===t).pop();}else e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return [r.left,r.top,r.width,r.height];}""",s)
        out.append(b)
    return out
async def shot(pg,name,hl=(),clip=None,pad=4):
    bx=await boxes(pg,hl) if hl else []
    p=f'/home/claude/tut/shots/{name}.png'
    await pg.screenshot(path=p)
    im=Image.open(p).convert('RGB');sc=im.width/pg.viewport_size['width'];d=ImageDraw.Draw(im);f=ImageFont.truetype(FONT,int(15*sc))
    for i,b in enumerate(bx):
        if not b: print('  ! tidak ketemu',hl[i]);continue
        x,y,w,h=[v*sc for v in b];P=pad*sc
        d.rounded_rectangle([x-P,y-P,x+w+P,y+h+P],radius=int(5*sc),outline=(229,57,53),width=int(3*sc))
        r=int(12*sc);cx=x-P;cy=y-P
        cx=max(r+2,cx);cy=max(r+2,cy)
        d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(229,57,53),outline='white',width=int(2*sc));t=str(i+1);tw=d.textlength(t,font=f);d.text((cx-tw/2,cy-int(9*sc)),t,font=f,fill='white')
    if clip:
        x,y,w,h=clip;im=im.crop((int(x*sc),int(y*sc),int((x+w)*sc),int((y+h)*sc)))
    im.save(p);print('shot',name);return p
async def menu(pg,n,open_=True):
    on=await pg.evaluate("(n)=>{const b=document.querySelector('#mbar .mbb[data-n=\"'+n+'\"]');return b&&b.classList.contains('on')}",n)
    if on!=open_: await pg.click(f'#mbar .mbb[data-n="{n}"]')
    await pg.wait_for_timeout(400)
async def sub(pg,txt):
    await pg.evaluate("""(t)=>{const e=[...document.querySelectorAll('.subh')].find(x=>x.offsetParent&&x.textContent.replace(/[\\u25b8\\u25be]/g,'').trim().startsWith(t));if(e&&!e.classList.contains('open'))e.click();}""",txt)
    await pg.wait_for_timeout(300)
