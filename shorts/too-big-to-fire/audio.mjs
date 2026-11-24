import { chromium } from 'playwright'; import { writeFileSync } from 'node:fs'; import path from 'node:path'; import { pathToFileURL } from 'node:url';
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }); const p = await b.newPage();
await p.goto(pathToFileURL(path.resolve('short.html')).href + '?render');
const b64 = await p.evaluate(async () => { const sr = 48000, ctx = new OfflineAudioContext(2, Math.ceil(sr * VIDEO.duration), sr); await buildAudio(ctx);
  const bb = await ctx.startRendering(), L = bb.getChannelData(0), R = bb.getChannelData(1), i16 = new Int16Array(L.length * 2);
  for (let i = 0; i < L.length; i++) { i16[2*i] = Math.max(-1, Math.min(1, L[i])) * 32767; i16[2*i+1] = Math.max(-1, Math.min(1, R[i])) * 32767; }
  const u8 = new Uint8Array(i16.buffer); let s = ''; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(s); });
writeFileSync('short.pcm', Buffer.from(b64, 'base64')); await b.close();
