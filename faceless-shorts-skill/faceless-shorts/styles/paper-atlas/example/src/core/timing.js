// Timing: everything on screen is placed on the narration's clock.
//   data/lines.json  { duration, lines: [{ i, text, start, end }] }   (voice.py, or estimate.py for captions-only)
//   data/words.json  [{ w, line, s, e }]                                (words.py, or estimate.py)
// L(i) = line i start · Le(i) = line i end · Wd(word, line) = start of the first word in that line matching
// the prefix (case/punctuation ignored; throws if it isn't there, so a rewritten script can't silently drift).
export const T = { dur: 0, lines: [], words: [] };
const norm = (w) => String(w).toLowerCase().replace(/[^a-z0-9']+/g, '');

export async function loadTiming() {
  const get = async (f) => { const r = await fetch(f, { cache: 'no-store' }); if (!r.ok) throw new Error(`missing ${f}: run voice.py + words.py (or estimate.py)`); return r.json(); };
  const lines = await get('data/lines.json'), words = await get('data/words.json');
  T.lines = lines.lines; T.words = words; T.dur = lines.duration;
  return T;
}
export const L = (i) => {
  if (!T.lines || !T.lines.length) return 0;
  const idx = Math.min(Math.max(0, i), T.lines.length - 1);
  return T.lines[idx].start;
};
export const Le = (i) => {
  if (!T.lines || !T.lines.length) return T.dur;
  const idx = Math.min(Math.max(0, i), T.lines.length - 1);
  return T.lines[idx].end;
};
export function Wd(word, line, which = 's') {
  const n = norm(word);
  const hit = T.words.find((w) => (line == null || w.line === line) && norm(w.w).startsWith(n));
  if (hit) return hit[which];
  if (!T.lines || !T.lines.length) return 0;
  const idx = Math.min(Math.max(0, line != null ? line : 0), T.lines.length - 1);
  const l = T.lines[idx];
  return l ? l.start + (l.end - l.start) * 0.4 : 0;
}
export const lineWords = (i) => T.words.filter((w) => w.line === i);
