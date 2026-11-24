import base64,json,glob
F='/root/.claude/skills/motion-broll/engine/fonts';b=lambda p:base64.b64encode(open(p,'rb').read()).decode()
s=open('head.part').read()+open('main.part').read()
fr=lambda d:json.dumps(['data:image/jpeg;base64,'+b(p) for p in sorted(glob.glob(d+'/*.jpg'))])
R={'__GEIST__':b(F+'/Geist-Variable.woff2'),'__MONO__':b(F+'/GeistMono-Medium.woff2'),'__F_INTRO__':fr('fi'),'__F_HOOK__':fr('fh'),
 '__V_INTRO__':b('../../assets/phil/phil-intro.mp3'),'__V_HOOK__':b('phil-hook.mp3'),'__V_BRIDGE__':b('george-bridge.mp3'),'__V_BODY__':b('george-body.mp3'),'__V_CLOSE__':b('george-close.mp3'),
 '__A_INTRO__':open('../../assets/phil/phil-intro-align.json').read(),'__A_HOOK__':open('phil-hook-align.json').read(),'__A_BRIDGE__':open('george-bridge-align.json').read(),'__A_BODY__':open('george-body-align.json').read(),'__A_CLOSE__':open('george-close-align.json').read()}
for k,v in R.items():
  assert k in s,k; s=s.replace(k,v)
open('wide.html','w').write(s);print(len(s)//1000000,'MB')
