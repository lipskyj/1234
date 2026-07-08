#!/usr/bin/env python3
"""
scheduler.py — Master scheduler. Run once, manages all agents.
Or use cron (see CRON SETUP below).

OPTION A: Run this script and it handles scheduling internally.
  python agents/scheduler.py

OPTION B: Add these lines to your crontab (crontab -e):
  # Daily SEO blog post (9 AM)
  0 9 * * * cd /path/to/resumeaipro && python agents/content_agent.py >> logs/content.log 2>&1

  # Reddit posts (Mon/Wed/Fri at 10 AM — peak engagement time)
  0 10 * * 1,3,5 cd /path/to/resumeaipro && python agents/reddit_agent.py >> logs/reddit.log 2>&1

  # Email queue processor (every hour)
  0 * * * * cd /path/to/resumeaipro && python agents/email_agent.py >> logs/email.log 2>&1

  # MRR report (daily 8 AM)
  0 8 * * * cd /path/to/resumeaipro && python agents/scheduler.py --report >> logs/report.log 2>&1
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

SCHEDULE = [
    # (agent, run_every_hours, last_run_key)
    ("content_agent", 24, "last_content"),
    ("reddit_agent", 48, "last_reddit"),   # Every 2 days
    ("email_agent", 1, "last_email"),
]

STATE_FILE = Path("content/.scheduler_state.json")


def load_state() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def should_run(key: str, every_hours: int, state: dict) -> bool:
    last = state.get(key)
    if not last:
        return True
    last_dt = datetime.fromisoformat(last)
    return datetime.now() - last_dt >= timedelta(hours=every_hours)


def run_agent(agent_name: str) -> bool:
    script = Path(f"agents/{agent_name}.py")
    log_file = LOG_DIR / f"{agent_name}.log"

    print(f"[scheduler] Running {agent_name}...")
    try:
        with open(log_file, "a") as lf:
            lf.write(f"\n\n=== {datetime.now().isoformat()} ===\n")
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=False,
                stdout=lf,
                stderr=lf,
                timeout=300,
                env={**os.environ},
            )
        success = result.returncode == 0
        print(f"[scheduler] {agent_name} {'✓' if success else '✗'} (exit {result.returncode})")
        return success
    except subprocess.TimeoutExpired:
        print(f"[scheduler] {agent_name} TIMEOUT")
        return False
    except Exception as e:
        print(f"[scheduler] {agent_name} ERROR: {e}")
        return False


def print_mrr_report():
    customers_file = Path("content/.customers.json")
    if not customers_file.exists():
        print("[report] No customer data yet.")
        return

    customers = json.loads(customers_file.read_text())
    active = [c for c in customers if c.get("status") == "active"]
    plan_prices = {"pro": 29.0, "career": 49.0}
    mrr = sum(plan_prices.get(c.get("plan", ""), 0) for c in active)
    target = 5000.0

    bar_len = 30
    filled = int(bar_len * mrr / target)
    bar = "█" * filled + "░" * (bar_len - filled)

    print(f"""
╔══════════════════════════════════════╗
║        ResumeAI Pro — MRR Report     ║
╠══════════════════════════════════════╣
║  MRR:     ${mrr:>8.2f} / ${target:.0f} target    ║
║  [{bar}] {mrr/target*100:.1f}%  ║
║  Subscribers: {len(active):>4} active             ║
║  Need {max(0,int((target-mrr)/29)):>3} more Pro subs to hit goal  ║
╚══════════════════════════════════════╝""")

    # Milestone celebrations
    if mrr >= 5000:
        print("  🎉 GOAL REACHED! $5K/month achieved!")
    elif mrr >= 2500:
        print("  🚀 Halfway there! Keep going.")
    elif mrr >= 1000:
        print("  ✅ $1K MRR milestone hit!")


def run_loop():
    """Main scheduler loop. Checks every 5 minutes and runs agents on schedule."""
    print(f"[scheduler] Starting at {datetime.now()}")
    print("[scheduler] Press Ctrl+C to stop")

    while True:
        state = load_state()

        for agent_name, every_hours, state_key in SCHEDULE:
            if should_run(state_key, every_hours, state):
                success = run_agent(agent_name)
                if success:
                    state[state_key] = datetime.now().isoformat()
                    save_state(state)

        print_mrr_report()
        time.sleep(300)  # Check every 5 minutes


if __name__ == "__main__":
    if "--report" in sys.argv:
        print_mrr_report()
    elif "--once" in sys.argv:
        # Run all agents once immediately
        for agent_name, _, _ in SCHEDULE:
            run_agent(agent_name)
        print_mrr_report()
    else:
        run_loop()
