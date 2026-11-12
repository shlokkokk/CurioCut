// Cloudflare worker for scheduled cron triggers, Discord interactions, and Instagram comment webhooks

const SKIP_CACHE_URL = "https://curiocut.internal/skip-state";

async function isSlotSkipped() {
  try {
    const res = await caches.default.match(SKIP_CACHE_URL);
    if (res) {
      const data = await res.json();
      if (data && data.expireAt && Date.now() < data.expireAt) {
        return true;
      }
    }
  } catch (e) {
    console.error("Cache read error:", e);
  }
  return false;
}

async function setSlotSkipped(hours = 12) {
  try {
    const expireAt = Date.now() + hours * 3600 * 1000;
    const res = new Response(JSON.stringify({ expireAt }), {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": `max-age=${hours * 3600}`
      }
    });
    await caches.default.put(SKIP_CACHE_URL, res);
  } catch (e) {
    console.error("Cache write error:", e);
  }
}

async function clearSlotSkipped() {
  try {
    await caches.default.delete(SKIP_CACHE_URL);
  } catch (e) {
    console.error("Cache clear error:", e);
  }
}

async function sha256Hex(str) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

async function verifyEdgeAuth(request, env) {
  const provided = (
    request.headers.get("x-curio-auth") ||
    (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, "")
  ).trim();
  if (!provided) return false;

  if (env.EDGE_REGISTER_SECRET && provided === env.EDGE_REGISTER_SECRET) {
    return true;
  }
  if (env.DISCORD_WEBHOOK_DMS_SENT) {
    const expected = await sha256Hex(env.DISCORD_WEBHOOK_DMS_SENT);
    if (provided === expected) return true;
  }
  return false;
}

function normalizeToken(str) {
  return (str || "").replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
}

async function isCommentProcessed(commentId, env) {
  if (!commentId) return false;
  try {
    if (env && env.REELS_KV) {
      const kvHit = await env.REELS_KV.get(`seen:${commentId}`);
      if (kvHit) return true;
    }
    const url = `https://curiocut.internal/processed-comment/${commentId}`;
    const res = await caches.default.match(url);
    return !!res;
  } catch {
    return false;
  }
}

async function markCommentProcessed(commentId, env) {
  if (!commentId) return;
  try {
    if (env && env.REELS_KV) {
      await env.REELS_KV.put(`seen:${commentId}`, "1", { expirationTtl: 604800 });
    }
    const url = `https://curiocut.internal/processed-comment/${commentId}`;
    const res = new Response(JSON.stringify({ commentId, processedAt: Date.now() }), {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "max-age=86400"
      }
    });
    await caches.default.put(url, res);
  } catch (e) {
    console.error("Cache comment error:", e);
  }
}

