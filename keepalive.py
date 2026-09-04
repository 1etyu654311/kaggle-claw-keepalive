#!/usr/bin/env python3
"""
🦅 Claw Agent KeepAlive
Checks whether the Kaggle notebook hosting the Claw agent is running.
If it stopped (session timeout / error), re-pushes it to restart.

Run from GitHub Actions on a cron schedule (default: every 25 min).
Requires env: KAGGLE_USERNAME, KAGGLE_KEY
"""
import os
import sys
import subprocess
import datetime

USER = os.environ.get("KAGGLE_USERNAME", "")
KEY = os.environ.get("KAGGLE_KEY", "")
KERNEL = f"{USER}/claw-agent"
KERNEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kernel")

os.environ["KAGGLE_USERNAME"] = USER
os.environ["KAGGLE_KEY"] = KEY

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout + r.stderr

def get_status():
    out = sh(["kaggle", "kernels", "status", KERNEL])
    return out.strip()

def main():
    if not USER or not KEY:
        print("❌ Missing KAGGLE_USERNAME / KAGGLE_KEY")
        sys.exit(1)

    status = get_status()
    print(f"[{now}] Kernel status: {status}")

    if "RUNNING" in status:
        print("✅ Agent is running. Nothing to do.")
        return

    print("⚠️  Agent not running. Restarting via push...")
    out = sh(["kaggle", "kernels", "push", "-p", KERNEL_DIR])
    print(out)
    if "successfully pushed" in out.lower() or "Successfully pushed" in out:
        print("🔄 Restart triggered.")
    else:
        print("⚠️  Push output unclear — check manually: "
              f"https://www.kaggle.com/code/{KERNEL}")

if __name__ == "__main__":
    main()