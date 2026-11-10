/**
 * Cloudflare Worker: 100% Cloud Autonomous CurioCut Edge Cron Dispatcher
 * Runs on Cloudflare's Global Edge Network (100,000 free requests/day, 0% delay).
 * Triggers GitHub Actions 'repository_dispatch' with zero cold-start delay.
 *
 * 3 Daily Upload Slots:
 * - 25 6 * * *   (11:55 AM IST / 06:25 UTC) -> Slot 1: Classic Story #1 (Live at 1:00 PM IST)
 * - 25 12 * * *  (05:55 PM IST / 12:25 UTC) -> Slot 2: Classic Story #2 (Live at 7:00 PM IST)
 * - 55 15 * * *  (08:55 PM IST / 15:55 UTC) -> Slot 3: Flagship 3D Claude-Desk Tech Exploit (Live at 9:30 PM IST)
 */

export default {
  async scheduled(event, env, ctx) {
    const hourUTC = new Date().getUTCHours();
    const cronStr = (event && event.cron) || "";

    // Late Night Slot (8:55 PM IST / 15:55 UTC) is the Flagship 3D Claude-Desk Tech Exploit
    let slotType = "classic";
    if (hourUTC === 15 || cronStr.includes("15")) {
      slotType = "claude-desk";
    }

    const url = "https://api.github.com/repos/shlokkokk/CurioCut/dispatches";
    console.log(`[CurioCut Edge Cron] Firing slot: ${slotType} (cron: '${cronStr}', hourUTC: ${hourUTC}) at ${new Date().toISOString()}`);

    const res = await fetch(url, {
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

    console.log(`GitHub API Response status: ${res.status}`);
    return res;
  },

  async fetch(request, env, ctx) {
    // 1-Tap Mobile Dashboard & Manual Trigger URL
    const urlObj = new URL(request.url);
    const path = urlObj.pathname.toLowerCase();

    let targetSlot = "auto";
    if (path.includes("tech") || path.includes("claude")) {
      targetSlot = "claude-desk";
    } else if (path.includes("classic")) {
      targetSlot = "classic";
    }

    const githubUrl = "https://api.github.com/repos/shlokkokk/CurioCut/dispatches";
    const res = await fetch(githubUrl, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CurioCut-Manual-Trigger"
      },
      body: JSON.stringify({
        event_type: "daily_short",
        client_payload: {
          slot: targetSlot,
          trigger_source: "manual_url_click",
          triggered_at: new Date().toISOString()
        }
      })
    });

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CurioCut Cloud Dispatcher</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
    .card { background: #1e293b; border-radius: 16px; padding: 28px; max-width: 440px; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
    h1 { margin: 0 0 10px 0; font-size: 22px; color: #38bdf8; display: flex; align-items: center; gap: 8px; }
    p { color: #94a3b8; font-size: 14px; line-height: 1.5; margin: 0 0 20px 0; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; background: ${res.status === 204 ? "#065f46" : "#7f1d1d"}; color: ${res.status === 204 ? "#34d399" : "#f87171"}; margin-bottom: 20px; }
    .btn { display: block; width: 100%; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: 600; text-align: center; text-decoration: none; margin-bottom: 10px; box-sizing: border-box; transition: 0.2s; }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-secondary { background: #334155; color: #e2e8f0; }
    .schedule { margin-top: 20px; border-top: 1px solid #334155; padding-top: 16px; font-size: 13px; color: #cbd5e1; }
    .schedule li { margin-bottom: 6px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🎬 CurioCut Dispatcher</h1>
    <p>Triggered slot: <strong>${targetSlot.toUpperCase()}</strong></p>
    <div class="badge">${res.status === 204 ? "✓ DISPATCH SENT (Status 204)" : "⚠ Status: " + res.status}</div>
    <a href="/trigger/classic" class="btn btn-primary">⚡ Trigger Classic Story (Slot 1 & 2)</a>
    <a href="/trigger/tech" class="btn btn-secondary">🤖 Trigger 3D Claude-Desk (Slot 3)</a>
    <div class="schedule">
      <strong>Active Daily Schedule:</strong>
      <ul>
        <li>12:25 PM IST -> Classic Story 1 (1:00 PM)</li>
        <li>05:55 PM IST -> Classic Story 2 (7:00 PM)</li>
        <li>08:55 PM IST -> 3D Claude-Desk (9:30 PM)</li>
      </ul>
    </div>
  </div>
</body>
</html>`;

    return new Response(html, {
      status: 200,
      headers: { "Content-Type": "text/html; charset=utf-8" }
    });
  }
};


