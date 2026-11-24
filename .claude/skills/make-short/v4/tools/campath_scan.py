"""campath_scan.py: read `film.py SET dir campath:a-b` output and flag what lesson 46 forbids.
  blender -b -P film.py -- SET renders/x campath:A-B | python3 tools/campath_scan.py
film.py prints a MOVES line (every planned slam/whip/exit window); jumps inside those windows are intended.
Flags (a) REVERSALS: the direction of travel flips (> 100 deg) while BOTH frames move faster than 30 mm/frame (a slow
creep turning into a whip is fine), (b) JERKS: a speed jump > 25 mm/f outside every planned move window (+-2 frames),
(c) STALLS: 25+ frames under 1.5 mm/f and 0.08 deg/f (the reference never holds still longer), (d) NEAR: the camera
within 0.45 m of a character's head/chest/hips: it is inside or grazing them (Dutch flood: a whole shot rendered as blank
teal from inside a soldier, lesson 61), (e) COLLAPSED: a slam/whip window of 4 frames or less, and CAMWARN lines from
CamPath (rc3): a move that starts late because the previous move ends inside its window (pineapple pit: 8 whips had shrunk to
1-2 frame pops), or calls out of time order (the camera snaps back: the pineapple pit's 0:36 'repeat')."""
import re, sys, math
rows, wins, near, warns, short = [], [], [], [], []
for line in sys.stdin:
    if line.startswith('CAMWARN '): warns.append(line.strip())
    if line.startswith('MOVES '):
        ends_slam = set()
        for w in line.split()[1:]:
            ab, st = w.split(':'); a, b = ab.split('-'); a, b = int(a), int(b); wins.append((a - 2, b + 2))
            if a in ends_slam and b - a <= 4: short.append(f'COLLAPSED f{a}-{b}: a slam/whip of {b - a} frames (EXPO moves {100 * (1 - 2 ** (-10 / max(1, b - a))):.0f}% of it in ONE frame: a pop)')
            if st == 'slam': ends_slam.add(b)
    m = re.match(r'CAM f\s*(\d+) pos \(\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\) speed\s+([\d.]+) mm/f\s+turn\s+([\d.]+) deg/f\s+jerk\s+([\d.]+)', line)
    if m: rows.append([float(v) for v in m.groups()])
    if line.startswith('NEAR '): near.append(line.strip())
inwin = lambda f: any(a <= f <= b for a, b in wins)
bad = 0; still = 0
for i in range(1, len(rows)):
    f, x, y, z, sp, tn, jk = rows[i]; f0, x0, y0, z0, sp0, _, _ = rows[i - 1]
    if i >= 2:
        _, xa, ya, za, *_ = rows[i - 2]
        v1 = (x0 - xa, y0 - ya, z0 - za); v2 = (x - x0, y - y0, z - z0)
        n1 = math.sqrt(sum(a * a for a in v1)); n2 = math.sqrt(sum(a * a for a in v2))
        if n1 * 1000 > 30 and n2 * 1000 > 30:
            ang = math.degrees(math.acos(max(-1, min(1, sum(a * b for a, b in zip(v1, v2)) / (n1 * n2)))))
            if ang > 100: print(f'REVERSAL f{int(f)}: travel turns {ang:.0f} deg at {sp:.1f} mm/f'); bad += 1
    if abs(sp - sp0) > 25 and not inwin(f): print(f'JERK f{int(f)}: speed {sp0:.1f} -> {sp:.1f} mm/f (no planned move here)'); bad += 1
    still = still + 1 if (sp < 1.5 and tn < 0.08) else 0
    if still == 25: print(f'STALL ending f{int(f)}: 25 frames near-still'); bad += 1
for w_ in warns + short: print(w_)
bad += len(warns) + len(short)
for n_ in near[:12]: print(n_)
if len(near) > 12: print(f'... {len(near) - 12} more NEAR frames')
bad += len(near)
print(f'campath_scan: {len(rows)} frames, {len(wins)} planned moves, {bad} flags ({len(near)} NEAR)')
