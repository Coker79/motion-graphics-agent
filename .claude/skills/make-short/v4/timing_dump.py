"""blender -b -P timing_dump.py : voice/voice.json + script.txt -> voice/timing.json (finish.py reads it), and print every line's frames."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from toykit import film
T = film.Timing(os.path.join(HERE, 'voice', 'voice.json'), os.path.join(HERE, 'script.txt'), lead=1)
T.dump(os.path.join(HERE, 'voice', 'timing.json'))
print('TIMING duration', round(T.duration, 2), 's  end frame', T.f(T.duration))
for l in T.lines:
    f0, f1 = T.f(l['s']), T.f(l['e'])
    print(f"L{l['n']:2d} {f0:5d}-{f1:5d} ({(f1 - f0) / 30:4.1f}s)  " + ' '.join(f"{w['w']}@{T.f(w['s'])}" for w in l['words']))
