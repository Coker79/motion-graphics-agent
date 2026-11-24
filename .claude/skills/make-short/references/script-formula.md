# Script formula: RicksClips-style animated explainer Shorts

Reverse-engineered from 29 Shorts by @RicksClips3000 (0.1M–29.5M views): 28 YouTube auto-caption transcripts + 1 Whisper transcript, cleaned into `transcripts/clean/<id>.txt`, plus the frame-by-frame breakdown of "Why Perfect Railroads Don't Work" (`railroads-ref/BREAKDOWN.md`). Every number below was measured on those files unless it is marked as a target. The top Short (34.8M) had no transcript and is not analysed. The method and caveats are in Appendix B.

---

## 0. Why these scripts work

They are **fables wrapped around one true, counterintuitive mechanism**. Sentence 1 shows a specific, drawable act (or a contradiction) that looks wrong and gives no reason, so the viewer's "why?" opens within ~4 s. "You see," rewinds to the stakes. Then ~40% of the runtime is a *but/so* chain: the odd plan escalates in three rungs while a skeptic mocks it and someone gloats (dramatic irony). The answer is held back until **~70–80% of the runtime**. It lands as a reversal you can see (usually the mocker's comeuppance) and is paid off in 1–3 plain sentences built on an everyday analogy, not on the jargon name. The last line reuses a word or image from the hook, so it reads as closure and the loop restarts cleanly. Everything is concrete: archetypes instead of names, small exact numbers, objects and sounds instead of abstractions. Narration runs wall to wall at **~3.7 words/s** with one picture per sentence, and there is no moral and no call to action.

---

## 1. The formula (55–65 s Short, 3.7 words/s, about 205 / 222 / 240 words at 55 / 60 / 65 s)

