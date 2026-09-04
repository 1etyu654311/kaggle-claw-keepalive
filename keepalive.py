#!/usr/bin/env python3
"""
🦅 Claw Agent KeepAlive
Checks whether the Kaggle notebook hosting the Claw agent is running.
If it stopped (session timeout / error), re-pushes it to restart.

Runs from GitHub Actions on a cron schedule.
Secrets are READ FROM ENV (GitHub Secrets) and injected into the notebook
template at push time — the repo itself contains NO real keys, so it can be
public (which keeps the cron on schedule on the free plan).

Required env: KAGGLE_USERNAME, KAGGLE_KEY
Optional env: GROQ_KEY, CLAW_TG_TOKEN, CLAW_TG_ALLOW (injected into notebook)
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
USER = os.environ.get("KAGGLE_USERNAME", "")
KEY = os.environ.get("KAGGLE_KEY", "")
KERNEL = f"{USER}/claw-agent"
TEMPLATE = os.path.join(HERE, "kernel", "claw_kaggle_template.ipynb")
METADATA = os.path.join(HERE, "kernel", "kernel-metadata.json")

os.environ["KAGGLE_USERNAME"] = USER
os.environ["KAGGLE_KEY"] = KEY

def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return (r.stdout or "") + (r.stderr or "")

def get_status():
    return sh(["kaggle", "kernels", "status", KERNEL]).strip()

def build_and_push():
    """Inject secrets into template, write to a temp dir, push."""
    with open(TEMPLATE, encoding="utf-8") as f:
        nb = f.read()
    # inject secrets from env
    nb = nb.replace("__GROQ_KEY__", os.environ.get("GROQ_KEY", ""))
    nb = nb.replace("__CLAW_TG_TOKEN__", os.environ.get("CLAW_TG_TOKEN", ""))
    nb = nb.replace("__CLAW_TG_ALLOW__", os.environ.get("CLAW_TG_ALLOW", "1894539838"))

    tmp = tempfile.mkdtemp(prefix="claw_push_")
    with open(os.path.join(tmp, "claw_kaggle.ipynb"), "w", encoding="utf-8") as f:
        f.write(nb)
    shutil.copy(METADATA, os.path.join(tmp, "kernel-metadata.json"))
    return sh(["kaggle", "kernels", "push", "-p", tmp])

def main():
    if not USER or not KEY:
        print("❌ Missing KAGGLE_USERNAME / KAGGLE_KEY")
        sys.exit(1)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = get_status()
    print(f"[{now}] Kernel status: {status}")

    if "RUNNING" in status:
        print("✅ Agent is running. Nothing to do.")
        return

    print("⚠️  Agent not running. Restarting via push...")
    out = build_and_push()
    print(out)
    if "successfully pushed" in out.lower():
        print("🔄 Restart triggered.")
    else:
        print("⚠️  Push output unclear — check: "
              f"https://www.kaggle.com/code/{KERNEL}")

if __name__ == "__main__":
    main()