/**
 * Cloudflare Worker: 100% Cloud Autonomous CurioCut Scheduler
 * Runs on Cloudflare's Global Edge Network (100,000 free requests/day, 0% delay).
 * Triggers GitHub Actions 'repository_dispatch' at the exact scheduled second!
 *
 * Setup in 60 seconds:
 * 1. Go to dash.cloudflare.com -> Workers & Pages -> Create Worker.
 * 2. Paste this code into Worker.
 * 3. Add Secret Variable in Worker Settings: GITHUB_TOKEN (Personal Access Token with 'repo' scope).
 * 4. Add Cron Triggers under Settings -> Triggers:
 *    - 25 6 * * *   (12:25 PM IST / 06:25 UTC)
 *    - 25 12 * * *  (06:25 PM IST / 12:25 UTC)
 */

export default {
  async scheduled(event, env, ctx) {
    const owner = "shlokkokk";
    const repo = "CurioCut";
    const url = `https://api.github.com/repos/${owner}/${repo}/dispatches`;

    console.log(`[CurioCut Trigger] Firing repository_dispatch at ${new Date().toISOString()}`);

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
          trigger_source: "cloudflare_worker_cron",
          scheduled_time: new Date().toISOString()
        }
      })
    });

    console.log(`GitHub API Response status: ${res.status}`);
    return res;
  },

  async fetch(request, env, ctx) {
    // Allows 1-click manual trigger from browser or phone bookmark!
    const owner = "shlokkokk";
    const repo = "CurioCut";
    const url = `https://api.github.com/repos/${owner}/${repo}/dispatches`;

    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CurioCut-Cloudflare-Manual"
      },
      body: JSON.stringify({
        event_type: "daily_short",
        client_payload: { trigger_source: "manual_url_click" }
      })
    });

    return new Response(`CurioCut Pipeline Triggered! GitHub Status: ${res.status}`, {
      headers: { "Content-Type": "text/plain" }
    });
  }
};

