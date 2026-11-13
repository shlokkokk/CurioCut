#!/usr/bin/env python3
"""
Direct live Kaggle log viewer for CurioCut.
Reads the real-time execution logs directly from Kaggle's REST API.
"""
import os
import sys
import json
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

TOKEN = os.environ.get("KAGGLE_API_TOKEN", "KGAT_2b148c0780213910a41e366af92f5e16")
USER = os.environ.get("KAGGLE_USERNAME", "shlokkshahh")
SLUG = "curiocut-gpu-engine"

def get_status(version=None):
    url = f"https://www.kaggle.com/api/v1/kernels/status?userName={USER}&kernelSlug={SLUG}"
    if version:
        url += f"&versionNumber={version}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def get_logs(tail_lines=60, version=None):
    url = f"https://www.kaggle.com/api/v1/kernels/output?userName={USER}&kernelSlug={SLUG}"
    if version:
        url += f"&versionNumber={version}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = data.get("log", "")
            if not raw:
                return []
            lines = []
            if raw.strip().startswith("[") and "stream_name" in raw:
                try:
                    entries = json.loads(raw)
                    for item in entries:
                        d = item.get("data", "")
                        for sub in d.splitlines():
                            if sub.strip():
                                lines.append(sub)
                except Exception:
                    lines = [l for l in raw.splitlines() if l.strip()]
            else:
                lines = [l for l in raw.splitlines() if l.strip()]
            return lines[-tail_lines:] if tail_lines > 0 else lines
    except Exception as e:
        return [f"Error fetching logs: {e}"]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="View live or versioned Kaggle execution logs")
    parser.add_argument("--version", "-v", type=int, default=None, help="Specific version number to inspect (defaults to latest active run)")
    parser.add_argument("--tail", "-n", type=int, default=50, help="Number of trailing lines to display")
    args = parser.parse_args()

    v_str = f"Version #{args.version}" if args.version else "Latest Active Version"
    st = get_status(version=args.version)
    print("=" * 60)
    print(f"KAGGLE RUN: {USER}/{SLUG} ({v_str})")
    print(f"STATUS: {st.get('status', 'unknown').upper()}")
    if st.get("failureMessage"):
        print(f"FAILURE MESSAGE: {st.get('failureMessage')}")
    print("=" * 60)
    logs = get_logs(tail_lines=args.tail, version=args.version)
    print(f"\n--- LOGS ({v_str} | Last {args.tail} lines) ---")
    for l in logs:
        print(l)

