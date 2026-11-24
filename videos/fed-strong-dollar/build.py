import base64,json,glob,sys
F='/root/.claude/skills/motion-broll/engine/fonts';b=lambda p:base64.b64encode(open(p,'rb').read()).decode()
pce_text=sys.argv[1] if len(sys.argv)>1 else 'RESULT DUE WEDNESDAY'
import os;pce_mp3='pce.mp3' if os.path.exists('pce.mp3') else None
pce_dur=json.load(open('pce-align.json'))['character_end_times_seconds'][-1]+.3 if pce_mp3 else 0.0
src=open('src.html').read()
for vert,name in [(False,'wide.html'),(True,'vert.html')]:
  s=src;R={'__VERT__':'true' if vert else 'false','__PCE_TEXT__':json.dumps(pce_text),'__P_DUR__':str(round(pce_dur,2)),'__GEIST__':b(F+'/Geist-Variable.woff2'),'__MONO__':b(F+'/GeistMono-Medium.woff2'),
   '__F_INTRO__':json.dumps(['data:image/jpeg;base64,'+b(p) for p in sorted(glob.glob('fi/*.jpg'))]),'__V_INTRO__':b('../../assets/phil/phil-intro.mp3'),'__V_A__':b('part-a.mp3'),'__V_PCE__':b(pce_mp3) if pce_mp3 else '','__V_C__':b('part-c.mp3'),
   '__A_INTRO__':open('../../assets/phil/phil-intro-align.json').read(),'__A_A__':open('part-a-align.json').read(),'__A_PCE__':open('pce-align.json').read() if pce_mp3 else 'null','__A_C__':open('part-c-align.json').read(),'__BUS__':'0.42','__CAVEAT__':b('/root/.claude/skills/directing-stickman-videos/assets/fonts/Caveat.ttf')}
  for k,v in R.items():
    assert k in s,k;s=s.replace(k,v)
  open(name,'w').write(s)
print('built, pce_dur',pce_dur)