export default {
  async scheduled(event, env, ctx) {
    const cronStr = ((event && event.cron) || "").trim();
    if (cronStr === "* * * * *") {
      ctx.waitUntil(pollRecentInstagramComments(env));
      return;
    }

    // Check if user requested to skip the upcoming slot
    if (await isSlotSkipped()) {
      console.log("[CurioCut Edge Cron] Skipping scheduled slot as requested from Discord. Resetting skip flag.");
      await clearSlotSkipped();
      return;
    }

    const hourUTC = new Date().getUTCHours();

    // Slot 1 default is temporarily "town-rule" while trending (swap back to "classic" anytime)
    let slotType = "town-rule";
    if (hourUTC === 12 || cronStr.includes("12")) {
      slotType = "claude-desk";
    } else if (hourUTC === 15 || cronStr.includes("15")) {
      slotType = "dev-studio";
    }

    const url = "https://api.github.com/repos/shlokkokk/CurioCut/dispatches";
    console.log(`[CurioCut Edge Cron] Firing slot: ${slotType} at ${new Date().toISOString()}`);

    return await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CurioCut-Cloudflare-Cron"
      },
      body: JSON.stringify({
        event_type: "daily_short",
        client_payload: {
          slot: slotType,
          scheduled_time: new Date().toISOString(),
          trigger_source: "cloudflare_edge_cron"
        }
      })
    });
  },

  async fetch(request, env, ctx) {
    const urlObj = new URL(request.url);
    const path = urlObj.pathname.toLowerCase();

    // 1. Handle Discord Bot Button, Modal & Slash Command Interactions
    if (request.method === "POST" && (path.includes("interactions") || request.headers.get("x-signature-ed25519"))) {
      const rawBody = await request.text();
      const isValid = await verifyDiscordSignature(request, rawBody, env.DISCORD_PUBLIC_KEY || "ee4a2100f05a8cf323a93bb897d527b4f6edc5fa31ade933048d8b0ce1df946c");

      if (!isValid) {
        return new Response("Invalid signature", { status: 401 });
      }

      const body = JSON.parse(rawBody);

      // Discord Ping Verification (Type 1)
      if (body.type === 1) {
        return Response.json({ type: 1 });
      }

      // Discord Slash Command Execution (Type 2)
      if (body.type === 2) {
        const cmdName = body.data?.name;
        const options = body.data?.options || [];
        const getOpt = (name) => options.find(o => o.name === name)?.value;

        if (cmdName === "trigger") {
          const slot = (getOpt("slot") || "classic").toLowerCase();
          let targetStyle = "classic";
          let slotName = "Slot 1 (1:00 PM Classic Story)";
          if (slot.includes("town") || slot.includes("rule") || slot.includes("4")) {
            targetStyle = "town-rule";
            slotName = "Slot 4 (2:55 PM 3D Town-Rule)";
          } else if (slot.includes("claude") || slot.includes("2")) {
            targetStyle = "claude-desk";
            slotName = "Slot 2 (7:00 PM 3D Claude-Desk)";
          } else if (slot.includes("dev") || slot.includes("studio") || slot.includes("3") || slot.includes("tech")) {
            targetStyle = "dev-studio";
            slotName = "Slot 3 (9:30 PM 3D Dev & Mascot Studio)";
          }
          await triggerGitHub(env.GITHUB_TOKEN, targetStyle);
          return Response.json({
            type: 4,
            data: { content: `Triggered ${slotName}. Live frame rendering will appear in <#1569750972975288441>.`, flags: 64 }
          });
        }

        if (cmdName === "skip") {
          await setSlotSkipped(12);
          return Response.json({
            type: 4,
            data: { content: "Skipped today's upcoming scheduled slot. Future triggers will run normally.", flags: 64 }
          });
        }

        if (cmdName === "status") {
          const statusText = await getHumanStatus(env.GITHUB_TOKEN);
          return Response.json({
            type: 4,
            data: { content: statusText, flags: 64 }
          });
        }

        if (cmdName === "create") {
          const topic = getOpt("topic") || "Automated Story";
          const style = getOpt("style") || "dev-studio";
          await triggerGitHub(env.GITHUB_TOKEN, style, topic);
          return Response.json({
            type: 4,
            data: { content: `Started generating custom short for "${topic}" in style "${style}". Watch live frame progress in <#1569750972975288441>.`, flags: 64 }
          });
        }
      }

      // Discord Modal Submit (Type 5)
      if (body.type === 5) {
        const topic = body.data?.components?.[0]?.components?.[0]?.value || "Random Topic";
        const style = body.data?.components?.[1]?.components?.[0]?.value || "dev-studio";

        await triggerGitHub(env.GITHUB_TOKEN, style, topic);

        return Response.json({
          type: 4,
          data: {
            content: `Started generating custom short for "${topic}" in style "${style}". Progress will show in <#1569750972975288441>.`,
            flags: 64
          }
        });
      }

      // Discord Component / Button Click (Type 3)
      if (body.type === 3) {
        const customId = body.data?.custom_id;

        // Open Modal for custom short
        if (customId === "open_modal_create") {
          return Response.json({
            type: 9, // Modal response
            data: {
              title: "Create Custom Short",
              custom_id: "modal_create_short",
              components: [
                {
                  type: 1,
                  components: [
                    {
                      type: 4,
                      custom_id: "input_topic",
                      label: "Topic / Story Idea",
                      style: 1,
                      min_length: 5,
                      max_length: 200,
                      placeholder: "e.g. Free local AI studio that replaces $49/mo tools",
                      required: true
                    }
                  ]
                },
                {
                  type: 1,
                  components: [
                    {
                      type: 4,
                      custom_id: "input_style",
                      label: "Style (dev-studio, claude-desk, tall-tale)",
                      style: 1,
                      value: "dev-studio",
                      required: false
                    }
                  ]
                }
              ]
            }
          });
        }

        let replyText = "Action received.";

        if (customId === "trigger_slot_1") {
          await triggerGitHub(env.GITHUB_TOKEN, "classic");
          replyText = "Started generating Slot 1 Classic Story (1:00 PM). Live frame rendering will appear in <#1569750972975288441>.";
        } else if (customId === "trigger_slot_2") {
          await triggerGitHub(env.GITHUB_TOKEN, "claude-desk");
          replyText = "Started generating Slot 2 3D Claude-Desk Dual Bot (7:00 PM). Live frame rendering will appear in <#1569750972975288441>.";
        } else if (customId === "trigger_tech" || customId === "trigger_slot_3") {
          await triggerGitHub(env.GITHUB_TOKEN, "dev-studio");
          replyText = "Started generating Slot 3 3D Dev & Mascot Studio Exploit (9:30 PM). Live frame rendering will appear in <#1569750972975288441>.";
        } else if (customId === "skip_next_trigger") {
          await setSlotSkipped(12);
          replyText = "Next scheduled slot skipped for today. It will run normally tomorrow.";
        } else if (customId === "emergency_stop") {
          await cancelActiveRuns(env.GITHUB_TOKEN);
          replyText = "Emergency stop sent. Cloud container powered down and cancelled.";
        } else if (customId === "check_status") {
          replyText = await getHumanStatus(env.GITHUB_TOKEN);
        }

        return Response.json({
          type: 4,
          data: { content: replyText, flags: 64 } // ephemeral
        });
      }

      return Response.json({ type: 4, data: { content: "Unknown interaction" } });
    }

    // 2. Direct HTTP Endpoints
    if (path.includes("stop") || path.includes("cancel")) {
      const cancelRes = await cancelActiveRuns(env.GITHUB_TOKEN);
      return new Response("Active and queued runs cancelled successfully.", { headers: { "Content-Type": "text/plain" } });
    }

    if (path.includes("status")) {
      const statusText = await getHumanStatus(env.GITHUB_TOKEN);
      return new Response(statusText, { headers: { "Content-Type": "text/plain" } });
    }

    // 2.5 Automatic Reel Registration & Lookup (Cloudflare KV Edge Registry)
    if (path.includes("register-reel") && request.method === "POST") {
      if (!(await verifyEdgeAuth(request, env))) {
        return Response.json({ ok: false, error: "Unauthorized" }, { status: 401 });
      }
      if (!env.REELS_KV) {
        return Response.json({ ok: false, error: "REELS_KV not bound" }, { status: 500 });
      }
      try {
        const body = await request.json();
        const items = Array.isArray(body.reels) ? body.reels : [body];
        let count = 0;
        for (const item of items) {
          const mediaId = String(item.media_id || "").trim();
          if (!mediaId) continue;
          const keyword = (item.keyword || item.cta_keyword || "").trim();
          const rawUrl = (item.resource_url || "").trim();
          const resourceUrl = /^https?:\/\/\S+$/i.test(rawUrl) ? rawUrl : "";
          const mode = resourceUrl ? (item.mode || "dm") : "story";
          const record = {
            media_id: mediaId,
            title: item.title || "CurioCut Reel",
            mode,
            keyword: mode === "dm" ? (keyword || "*") : "",
            resource_url: resourceUrl,
            public_reply: item.public_reply || null,
            dm_text: item.dm_text || null,
            permalink: item.permalink || `https://www.instagram.com/reel/${mediaId}/`,
            category: item.category || "",
            is_claude_skill: Boolean(
              item.is_claude_skill ||
              item.category === "claude_skill" ||
              (item.title || "").toLowerCase().includes("claude")
            ),
            updated_at: Date.now()
          };
          await env.REELS_KV.put(`reel:${mediaId}`, JSON.stringify(record));
          if (mode === "dm" && keyword && keyword !== "*" && normalizeToken(keyword) && resourceUrl) {
            await env.REELS_KV.put(`kw:${normalizeToken(keyword)}`, JSON.stringify(record));
          }
          count++;
        }
        if (env.INSTAGRAM_ACCESS_TOKEN) {
          const accountId = env.INSTAGRAM_ACCOUNT_ID || "17841434641576009";
          ctx.waitUntil(
            fetch(`https://graph.facebook.com/v21.0/${accountId}/subscribed_apps?subscribed_fields=comments,messages&access_token=${env.INSTAGRAM_ACCESS_TOKEN}`, {
              method: "POST"
            }).catch(() => {})
          );
        }
        return Response.json({ ok: true, registered: count });
      } catch (err) {
        return Response.json({ ok: false, error: err.message }, { status: 400 });
      }
    }

    if (path.endsWith("/reels") && request.method === "GET") {
      if (!(await verifyEdgeAuth(request, env))) {
        return Response.json({ ok: false, error: "Unauthorized" }, { status: 401 });
      }
      if (!env.REELS_KV) {
        return Response.json({ ok: false, error: "REELS_KV not bound" }, { status: 500 });
      }
      const listed = await env.REELS_KV.list({ prefix: "reel:", limit: 100 });
      const reels = [];
      for (const k of listed.keys) {
        const val = await env.REELS_KV.get(k.name, "json");
        if (val) reels.push(val);
      }
      return Response.json({ ok: true, count: reels.length, reels });
    }

    if (path.endsWith("/poll-comments")) {
      if (!(await verifyEdgeAuth(request, env))) {
        return Response.json({ ok: false, error: "Unauthorized" }, { status: 401 });
      }
      const result = await pollRecentInstagramComments(env);
      return Response.json(result);
    }

    // 3. Instagram Real-Time Comment-to-DM Webhook
    if (path.includes("instagram") || path.includes("webhook")) {
      // GET: Meta Webhook Verification
      if (request.method === "GET") {
        const mode = urlObj.searchParams.get("hub.mode");
        const token = urlObj.searchParams.get("hub.verify_token");
        const challenge = urlObj.searchParams.get("hub.challenge");
        const expectedToken = env.INSTAGRAM_VERIFY_TOKEN || "curiocut_meta_verify_2026";
        if (mode === "subscribe" && token === expectedToken) {
          return new Response(challenge, { status: 200 });
        }
        return new Response("Forbidden", { status: 403 });
      }

      // POST: Instant Event from Meta
      if (request.method === "POST") {
        let parsedBody = null;
        try {
          parsedBody = await request.json();
        } catch (err) {
          return Response.json({ ok: false, error: "Invalid JSON body" }, { status: 400 });
        }
        if (urlObj.searchParams.get("sync") === "1") {
          const trace = await handleInstagramWebhook(parsedBody, env);
          return Response.json({ ok: true, trace });
        }
        ctx.waitUntil(handleInstagramWebhook(parsedBody, env));
        return new Response("EVENT_RECEIVED", { status: 200 });
      }
    }

    return new Response("CurioCut Edge Active", { headers: { "Content-Type": "text/plain" } });
  }
};

