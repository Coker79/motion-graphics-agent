import re, statistics as st, sys
L=[l.strip() for l in open(sys.argv[1]) if l.strip()]; secs=float(sys.argv[2])
tag=[l[:2] if l[:2] in('>T','>X') else '' for l in L]; L=[l[2:].strip() if t else l for l,t in zip(L,tag)]
n=[len(re.findall(r"[A-Za-z0-9$%'-]+",l)) for l in L]; W=sum(n); off=[sum(n[:i]) for i in range(len(n))]
c=sum(bool(re.match(r"(so|but|and|then|yet|until|well|you see|still|instead|meanwhile|eventually|when)\b",l,re.I)) for l in L)
# the ear hears SENTENCES, not lines: a quote line can hold two or three ("Water?" / "We brought boats.")
S=[x for l in L for x in re.split(r'(?<=[.?!])["\u201d]?\s+', l) if re.search(r'[A-Za-z0-9]', x)]
ns=[len(re.findall(r"[A-Za-z0-9$%'-]+",x)) for x in S]; frag=[i for i,k in enumerate(ns) if k<=5]
runs=[i for i in range(len(ns)-1) if ns[i]<=5 and ns[i+1]<=5]
q=sum(l.count('"')//2 for l in L)
print(f"{W} words = {W/secs:.2f} w/s | {len(L)} lines, {len(S)} sentences | median sentence {st.median(ns)} | max {max(ns)} | <=5w: {len(frag)} (aim 0-2)")
if len(frag) > 2 or runs: print("EAR CHECK: too staccato (v2 'Crack. / Green. Fuzzy. Squish.' read as jarring):", [S[i] for i in frag], "back to back:", [(S[i], S[i+1]) for i in runs] or "-")
print(f"connective starts {100*c/len(L):.0f}% | hook {n[0]} w | last {n[-1]} w | at 3.67 w/s: {W/3.67:.1f} s" + (f" (+ about {2.2*q:.0f} s for {q} quoted line(s): the second voice and its pauses)" if q else ""))
for t in('>T','>X'):
    if t in tag: print(t, f"at {100*off[tag.index(t)]/W:.0f}% of words")
