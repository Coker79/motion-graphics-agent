#!/usr/bin/env python3
"""Build an .srt from ElevenLabs-style alignments: srt_from_align.py out.srt align.json:OFFSET [align.json:OFFSET ...]"""
import json,sys
def words(path,off):
    a=json.load(open(path));out=[];cur='';st=None;en=0
    for c,s,e in zip(a['characters'],a['character_start_times_seconds'],a['character_end_times_seconds']):
        if c==' ':
            if cur: out.append((cur,st+off,en+off))
            cur='';st=None
        else:
            if st is None: st=s
            cur+=c;en=e
    if cur: out.append((cur,st+off,en+off))
    return out
W=[w for arg in sys.argv[2:] for w in words(arg.rsplit(':',1)[0],float(arg.rsplit(':',1)[1]))]
chunks=[];cu=[]
for i,w in enumerate(W):
    cu.append(w)
    if len(cu)>=6 or i==len(W)-1 or w[0][-1] in '.,?!': chunks.append(cu);cu=[]
f=lambda t:'%02d:%02d:%02d,%03d'%(t//3600,t%3600//60,t%60,round(t%1*1000)%1000)
with open(sys.argv[1],'w') as o:
    for n,c in enumerate(chunks,1):
        end=min(c[-1][2]+.3,chunks[n][0][1] if n<len(chunks) else 1e9)
        o.write(f"{n}\n{f(c[0][1])} --> {f(end)}\n{' '.join(w[0] for w in c)}\n\n")
