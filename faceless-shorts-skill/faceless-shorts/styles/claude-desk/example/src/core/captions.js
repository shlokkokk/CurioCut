// Captions & Top Chapter Header Plaque for Claude-Desk format:
// 1. Top Chapter Header Plaque: Displays dynamic scene title (e.g. "CLAUDE KILLED $1B JARVIS") with a red tech badge.
// 2. High-Retention Karaoke Captions: Word-by-word bold text with vibrant red rounded highlight pill.
import { ctx, clamp, lerp, seg, eob } from './lib.js';
import { T, lineWords } from './timing.js';

export const CAP = { y: 1530, size: 80, maxW: 960 };
let caps = [];
let scriptHeaders = [];

const SHORT = /^(a|an|the|to|of|in|on|at|by|and|but|or|so|is|it|he|she|we|i|his|her|my|no|up|for|was|now)$/i;

function autoChunks(ws) {
  const out = [];
  for (let i = 0; i < ws.length; i++) {
    const w = ws[i], n = ws[i + 1], bare = w.replace(/[^A-Za-z']/g, '');
    if (n && SHORT.test(bare) && !/[,.!?;:]$/.test(w) && (w + n).length <= 11) {
      out.push([i, i + 1]);
      i++;
    } else {
      out.push([i, i]);
    }
  }
  return out;
}

export function buildCaptions(script) {
  caps = [];
  scriptHeaders = [];

  if (!script || !script.lines) return caps;

  script.lines.forEach((ln, i) => {
    const ws = lineWords(i);
    if (!ws || !ws.length) return;

    // Record header for top plaque
    const headerText = (ln.header || script.title || 'TECH INTEL').toUpperCase();
    scriptHeaders.push({
      line: i,
      s: ws[0].s - 0.05,
      e: ws[ws.length - 1].e + 0.1,
      header: headerText
    });

    const textWords = ln.text.split(/\s+/).filter(Boolean);
    const spoken = ws.length === textWords.length ? textWords : ws.map((w) => w.w);

    autoChunks(spoken).forEach(([a, b]) => {
      caps.push({
        line: i,
        s: ws[a].s - 0.03,
        text: spoken.slice(a, b + 1).join(' ')
      });
    });
  });

  // Calculate chunk end times
  caps.forEach((c, k) => {
    const next = caps[k + 1];
    const lineEnd = T.lines && T.lines[c.line] ? T.lines[c.line].end : T.dur;
    c.e = next ? (next.s - lineEnd > 0.6 && next.line !== c.line ? lineEnd + 0.25 : next.s) : T.dur;
  });

  // Smooth header transitions
  scriptHeaders.forEach((h, k) => {
    const next = scriptHeaders[k + 1];
    if (next) h.e = next.s;
    else h.e = T.dur;
  });

  return caps;
}

export const captionList = () => caps.map((c) => ({ ...c, words: [{ txt: c.text }] }));

/** Draw the Top Chapter Plaque */
export function drawTopHeader(t) {
  const h = scriptHeaders.find((item) => t >= item.s && t < item.e) || scriptHeaders[0];
  if (!h || !h.header) return;

  const text = h.header;
  ctx.save();
  ctx.font = '900 48px Inter, sans-serif';
  ctx.letterSpacing = '1px';

  const textW = ctx.measureText(text).width;
  const cardW = Math.max(520, Math.min(940, textW + 120));
  const cardH = 120;
  const cardX = 540 - cardW / 2;
  const cardY = 190;

  // Glass card background
  ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
  ctx.shadowBlur = 24;
  ctx.shadowOffsetY = 8;

  ctx.fillStyle = 'rgba(17, 19, 29, 0.92)';
  ctx.beginPath();
  ctx.roundRect(cardX, cardY, cardW, cardH, 28);
  ctx.fill();

  // Subtle border
  ctx.shadowBlur = 0;
  ctx.shadowOffsetY = 0;
  ctx.lineWidth = 3;
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
  ctx.stroke();

  // Red Tech Badge ("● TECH EXPLOIT")
  ctx.fillStyle = '#FF3B30';
  ctx.font = '800 22px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('● 100% FREE AI EXPLOIT', 540, cardY + 36);

  // Main Header Text
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '900 44px Inter, sans-serif';
  ctx.fillText(text, 540, cardY + 82);

  ctx.restore();
}

/** Draw the Word-By-Word Subtitles with Red Highlight Pill */
export function drawCaption(t) {
  // Always draw the top header plaque
  drawTopHeader(t);

  const c = caps.find((c) => t >= c.s && t < c.e);
  if (!c) return;

  const lt = t - c.s;
  const sc = lt < 0.1 ? lerp(0.88, 1, eob(seg(lt, 0, 0.1))) : 1;
  const text = c.text.toUpperCase();

  ctx.save();
  ctx.font = `900 ${CAP.size}px Inter, sans-serif`;
  ctx.letterSpacing = '0px';

  const fit = Math.min(1, CAP.maxW / ctx.measureText(text).width);
  const textW = ctx.measureText(text).width * fit;

  ctx.translate(540, CAP.y);
  ctx.scale(sc * fit, sc * fit);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  // Red Highlight Background Pill
  const pillW = textW + 64;
  const pillH = CAP.size + 36;
  ctx.fillStyle = '#FF3333';
  ctx.shadowColor = 'rgba(255, 51, 51, 0.45)';
  ctx.shadowBlur = 24;
  ctx.beginPath();
  ctx.roundRect(-pillW / 2, -pillH / 2, pillW, pillH, 22);
  ctx.fill();

  // Subtitle Text
  ctx.shadowBlur = 0;
  ctx.fillStyle = '#FFFFFF';
  ctx.fillText(text, 0, 2);

  ctx.restore();
}