| # | Beat | Runtime % | Words @60 s | Sentences | What it must accomplish |
|---|---|---|---|---|---|
| 1 | **Hook: the strange act** | 0–6 | 12–16 | 1 | State one drawable act (or contradiction) as fact, with no motive. Use past tense for an act ("He drilled 82 holes…") and present tense for a contradiction. Include one exact detail: a number, a distance or a colour. |
| 2 | **Rewind + stakes** | 6–27 | 30–50 | 2–4 | "You see," + who/where + the rule of this world + what someone stands to lose (the whole country's business, his last 100 bucks). Switch to present tense. Keep world-building to 60 words or fewer. |
| 3 | **Escalation ladder** | 27–55 | 55–75 | 4–6 | The odd plan continues in 3 rising rungs. A skeptic gets one line of 12 words or fewer, usually a joke. Plant 1–2 details that pay off later. The hero stays calm and never explains. |
| 4 | **Low point / false win** | 50–70 | 25–40 | 2–3 | The hero looks most wrong (the rival finishes first, everyone switches), or the plan seems to work ("At first, it's paradise."). Someone gloats or relaxes, which creates dramatic irony. Optionally voice the viewer's doubt here ("Wait, what?"). |
| 5 | **Turn / twist** | 65–85 | 25–40 | 2–4 | Open with a time cue ("Then, one rainy morning…"). The hidden mechanism acts **on screen**: an object, a sound or a person changes. The mocker's side fails or the cheat is caught. |
| 6 | **Explanation** | 70–90 | 20–40 | 1–3 | "You see," + the true mechanism in plain words + **one everyday analogy** (soup, a phone sliding off a table). Use the jargon name once at most, or not at all. Skip this beat when the twist image already explains the mechanism. |
| 7 | **Sting** | 90–100 | 10–18 | 1 | A final image or irony line that reuses a word or image from the hook or the mocker. Hard end: no moral, no CTA. |

**Measured basis** (22 narrative Shorts, beats annotated by sentence; median, IQR): hook 14 words (12–19). Setup 42 (28–59), starting at 7%. Escalation including the low point 92 (68–115), starting at ~30%. Twist 33 (20–48), starting at **73% (65–82)**. Explanation 35 (20–51), starting at **71% (66–78)**, present in 14/22. Sting 15.5 (12–18), starting at 93% (90–95). In the core 55–67 s stories (n=15) the twist median is **80%** and the explanation median 72.5%.

**Ending order: pick one.**
- **A. Show → tell → sting** (7 Shorts, median 9.9M). Reversal, then "You see," then a one-line sting (Japan job room, pink cell, lottery clerk, furniture burglar). **Default.**
- **B. Tell → show** (5, median 9.6M). Explain while the danger approaches, then make the last line the payoff image (storm oil, roller-coaster loop, mirror race).
- **C. Show only** (7, median 4.6M, but includes the 29.5M railroads). The payoff image *is* the explanation (gaps close, the seamless track buckles). Use it only when the mechanism is visible as an object changing.

---

## 2. Hook archetypes

| Archetype | Pattern | Paraphrased illustration (from the set) | n, median views |
|---|---|---|---|
| **Inexplicable act** | "[Role] [did a specific, self-defeating-looking thing]." Past tense, no motive. | a young engineer saws a gap into new rail every 39 ft; a man shifts everything in a family's house an inch left every night | 12, 8.2M (includes the 29.5M top) |
| **Act + ticking threat** | The same, plus a danger closing in, in the same sentence. | a sailor pours cooking oil overboard with pirates close enough to hear laughing; a soldier drills 82 holes while an army marches up the hill | 2: 16.7M, 8.4M |
| **Contradiction** | "[X] is illegal/impossible. Yet [X is everywhere / they found something worse]." Or "The best [role] had one rule: never [the obvious move]." | gambling is banned in Japan, yet there's a parlour on every street; the fastest gun in the West never drew first | 3, **16.0M (best)** |
| **Absurd conditional** | "If you [ordinary act], [backwards result]." Second person. | nap holding two steel balls and you might wake up a genius; being hit by a cannonball made you one of the lucky ones | 5, 5.3M (1.0–16.4) |
| **Hidden tell** | "There's a way to tell [X] without [the obvious test]." | two scratch cards, and a way to spot the winner without scratching either | 2: 9.5M, 6.6M |
| **Transgression** | "[Role] [commits a small dark act on camera] + a casual line." | a cashier scans a million-dollar ticket and tells the customer it lost | 1: 9.6M |
| **Doom prophecy** | "When [future thing] arrives, [huge loss] and nobody will notice." | teleporters that quietly kill every traveller | 1: 7.3M |
| **Forbidden object** (fiction only) | "There's a [thing] nobody is allowed to touch." | a button in the middle of town under glass and guards | 1: 3.8M |

**How the curiosity gap opens in sentences 1–2**
- **Assert, don't ask.** 28/29 hooks are statements. The one question hook is the second-lowest Short (0.3M).
- **Show the strangest moment.** The act is either the premise (sawing gaps, drilling holes) or taken from mid-story (the loop is bent at 24%, the memory is sold at 82%). "You see," then rewinds: 8/29 do this at 4–14% of the words.
- **Use one exact, drawable detail**: 39 ft, 82 holes, one inch, "not just any pink".
- **Withhold the motive.** Four Shorts give the surface "why" early (salting, insurance money, safety coffins, the experiment's aim), and each immediately opens a deeper question: will the con survive the expert? Why won't the wife dig? In **all 14 act-hook Shorts the decisive twist lands at 62–91%**.
- **Sentence 2** is either the rewind ("You see," + stakes) or the immediate reaction to the act (6/29), often a witness's disbelief: the buddy watches the gold vanish into rock; the betting room laughs.

**Anti-patterns** (each one appears in the bottom five): a direct question as the hook (painkillers, 0.3M). "You" in a mundane moment with no anomaly (slot reels stopping one short, 0.1M). A warning hook that names and explains itself by 10–30% (the poison tree, 1.0M). World-building before anything happens (the memory market spent 108 words, 37% of the script, and got 0.6M; the button town spent 98 words and got 3.8M; every other narrative Short spent 67 words or fewer).

---

## 3. Language rules (measured; median and IQR, n = 29 unless stated)

| Rule | Measured | Target |
|---|---|---|
| Pace | **3.67 words/s** over the full runtime (IQR 3.58–3.78, range 3.28–4.10); 3.95 within speech. The top Short is the slowest (3.28 = 197 wpm). | 3.5–3.8 words/s; hard limits 3.3–3.9 |
| Sentences | 16 per Short (core: IQR 15.5–17), about one every 3.8 s | 15–18 per 60 s |
| Sentence length | median **13.5 words** (12–15); longest 24–30; hook 14 (11–17); last 16 (12–19) | median 9–15; none over 32; hook 16 or fewer |
| Punch fragments | 1–3 per Short of **5 words or fewer**, placed right after a long build sentence ("But, it's too late." / "That night it pours."). Within stories, more fragments go with more views (ρ = +0.48, n = 22). | **0–2 at most, never back to back** (client test: v2's run of fragments, "Crack." / "Green. Fuzzy. Squish.", read as "very jarring when listening"; v3 with one was approved straight away) |
| Connectives | **36%** of all 435 sentences open with So (12%), But (7%), And (6%), You see (5%), Then (3%), Well, or Yet. Cause and contrast, never "and then". | at least 30% |
| Hinge phrases | "You see," in 19/29 Shorts: 8 times as the rewind (4–14%), 12 times as the reveal (64–90%). Voiced doubt ("Wait, what?", "But how?") answered by "Well, …" in 6/29. | 1 rewind + 1 reveal "You see," |
| POV | 3P fables: "you" = **0.4%** of words, only in asides (a gold vein *as thick as your arm*; *ever blown on soup?*). You-POV Shorts (n=9): **7.3%**. | pick one and don't switch in the body |
| Tense | 11 of 14 past-tense act hooks switch to **present tense** for the story. Explanations may drop to past for history ("back then…"). | past hook, present story |
| Names | Proper character names in 3/29 (two of them in the fiction flops). Everyone else is a role: his boss, his buddy, the rich guy, the quiet guy, a scientist. | 0 names; costume-coded roles |
| Jargon | The phenomenon is named in 6/29, never in the top two. When named it is plain English ("storm oil") or glossed in the same breath. | 0–1 uses; never in the hook or title |
| Numbers | median **5 numerals** per Short (4–7): small, physical, odd (39 ft, 15 minutes, 300 lb, 47 then 48 scratches). The key number repeats as a motif (82 holes, 82 flames, all 82). | at least 4; repeat the key one 2–3 times |
| Dialogue | 0–4 in-character lines (core median 2), each 12 words or fewer, almost always the skeptic and usually a joke. The hero says at most a cryptic 2–4 words ("Trust the oil."). | 1–3 lines, speaker marked for the VO |
| Questions | median 1 per Short: the viewer's doubt voiced right before an answer | 1–2 |
| Sound words | 15/29 have 2 or more: clickety-clack, a hook clangs off the rail, the wire starts clicking, a tiny scratching | 1–3 that carry plot |
| Intensifiers | "just" appears 42 times in 25/29 (the calm hero *just* points). every / single / whole / nobody / never raise the stakes. | "just" for the hero's calm |
| Ending | In 22/29 the last two sentences reuse a content word from the hook. 0/29 have a CTA (two thought experiments end on a question to the viewer). | echo the hook; hard end |

---

## 4. Story mechanics to build into every fable

1. **A quiet hero with a secret plan**: unnamed and calm; never explains; acts with "just" (just points at the clouds, just sits smiling). Calm against everyone else's panic is the tell that he knows something.
2. **A skeptic chorus** (boss, captain, rival, officials, a laughing room), one joke line each. In 12/22 stories someone gloats or relaxes right before the reversal: the boss gloats as the gaps shrink, and the pirates are glad the storm will do their work.
3. **Stakes in five words**: the whole country's business, his life savings, the fort, his last 100 bucks.
4. **Three-rung ladders** (about 20/29): coin in May, paper by July, closed. Sitting at 15 minutes, pacing at 20, ripping out the bench. The neighbour, the street and then the doctor all dismiss the bell.
5. **Plant and pay off**: every odd detail returns. The exact 15-minute rule; the rope nobody may touch; pouring always on the windward side; 47 scratches become 48; the captain's "making soup?" jibe becomes the soup analogy.
6. **Voiced doubt** at 8–35% (right after the hook) or 55–76% (right before the reveal), answered with "Well, …".
7. **False win, then a time cue**: "At first, it's paradise." / the insurance pays / every jail paints its cells pink. About three-quarters of the stories mark the climax with a time cue ("Then, one Monday…", "Until one night…", "The next morning…").
8. **Comeuppance** (about 12/22): the twist lands on the mocker or the cheat. The seamless rail buckles, the wave drops on the pirates, the room stops laughing.
9. **A truth stamp** in the explanation reconnects the fable to reality in a few words ("sailors really carried oil…", "in real life, lotteries noticed…"); legends get a hedge ("was rumored to").
10. **Jokes**: 16/22 narrative Shorts have at least one comic line (an exaggerated simile or the skeptic's quip), roughly one every 20 s. The six without include all four narrative Shorts of 45 s or less.

---

## 5. Topic selection

| Family | In the set (views) | Median |
|---|---|---|
| **The wrong-looking fix wins** (engineering/physics: the "imperfect" design beats the "perfect" one) | rail gaps 29.5M, storm oil 16.7M, loop shape 11.8M, rocket cart 8.4M | **14.3M** |
| **Loophole in a strict system** (a hard rule beaten by a technicality) | Japan's banishment room 18.3M, pachinko window 16.0M, spear & shield 9.6M, pre-paid forgiveness 1.7M | 12.8M |
| **Brain/body quirk staged as a story** | idea nap 16.4M, pink cell 10.9M, second draw 9.8M, falling-time test 6.8M, target fixation 5.3M, near-miss slots 0.1M | 8.3M |
| **A con or scheme, and its tell** | grave bell 13.5M, furniture 9.9M, lottery clerks 9.6M, fake checks 9.5M, scratch cards 6.6M, mirror race 5.6M, salting 4.9M, crash-for-cash 4.6M | 8.1M |
| Levels list (the one that worked had a backwards hook and a navy-vs-pirates rivalry) | cannonballs 9.9M vs poison tree 1.0M | — |
| Thought experiment / pure fiction / plain explainer | 7.3M, 4.0M / 3.8M, 0.6M / 0.3M | weak |

**Topic checklist** (1 point each; pass at 8 or more, and items 1 and 2 are mandatory)
1. The mechanism is true, fits one plain sentence, and has a source.
2. Someone can act on it in a way that looks stupid, crazy or illegal to a bystander, or two true facts contradict.
3. The wrong-looking choice beats the obvious or "perfect" one, or a strict rule loses to a workaround.
4. The mechanism can be **shown** changing through objects or sounds in the world.
5. There's an everyday analogy for it (kitchen, phone, car, body).
6. The stakes can be felt in five words.
7. There's a natural skeptic who can mock the hero.
8. Most viewers can't guess the answer from the hook or title (famous idioms and legends fail this).
9. It fits 2–4 archetypes, 1–2 locations and 1 time skip.
10. There's a final image that shows the reversal and can echo the hook.

**Title formulas** (4–8 words, median 6). The title names the object or category and implies a paradox. The hook shows one instance in motion. Neither contains the answer.
- *Why [Perfect/Normal Thing] [Fails / Always Wins]*: railroads 29.5M, second draw 9.8M
- *Why [Group] [Carried/Did an Odd Thing]*: storm oil 16.7M, cashiers 9.6M, drivers filming 4.6M
- *The [Ordinary Thing] That [Broke a Law / Warned an Empire]*: window 16.0M, ancient jar 34.8M, burglar who only moved furniture 9.9M
- *The [Thing] Nobody [Wants] in [Place]*: Japan job 18.3M
- *What the [Object] Really Meant*: grave bell 13.5M
- Avoid "How X Actually Works" (0.3M), "The Science Behind X" (0.1M), abstract or personified titles (0.6M, 1.0M), and hype adjectives.

Measured by title opening: "Why…" n=6, median 9.7M; "The X that/who…" n=9, median 9.9M; "How…" n=4, median 5.3M; "This…" n=3, median 1.7M. These groups are small, so read them as a lean, not a law.

---

## 6. Visual-script coupling (railroads breakdown + this corpus)

- **One sentence = one visual beat.** Railroads has ~22 beats for ~23 sentences, ~3 s each. Start each sentence with its new subject so the camera move can land on its first word (≈28 camera events in 65 s, mostly on sentence starts).
- Sentences of 20 words or more (3–4 per Short) carry **two** visual beats. Split them at the comma and describe both pictures.
- **Exposition lives in props, never overlays**: station banner, newspaper headline, wall calendar flipping May to July, thermometer, rail length chalked on a sleeper. Name the prop in the line ("By July, barely a sheet of paper" = calendar + paper in the gap).
- **Time cues are the only dissolves** (summer arrives, "meanwhile", next morning). Everything else is hidden inside a camera move, so write a time cue only where you want a transition.
- **Sound words become SFX hits** and can carry the explanation (clatter against silence; rails groaning in the heat).
- The science stays unnamed on screen. The only "diagram" is painted onto the world (heat-map rails).
- **Make the hook frame rhyme with the last frame** (a train bearing down at 0 s; a train rolling onto the buckled track at the end), so the loop reads as one take.
- Characters are costume-coded archetypes. One narrator voices them by pitching up (the boss's line ≈330 Hz against ≈200 Hz narration), so mark speakers.
- Captions are set from the written script (one word per card 78% of the time). Write the words you want on screen.
- The explanation's analogy needs its own insert picture (a rippling bowl of soup, a phone sliding off a table), drawn in the same world style.

**Script deliverable (one row per sentence):**
`| # | line | words | cum. % | beat | picture (subject + action) | prop that carries the fact | SFX | speaker |`

---

## 7. Procedure for writing a new script

1. **Topic**: run the checklist (§5). Write the mechanism in one plain sentence, with a source. Reject the topic below 8.
2. **Find the act**: list 5 moments where someone acts on the mechanism and looks wrong. Pick the most drawable and self-defeating one, or two true facts that collide (contradiction hook).
3. **Cast**: the hero (quiet, unnamed, costume-coded), 1–2 skeptics and whoever holds the stakes. Set the world in one sentence.
4. **Ending order**: A by default; B if the danger can approach during the explanation; C only if the payoff image explains itself.
5. **Hooks**: draft 5. Score each 0–6, one point each for: drawable, exact detail, looks self-defeating or contradictory, 16 words or fewer, no motive, an assertion. Keep the best one, and only if it scores at least 5.
6. **Beat sheet**: fill the 7 beats with word budgets (target seconds × 3.7). Place the ladder, the skeptic's joke, 1–2 plants, the gloat, the time cue, the twist, the explanation + analogy and the sting echo.
7. **Write for the EAR, line by line** (client rule, after v2 was "hard to follow… very jarring when listening"):
   - One picture per sentence, new subject first.
   - **Introduce each character before they act** ("When a new recruit bit into his first one…"), so every pronoun has a referent the listener has already heard.
   - **Keep one tense** all the way through (past is fine).
   - **Lead each line into the next** (So / Then / But / You see).
   - **At most 1–2 fragments** of 5 words or fewer, never back to back.
   - A joke must land on first hearing, without the picture.
   - Read the script aloud at the target pace. Rewrite any line that needs the picture to make sense.
8. **Measure** with the snippet below. Put one sentence per line, prefix the first twist line with `>T` and the first explanation line with `>X`, then run `python -I measure.py script.txt 60`.

```python
import re, statistics as st, sys
L=[l.strip() for l in open(sys.argv[1]) if l.strip()]; secs=float(sys.argv[2])
tag=[l[:2] if l[:2] in('>T','>X') else '' for l in L]; L=[l[2:].strip() if t else l for l,t in zip(L,tag)]
n=[len(re.findall(r"[A-Za-z0-9$%'-]+",l)) for l in L]; W=sum(n); off=[sum(n[:i]) for i in range(len(n))]
c=sum(bool(re.match(r"(so|but|and|then|yet|until|well|you see|still|instead|meanwhile|eventually)\b",l,re.I)) for l in L)
print(f"{W} words = {W/secs:.2f} w/s | {len(L)} sentences | median {st.median(n)} | max {max(n)} | <=5w: {sum(x<=5 for x in n)}")
print(f"connective starts {100*c/len(L):.0f}% | hook {n[0]} w | last {n[-1]} w")
for t in('>T','>X'):
    if t in tag: print(t, f"at {100*off[tag.index(t)]/W:.0f}% of words")
```

9. **Score** against the rubric below, fix the lowest items, and measure again.
10. **Fact pass**: tag every claim [TRUE + source], [FABLE] (invented people or scenes: allowed, but never presented as documented) or [CHECK]. A [CHECK] left in the mechanism, the explanation, the numbers, or any "that's how X was invented" line blocks the script.
11. **Output** the §6 table for the animator and the plain script for the VO and captions.

**Rubric** (10 items, 1 point each, half points allowed). **Pass = 8.5 or more with every GATE at 1.**

| # | Criterion |
|---|---|
| 1 | **GATE · Hook**: one sentence of 16 words or fewer; drawable; a strange act or contradiction stated as fact; no motive; no question. |
| 2 | **GATE · Gap held**: the decisive answer lands at 65% of the words or later. Any early partial answer opens a deeper question. |
| 3 | Stakes and world are set by 27%: who stands to lose what, in concrete terms, in 60 words of setup or fewer. |
| 4 | Escalation: a 3-rung ladder, one skeptic line (12 words or fewer, ideally funny), and a gloat or false win before the turn. |
| 5 | The twist lands on screen at 65–85%, opened by a time cue. An object, sound or person visibly changes, ideally on the mocker's side. |
| 6 | Explanation: 3 sentences / 45 words or fewer, plain words, one everyday analogy, the jargon name once at most (or no explanation if the payoff shows the mechanism). |
| 7 | Ending: last sentence 8–20 words, echoes a word or image from the hook, no moral, no CTA. |
| 8 | Rhythm and EAR: 3.3–3.9 words/s at the target length; median sentence 9–15 words; **at most 2 fragments of 5 words or fewer, never consecutive**; no sentence over 32 words; at least 30% connective starts; one tense; every character introduced before they act; it reads smoothly aloud. |
| 9 | Concreteness: every sentence has a drawable subject; at least 4 exact numbers or measures; at least 2 props carry exposition; no proper names unless famous and needed. |
| 10 | **GATE · Truth**: every factual claim is tagged and sourced; fable elements are obviously archetypal; no invented "real" claims. |

Calibration: railroads scores ~9.5 and the Japan job room ~9. The two lowest Shorts (slot machines, painkillers) score 4–5 and fail gates 1 and 2.

**Field notes (rc3, the pineapple pit):**
- **Twist position vs length.** With 5 post-twist sentences (twist, result, explanation, analogy, sting) at about 13 words each, the twist reaches 65% only at about 185 words: about 55 s with two quoted lines. At 45–55 s, budget the post-twist block at 60–65 words, or use one quote.
- **The cold-listener bar.** Fresh listeners stuck at 7/10 when they could predict the mechanism from the hook and liked the side fact more. What moved them: a payoff they can't predict (the mocker begging for dung), and an explanation that adds a reason the payoff image doesn't show ("no fire to go out"), instead of restating the climax.
- **One review round, not a loop** (2.3.0). Run the critic and one cold listener once, in parallel, apply both in one rewrite, and take both reports to the user. Re-scoring v6–v7 for about 4 h never moved the listener off 7/10; the fix came from the user's note at GATE 1.
- **Checking a channel** (§5): WebFetch of a Shorts tab returns no titles. `curl` the channel page, take the `UC…` id from `"browseId"`, then read `https://www.youtube.com/feeds/videos.xml?channel_id=<id>` (the latest 15 uploads).

---

## 8. Three worked outlines (new topics; facts flagged)

### 8.1 "Why They Armored the Parts Nobody Shot" (inexplicable act · 3P fable · ending A · ~223 words)
Mechanism [TRUE, cite Abraham Wald / Statistical Research Group, WWII memos on estimating plane vulnerability from survivors' damage]: holes on planes that *return* mark hits a plane survives, so the clean areas mark the fatal hits. [FABLE] the general, the hangar chart, the runway scene. [CHECK] don't claim the military adopted the advice unless sourced. The famous red-dot plane drawing is a modern illustration, so keep the chart as an in-story prop.

| # | % | Words | Lines do | Picture / prop |
|---|---|---|---|---|
| 1 Hook | 0–6 | 14 | *He told the generals to bolt armor only where the bombers never got shot.* | hero's finger on the spotless engine of a shredded bomber |
| 2 Rewind | 6–25 | 40 | You see: bombers limp home shredded; every hole is painted as a red dot on a giant hangar chart; armor is so heavy each plane gets only a little or it can't take off | chart; crane lowering one steel plate |
| 3 Ladder | 25–55 | 65 | dots pile onto the wings and tail; the general slaps the chart (skeptic: armor goes where the bullets go); crews plate the wings; the hero *just* stares at the clean engines (plant, said twice); joke: the math guy turns green on the tarmac before an engine even starts | chart filling; plated wings |
| 4 Low point | 50–70 | 30 | the armored planes still don't come back; the general laughs that he wants steel where nobody is even aiming; voiced: wait, armor the parts that are fine? | empty seats in the mess hall |
| 5 Turn | 65–85 | 32 | *Then, one evening*, he walks the general down the runway counting empty parking spots: every plane hit in the engine is out there, and none came home to be painted | empty hardstands at dusk |
| 6 Explain | 72–90 | 28 | You see: the chart only counted survivors; half a wing gone and you limp home, one engine hit and you never land to be counted; analogy: asking only marathon finishers if the course was easy | finish-line insert |
| 7 Sting | 90–100 | 14 | the clean spots on the chart were never the safe spots; they were the deadly ones (echoes "never got shot") | chart's clean engine glowing |

### 8.2 "The Shortcut That Made Everyone Late" (contradiction · you-story · ending A · ~220 words)
Mechanism [TRUE, cite Braess 1968 and the standard textbook example: 4,000 drivers, 65 → 80 minutes]: when each driver takes their own fastest route, a new free link can make every trip longer. [FABLE] your town, the old engineer, the crack. [CHECK] any real-city example before mentioning one. The numbers below are the textbook model; present them as "your town".

| # | % | Words | Lines do | Picture / prop |
|---|---|---|---|---|
| 1 Hook | 0–6 | 12 | *Your town builds a brand-new shortcut, and everybody's drive home gets slower.* | ribbon-cut shortcut, then a jam of brake lights |
| 2 Rewind | 6–25 | 40 | Imagine two ways home: a narrow bridge that jams when it's busy, plus a highway that always takes 45 minutes; half the town takes each; everyone's home in 65, in time for dinner | map sign at the fork; kitchen clock |
| 3 Ladder | 25–55 | 65 | a free link joins the two bridges; the old engineer who voted no gets booed at the ribbon-cutting; day one you skip both highways in 40 minutes (false win); your neighbour copies you, then the whole street, then the town | dashboard clock 40; cars peeling off the highway |
| 4 Low point | 50–70 | 30 | now every trip takes 80 minutes, and leaving the shortcut alone makes yours 85; voiced: wait, the old way is slower too? | clock 80; cold dinner |
| 5 Turn | 65–85 | 32 | *Then, one Monday*, a crack closes the shortcut for repairs; the town groans, and everyone gets home in 65; the old engineer *just* taps his stopwatch | barrier tape; clock 65 |
| 6 Explain | 72–90 | 29 | You see: everyone picks what's fastest for them, but every extra car on a bridge slows everyone else on it; analogy: one person stands up at a concert, then everyone does, and nobody sees better | concert insert |
| 7 Sting | 90–100 | 12 | the fastest road in town was the one they closed (echoes "shortcut") | empty closed shortcut, traffic flowing |

### 8.3 "What Was Really in London's Best Water" (act + threat · 3P history fable · ending A · ~222 words)
Mechanism [TRUE, cite John Snow, *On the Mode of Communication of Cholera*, 2nd ed. 1855]: cholera spreads through sewage-tainted water, not "bad air". [CHECK every detail]: Broad Street, Soho, 1854 (~600 deaths); handle removed 8 Sept 1854 after Snow addressed the parish board; brewery workers drank beer and had their own supply; the workhouse with its own well had few deaths; the Hampstead widow who had the water delivered died; a cesspool a few feet from the well. Deaths were already falling when the handle came off, so never say the handle alone ended it. [FABLE] the board's lines and the "best taste" chorus.

| # | % | Words | Lines do | Picture / prop |
|---|---|---|---|---|
| 1 Hook | 0–6 | 13 | *Mid-outbreak, a doctor had the handle taken off the street's best water pump.* | handle lifting off; a queue with empty buckets |
| 2 Rewind | 6–25 | 40 | You see: one street is losing people faster than the carts can carry them; everyone knows it's the stink, so they burn tar and seal their windows; he knocks on doors and draws a black bar on a map for every death | tar fires; the map |
| 3 Ladder | 25–55 | 65 | the bars pile up around one pump (the board scoffs: smell the air); the brewery beside it barely loses a man, since they drink beer all day (joke); the poorhouse with its own well is almost untouched; a widow miles away who loved that water's taste had a bottle delivered daily, and she is a bar too | map bars; beer mugs; delivered bottle |
| 4 Low point | 50–70 | 30 | the board takes the handle off mostly to be rid of him; the street curses him for stealing their best water | angry queue at a handleless pump |
| 5 Turn | 65–85 | 32 | *Then* the new bars stop [CHECK; fallback line: the pump never adds another bar]; workers digging beside the well find an old cesspit a few feet away, seeping straight in | map stops filling; dig reveals leaking bricks |
| 6 Explain | 72–90 | 28 | You see: it was never the air; it was the water, and the best-tasting pump was drinking from a sewer; analogy: making tea with the mop bucket | mop-bucket insert |
| 7 Sting | 90–100 | 14 | the deadliest thing on the street was the water everyone said tasted best (echoes "best pump") | pump without a handle at dusk |

(None of these three topics is in the analysed sample; check the channel before using one.)

---

## Appendix A. Evidence (sorted by views; %t = position in runtime; "–" = none)

| # | Title | Views | s | Words | w/s | POV | Form | Twist %t | Explain %t | Hook |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Why Perfect Railroads Don't Work | 29.5M | 65 | 213 | 3.28 | 3P | fable | 84 | – | Inexplicable act |
| 2 | The Job Nobody Wants in Japan | 18.3M | 61 | 225 | 3.69 | you | you-story | 69 | 81 | Contradiction |
| 3 | Why Sailors Carried Storm Oil | 16.7M | 65 | 246 | 3.78 | 3P | fable | 86 | 66 | Act + threat |
| 4 | Your Brain's Secret Idea Zone | 16.4M | 39 | 145 | 3.72 | you | you-story | – | 59 | Absurd conditional |
| 5 | The Window That Breaks Japan's Gambling Law | 16.0M | 45 | 160 | 3.56 | you | you-story | 67 | 67 | Contradiction |
| 6 | What the Grave Bell Really Meant | 13.5M | 60 | 220 | 3.67 | 3P | fable | 62 | 90 | Inexplicable act |
| 7 | This Shape Saved Roller Coasters | 11.8M | 63 | 237 | 3.76 | 3P | fable | 82 | 65 | Inexplicable act |
| 8 | The Pink Prison Cell Experiment | 10.9M | 65 | 237 | 3.65 | 3P | fable | 66 | 81 | Inexplicable act |
| 9 | The Burglar Who Only Moved Furniture | 9.9M | 58 | 238 | 4.10 | 3P | fable | 82 | 88 | Inexplicable act |
| 10 | Levels of Pirate Cannonballs | 9.9M | 64 | 218 | 3.41 | 3P, you-hook | levels | – | – | Absurd conditional |
| 11 | Why the Second Draw Always Wins | 9.8M | 56 | 219 | 3.91 | you | you-story | – | 65 | Contradiction |
| 12 | Why Cashiers Keep Winning The Lottery | 9.6M | 58 | 199 | 3.43 | 3P | fable | 65 | 75 | Transgression |
| 13 | An Unstoppable Spear vs an Unbreakable Shield | 9.6M | 45 | 164 | 3.64 | 3P | fable | 84 | 73 | Inexplicable act |
| 14 | Why Humans Can't Pick Random Numbers | 9.5M | 47 | 163 | 3.47 | mixed | explainer | 75 | 22 | Hidden tell |
| 15 | How One Cart Stopped an Entire Army | 8.4M | 67 | 235 | 3.51 | 3P | fable | 76 | – | Act + threat |
| 16 | What If Humans Invented Teleportation? | 7.3M | 54 | 198 | 3.67 | you | thought-exp | 69 | 69 | Doom prophecy |
| 17 | The Scientist's Insane Time Test | 6.8M | 40 | 143 | 3.58 | 3P | fable | 71 | 79 | Inexplicable act |
| 18 | He Could Spot Winning Tickets Just by Looking | 6.6M | 63 | 231 | 3.67 | 3P, you-hook | fable | 78 | 50 | Hidden tell |
| 19 | How a Mirror Rigged a Horse Race | 5.6M | 64 | 244 | 3.81 | 3P | fable | 82 | 71 | Inexplicable act |
| 20 | The Instinct That Makes You Crash | 5.3M | 59 | 216 | 3.66 | 3P, you-hook | fable | 60 | 74 | Absurd conditional |
| 21 | How Mine Salting Worked | 4.9M | 61 | 231 | 3.79 | 3P | fable | 90 | 15 | Inexplicable act |
| 22 | Why Drivers Started Filming The Road | 4.6M | 62 | 236 | 3.81 | 3P | fable | 85 | – | Inexplicable act |
| 23 | Would You Upload Your Brain? | 4.0M | 57 | 214 | 3.75 | you | thought-exp | 85 | – | Absurd conditional |
| 24 | The Town Built Around a Button | 3.8M | 66 | 245 | 3.71 | 3P, named | fiction | 73 | – | Forbidden object |
| 25 | This Knight Found the Ultimate Loophole | 1.7M | 41 | 158 | 3.85 | 3P | fable | 72 | – | Inexplicable act |
| 26 | This Tree Hates You | 1.0M | 68 | 235 | 3.46 | you | levels | – | 29 | Absurd conditional |
| 27 | Every Memory Has a Price | 0.6M | 78 | 295 | 3.78 | 3P, named | fiction | 91 | – | Inexplicable act |
| 28 | How Painkillers Actually Work | 0.3M | 35 | 137 | 3.91 | you | explainer | – | 42 | Question (anti) |
| 29 | The Science Behind Slot Machines | 0.1M | 31 | 112 | 3.61 | you | explainer | – | 58 | You-in-the-moment (anti) |
| – | The Ancient Jar That Warned an Empire | 34.8M | 65 | – | – | – | – | – | – | no transcript, not analysed |

Group medians: by form, you-story 16.2M (n=4), fable 9.0M (16), levels 5.5M (2), thought experiment 5.6M (2), fiction 2.2M (2), explainer 0.3M (3). By duration, 48–70 s 9.0M (20), under 48 s 8.1M (8), and the single 78 s Short 0.6M.

## Appendix B. Method and caveats

- **Transcripts.** 28 from YouTube `en-orig` auto-captions. The rolling cues were de-duplicated by keeping only each cue's word-timed line, and `[music]` was removed. 1 came from Whisper (`0m6G8pDtzNs.json`). The three `.en.vtt` tracks are machine translations (one turns "He sold" into "She sold") and were ignored.
- **Accuracy.** Word counts are reliable: railroads gives 213, the same as BREAKDOWN's count. Sentence boundaries come from YouTube's auto-punctuation (railroads: 20 sentences against 23 split by hand; median 9 words against 7), so the real scripts are slightly choppier than these medians. Known ASR slips ("He saw gaps" for *saws*, "the crash yank" for *yanks*) don't change the structure.
- **Truncated endings.** Four captions end one word short (the dashcam ___, the exact ___, the pirates' ___, a way to ___). The word was either clipped by the loop edit or missed under the final sound effect; without the audio there's no way to tell, so don't copy this as a technique until it has been checked by ear.
- **Positions and pace.** Twist and explanation positions are my own sentence-level annotations: the twist is the first sentence of the decisive reversal, the explanation the first sentence stating the mechanism. Percentages of runtime use the caption word timings. Words/s uses YouTube's integer durations (±0.5 s).
- **Views and correlation.** Views are a single snapshot and upload dates are unknown. The order of `meta.txt` looks newest-first; if it is, the channel moved from 31–47 s explainers and thought experiments to ~60 s fables. With n = 29, correlations are hints only.
  - Explaining late goes with more views (ρ = +0.47, 90% CI +0.12 to +0.70). That is driven by the early-explaining explainers; within stories it is +0.22.
  - Within stories, more fragments of 5 words or fewer (ρ = +0.48), shorter median sentences (−0.38) and slower pace (−0.32) lean positive.
  - Overall, the share of sentences opening with a connective is +0.33 (90% CI +0.02 to +0.58). Every other measure has |ρ| ≤ 0.26 overall, with intervals spanning 0.