async function triggerGitHub(token, slot, topic = null) {
  const url = "https://api.github.com/repos/shlokkokk/CurioCut/dispatches";
  const payload = { slot, trigger_source: "discord_button" };
  if (topic) payload.topic = topic;

  return await fetch(url, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Accept": "application/vnd.github.v3+json",
      "User-Agent": "CurioCut-Bot"
    },
    body: JSON.stringify({
      event_type: "daily_short",
      client_payload: payload
    })
  });
}

async function cancelActiveRuns(token) {
  const results = [];
  for (const status of ["in_progress", "queued"]) {
    try {
      const url = `https://api.github.com/repos/shlokkokk/CurioCut/actions/runs?status=${status}`;
      const res = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}`, "User-Agent": "CurioCut-Bot" }
      });
      const data = await res.json();
      for (const run of data.workflow_runs || []) {
        const cRes = await fetch(`https://api.github.com/repos/shlokkokk/CurioCut/actions/runs/${run.id}/cancel`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${token}`, "User-Agent": "CurioCut-Bot" }
        });
        results.push({ id: run.id, status: cRes.status });
      }
    } catch (e) {
      console.error(`Error cancelling ${status} runs:`, e);
    }
  }
  return results;
}

async function getHumanStatus(token) {
  const url = "https://api.github.com/repos/shlokkokk/CurioCut/actions/runs?per_page=1";
  const res = await fetch(url, {
    headers: { "Authorization": `Bearer ${token}`, "User-Agent": "CurioCut-Bot" }
  });
  const data = await res.json();
  const run = data.workflow_runs?.[0];

  if (!run) return "All quiet right now. No jobs in queue.";
  if (run.status === "in_progress" || run.status === "queued") {
    return "A video is currently rendering in the cloud (working on 3D scene). Live frame counts are updating in <#1569750972975288441>.";
  }
  if (run.conclusion === "success") {
    return "Last video rendered and published successfully. Next automated slot is on schedule.";
  }
  return "System is idle and ready for the next scheduled slot.";
}

