# -*- coding: utf-8 -*-
# Data fiktif: vein V1 bercabang 3 ke arah bawah (trident). Jurus N-S (0°), penampang E-W. Koordinat lokal fiktif.
import numpy as np, math, csv, json, sys, os
OUT=(sys.argv[1] if len(sys.argv)>1 else '/tmp/br').rstrip('/')+'/'; os.makedirs(OUT,exist_ok=True)
E0,N0=50000.0,80000.0
ZT=205.0; ZS=150.0; ZB=50.0   # permukaan, RL percabangan, dasar
def xc(code,z):
    # posisi pusat (offset E dari E0) pada RL z
    if code=='V1':  return -(ZT-z)/math.tan(math.radians(75))
    x0=-(ZT-ZS)/math.tan(math.radians(75))
    dz=ZS-z
    if code=='V1A': return x0-dz/math.tan(math.radians(60))   # cabang barat, landai
    if code=='V1B': return x0-dz/math.tan(math.radians(80))   # cabang tengah, hampir tegak
    if code=='V1C': return x0+dz/math.tan(math.radians(65))   # cabang timur, berlawanan arah
TH={'V1':3.0,'V1A':2.0,'V1B':2.2,'V1C':1.8}   # tebal horizontal
def code_at(x,z,n):
    w=1+0.15*math.sin(n/25.0)   # sedikit variasi tebal sepanjang jurus
    if ZS<=z<=ZT and abs(x-xc('V1',z))<=TH['V1']*w/2: return 'V1'
    if ZB<=z<ZS:
        for c in ('V1A','V1B','V1C'):
            if abs(x-xc(c,z))<=TH[c]*w/2: return c
    return ''
holes=[];NS=list(range(0,121,10))
for n in NS:
    for k,(x0,az,dip,L) in enumerate([(-130,90,-55,190),(-95,90,-60,180),(-60,90,-65,170),(-30,90,-70,170),(25,270,-60,180),(60,270,-55,190),(-10,90,-85,175)]):
        holes.append(('BR%03d_%d'%(n,k+1),E0+x0,N0+n,ZT-0.3*math.sin(n/17.0)-0.02*x0,az,dip,L))
col=[['Hole_ID','X','Y','Z','Max_Depth','Hole_Purpose']];sv=[['Hole_ID','Depth','Dip','Azimuth']];asy=[['Hole_ID','From','To','Au_ppm','Ag_ppm']];geo=[['Hole_ID','From','To','Lith','Alt','Vein_Type']]
rng=np.random.default_rng(7);truth=[]
for hid,x,y,z,az,dip,L in holes:
    col.append([hid,round(x,2),round(y,2),round(z,2),L,'Exploration']);sv.append([hid,0,dip,az])
    a=math.radians(az);d=math.radians(dip);dx=math.sin(a)*math.cos(d);dy=math.cos(a)*math.cos(d);dz=math.sin(d)
    for f in range(0,L):
        cs=[];
        for t in np.arange(f+0.05,f+1,0.1):
            px=x+dx*t-E0;pz=z+dz*t;cs.append(code_at(px,pz,y-N0))
        c=max(set(cs),key=cs.count)
        if c and cs.count(c)<5: c=''
        if c: truth.append([hid,f,f+1,c])
        au=round(float(rng.lognormal(1.3,0.6)) if c else float(rng.lognormal(-3.2,0.7)),3);ag=round(au*float(rng.uniform(4,9)),2)
        asy.append([hid,f,f+1,au,ag]);geo.append([hid,f,f+1,'QV' if c else 'AND','SIL' if c else ('ARG' if any(cs) else 'PRO'),c or '-'])
for nm,R in [('BR_collar',col),('BR_survey',sv),('BR_assay',asy),('BR_geologi',geo)]:
    csv.writer(open(OUT+'%s.csv'%nm,'w',newline='')).writerows(R)
from collections import Counter
print(len(holes),'lubang ·',Counter(t[3] for t in truth))
json.dump({'E0':E0,'N0':N0,'ZT':ZT,'ZS':ZS,'ZB':ZB,'TH':TH},open(OUT+'geom.json','w'))
