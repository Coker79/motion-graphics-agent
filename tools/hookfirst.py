#!/usr/bin/env python3
"""Convert a hybrid Short page (src.html or built short.html) to hook-first: no Phil intro, bold pop captions, 1.4 s Phil end card.
Usage: hookfirst.py in.html out.html"""
import re,sys
s=open(sys.argv[1]).read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(a,s.count(a));s=s.replace(a,b)
rep("OFF=7.0","OFF=0.0");rep("T1=6.15,T2=7.05","T1=-9,T2=-8")
s=re.sub(r"(VO=OFF\+0\.15(?:,B=[^,]+)?,D=)([^;]+);",lambda m:m.group(1)+"("+m.group(2)+")+1.4;",s,count=1)
rep("ALI.characters.forEach","[].forEach");rep("s2.start(0)","0")
rep("bus.gain.setValueAtTime(.08,0);bus.gain.setValueAtTime(.08,4.9);bus.gain.linearRampToValueAtTime(.42,T2);","")
rep("for(let t=4.9;","for(let t=0;");rep("for(let t=4.9+beat*2;","for(let t=beat*2;")
rep("nz(T1+.05,.75,.22,'bandpass',500,4200);nz(T1+.55,.25,.12,'highpass',2500);osc(80,T2-.05,.35,.25,45);","")
rep("cu.length>=5","cu.length>=3")
i=s.index("function captions(t){");j=s.index("\n",i)
s=s[:i]+r"""function endcard(t){const k=ease(seg(t,D-1.4,D-1.0));x.save();x.globalAlpha=k;x.fillStyle='#ece3cc';x.fillRect(0,0,W,H);x.restore();x.save();x.globalAlpha=k;x.translate(W/2,820);x.rotate(-.03);const pw=520,ph=pw*1458/1088;x.fillStyle='#faf7ef';x.fillRect(-pw/2-26,-ph/2-26,pw+52,ph+130);x.drawImage(PH[PH.length-1],-pw/2,-ph/2,pw,ph);hand('The Efficiency Edge',0,ph/2+80,56,INK);x.restore();x.save();x.globalAlpha=k;hand('Follow for the next case file',W/2,1460,66,RED);x.restore();}
function captions(t){if(t<VO||t>D-1.4)return;let ci=-1;CH.forEach((c,i)=>{if(t>=c[0].t)ci=i;});if(ci<0)return;const c=CH[ci];if(t>c[c.length-1].t+1.0)return;x.save();x.font='900 80px Sans';x.textAlign='center';x.lineJoin='round';const ws=c.map(o=>o.w.toUpperCase());const sp=x.measureText(' ').width+26;const tot=ws.map(w=>x.measureText(w).width+sp).reduce((a,b)=>a+b,0)-sp;const sc=Math.min(1,960/tot);x.translate(W/2,1690);x.scale(sc,sc);let px=-tot/2;
 ws.forEach((w,i)=>{const ww=x.measureText(w).width;const cur=t>=c[i].t&&(i==c.length-1||t<c[i+1].t);const num=/[0-9%$]|PERCENT|TRILLION|ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|TWENTY|THIRTY|FORTY|FIFTY|SIXTY|SEVENTY|EIGHTY|NINETY|BILLION|MILLION|HUNDRED|THOUSAND/.test(w);const col=num?'#5df07a':(cur?'#ffd84a':'#ffffff');const pop=cur?1+.14*(1-clamp((t-c[i].t)/.15)):1;x.save();x.translate(px+ww/2,0);x.scale(cur?1.1*pop:1,cur?1.1*pop:1);x.strokeStyle='#111';x.lineWidth=16;x.strokeText(w,0,0);x.fillStyle=col;x.fillText(w,0,0);x.restore();px+=ww+sp;});x.restore();}"""+s[j:]
k=s.rindex(" captions(t)");s=s[:k]+" if(t>D-1.4)endcard(t);captions(t)"+s[k+12:]
open(sys.argv[2],'w').write(s)