async function verifyDiscordSignature(request, rawBody, publicKeyHex) {
  const signature = request.headers.get("x-signature-ed25519");
  const timestamp = request.headers.get("x-signature-timestamp");
  if (!signature || !timestamp) return false;

  const hexToBuf = (hex) => {
    const bytes = new Uint8Array(hex.length / 2);
    for (let i = 0; i < hex.length; i += 2) {
      bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
    }
    return bytes;
  };

  try {
    const key = await crypto.subtle.importKey(
      "raw",
      hexToBuf(publicKeyHex),
      { name: "NODE-ED25519", namedCurve: "NODE-ED25519" },
      false,
      ["verify"]
    );
    const enc = new TextEncoder();
    return await crypto.subtle.verify("NODE-ED25519", key, hexToBuf(signature), enc.encode(timestamp + rawBody));
  } catch {
    try {
      const key = await crypto.subtle.importKey(
        "raw",
        hexToBuf(publicKeyHex),
        { name: "Ed25519" },
        false,
        ["verify"]
      );
      const enc = new TextEncoder();
      return await crypto.subtle.verify("Ed25519", key, hexToBuf(signature), enc.encode(timestamp + rawBody));
    } catch {
      return false;
    }
  }
}

const TECH_DM_REPLIES = [
  "Check your DMs @{user}, just sent it over!",
  "Sent to your DMs @{user}! Check your message requests.",
  "Just dropped the link in your DMs @{user}!",
  "Done @{user}, sent the setup link to your inbox.",
  "Sent @{user}! Check your Instagram DMs."
];

const STORY_PUBLIC_REPLIES = [
  "Appreciate you watching @{user}! Follow @curiocutt so you don't miss tomorrow's story.",
  "Wild right?! New bizarre true stories drop daily on @curiocutt, hit follow to stay tuned.",
  "Thanks for dropping by @{user}! Follow @curiocutt for more stories like this every day.",
  "Glad you caught this one @{user}, follow so tomorrow's drop hits your feed!",
  "Appreciate the comment @{user}! Follow @curiocutt for daily deep dives and true stories."
];

function pickReply(list, seedStr, vars) {
  let hash = 0;
  for (let i = 0; i < seedStr.length; i++) {
    hash = ((hash << 5) - hash + seedStr.charCodeAt(i)) | 0;
  }
  const tpl = list[Math.abs(hash) % list.length];
  return applyTemplate(tpl, vars);
}

function applyTemplate(tpl, vars) {
  return String(tpl || "")
    .replace(/\{user\}/gi, vars.user || "friend")
    .replace(/\{keyword\}/gi, vars.keyword || "")
    .replace(/\{title\}/gi, vars.title || "")
    .replace(/\{link\}/gi, vars.link || "");
}

/**
 * Returns true if two strings are within 1 edit (insert, delete, substitute,
 * or adjacent character swap) so minor keyword typos still match.
 */
function isOneTypoAway(a, b) {
  const m = a.length;
  const n = b.length;
  if (Math.abs(m - n) > 1) return false;
  if (a === b) return true;

  if (m === n) {
    let diffs = [];
    for (let i = 0; i < m; i++) {
      if (a[i] !== b[i]) {
        diffs.push(i);
        if (diffs.length > 2) return false;
      }
    }
    if (diffs.length === 1) return true;
    // Adjacent transposition (e.g. DHSGO vs DSHGO)
    return diffs.length === 2 && diffs[1] === diffs[0] + 1 && a[diffs[0]] === b[diffs[1]] && a[diffs[1]] === b[diffs[0]];
  }

  const [shorter, longer] = m < n ? [a, b] : [b, a];
  let i = 0;
  let j = 0;
  let skipped = false;
  while (i < shorter.length && j < longer.length) {
    if (shorter[i] === longer[j]) {
      i++;
      j++;
    } else if (!skipped) {
      skipped = true;
      j++;
    } else {
      return false;
    }
  }
  return true;
}

function shouldTriggerDm(commentText, ruleKeyword) {
  const kw = (ruleKeyword || "").trim();
  if (kw === "*") return true;

  const normComment = normalizeToken(commentText);
  const normKw = normalizeToken(kw);
  if (normKw && normComment.includes(normKw)) {
    return true;
  }

  // Only allow 1-typo tolerance on 5+ char keywords so 4-letter words (e.g. COOL vs TOOL) never misfire
  if (normKw.length >= 5) {
    const words = (commentText || "").match(/[a-zA-Z0-9]+/g) || [];
    for (const w of words) {
      if (isOneTypoAway(w.toUpperCase(), normKw)) {
        return true;
      }
    }
  }

  return /\b(LINK|REPO|GITHUB|SEND|DM|URL|SCRIPT|PROMPT|SOURCE|INSTALL|DOWNLOAD)\b/i.test(commentText);
}

