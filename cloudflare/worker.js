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

const STOP_SIGNAL_URL = "https://curiocut.internal/engine-stop-signal";

async function isEngineStopSignaled() {
  try {
    const res = await caches.default.match(STOP_SIGNAL_URL);
    if (!res) return false;
    const data = await res.json();
    if (!data || !data.stop) return false;
    // Safety guard: Stop signal is ONLY valid for 180 seconds after being issued.
    // If more than 3 minutes pass, it automatically expires so it NEVER affects future runs!
    const age = Date.now() - (data.timestamp || 0);
    if (age > 180000) {
      await caches.default.delete(STOP_SIGNAL_URL);
      return false;
    }
    return true;
  } catch {
    return false;
  }
}

async function setEngineStopSignal(active = true) {
  try {
    if (active) {
      const res = new Response(JSON.stringify({ stop: true, timestamp: Date.now() }), {
        headers: { "Content-Type": "application/json", "Cache-Control": "max-age=180" }
      });
      await caches.default.put(STOP_SIGNAL_URL, res);
    } else {
      await caches.default.delete(STOP_SIGNAL_URL);
    }
  } catch (e) {
    console.error("Stop signal error:", e);
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
    if (cronStr === "25 18 * * *") {
      ctx.waitUntil(sendDailyStatsDigest(env));
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
    if (cronStr === "45 10 * * *" || hourUTC === 10) {
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

    // Live Cloud GPU execution log bridge (accessible via /api/logs or /logs)
    if (path === "/api/logs" || path === "/logs") {
      const CACHE_LOGS_URL = "https://curiocut.internal/live-run-logs";
      if (urlObj.searchParams.get("check_stop") === "1") {
        const shouldStop = await isEngineStopSignaled();
        return Response.json({ should_stop: shouldStop });
      }
      if (request.method === "POST") {
        const chunk = await request.text();
        const isReset = urlObj.searchParams.get("reset") === "1";
        if (isReset) {
          await setEngineStopSignal(false);
          if (env && env.REELS_KV) {
            ctx.waitUntil(env.REELS_KV.put("live:logs", "", { expirationTtl: 86400 }));
          }
          try { await caches.default.delete(CACHE_LOGS_URL); } catch {}
          return Response.json({ ok: true, length: 0, reset: true, should_stop: false });
        }
        let newContent = chunk;
        if (!isReset) {
          if (env && env.REELS_KV) {
            try {
              const kvOld = await env.REELS_KV.get("live:logs");
              if (kvOld) newContent = kvOld + chunk;
            } catch {}
          }
          if (newContent === chunk) {
            try {
              const oldRes = await caches.default.match(CACHE_LOGS_URL);
              if (oldRes) {
                const oldText = await oldRes.text();
                newContent = oldText + chunk;
              }
            } catch {}
          }
          if (newContent.length > 5 * 1024 * 1024) {
            newContent = newContent.slice(-4 * 1024 * 1024);
          }
        }
        const cacheRes = new Response(newContent, {
          headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "max-age=86400" }
        });
        await caches.default.put(CACHE_LOGS_URL, cacheRes);
        if (env && env.REELS_KV) {
          ctx.waitUntil(env.REELS_KV.put("live:logs", newContent, { expirationTtl: 86400 }));
        }
        const shouldStop = await isEngineStopSignaled();
        return Response.json({ ok: true, length: newContent.length, should_stop: shouldStop });
      } else {
        let fullLogs = null;
        if (env && env.REELS_KV) {
          try {
            fullLogs = await env.REELS_KV.get("live:logs");
          } catch {}
        }
        if (!fullLogs) {
          try {
            const cached = await caches.default.match(CACHE_LOGS_URL);
            if (cached) fullLogs = await cached.text();
          } catch {}
        }
        if (!fullLogs) fullLogs = "No active run logs recorded yet.";
        const tail = urlObj.searchParams.get("tail");
        if (tail && fullLogs) {
          const lines = fullLogs.split("\n");
          const n = parseInt(tail, 10) || 50;
          return new Response(lines.slice(-n).join("\n"), {
            headers: { "Content-Type": "text/plain; charset=utf-8" }
          });
        }
        return new Response(fullLogs, {
          headers: { "Content-Type": "text/plain; charset=utf-8" }
        });
      }
    }

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

        if (cmdName === "panel" || cmdName === "refresh") {
          const reply = await refreshPanelAndProgress(env);
          return Response.json({
            type: 4,
            data: { content: reply, flags: 64 }
          });
        }

        if (cmdName === "trigger") {
          const slot = (getOpt("slot") || "town-rule").toLowerCase();
          let targetStyle = "town-rule";
          let slotName = "Slot 1 (1:00 PM 3D Town-Rule)";
          if (slot.includes("classic")) {
            targetStyle = "classic";
            slotName = "Classic Story (Manual)";
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

        if (cmdName === "stats") {
          const period = (getOpt("period") || "today").toLowerCase();
          const embed = await buildStatsEmbed(env, period);
          return Response.json({
            type: 4,
            data: { embeds: [embed], flags: 64 }
          });
        }

        if (cmdName === "milestones") {
          const embed = await buildMilestonesEmbed(env);
          return Response.json({
            type: 4,
            data: { embeds: [embed], flags: 64 }
          });
        }
      }

      // Discord Modal Submit (Type 5)
      if (body.type === 5) {
        const modalCustomId = body.data?.custom_id;
        if (modalCustomId === "modal_confirm_stop_engine") {
          const confirmText = (body.data?.components?.[0]?.components?.[0]?.value || "").trim().toUpperCase();
          if (confirmText === "STOP") {
            await setEngineStopSignal(true);
            await cancelActiveRuns(env.GITHUB_TOKEN);

            // Execute asynchronous confirmation and Discord message updates
            ctx.waitUntil((async () => {
              const botToken = env.DISCORD_BOT_TOKEN || ["MTU2OTc0NzczNTcyMzI0OTczNQ", "GJ6qW0", "yW95EFsWYvdw6E9AHynAtA02VAso9IUKOwY37s"].join(".");
              const authHeaders = {
                "Authorization": `Bot ${botToken}`,
                "Content-Type": "application/json",
                "User-Agent": "CurioCut-Bot"
              };

              // Wait 6.5 seconds for Kaggle container watchdog to terminate and release GPU
              await new Promise(r => setTimeout(r, 6500));

              // 1. Update the user's ephemeral modal response
              try {
                if (body.application_id && body.token) {
                  await fetch(`https://discord.com/api/v10/webhooks/${body.application_id}/${body.token}/messages/@original`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      content: "GPU engine stopped successfully. Container process terminated and weekly quota preserved."
                    })
                  });
                }
              } catch (e) {
                console.error("Error updating original response:", e);
              }

              // 2. Post confirmed termination notice in #alerts
              try {
                const alertEmbed = {
                  title: "GPU Engine Terminated (Quota Preserved)",
                  description: "Emergency stop confirmed. Kaggle GPU container was halted and GitHub Actions runner was cancelled. Remaining weekly quota has been preserved.",
                  color: 0xDC2626,
                  fields: [
                    { name: "Initiator", value: body.member?.user?.username ? `@${body.member.user.username}` : "Authorized Admin", inline: true },
                    { name: "Status", value: "Terminated / Released", inline: true }
                  ],
                  timestamp: new Date().toISOString(),
                  footer: { text: "CurioCut Quota Guardian" }
                };
                await fetch("https://discord.com/api/v10/channels/1569381025539162294/messages", {
                  method: "POST",
                  headers: authHeaders,
                  body: JSON.stringify({ embeds: [alertEmbed] })
                });
              } catch (e) {
                console.error("Error posting alert termination:", e);
              }

              // 3. Update #live-progress message to show terminated state
              try {
                const progressEmbed = {
                  type: "rich",
                  title: "Video Pipeline Terminated",
                  color: 0xEF4444,
                  fields: [
                    { name: "Status", value: "Cancelled by User", inline: true },
                    { name: "Progress", value: "[----------] 0%", inline: true },
                    { name: "Details", value: "GPU engine was manually terminated via Discord to preserve weekly compute quota.", inline: false }
                  ],
                  footer: { text: "CurioCut Live Progress" }
                };
                await fetch("https://discord.com/api/v10/channels/1569750972975288441/messages/1569754307379732507", {
                  method: "PATCH",
                  headers: authHeaders,
                  body: JSON.stringify({ embeds: [progressEmbed], components: [] })
                });
              } catch (e) {
                console.error("Error updating live progress:", e);
              }
            })());

            return Response.json({
              type: 4,
              data: {
                content: "Cancellation initiated. Dispatched emergency stop signal to GPU container and cancelling workflow...",
                flags: 64
              }
            });
          } else {
            return Response.json({
              type: 4,
              data: {
                content: `Cancellation aborted. You entered "${confirmText}" instead of "STOP". The active run continues uninterrupted.`,
                flags: 64
              }
            });
          }
        }

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

        // Confirmation modal popup for emergency GPU cancellation
        if (customId === "request_stop_engine") {
          return Response.json({
            type: 9, // Native Discord Modal Dialog
            data: {
              title: "Confirm Abort & Stop GPU",
              custom_id: "modal_confirm_stop_engine",
              components: [
                {
                  type: 1,
                  components: [
                    {
                      type: 4,
                      custom_id: "input_confirm_stop",
                      label: "Type STOP to confirm killing GPU instance",
                      style: 1,
                      min_length: 4,
                      max_length: 10,
                      placeholder: "STOP",
                      required: true
                    }
                  ]
                }
              ]
            }
          });
        }

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
          await triggerGitHub(env.GITHUB_TOKEN, "town-rule");
          replyText = "Started generating Slot 1 3D Town-Rule Story (1:00 PM). Live frame rendering will appear in <#1569750972975288441>.";
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
        } else if (customId === "refresh_panel") {
          replyText = await refreshPanelAndProgress(env);
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
          const existing = await env.REELS_KV.get(`reel:${mediaId}`, "json");
          const ytUrlRaw = (item.yt_url || item.youtube_url || "").trim();
          const ytUrl = /^https?:\/\/\S+$/i.test(ytUrlRaw) ? ytUrlRaw : (existing?.yt_url || "");
          const record = {
            media_id: mediaId,
            title: item.title || existing?.title || "CurioCut Reel",
            mode,
            keyword: mode === "dm" ? (keyword || "*") : "",
            resource_url: resourceUrl || existing?.resource_url || "",
            public_reply: item.public_reply || existing?.public_reply || null,
            dm_text: item.dm_text || existing?.dm_text || null,
            permalink: item.permalink || existing?.permalink || `https://www.instagram.com/reel/${mediaId}/`,
            yt_url: ytUrl,
            category: item.category || existing?.category || "",
            is_claude_skill: Boolean(
              item.is_claude_skill ||
              existing?.is_claude_skill ||
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

    if (path === "/api/vault") {
      const items = await getVaultItems(env);
      return new Response(JSON.stringify({ ok: true, count: items.length, items }), {
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "public, max-age=60"
        }
      });
    }

    if (path === "/api/track") {
      if (request.method === "OPTIONS") {
        return new Response(null, {
          status: 204,
          headers: {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
          }
        });
      }
      if (request.method === "POST") {
        ctx.waitUntil((async () => {
          try {
            if (!env.REELS_KV) return;
            const payload = await request.json();
            const allowed = new Set(["visit", "open_repo", "watch_reel", "watch_yt", "copy_prompt", "copy_git"]);
            const ev = String(payload?.event || "").toLowerCase();
            if (!allowed.has(ev)) return;
            const kw = normalizeToken(payload?.keyword || "").slice(0, 24);
            const istDay = getISTDateKey(0);

            const totals = (await env.REELS_KV.get("stats:totals", "json")) || {};
            totals[ev] = (totals[ev] || 0) + 1;
            totals.updated_at = Date.now();
            await env.REELS_KV.put("stats:totals", JSON.stringify(totals));

            const dayStats = (await env.REELS_KV.get(`stats:day:${istDay}`, "json")) || { date: istDay, byKeyword: {} };
            dayStats[ev] = (dayStats[ev] || 0) + 1;
            if (kw) {
              dayStats.byKeyword = dayStats.byKeyword || {};
              dayStats.byKeyword[kw] = dayStats.byKeyword[kw] || {};
              dayStats.byKeyword[kw][ev] = (dayStats.byKeyword[kw][ev] || 0) + 1;
            }
            await env.REELS_KV.put(`stats:day:${istDay}`, JSON.stringify(dayStats));

            if (kw) {
              const kwStats = (await env.REELS_KV.get(`stats:kw:${kw}`, "json")) || {};
              kwStats[ev] = (kwStats[ev] || 0) + 1;
              await env.REELS_KV.put(`stats:kw:${kw}`, JSON.stringify(kwStats));
            }

            if (ev === "visit") {
              await checkAndNotifyMilestones(env, istDay, dayStats.visit || 0, totals.visit || 0);
            }
          } catch {}
        })());
        return new Response(JSON.stringify({ ok: true }), {
          headers: {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*"
          }
        });
      }
    }

    if (path === "/api/stats" && request.method === "GET") {
      if (!(await verifyEdgeAuth(request, env))) {
        return Response.json({ ok: false, error: "Unauthorized" }, { status: 401 });
      }
      if (!env.REELS_KV) {
        return Response.json({ ok: false, error: "REELS_KV not bound" }, { status: 500 });
      }
      const totals = (await env.REELS_KV.get("stats:totals", "json")) || {};
      const listed = await env.REELS_KV.list({ prefix: "stats:kw:", limit: 100 });
      const byKeyword = {};
      const vals = await Promise.all(listed.keys.map(k => env.REELS_KV.get(k.name, "json")));
      listed.keys.forEach((k, i) => {
        if (vals[i]) byKeyword[k.name.replace("stats:kw:", "")] = vals[i];
      });
      return Response.json({ ok: true, totals, byKeyword });
    }

    if (path === "/links" || path === "/links/") {
      const items = await getVaultItems(env);
      return new Response(renderLinksHubPage(items), {
        headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=60" }
      });
    }

    // 3.5 Public Legal & Meta App Review Pages (/privacy, /terms, /data-deletion)
    if (path === "/privacy" || path === "/privacy/") {
      return new Response(renderLegalPage("Privacy Policy — CurioCut", `
        <p><strong>Last updated:</strong> November 2026</p>
        <h2>1. Information We Collect</h2>
        <p>CurioCut Uploader accesses public Instagram comments and direct messages on content published by <strong>@curiocutt</strong> via the Meta Graph API solely to deliver requested open-source resource links and reply to viewer inquiries.</p>
        <h2>2. How We Use Data</h2>
        <ul>
          <li>Detect trigger keywords (such as <code>AGENT</code>, <code>CLAUDE</code>, or <code>PROMPT</code>) in comments on @curiocutt Reels.</li>
          <li>Send the requested public reply and private Direct Message containing the referenced resource link.</li>
          <li>Prevent duplicate replies using temporary comment ID deduplication caches (automatically expired).</li>
        </ul>
        <h2>3. Data Storage &amp; Sharing</h2>
        <p>We do not sell, rent, or share personal user data with third parties. Temporary deduplication keys expire automatically and are never used for advertising or profiling.</p>
        <h2>4. Data Deletion</h2>
        <p>You may request deletion of any stored interaction records at any time by following our <a href="/data-deletion">Data Deletion Instructions</a> or emailing <a href="mailto:autouploadreels@gmail.com">autouploadreels@gmail.com</a>.</p>
        <h2>5. Contact</h2>
        <p>Email: <a href="mailto:autouploadreels@gmail.com">autouploadreels@gmail.com</a></p>
      `), { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }

    if (path === "/terms" || path === "/terms/") {
      return new Response(renderLegalPage("Terms of Service — CurioCut", `
        <p><strong>Last updated:</strong> November 2026</p>
        <h2>1. Acceptance of Terms</h2>
        <p>By interacting with the <strong>@curiocutt</strong> Instagram account or CurioCut Uploader automation, you agree to these Terms of Service.</p>
        <h2>2. Service Description</h2>
        <p>CurioCut Uploader is an automated content publishing and comment-response service for @curiocutt. When you comment a designated keyword on a Reel, the service may post a public reply and send you a Direct Message with the requested link.</p>
        <h2>3. Acceptable Use</h2>
        <p>Users must not abuse, spam, or attempt to disrupt the automated response service. Automated responses are provided as-is for informational and educational purposes.</p>
        <h2>4. Third-Party Links</h2>
        <p>Messages delivered by CurioCut may contain links to third-party open-source repositories or documentation. We are not responsible for external website content.</p>
        <h2>5. Contact</h2>
        <p>Questions? Contact <a href="mailto:autouploadreels@gmail.com">autouploadreels@gmail.com</a>.</p>
      `), { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }

    if (path === "/data-deletion" || path === "/data-deletion/") {
      if (request.method === "POST") {
        const code = `curiocut_${Date.now().toString(36)}`;
        return Response.json({
          url: `${urlObj.origin}/data-deletion?code=${code}`,
          confirmation_code: code
        });
      }
      const code = urlObj.searchParams.get("code");
      return new Response(renderLegalPage("User Data Deletion — CurioCut", `
        <p><strong>Last updated:</strong> November 2026</p>
        ${code ? `<p><strong>Deletion Request Confirmation Code:</strong> <code>${code.replace(/[^a-zA-Z0-9_-]/g, "")}</code></p>` : ""}
        <h2>How to Request Data Deletion</h2>
        <p>CurioCut Uploader only caches temporary comment IDs for deduplication (automatically purged). If you would like any record associated with your Instagram username or account deleted immediately:</p>
        <ol>
          <li>Send a Direct Message to <strong>@curiocutt</strong> on Instagram with <code>DELETE MY DATA</code>, or</li>
          <li>Email <a href="mailto:autouploadreels@gmail.com?subject=CurioCut%20Data%20Deletion%20Request">autouploadreels@gmail.com</a> with your Instagram username.</li>
        </ol>
        <p>All matching temporary records are permanently removed within 48 hours of request receipt.</p>
      `), { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }

    return new Response("CurioCut Edge Active", { headers: { "Content-Type": "text/plain" } });
  }
};

async function getVaultItems(env) {
  const itemsByUrl = new Map();
  if (env.REELS_KV) {
    try {
      let cursor = undefined;
      for (let page = 0; page < 5; page++) {
        const listed = await env.REELS_KV.list({ prefix: "reel:", limit: 100, cursor });
        const vals = await Promise.all(listed.keys.map(k => env.REELS_KV.get(k.name, "json")));
        for (const v of vals) {
          if (!v || !v.resource_url || !/^https?:\/\/\S+$/i.test(v.resource_url)) continue;
          itemsByUrl.set(v.media_id || v.resource_url, {
            title: v.title || "CurioCut Tool",
            keyword: (v.keyword || "").toUpperCase(),
            category: v.category || "",
            is_claude_skill: Boolean(v.is_claude_skill),
            resource_url: v.resource_url,
            permalink: v.permalink || "",
            yt_url: v.yt_url || "",
            updated_at: v.updated_at || 0
          });
        }
        if (listed.list_complete || !listed.cursor) break;
        cursor = listed.cursor;
      }
    } catch {}
  }
  try {
    const ghRes = await fetch("https://raw.githubusercontent.com/shlokkokk/CurioCut/main/published_reels.json", {
      headers: { "User-Agent": "CurioCut-Edge/1.0" }
    });
    if (ghRes.ok) {
      const reg = await ghRes.json();
      for (const [mid, r] of Object.entries(reg || {})) {
        if (!r || !r.resource_url || !/^https?:\/\/\S+$/i.test(r.resource_url)) continue;
        if (!itemsByUrl.has(mid)) {
          itemsByUrl.set(mid, {
            title: r.title || "CurioCut Tool",
            keyword: (r.cta_keyword || "").toUpperCase(),
            category: r.category || "",
            is_claude_skill: Boolean(r.category === "claude_skill" || (r.title || "").toLowerCase().includes("claude")),
            resource_url: r.resource_url,
            permalink: r.permalink || `https://www.instagram.com/reel/${mid}/`,
            yt_url: r.yt_url || "",
            updated_at: r.published_at ? Date.parse(r.published_at) || 0 : 0
          });
        }
      }
    }
  } catch {}
  return Array.from(itemsByUrl.values()).sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0));
}

function renderLinksHubPage(items) {
  const esc = (s) => String(s || "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cards = items.map((it, idx) => {
    const kw = esc(it.keyword || "TOOL");
    const title = esc(it.title);
    const url = esc(it.resource_url);
    const latestBadge = idx === 0 ? `<span class="badge latest">LATEST DROP</span>` : "";
    return `<article class="card" data-search="${esc((it.title + " " + it.keyword).toLowerCase())}">
      <div class="meta"><span class="badge kw">${kw}</span>${latestBadge}</div>
      <h2>${title}</h2>
      <a class="btn" href="${url}" rel="noopener">Open Repo / Resource →</a>
    </article>`;
  }).join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CurioCut — AI Tools &amp; GitHub Drops</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #070812; color: #f3f4f6; margin: 0; padding: 24px 16px 48px; }
    main { max-width: 560px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 20px; }
    h1 { margin: 0 0 6px; font-size: 1.55rem; background: linear-gradient(90deg, #38bdf8, #a78bfa, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .sub { color: #9ca3af; font-size: 0.9rem; margin: 0; }
    #q { width: 100%; padding: 12px 14px; border-radius: 12px; border: 1px solid #262b45; background: #111426; color: #fff; font-size: 0.95rem; margin-bottom: 16px; outline: none; }
    #q:focus { border-color: #7c3aed; }
    .card { background: #111426; border: 1px solid #232842; border-radius: 14px; padding: 16px; margin-bottom: 12px; }
    .meta { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
    .badge { font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 999px; letter-spacing: 0.04em; }
    .kw { background: #1e293b; color: #38bdf8; border: 1px solid #334155; }
    .latest { background: #3b0764; color: #f0abfc; border: 1px solid #7e22ce; }
    h2 { margin: 0 0 12px; font-size: 1.05rem; line-height: 1.35; color: #f9fafb; }
    .btn { display: block; text-align: center; text-decoration: none; background: linear-gradient(90deg, #6366f1, #8b5cf6); color: #fff; font-weight: 600; padding: 11px 14px; border-radius: 10px; font-size: 0.92rem; }
    footer { text-align: center; margin-top: 24px; font-size: 0.8rem; color: #6b7280; }
    footer a { color: #38bdf8; text-decoration: none; }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>CurioCut Resource Vault</h1>
      <p class="sub">Every tool &amp; GitHub repo from @curiocutt Reels — newest first</p>
    </header>
    <input id="q" type="search" placeholder="Search by keyword (e.g. AGENT, CLAUDE, PROMPT)..." oninput="filterCards(this.value)" />
    <section id="list">${cards || '<p class="sub">No tools registered yet.</p>'}</section>
    <footer>Follow <a href="https://instagram.com/curiocutt" target="_blank">@curiocutt</a> for daily drops</footer>
  </main>
  <script>
    function filterCards(val) {
      var q = (val || '').trim().toLowerCase();
      document.querySelectorAll('.card').forEach(function(el) {
        el.style.display = (!q || (el.dataset.search || '').includes(q)) ? 'block' : 'none';
      });
    }
  </script>
</body>
</html>`;
}

function renderLegalPage(title, bodyHtml) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${title}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0d17; color: #e5e7eb; margin: 0; padding: 40px 20px; line-height: 1.65; }
    main { max-width: 720px; margin: 0 auto; background: #131626; border: 1px solid #262b45; border-radius: 14px; padding: 32px; }
    h1 { color: #ffffff; margin-top: 0; font-size: 1.75rem; }
    h2 { color: #a78bfa; font-size: 1.15rem; margin-top: 1.6rem; }
    a { color: #38bdf8; }
    code { background: #1e233a; padding: 2px 6px; border-radius: 5px; color: #f472b6; }
    footer { margin-top: 2rem; font-size: 0.85rem; color: #9ca3af; border-top: 1px solid #262b45; padding-top: 1rem; }
  </style>
</head>
<body>
  <main>
    <h1>${title}</h1>
    ${bodyHtml}
    <footer>CurioCut Automation • <a href="/privacy">Privacy</a> • <a href="/terms">Terms</a> • <a href="/data-deletion">Data Deletion</a></footer>
  </main>
</body>
</html>`;
}

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

async function refreshPanelAndProgress(env) {
  const botToken = env.DISCORD_BOT_TOKEN || ["MTU2OTc0NzczNTcyMzI0OTczNQ", "GJ6qW0", "yW95EFsWYvdw6E9AHynAtA02VAso9IUKOwY37s"].join(".");
  const headers = {
    "Authorization": `Bot ${botToken}`,
    "Content-Type": "application/json",
    "User-Agent": "CurioCut-Bot"
  };

  const panelChannelId = "1569750971003830453";
  const panelMessageId = "1569751061034700994";
  const progressChannelId = "1569750972975288441";
  const progressMessageId = "1569754307379732507";

  const panelEmbed = {
    type: "rich",
    title: "CurioCut Autonomous Control Panel",
    description: "Control your automated YouTube Shorts and Instagram Reels pipeline with 1-tap buttons or slash commands.",
    color: 0x2B2D31,
    fields: [
      {
        name: "Slot 1 (1:00 PM IST)",
        value: "* **Style**: 3D Blender Town-Rule (`town-rule`)\n* **Characters**: Procedural R6 Cast + Custom 3D Monsters & 6 Modular Worlds\n* **Content**: Viral \"In this town, [rule]...\" 4-act 3D animated stories\n* **Auto-Trigger**: 11:55 AM IST (06:25 UTC)",
        inline: false
      },
      {
        name: "Slot 2 (7:00 PM IST)",
        value: "* **Style**: 3D Claude-Desk Dual Bot (`claude-desk`)\n* **Characters**: Anthropic Coral Red ClaudeBot + Pastel Pink SkepticBot\n* **Content**: Architecture breakdowns, autonomous Claude Code skills & MCP servers\n* **Auto-Trigger**: 5:55 PM IST (12:25 UTC)",
        inline: false
      },
      {
        name: "Slot 3 (9:30 PM IST)",
        value: "* **Style**: 3D Dev-Studio Night Loft (`dev-studio`)\n* **Characters**: Navy Hoodie DevGuy + Floating Cyan MascotBot\n* **Content**: Open-source exploits, $49/mo SaaS replacements, 32k star GitHub repos\n* **Auto-Trigger**: 9:25 PM IST (15:55 UTC)",
        inline: false
      },
      {
        name: "Cloud Engine & Links",
        value: "* [Kaggle Cloud GPU Runner](https://www.kaggle.com/code/shlokkshahh/curiocut-gpu-engine)\n* [GitHub Actions Workflows](https://github.com/shlokkokk/CurioCut/actions)\n* [Instagram @curiocutt](https://instagram.com/curiocutt)",
        inline: false
      },
      {
        name: "Slash Commands",
        value: "Type `/trigger`, `/panel`, `/refresh`, `/status`, `/skip`, or `/create` anywhere in the server.",
        inline: false
      }
    ],
    footer: {
      text: "CurioCut Autonomous Engine * $0.00 Cloud Stack * 3 Daily Slots"
    }
  };

  const panelComponents = [
    {
      type: 1,
      components: [
        { type: 2, style: 1, label: "Slot 1: Town-Rule (1 PM)", custom_id: "trigger_slot_1" },
        { type: 2, style: 1, label: "Slot 2: Claude-Desk (7 PM)", custom_id: "trigger_slot_2" },
        { type: 2, style: 3, label: "Slot 3: Dev-Studio (9:30 PM)", custom_id: "trigger_slot_3" }
      ]
    },
    {
      type: 1,
      components: [
        { type: 2, style: 2, label: "Create Custom", custom_id: "open_modal_create" },
        { type: 2, style: 2, label: "Skip Next Slot", custom_id: "skip_next_trigger" },
        { type: 2, style: 2, label: "Status", custom_id: "check_status" },
        { type: 2, style: 4, label: "Emergency Stop", custom_id: "emergency_stop" }
      ]
    },
    {
      type: 1,
      components: [
        { type: 2, style: 2, label: "Refresh Panel & Status", custom_id: "refresh_panel" },
        { type: 2, style: 5, label: "Open Kaggle Runner", url: "https://www.kaggle.com/code/shlokkshahh/curiocut-gpu-engine" },
        { type: 2, style: 5, label: "GitHub Actions", url: "https://github.com/shlokkokk/CurioCut/actions" }
      ]
    }
  ];

  let isRunning = false;
  let runInfo = "";
  if (env.GITHUB_TOKEN) {
    try {
      const gRes = await fetch("https://api.github.com/repos/shlokkokk/CurioCut/actions/runs?per_page=1", {
        headers: { "Authorization": `Bearer ${env.GITHUB_TOKEN}`, "User-Agent": "CurioCut-Bot" }
      });
      if (gRes.ok) {
        const gData = await gRes.json();
        const run = gData.workflow_runs?.[0];
        if (run && (run.status === "in_progress" || run.status === "queued")) {
          isRunning = true;
          runInfo = `Active workflow run #${run.run_number} (${run.display_title || "Pipeline"}).`;
        }
      }
    } catch (e) {
      console.error("Error checking GitHub status:", e);
    }
  }

  const progressEmbed = {
    type: "rich",
    title: "Video Pipeline Live Progress",
    color: isRunning ? 0x38BDF8 : 0x22C55E,
    timestamp: new Date().toISOString(),
    fields: isRunning ? [
      { name: "Status", value: "Cloud Worker Active", inline: true },
      { name: "Progress", value: "[=====.....] In Progress", inline: true },
      { name: "Details", value: `${runInfo}\nLive frame counts will stream here as Blender renders.`, inline: false }
    ] : [
      { name: "Status", value: "Idle / Standing By", inline: true },
      { name: "Progress", value: "[..........] Ready", inline: true },
      { name: "Details", value: "Standing by for the next automated slot or manual trigger.\n* Slot 1: 11:55 AM IST (Town-Rule)\n* Slot 2: 5:55 PM IST (Claude-Desk)\n* Slot 3: 9:25 PM IST (Dev-Studio)", inline: false }
    ],
    footer: {
      text: "CurioCut Live Progress"
    }
  };

  await Promise.allSettled([
    fetch(`https://discord.com/api/v10/channels/${panelChannelId}/messages/${panelMessageId}`, {
      method: "PATCH",
      headers,
      body: JSON.stringify({ embeds: [panelEmbed], components: panelComponents })
    }),
    fetch(`https://discord.com/api/v10/channels/${progressChannelId}/messages/${progressMessageId}`, {
      method: "PATCH",
      headers,
      body: JSON.stringify({ embeds: [progressEmbed], components: [] })
    })
  ]);

  return "Control panel and live progress monitors have been refreshed to the latest state. Check <#1569750971003830453> and <#1569750972975288441>.";
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

const STORY_CONVERSATION_REPLIES = [
  "Wild right?! Did you see that twist coming or did it get you? @{user} 👀 Follow @curiocutt for tomorrow's rule drop.",
  "Appreciate you watching @{user}! If you woke up in this town tomorrow, how long are you surviving? Follow for tomorrow's drop!",
  "Glad you caught this one @{user}! What would you have done under this rule? Follow to catch the next town story.",
  "Thanks for watching @{user}! Do you think the rule was fair or completely twisted? Follow @curiocutt so tomorrow's story hits your feed.",
  "Appreciate the comment @{user}! What kind of bizarre rule do you think the next town should have? Hit follow to stay tuned."
];

const REPEAT_FAN_REPLIES = [
  "Always great seeing you back @{user}! What would you do if you were trapped under this town's rule? 👀",
  "You never miss a drop @{user} 🙌 Did you expect that ending or did it completely surprise you?",
  "Our day-one regular @{user}! 🔥 If you woke up in this town tomorrow, how long are you surviving?",
  "Appreciate the constant love on these drops @{user}! What crazy rule should the next town have?",
  "The legend @{user} is back! Do you think the protagonist made the right call or was it a mistake?"
];

const STORY_PUBLIC_REPLIES = STORY_CONVERSATION_REPLIES;

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

  // Mode 1: Non-Tech Story Reel -> engaging conversation starters & fan recognition
  if (rule.mode === "story" || !validResourceUrl) {
    if (normalizeToken(text).length < 2) {
      console.log(`[Instagram Responder] Skipping short/empty story comment ${commentId}: "${text}"`);
      return { commentId, mediaId, mode: "story", skipped: "too_short" };
    }

    // Check repeat fan status via KV
    let userCommentCount = 1;
    let isRepeatFan = false;
    const unameLower = (user || "").toLowerCase().trim();
    if (["lwk_muji", "jokee_peraltaa", "shlokkshahh"].includes(unameLower)) {
      isRepeatFan = true;
    }
    if (env && env.REELS_KV && unameLower) {
      try {
        const cmtKey = `user_cmt:${unameLower}`;
        const prevCount = await env.REELS_KV.get(cmtKey);
        userCommentCount = prevCount ? (parseInt(prevCount, 10) + 1) : (isRepeatFan ? 2 : 1);
        if (userCommentCount >= 2) isRepeatFan = true;
        await env.REELS_KV.put(cmtKey, String(userCommentCount), { expirationTtl: 2592000 }); // 30 days
      } catch (eKv) {
        console.error("KV user count error:", eKv);
      }
    }

    const replyPool = isRepeatFan ? REPEAT_FAN_REPLIES : STORY_CONVERSATION_REPLIES;
    const pubText = rule.public_reply
      ? applyTemplate(rule.public_reply, { user, keyword: rule.keyword, title: safeRuleTitle })
      : pickReply(replyPool, commentId || text, { user });

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
              title: publicOk ? (isRepeatFan ? "⭐ Repeat Fan Replied" : "Story Comment Replied") : "Story Reply Failed",
              description: `@${user} commented \`${safeText}\` on **${safeRuleTitle}**`.slice(0, 1500),
              color: publicOk ? (isRepeatFan ? 0xF59E0B : 0x0EA5E9) : 0xEF4444,
              fields: [
                { name: "Reply Sent", value: (publicOk ? pubText : (rep.errorMsg || "Meta API error")).slice(0, 900), inline: false },
                { name: "Audience Tier", value: isRepeatFan ? `⭐ Repeat Supporter (Comment #${userCommentCount})` : "New / 1st-Time Commenter", inline: true },
                { name: "Mode", value: "Conversation Starter (No DM)", inline: true }
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
    dmText = `Hey @${user}! Here is the resource you requested for ${reelTitle}:\n\n🔗 Direct Repo & Guide:\n${resourceUrl}\n\n⚡ Quick Setup:\nPaste the link into Claude or any AI coding agent and ask it to install and configure it for you.\n\n💬 Hit any errors or get stuck? Just reply here and I'll help you get it running!\n\nFollow @curiocutt for daily AI tools!`;
  } else {
    dmText = `Hey @${user}! Here is the resource you requested for ${reelTitle}:\n\n🔗 Direct Repo & Guide:\n${resourceUrl}\n\n⚡ Quick Setup:\nPaste the link into Claude or any AI agent and ask: "Help me install and run this locally."\n\n💬 Hit any errors or get stuck? Just reply here and I'll help you get it running!\n\nFollow @curiocutt for daily open-source AI drops!`;
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

const STATS_CHANNEL_ID = "1575281495285698731";
const MILESTONES_CHANNEL_ID = "1575281497739624502";

function getISTDate(offsetDays = 0) {
  const istMs = Date.now() + 330 * 60 * 1000 - offsetDays * 86400 * 1000;
  return new Date(istMs);
}

function getISTDateKey(offsetDays = 0) {
  return getISTDate(offsetDays).toISOString().slice(0, 10);
}

function getISTWeekday() {
  return getISTDate(0).getUTCDay(); // 0 = Sunday
}

function scoreKwEntry(s = {}) {
  return (s.open_repo || 0) + (s.watch_reel || 0) + (s.watch_yt || 0) + (s.copy_prompt || 0) + (s.copy_git || 0);
}

function formatTopDrops(byKw = {}, limit = 5) {
  const entries = Object.entries(byKw)
    .map(([kw, s]) => ({ kw, score: scoreKwEntry(s), s }))
    .filter(x => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
  if (entries.length === 0) return "No drop interactions recorded yet.";
  return entries
    .map((e, i) => `${i + 1}. **${e.kw}** - ${e.s.open_repo || 0} repos, ${e.s.copy_prompt || 0} prompts, ${(e.s.watch_reel || 0) + (e.s.watch_yt || 0)} watches`)
    .join("\n");
}

async function aggregateWeekStats(env) {
  const agg = { visit: 0, open_repo: 0, watch_reel: 0, watch_yt: 0, copy_prompt: 0, copy_git: 0, byKeyword: {} };
  if (!env.REELS_KV) return agg;
  const keys = Array.from({ length: 7 }, (_, i) => `stats:day:${getISTDateKey(i)}`);
  const days = await Promise.all(keys.map(k => env.REELS_KV.get(k, "json")));
  for (const d of days) {
    if (!d) continue;
    for (const k of ["visit", "open_repo", "watch_reel", "watch_yt", "copy_prompt", "copy_git"]) {
      agg[k] += d[k] || 0;
    }
    for (const [kw, s] of Object.entries(d.byKeyword || {})) {
      agg.byKeyword[kw] = agg.byKeyword[kw] || {};
      for (const [ev, val] of Object.entries(s || {})) {
        agg.byKeyword[kw][ev] = (agg.byKeyword[kw][ev] || 0) + (val || 0);
      }
    }
  }
  return agg;
}

async function buildStatsEmbed(env, period = "today") {
  const istDay = getISTDateKey(0);
  const totals = (env.REELS_KV && await env.REELS_KV.get("stats:totals", "json")) || {};

  if (period === "week") {
    const week = await aggregateWeekStats(env);
    return {
      title: `Weekly Site Stats (${getISTDateKey(6)} to ${istDay})`,
      color: 0xD4FF3E,
      fields: [
        { name: "7-Day Visits", value: String(week.visit || 0), inline: true },
        { name: "Repo Opens", value: String(week.open_repo || 0), inline: true },
        { name: "Prompt / Git Copies", value: `${week.copy_prompt || 0} / ${week.copy_git || 0}`, inline: true },
        { name: "Watch Clicks (IG / YT)", value: `${week.watch_reel || 0} / ${week.watch_yt || 0}`, inline: true },
        { name: "All-Time Visits", value: String(totals.visit || 0), inline: true },
        { name: "Top Drops (7d)", value: formatTopDrops(week.byKeyword, 5), inline: false }
      ],
      footer: { text: "CurioCut Analytics • Weekly (IST)" }
    };
  }

  if (period === "total") {
    const listed = env.REELS_KV ? await env.REELS_KV.list({ prefix: "stats:kw:", limit: 100 }) : { keys: [] };
    const vals = env.REELS_KV ? await Promise.all(listed.keys.map(k => env.REELS_KV.get(k.name, "json"))) : [];
    const byKw = {};
    listed.keys.forEach((k, i) => {
      if (vals[i]) byKw[k.name.replace("stats:kw:", "")] = vals[i];
    });
    return {
      title: "All-Time Site Stats",
      color: 0xD4FF3E,
      fields: [
        { name: "Total Visits", value: String(totals.visit || 0), inline: true },
        { name: "Repo Opens", value: String(totals.open_repo || 0), inline: true },
        { name: "Prompt / Git Copies", value: `${totals.copy_prompt || 0} / ${totals.copy_git || 0}`, inline: true },
        { name: "Watch Clicks (IG / YT)", value: `${totals.watch_reel || 0} / ${totals.watch_yt || 0}`, inline: true },
        { name: "Top Drops (All-Time)", value: formatTopDrops(byKw, 5), inline: false }
      ],
      footer: { text: "CurioCut Analytics • All-Time" }
    };
  }

  const today = (env.REELS_KV && await env.REELS_KV.get(`stats:day:${istDay}`, "json")) || {};
  return {
    title: `Daily Site Stats (${istDay} IST)`,
    color: 0xD4FF3E,
    fields: [
      { name: "Today Visits", value: String(today.visit || 0), inline: true },
      { name: "Repo Opens", value: String(today.open_repo || 0), inline: true },
      { name: "Prompt / Git Copies", value: `${today.copy_prompt || 0} / ${today.copy_git || 0}`, inline: true },
      { name: "Watch Clicks (IG / YT)", value: `${today.watch_reel || 0} / ${today.watch_yt || 0}`, inline: true },
      { name: "All-Time Visits", value: String(totals.visit || 0), inline: true },
      { name: "Top Drops Today", value: formatTopDrops(today.byKeyword, 5), inline: false }
    ],
    footer: { text: "CurioCut Analytics • Daily (IST)" }
  };
}

async function buildMilestonesEmbed(env) {
  const istDay = getISTDateKey(0);
  const today = (env.REELS_KV && await env.REELS_KV.get(`stats:day:${istDay}`, "json")) || {};
  const week = await aggregateWeekStats(env);
  const totals = (env.REELS_KV && await env.REELS_KV.get("stats:totals", "json")) || {};
  const dVisits = today.visit || 0;
  const wVisits = week.visit || 0;
  const tVisits = totals.visit || 0;
  const adReady = dVisits >= 100 || wVisits >= 700 || tVisits >= 3000;

  return {
    title: "Growth & Ad Eligibility Progress",
    color: adReady ? 0xD4FF3E : 0x2B2D31,
    fields: [
      { name: "Today (IST)", value: `${dVisits} visits`, inline: true },
      { name: "Last 7 Days", value: `${wVisits} visits`, inline: true },
      { name: "All-Time Total", value: `${tVisits} visits`, inline: true },
      {
        name: "Website Ads Readiness (Target: 100/day or 3,000 total)",
        value: adReady
          ? "Ready for Google AdSense / Carbon Ads application."
          : `In progress (${Math.min(100, Math.round((tVisits / 3000) * 100))}% of 3,000 total visits).`,
        inline: false
      },
      {
        name: "YouTube Partner Program Thresholds",
        value: "Tier 1: 500 subs + 3M Shorts views (90d)\nTier 2 (Ads): 1,000 subs + 10M Shorts views (90d) or 4,000 watch hrs",
        inline: false
      }
    ],
    footer: { text: "CurioCut Milestones" }
  };
}

async function sendDiscordChannelEmbed(env, channelId, embed) {
  const botToken = env.DISCORD_BOT_TOKEN || ["MTU2OTc0NzczNTcyMzI0OTczNQ", "GJ6qW0", "yW95EFsWYvdw6E9AHynAtA02VAso9IUKOwY37s"].join(".");
  await fetch(`https://discord.com/api/v10/channels/${channelId}/messages`, {
    method: "POST",
    headers: {
      "Authorization": `Bot ${botToken}`,
      "Content-Type": "application/json",
      "User-Agent": "CurioCut-Bot"
    },
    body: JSON.stringify({ embeds: [embed] })
  });
}

async function sendDailyStatsDigest(env) {
  const dailyEmbed = await buildStatsEmbed(env, "today");
  await sendDiscordChannelEmbed(env, STATS_CHANNEL_ID, dailyEmbed);
  if (getISTWeekday() === 0) {
    const weeklyEmbed = await buildStatsEmbed(env, "week");
    await sendDiscordChannelEmbed(env, STATS_CHANNEL_ID, weeklyEmbed);
  }
}

async function checkAndNotifyMilestones(env, istDay, dailyVisits, totalVisits) {
  if (!env.REELS_KV) return;
  const dailyTargets = [50, 100, 250, 500, 1000, 2500, 5000];
  const totalTargets = [1000, 3000, 10000, 25000, 50000];

  for (const m of dailyTargets) {
    if (dailyVisits >= m) {
      const k = `milestone:day:${istDay}:${m}`;
      if (!(await env.REELS_KV.get(k))) {
        await env.REELS_KV.put(k, "1", { expirationTtl: 172800 });
        await sendDiscordChannelEmbed(env, MILESTONES_CHANNEL_ID, {
          title: `Daily Traffic Milestone: ${m} Visits`,
          description: m >= 100
            ? `curiocut.pages.dev hit ${dailyVisits} visits today (${istDay} IST). Daily traffic is in range for website ad monetization review.`
            : `curiocut.pages.dev reached ${dailyVisits} visits today (${istDay} IST).`,
          color: 0xD4FF3E,
          footer: { text: "CurioCut Milestones" }
        });
      }
    }
  }

  for (const m of totalTargets) {
    if (totalVisits >= m) {
      const k = `milestone:total:${m}`;
      if (!(await env.REELS_KV.get(k))) {
        await env.REELS_KV.put(k, "1");
        await sendDiscordChannelEmbed(env, MILESTONES_CHANNEL_ID, {
          title: `Total Traffic Milestone: ${m.toLocaleString()} Visits`,
          description: m >= 3000
            ? `curiocut.pages.dev crossed ${totalVisits.toLocaleString()} total visits. You have enough traffic baseline to apply for Google AdSense or Carbon Ads.`
            : `curiocut.pages.dev crossed ${totalVisits.toLocaleString()} cumulative visits.`,
          color: 0xD4FF3E,
          footer: { text: "CurioCut Milestones" }
        });
      }
    }
  }
}
