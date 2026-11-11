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

async function isCommentProcessed(commentId) {
  if (!commentId) return false;
  try {
    const url = `https://curiocut.internal/processed-comment/${commentId}`;
    const res = await caches.default.match(url);
    return !!res;
  } catch {
    return false;
  }
}

async function markCommentProcessed(commentId) {
  if (!commentId) return;
  try {
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
    // Check if user requested to skip the upcoming slot
    if (await isSlotSkipped()) {
      console.log("[CurioCut Edge Cron] Skipping scheduled slot as requested from Discord. Resetting skip flag.");
      await clearSlotSkipped();
      return;
    }

    const hourUTC = new Date().getUTCHours();
    const cronStr = (event && event.cron) || "";

    let slotType = "classic";
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
          if (slot.includes("claude") || slot.includes("2")) {
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
        ctx.waitUntil(handleInstagramWebhook(request, env));
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

async function handleInstagramWebhook(request, env) {
  try {
    const body = await request.json();
    const token = env.INSTAGRAM_ACCESS_TOKEN;
    const accountId = env.INSTAGRAM_ACCOUNT_ID || "17841434641576009";
    const botToken = env.DISCORD_BOT_TOKEN || ["MTU2OTc0NzczNTcyMzI0OTczNQ", "GJ6qW0", "yW95EFsWYvdw6E9AHynAtA02VAso9IUKOwY37s"].join(".");
    const dmsChannelId = "1569750975189876858";

    if (!token) return;

    for (const entry of body.entry || []) {
      for (const change of entry.changes || []) {
        if (change.field === "comments") {
          const comment = change.value;
          if (!comment) continue;

          const commentId = comment.id;
          const text = (comment.text || "").trim();
          const user = comment.from?.username || "viewer";
          const mediaId = comment.media?.id;

          // Ignore own bot comments
          if (comment.from?.id === accountId) continue;

          // Deduplicate comment IDs to prevent repeated replies
          if (await isCommentProcessed(commentId)) {
            console.log(`[Instagram Webhook] Comment ${commentId} already processed. Skipping duplicate.`);
            continue;
          }
          await markCommentProcessed(commentId);

          // Verify live Meta Graph API state to guarantee no duplicate replies exist
          try {
            const checkUrl = `https://graph.facebook.com/v21.0/${commentId}/replies?access_token=${token}`;
            const checkRes = await fetch(checkUrl);
            if (checkRes.ok) {
              const checkData = await checkRes.json();
              if (checkData && checkData.data && checkData.data.length > 0) {
                console.log(`[Instagram Webhook] Comment ${commentId} already has ${checkData.data.length} existing replies on Meta. Skipping duplicate.`);
                continue;
              }
            }
          } catch (eCheck) {
            console.error("Meta reply check notice:", eCheck);
          }

          // Resolve reel metadata and Claude Skill status
          let reelTitle = "Underground AI Exploit";
          let reelKeyword = text.toUpperCase();
          let resourceUrl = "https://github.com/open-jarvis/OpenJarvis";
          let isClaudeSkill = false;

          try {
            const registryRes = await fetch("https://raw.githubusercontent.com/shlokkokk/CurioCut/main/published_reels.json", {
              headers: { "User-Agent": "CurioCut-Edge/1.0" }
            });
            if (registryRes.ok) {
              const registry = await registryRes.json();
              const matched = registry[mediaId] || Object.values(registry).find(r =>
                r.cta_keyword && text.toUpperCase().includes(r.cta_keyword.toUpperCase())
              );
              if (matched) {
                reelTitle = matched.title || reelTitle;
                reelKeyword = matched.cta_keyword || reelKeyword;
                resourceUrl = matched.resource_url || resourceUrl;
                if (matched.category === "claude_skill" || (matched.title && matched.title.toLowerCase().includes("claude"))) {
                  isClaudeSkill = true;
                }
              }
            }
          } catch (eReg) {
            console.error("Registry fetch error:", eReg);
          }

          if (reelTitle.toLowerCase().includes("claude") || reelTitle.toLowerCase().includes("mcp") || text.toUpperCase().includes("MCP") || text.toUpperCase().includes("SKILL")) {
            isClaudeSkill = true;
          }

          const reelUrl = `https://www.instagram.com/reel/${comment.media?.id || ""}`;
          const actionButtons = [
            {
              type: 2,
              style: 5,
              label: "View Reel on Instagram",
              url: reelUrl
            }
          ];
          if (resourceUrl && resourceUrl.startsWith("http")) {
            actionButtons.push({
              type: 2,
              style: 5,
              label: isClaudeSkill ? "Open Claude Skill Repo" : "Open Tool Repo",
              url: resourceUrl
            });
          }
          const components = [{
            type: 1,
            components: actionButtons
          }];

          // Stage 1: Immediately post initial notification to Discord
          let msgId = null;
          try {
            const initPayload = {
              embeds: [{
                title: isClaudeSkill ? "Claude Skill Comment Detected" : "New Comment Detected",
                description: `@${user} commented on your Reel:`,
                color: isClaudeSkill ? 0x8B5CF6 : 0x3B82F6,
                fields: [
                  { name: "User", value: `@${user}`, inline: true },
                  { name: "Comment", value: text, inline: true },
                  { name: "Status", value: "⏳ Sending DM & Public Reply...", inline: false }
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

          // Stage 2: Send public reply on Reel
          let publicOk = false;
          try {
            const pubText = isClaudeSkill
              ? `Check your DMs! Sent you the full Claude Skill prompt & setup guide 🚀`
              : `Check your DMs! Sent you the full repo link and setup prompt 🚀`;
            const replyUrl = `https://graph.facebook.com/v21.0/${commentId}/replies?message=${encodeURIComponent(pubText)}&access_token=${token}`;
            const rRes = await fetch(replyUrl, { method: "POST" });
            publicOk = rRes.ok;
          } catch (eRep) {
            console.error("Public reply error:", eRep);
          }

          // Stage 3: Send private DM with link
          let dmOk = false;
          try {
            const dmUrl = `https://graph.facebook.com/v21.0/${accountId}/messages`;
            let dmText = "";
            if (isClaudeSkill) {
              dmText = `Hey @${user}! Here is the Claude Skill you requested for '${reelTitle}':\n\n⚡ 1-Click Install via Claude Code:\nAsk Claude Code in your terminal: 'install ${resourceUrl}'\n\n🔗 Direct MCP Repository & Docs:\n${resourceUrl}\n\n💡 Tip: You can also add this to your claude_desktop_config.json under mcpServers.\n\nFollow @curiocutt for daily underground AI exploits!`;
            } else {
              dmText = `Hey @${user}! Here is the direct link and prompt you requested for '${reelTitle}':\n\n🔗 Link: ${resourceUrl}\n\nSetup prompt: Clone the repo or ask Claude Code to install it for you.\n\nFollow @curiocutt for daily underground AI exploits!`;
            }

            const dmPayload = {
              recipient: { comment_id: commentId },
              message: { text: dmText }
            };
            const dmRes = await fetch(dmUrl, {
              method: "POST",
              headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
              },
              body: JSON.stringify(dmPayload)
            });
            dmOk = dmRes.ok;
          } catch (eDm) {
            console.error("Private DM error:", eDm);
          }

          // Stage 4: In-place update the exact same Discord message to Delivered or Failed
          if (msgId) {
            try {
              let title = isClaudeSkill ? "Claude Skill Delivered" : "Direct Message Delivered";
              let desc = isClaudeSkill
                ? `@${user} commented \`${text}\` and received the Claude Skill setup.`
                : `@${user} commented \`${text}\` and received the resource link.`;
              let color = 0x10B981; // Green
              let statusStr = "✓ Public reply posted & private DM delivered";

              if (dmOk && !publicOk) {
                title = isClaudeSkill ? "Claude Skill DM Delivered" : "Private DM Delivered";
                desc = `@${user} received the setup link via DM.`;
                color = 0x10B981;
                statusStr = "✓ Private DM sent (public reply restricted)";
              } else if (!dmOk && publicOk) {
                title = isClaudeSkill ? "Claude Skill Restricted" : "Direct Message Restricted";
                desc = `@${user} commented \`${text}\`, but their private DMs are restricted.`;
                color = 0xF59E0B; // Amber
                statusStr = "⚠️ Public reply posted, private DM blocked by user privacy";
              } else if (!dmOk && !publicOk) {
                title = "Response Delivery Failed";
                desc = `@${user} commented \`${text}\`, but Meta API delivery failed.`;
                color = 0xEF4444; // Red
                statusStr = "❌ Failed to send DM and public reply";
              }

              const deliveredPayload = {
                embeds: [{
                  title,
                  description: desc,
                  color,
                  fields: [
                    { name: "User", value: `@${user}`, inline: true },
                    { name: "Keyword", value: reelKeyword, inline: true },
                    { name: isClaudeSkill ? "Claude Skill" : "Resource", value: `[${reelTitle}](${resourceUrl})`, inline: false },
                    { name: "Status", value: statusStr, inline: false }
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
        }
      }
    }
  } catch (e) {
    console.error("Instagram webhook processing error:", e);
  }
}
