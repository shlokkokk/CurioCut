/**
 * Cloudflare Worker: 100% Cloud Autonomous CurioCut Edge Cron Dispatcher & Discord Bot Controller
 * Runs on Cloudflare's Global Edge Network (100,000 free requests/day, 0% delay).
 */

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
    if (hourUTC === 15 || cronStr.includes("15")) {
      slotType = "claude-desk";
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
          const slot = getOpt("slot") || "classic";
          const slotName = slot === "claude-desk" ? "Slot 3 (9:30 PM Tech)" : (slot === "slot_2" ? "Slot 2 (7:00 PM Classic)" : "Slot 1 (1:00 PM Classic)");
          await triggerGitHub(env.GITHUB_TOKEN, slot === "claude-desk" ? "claude-desk" : "classic");
          return Response.json({
            type: 4,
            data: { content: `Triggered ${slotName}. Live frame rendering will appear in #live-progress.`, flags: 64 }
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
          const style = getOpt("style") || "claude-desk";
          await triggerGitHub(env.GITHUB_TOKEN, style, topic);
          return Response.json({
            type: 4,
            data: { content: `Started generating custom short for "${topic}" in style "${style}". Watch live frame progress in #live-progress.`, flags: 64 }
          });
        }
      }

      // Discord Modal Submit (Type 5)
      if (body.type === 5) {
        const topic = body.data?.components?.[0]?.components?.[0]?.value || "Random Topic";
        const style = body.data?.components?.[1]?.components?.[0]?.value || "claude-desk";

        await triggerGitHub(env.GITHUB_TOKEN, style, topic);

        return Response.json({
          type: 4,
          data: {
            content: `Started generating custom short for "${topic}" in style "${style}". Progress will show in #live-progress.`,
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
                      placeholder: "e.g. The casino glitch that paid out millions",
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
                      label: "Style (claude-desk, tall-tale, deep-dive)",
                      style: 1,
                      value: "claude-desk",
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
          replyText = "Started generating Slot 1 Classic Story (1:00 PM). Live frame rendering will appear in #live-progress.";
        } else if (customId === "trigger_slot_2") {
          await triggerGitHub(env.GITHUB_TOKEN, "classic");
          replyText = "Started generating Slot 2 Classic Story (7:00 PM). Live frame rendering will appear in #live-progress.";
        } else if (customId === "trigger_tech" || customId === "trigger_slot_3") {
          await triggerGitHub(env.GITHUB_TOKEN, "claude-desk");
          replyText = "Started generating Slot 3 (9:30 PM 3D Claude-Desk Tech Exploit). Live frame rendering will appear in #live-progress.";
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

    // 2. Mobile Dashboard Fallback
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
  const url = "https://api.github.com/repos/shlokkokk/CurioCut/actions/runs?status=in_progress";
  const res = await fetch(url, {
    headers: { "Authorization": `Bearer ${token}`, "User-Agent": "CurioCut-Bot" }
  });
  const data = await res.json();
  for (const run of data.workflow_runs || []) {
    await fetch(`https://api.github.com/repos/shlokkokk/CurioCut/actions/runs/${run.id}/cancel`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}`, "User-Agent": "CurioCut-Bot" }
    });
  }
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
    return "A video is currently rendering in the cloud (working on 3D scene). Live frame counts are updating in #live-progress.";
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