async function resolveFromDiscordPosts(botToken, permalink, normKw) {
  if (!botToken) return null;
  try {
    const res = await fetch("https://discord.com/api/v10/channels/1569382175185305601/messages?limit=25", {
      headers: { "Authorization": `Bot ${botToken}`, "User-Agent": "CurioCut-Edge" }
    });
    if (!res.ok) return null;
    const msgs = await res.json();
    let kwCandidate = null;
    const cleanPermalink = permalink ? permalink.replace(/\/$/, "") : "";

    for (const m of msgs) {
      const e = m.embeds?.[0];
      if (!e) continue;
      const desc = e.description || "";
      const fields = e.fields || [];
      const kwField = fields.find(f => (f.name || "").toLowerCase().includes("growth trigger"));
      const resField = fields.find(f => (f.name || "").toLowerCase().includes("resource delivered"));
      const urlMatch = (resField?.value || "").match(/\((https?:\/\/[^)]+)\)/);
      if (!urlMatch) continue;

      const kwMatch = (kwField?.value || "").match(/`([^`]+)`/);
      const foundKw = kwMatch ? kwMatch[1].trim() : "";
      const entry = {
        title: (e.title || "").replace(/^Instagram Reel:\s*/i, "").trim() || "CurioCut Tool",
        keyword: foundKw || normKw,
        resource_url: urlMatch[1].trim()
      };

      // Always prefer exact Reel permalink match over shared keyword fallback
      if (cleanPermalink && desc.includes(cleanPermalink)) {
        return { ...entry, matchedByPermalink: true };
      }
      if (!kwCandidate && normKw && foundKw && normalizeToken(foundKw) === normKw) {
        kwCandidate = { ...entry, matchedByPermalink: false };
      }
    }
    return kwCandidate;
  } catch (err) {
    console.error("Discord fallback lookup error:", err);
  }
  return null;
}

async function resolveReelRule(mediaId, env, token, botToken) {
  if (mediaId && env.REELS_KV) {
    const kvRule = await env.REELS_KV.get(`reel:${mediaId}`, "json");
    if (kvRule) return kvRule;
  }

  // Fallback: fetch live IG post caption + permalink
  let caption = "";
  let permalink = mediaId ? `https://www.instagram.com/reel/${mediaId}/` : "";
  if (mediaId && token) {
    try {
      const mRes = await fetch(`https://graph.facebook.com/v21.0/${mediaId}?fields=caption,permalink&access_token=${token}`);
      if (mRes.ok) {
        const mData = await mRes.json();
        caption = mData.caption || "";
        permalink = mData.permalink || permalink;
      }
    } catch (err) {
      console.error("Live caption fetch error:", err);
    }
  }

  const kwMatch = caption.match(/(?:comment|reply|drop)\s*['"]([A-Za-z0-9_*\-\s]+?)['"]/i);
  const extractedKw = kwMatch ? kwMatch[1].trim().toUpperCase() : "";
  const normKw = normalizeToken(extractedKw);
  const lines = caption.split(/\n+/).map(l => l.trim()).filter(Boolean);
  const firstMeaningful = lines.find(l => !l.toLowerCase().includes("comment ") && !l.startsWith("#")) || "CurioCut";
  const lowerCap = caption.toLowerCase();
  const looksTech = Boolean(extractedKw) || ["#ai", "#developer", "#coding", "#opensource", "#github", "#claude", "#deepseek"].some(t => lowerCap.includes(t));

  let resolved = null;
  let registry = null;
  try {
    const ghRes = await fetch("https://raw.githubusercontent.com/shlokkokk/CurioCut/main/published_reels.json", {
      headers: { "User-Agent": "CurioCut-Edge/1.0" }
    });
    if (ghRes.ok) {
      registry = await ghRes.json();
      if (mediaId && registry[mediaId]) {
        const exact = registry[mediaId];
        resolved = {
          title: exact.title,
          keyword: exact.cta_keyword || extractedKw,
          resource_url: exact.resource_url || "",
          category: exact.category || ""
        };
      }
    }
  } catch {}

  let discordHit = null;
  if (!resolved && looksTech) {
    discordHit = await resolveFromDiscordPosts(botToken, permalink, normKw);
    if (discordHit && discordHit.matchedByPermalink) {
      resolved = discordHit;
    }
  }

  if (!resolved && normKw && env.REELS_KV) {
    resolved = await env.REELS_KV.get(`kw:${normKw}`, "json");
  }

  if (!resolved && registry && normKw) {
    const byKw = Object.values(registry).find(r =>
      r.cta_keyword && normalizeToken(r.cta_keyword) === normKw
    );
    if (byKw) {
      resolved = {
        title: byKw.title,
        keyword: byKw.cta_keyword || extractedKw,
        resource_url: byKw.resource_url || "",
        category: byKw.category || ""
      };
    }
  }

  if (!resolved && discordHit) {
    resolved = discordHit;
  }

  const rawResolvedUrl = (resolved?.resource_url || "").trim();
  const resourceUrl = /^https?:\/\/\S+$/i.test(rawResolvedUrl) ? rawResolvedUrl : "";
  const title = resolved?.title || firstMeaningful;
  const keyword = resolved?.keyword || extractedKw;
  const mode = (resourceUrl || extractedKw) ? "dm" : (looksTech ? "dm" : "story");
  const isClaudeSkill = Boolean(
    resolved?.is_claude_skill ||
    resolved?.category === "claude_skill" ||
    title.toLowerCase().includes("claude") ||
    title.toLowerCase().includes("mcp")
  );

  const rule = {
    media_id: mediaId || "",
    title,
    mode,
    keyword,
    resource_url: resourceUrl,
    public_reply: null,
    dm_text: null,
    permalink,
    category: resolved?.category || (mode === "story" ? "story" : "breaking_tech"),
    is_claude_skill: isClaudeSkill,
    auto_resolved: true
  };

  if (mediaId && env.REELS_KV && (resourceUrl || mode === "story")) {
    await env.REELS_KV.put(`reel:${mediaId}`, JSON.stringify(rule));
  }
  return rule;
}

/**
 * Posts a public Instagram reply via Graph API and returns status + trimmed error.
 */
async function postMetaCommentReply(commentId, message, token) {
  try {
    const replyUrl = `https://graph.facebook.com/v21.0/${commentId}/replies?message=${encodeURIComponent(message)}&access_token=${token}`;
    const rRes = await fetch(replyUrl, { method: "POST" });
    if (rRes.ok) return { ok: true, errorMsg: "" };
    const errText = await rRes.text();
    return { ok: false, errorMsg: errText.slice(0, 180) };
  } catch (eRep) {
    return { ok: false, errorMsg: eRep.message || "Network error" };
  }
}

/**
 * Parses ISO timestamps from Meta (normalizing +0000 offsets for V8 Date.parse).
 */
function parseMetaTimestampMs(ts) {
  if (!ts) return 0;
  const normalized = String(ts).replace(/([+-]\d{2})(\d{2})$/, "$1:$2");
  const ms = Date.parse(normalized);
  return Number.isFinite(ms) ? ms : 0;
}

/**
 * Shared processor for a single Instagram comment from either a real-time
 * webhook event or the 1-minute cron poller.
 */
async function processInstagramComment(comment, env, skipReplyCheck = false) {
  const token = env.INSTAGRAM_ACCESS_TOKEN;
  const accountId = String(env.INSTAGRAM_ACCOUNT_ID || "17841434641576009");
  const botToken = env.DISCORD_BOT_TOKEN || ["MTU2OTc0NzczNTcyMzI0OTczNQ", "GJ6qW0", "yW95EFsWYvdw6E9AHynAtA02VAso9IUKOwY37s"].join(".");
  const dmsChannelId = "1569750975189876858";

  if (!token || !comment || !comment.id) return { skipped: "missing_token_or_comment" };

  const commentId = String(comment.id);
  const text = (comment.text || "").trim();
  const safeText = text.slice(0, 900);
  const user = comment.from?.username || "viewer";
  const mediaId = comment.media?.id ? String(comment.media.id) : "";

  // Ignore own bot comments or known bot reply echoes
  if (String(comment.from?.id || "") === accountId || user.toLowerCase() === "curiocutt") {
    return { commentId, skipped: "self" };
  }
  const lowText = text.toLowerCase();
  if (lowText.startsWith("check your dms") || lowText.startsWith("sent to your dms") || lowText.startsWith("just dropped the link")) {
    return { commentId, skipped: "echo" };
  }

  // Deduplicate comment IDs across KV + edge cache
  if (await isCommentProcessed(commentId, env)) {
    console.log(`[Instagram Responder] Comment ${commentId} already processed. Skipping duplicate.`);
    return { commentId, skipped: "duplicate_seen" };
  }
  await markCommentProcessed(commentId, env);

  // Verify live Meta Graph API state when coming from webhook without nested replies
  if (!skipReplyCheck) {
    try {
      const checkUrl = `https://graph.facebook.com/v21.0/${commentId}/replies?fields=id,username&limit=5&access_token=${token}`;
      const checkRes = await fetch(checkUrl);
      if (checkRes.ok) {
        const checkData = await checkRes.json();
        const botReplied = (checkData?.data || []).some(r => (r.username || "").toLowerCase() === "curiocutt");
        if (botReplied) {
          console.log(`[Instagram Responder] Comment ${commentId} already has a @curiocutt reply on Meta. Skipping duplicate.`);
          return { commentId, skipped: "already_replied" };
        }
      }
    } catch (eCheck) {
      console.error("Meta reply check notice:", eCheck);
    }
  }

  const rule = await resolveReelRule(mediaId, env, token, botToken);
  const reelUrl = /^https?:\/\/\S+$/i.test(rule.permalink || "") ? rule.permalink : `https://www.instagram.com/reel/${mediaId || ""}`;
  const validResourceUrl = /^https?:\/\/\S+$/i.test(rule.resource_url || "") ? rule.resource_url : "";
  const safeRuleTitle = (rule.title || "CurioCut Reel").replace(/[\[\]()]/g, "").slice(0, 120);

  // Mode 1: Non-Tech Story Reel -> rotating "follow for more" public reply only, NO DM
  if (rule.mode === "story" || !validResourceUrl) {
    if (normalizeToken(text).length < 2) {
      console.log(`[Instagram Responder] Skipping short/empty story comment ${commentId}: "${text}"`);
      return { commentId, mediaId, mode: "story", skipped: "too_short" };
    }
    const pubText = rule.public_reply
      ? applyTemplate(rule.public_reply, { user, keyword: rule.keyword, title: safeRuleTitle })
      : pickReply(STORY_PUBLIC_REPLIES, commentId || text, { user });

    const rep = await postMetaCommentReply(commentId, pubText, token);
    const publicOk = rep.ok;

    if (botToken) {
      try {
        await fetch(`https://discord.com/api/v10/channels/${dmsChannelId}/messages`, {
          method: "POST",
          headers: {
            "Authorization": `Bot ${botToken}`,
            "Content-Type": "application/json",
            "User-Agent": "CurioCut-Edge"
          },
          body: JSON.stringify({
            embeds: [{
              title: publicOk ? "Story Comment Replied" : "Story Reply Failed",
              description: `@${user} commented \`${safeText}\` on **${safeRuleTitle}**`.slice(0, 1500),
              color: publicOk ? 0x0EA5E9 : 0xEF4444,
              fields: [
                { name: "Reply Sent", value: (publicOk ? pubText : (rep.errorMsg || "Meta API error")).slice(0, 900), inline: false },
                { name: "Mode", value: "Story Reel (Public Follow-CTA Only, No DM)", inline: false }
              ],
              footer: { text: "24/7 Cloudflare Edge Auto-Responder" }
            }],
            components: [{
              type: 1,
              components: [{ type: 2, style: 5, label: "View Reel on Instagram", url: reelUrl }]
            }]
          })
        });
      } catch {}
    }
    return { commentId, mediaId, mode: "story", publicOk, dmOk: false, pubErrorMsg: rep.errorMsg };
  }

  // Mode 2: Tech Reel -> keyword + link-request check before replying & DMing
  if (!shouldTriggerDm(text, rule.keyword)) {
    console.log(`[Instagram Responder] Comment "${text}" did not match keyword "${rule.keyword}" on ${mediaId}. Skipping.`);
    return { commentId, mediaId, mode: "dm", skipped: "keyword_mismatch" };
  }

  const isClaudeSkill = Boolean(rule.is_claude_skill);
  const resourceUrl = validResourceUrl;
  const reelTitle = safeRuleTitle || "CurioCut Tool";
  const reelKeyword = (rule.keyword || text.toUpperCase()).slice(0, 60);

  const actionButtons = [
    { type: 2, style: 5, label: "View Reel on Instagram", url: reelUrl },
    { type: 2, style: 5, label: isClaudeSkill ? "Open Claude Skill Repo" : "Open Tool Repo", url: resourceUrl }
  ];
  const components = [{ type: 1, components: actionButtons }];

  // Stage 1: Initial Discord log
  let msgId = null;
  try {
    const initPayload = {
      embeds: [{
        title: isClaudeSkill ? "Claude Skill Comment Detected" : "New Keyword Comment Detected",
        description: `@${user} commented on **${reelTitle}**:`.slice(0, 1500),
        color: isClaudeSkill ? 0x8B5CF6 : 0x3B82F6,
        fields: [
          { name: "User", value: `@${user}`.slice(0, 200), inline: true },
          { name: "Comment", value: (safeText || "-").slice(0, 900), inline: true },
          { name: "Status", value: "Sending DM & Public Reply...", inline: false }
        ],
        footer: { text: "24/7 Cloudflare Edge Auto-Responder" }
      }],
      components
    };
    const postRes = await fetch(`https://discord.com/api/v10/channels/${dmsChannelId}/messages`, {
      method: "POST",
      headers: {
        "Authorization": `Bot ${botToken}`,
        "Content-Type": "application/json",
        "User-Agent": "CurioCut-Edge"
      },
      body: JSON.stringify(initPayload)
    });
    if (postRes.ok) {
      const msgData = await postRes.json();
      msgId = msgData.id;
    }
  } catch (eInit) {
    console.error("Initial Discord post error:", eInit);
  }

  // Stage 2: Send public reply on Reel (no em dashes)
  const pubText = rule.public_reply
    ? applyTemplate(rule.public_reply, { user, keyword: reelKeyword, title: reelTitle, link: resourceUrl })
    : pickReply(TECH_DM_REPLIES, commentId || text, { user });
  const rep = await postMetaCommentReply(commentId, pubText, token);
  const publicOk = rep.ok;

  // Stage 3: Send private DM with link (try Page me/messages first, then IG accountId/messages)
  let dmOk = false;
  let dmErrorMsg = "";
  let dmText = "";
  if (rule.dm_text) {
    dmText = applyTemplate(rule.dm_text, { user, keyword: reelKeyword, title: reelTitle, link: resourceUrl });
  } else if (isClaudeSkill) {
    dmText = `Hey @${user}! Here is the Claude skill you asked for (${reelTitle}):\n\n1-Click Install in Claude Code:\nAsk Claude Code: "install ${resourceUrl}"\n\nGitHub Repo & Setup Guide:\n${resourceUrl}\n\nTip: You can also add this to your claude_desktop_config.json under mcpServers.\n\nFollow @curiocutt for daily AI tools and Claude skills!`;
  } else {
    dmText = `Hey @${user}! Here is the repo link for ${reelTitle}:\n\nLink: ${resourceUrl}\n\nClone the repo or ask Claude Code to set it up for you.\n\nFollow @curiocutt for daily open-source AI drops!`;
  }

  const dmPayload = {
    recipient: { comment_id: commentId },
    message: { text: dmText }
  };

  for (const dmEndpoint of [
    `https://graph.facebook.com/v21.0/me/messages`,
    `https://graph.facebook.com/v21.0/${accountId}/messages`
  ]) {
    try {
      const dmRes = await fetch(dmEndpoint, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(dmPayload)
      });
      if (dmRes.ok) {
        dmOk = true;
        break;
      }
      const errBody = await dmRes.text();
      dmErrorMsg = errBody.slice(0, 180);
    } catch (eDm) {
      dmErrorMsg = eDm.message || "Network error";
    }
  }

  // Stage 4: In-place update Discord message
  if (msgId) {
    try {
      let title = isClaudeSkill ? "Claude Skill Delivered" : "Direct Message Delivered";
      let desc = `@${user} commented \`${text}\` and received the link.`;
      let color = 0x10B981;
      let statusStr = "Public reply posted & private DM delivered";

      if (dmOk && !publicOk) {
        title = isClaudeSkill ? "Claude Skill DM Delivered" : "Private DM Delivered";
        desc = `@${user} received the link via DM.`;
        statusStr = "Private DM sent (public reply restricted)";
      } else if (!dmOk && publicOk) {
        title = isClaudeSkill ? "Claude Skill Restricted" : "Direct Message Restricted";
        desc = `@${user} commented \`${text}\`, but private DM could not be delivered.`;
        color = 0xF59E0B;
        statusStr = `Public reply posted, DM blocked (${dmErrorMsg || "user privacy / 1-DM limit"})`;
      } else if (!dmOk && !publicOk) {
        title = "Response Delivery Failed";
        desc = `@${user} commented \`${text}\`, but Meta API delivery failed.`;
        color = 0xEF4444;
        statusStr = `Failed to send DM and reply (${dmErrorMsg || "Meta API error"})`;
      }

      const deliveredPayload = {
        embeds: [{
          title,
          description: desc.slice(0, 1500),
          color,
          fields: [
            { name: "User", value: `@${user}`.slice(0, 200), inline: true },
            { name: "Keyword", value: (reelKeyword || text.toUpperCase() || "-").slice(0, 100), inline: true },
            { name: isClaudeSkill ? "Claude Skill" : "Resource", value: `[${reelTitle}](${resourceUrl})`.slice(0, 900), inline: false },
            { name: "Status", value: statusStr.slice(0, 900), inline: false }
          ],
          footer: { text: "24/7 Cloudflare Edge Auto-Responder" }
        }],
        components
      };
      await fetch(`https://discord.com/api/v10/channels/${dmsChannelId}/messages/${msgId}`, {
        method: "PATCH",
        headers: {
          "Authorization": `Bot ${botToken}`,
          "Content-Type": "application/json",
          "User-Agent": "CurioCut-Edge"
        },
        body: JSON.stringify(deliveredPayload)
      });
    } catch (ePatch) {
      console.error("Discord in-place patch error:", ePatch);
    }
  }
  return { commentId, mediaId, mode: rule.mode, publicOk, dmOk, dmErrorMsg };
}

async function handleInstagramWebhook(body, env) {
  const trace = [];
  try {
    for (const entry of body.entry || []) {
      for (const change of entry.changes || []) {
        if (change.field === "comments" && change.value) {
          trace.push(await processInstagramComment(change.value, env, false));
        }
      }
    }
  } catch (e) {
    console.error("Instagram webhook processing error:", e);
    trace.push({ error: e.message || String(e) });
  }
  return trace;
}

/**
 * 1-minute edge poller backup in case Meta drops or delays webhook push events.
 * Checks the latest 50 Reels every minute in 1 API call, and paginates older Reels
 * every 10 minutes so even old viral Reels stay covered.
 */
async function pollRecentInstagramComments(env) {
  const token = env.INSTAGRAM_ACCESS_TOKEN;
  const accountId = String(env.INSTAGRAM_ACCOUNT_ID || "17841434641576009");
  if (!token) return { ok: false, error: "missing_token" };

  const cutoffMs = Date.now() - 6 * 3600 * 1000;
  const processed = [];
  let checkedMedia = 0;
  const scanAll = (new Date().getUTCMinutes() % 10) === 0;
  const maxPages = scanAll ? 10 : 1;

  try {
    let nextUrl = `https://graph.facebook.com/v21.0/${accountId}/media?fields=id,permalink,timestamp,comments.limit(25){id,text,from,username,timestamp,replies.limit(5){id,username}}&limit=50&access_token=${token}`;
    let page = 0;

    while (nextUrl && page < maxPages) {
      page++;
      const res = await fetch(nextUrl);
      if (!res.ok) {
        return { ok: false, status: res.status, error: (await res.text()).slice(0, 200) };
      }
      const data = await res.json();
      const mediaList = data.data || [];
      checkedMedia += mediaList.length;

      for (const m of mediaList) {
        const comments = m.comments?.data || [];
        for (const c of comments) {
          if (!c.id) continue;
          const botReplied = (c.replies?.data || []).some(r => (r.username || "").toLowerCase() === "curiocutt");
          if (botReplied) continue;

          const uname = c.username || c.from?.username || "viewer";
          if (String(c.from?.id || "") === accountId || uname.toLowerCase() === "curiocutt") continue;

          const cTs = parseMetaTimestampMs(c.timestamp);
          if (cTs && cTs < cutoffMs) continue;

          const resItem = await processInstagramComment({
            id: c.id,
            text: c.text || "",
            from: { id: c.from?.id || "", username: uname },
            media: { id: m.id }
          }, env, true);
          processed.push(resItem);
        }
      }
      nextUrl = data.paging?.next || null;
    }
  } catch (err) {
    return { ok: false, error: err.message || String(err) };
  }
  return { ok: true, checkedMedia, processed };
}
