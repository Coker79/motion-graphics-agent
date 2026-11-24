import base64,json,glob,sys
F='/root/.claude/skills/motion-broll/engine/fonts';b=lambda p:base64.b64encode(open(p,'rb').read()).decode()
s=open('src.html').read()
fr=['data:image/jpeg;base64,'+b(p) for p in sorted(glob.glob('frames/*.jpg'))]
s=(s.replace('__GEIST__',b(F+'/Geist-Variable.woff2')).replace('__MONO__',b(F+'/GeistMono-Medium.woff2'))
 .replace('__HOOK__',b('phil-hook.mp3')).replace('__BODY__',b('george-body.mp3'))
 .replace('__ALIGN_HOOK__',open('phil-hook-align.json').read()).replace('__ALIGN_BODY__',open('george-body-align.json').read())
 .replace('__PHIL__',json.dumps(fr)))
open('wide.html','w').write(s);open('vert.html','w').write(s.replace("const VERT=Q.get('v')==='1';","const VERT=true;"))
