#!/usr/bin/env python3
"""
email_agent.py — Automated email sequences for new sign-ups and lead nurturing.
Integrates with Mailchimp (free up to 500 contacts) or Resend.com ($20/mo for 50k emails).

SETUP:
  pip install mailchimp-marketing resend anthropic python-dotenv
  export RESEND_API_KEY=re_xxx       (preferred — simpler, $20/mo)
  export MAILCHIMP_API_KEY=xxx-us1   (alternative — free tier)
  export MAILCHIMP_LIST_ID=xxx
  export FROM_EMAIL=hello@resumeaipro.com
  export SITE_URL=https://resumeaipro.com

TRIGGER: Called by Stripe webhook when new customer subscribes (see stripe/webhook.py)
Also run daily via scheduler to send scheduled nurture emails.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    USE_RESEND = bool(os.environ.get("RESEND_API_KEY"))
except ImportError:
    USE_RESEND = False

FROM_EMAIL = os.environ.get("FROM_EMAIL", "hello@resumeaipro.com")
SITE_URL = os.environ.get("SITE_URL", "https://resumeaipro.com")

# ---- EMAIL TEMPLATES ----

SEQUENCES = {
    "free_signup": [
        {
            "delay_days": 0,
            "subject": "Your ATS score is ready 🎯",
            "template": "welcome_free",
        },
        {
            "delay_days": 1,
            "subject": "The #1 reason you're not getting callbacks (it's not your experience)",
            "template": "day1_education",
        },
        {
            "delay_days": 3,
            "subject": "Quick question about your job search...",
            "template": "day3_survey",
        },
        {
            "delay_days": 5,
            "subject": "3 things top candidates do that you're probably skipping",
            "template": "day5_tips",
        },
        {
            "delay_days": 7,
            "subject": "Still job hunting? Here's your shortcut 🚀",
            "template": "day7_upgrade",
        },
        {
            "delay_days": 14,
            "subject": "Last chance: 20% off Pro this week only",
            "template": "day14_discount",
        },
    ],
    "pro_subscriber": [
        {
            "delay_days": 0,
            "subject": "Welcome to Pro! Here's everything you can do 🎉",
            "template": "pro_welcome",
        },
        {
            "delay_days": 3,
            "subject": "Have you tried the cover letter generator yet?",
            "template": "pro_feature_coverletter",
        },
        {
            "delay_days": 7,
            "subject": "How's the job search going?",
            "template": "pro_checkin",
        },
        {
            "delay_days": 21,
            "subject": "Tips from users who got hired this month",
            "template": "pro_success_tips",
        },
    ],
}

TEMPLATES = {
    "welcome_free": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <h2 style="color:#111827;font-size:1.3rem;margin-bottom:16px">Hey {name}, your free analysis is ready 👋</h2>
  <p>Thanks for checking out ResumeAI Pro! Your resume analyzer is ready at the link below.</p>
  <p>Here's what you get for free:</p>
  <ul style="padding-left:20px;line-height:2">
    <li>Your ATS compatibility score (0–100)</li>
    <li>Top 3 critical issues holding you back</li>
    <li>Keywords you're missing for your target role</li>
  </ul>
  <a href="{SITE_URL}#demo" style="display:inline-block;background:#2563eb;color:#fff;padding:14px 28px;border-radius:8px;font-weight:700;text-decoration:none;margin:20px 0">
    Analyze My Resume →
  </a>
  <p style="color:#6b7280;font-size:.85rem">If you want the full rewrite + unlimited cover letters, <a href="{SITE_URL}#pricing" style="color:#2563eb">Pro is $29/month</a>.</p>
  <p>Let me know if you have any questions — just reply to this email.</p>
  <p>— The ResumeAI Pro Team</p>
</div>
""",
    "day1_education": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <h2 style="color:#111827;font-size:1.2rem">Hey {name} — the real reason you're getting ghosted</h2>
  <p>Quick stat that changed how I think about job applications:</p>
  <blockquote style="border-left:4px solid #2563eb;padding-left:16px;color:#4b5563;font-style:italic;margin:20px 0">
    <strong>75% of resumes are rejected by software before a single human reads them.</strong>
  </blockquote>
  <p>These systems — called Applicant Tracking Systems (ATS) — scan for:</p>
  <ul style="padding-left:20px;line-height:2">
    <li><strong>Exact keyword matches</strong> from the job description</li>
    <li><strong>Standard section headers</strong> (not creative ones)</li>
    <li><strong>Parseable formatting</strong> (no tables, columns, graphics)</li>
    <li><strong>Quantified achievements</strong> (numbers = higher score)</li>
  </ul>
  <p>If your resume fails any of these, it never reaches the hiring manager — no matter how qualified you are.</p>
  <p>This is exactly what our analyzer checks. If you haven't run your resume through it yet:</p>
  <a href="{SITE_URL}#demo" style="display:inline-block;background:#2563eb;color:#fff;padding:14px 28px;border-radius:8px;font-weight:700;text-decoration:none;margin:16px 0">
    Check My ATS Score Free →
  </a>
  <p style="color:#6b7280;font-size:.85rem">Tomorrow I'll share the 3 most common ATS mistakes we see (and how to fix them in 10 min).</p>
</div>
""",
    "day7_upgrade": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <h2 style="color:#111827;font-size:1.2rem">Ready to 3x your interview rate, {name}?</h2>
  <p>It's been a week since you signed up. Here's what Pro members got done this week:</p>
  <ul style="padding-left:20px;line-height:2">
    <li>Unlimited resume rewrites (target each job specifically)</li>
    <li>AI cover letters in 30 seconds</li>
    <li>LinkedIn headline optimization</li>
    <li>Job description keyword matcher</li>
  </ul>
  <p>Our Pro users average <strong>3.2x more interview callbacks</strong> within 2 weeks.</p>
  <div style="background:#eff6ff;border-radius:10px;padding:20px;margin:20px 0;text-align:center">
    <div style="font-size:1.5rem;font-weight:900;color:#1d4ed8">$29/month</div>
    <div style="color:#4b5563;margin:8px 0">Cancel anytime · 30-day money back</div>
    <a href="{SITE_URL}#pricing" style="display:inline-block;background:#2563eb;color:#fff;padding:12px 28px;border-radius:8px;font-weight:700;text-decoration:none;margin-top:8px">
      Upgrade to Pro →
    </a>
  </div>
  <p style="color:#6b7280;font-size:.85rem">Still on the fence? Reply to this email and tell me what's holding you back. I read every reply.</p>
</div>
""",
    "pro_welcome": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <h2 style="color:#111827;font-size:1.2rem">You're in, {name}! Here's your Pro quick-start 🚀</h2>
  <p>Welcome to ResumeAI Pro! Here's how to get your first interview callback fast:</p>
  <ol style="padding-left:20px;line-height:2.2">
    <li><strong>Run your resume through the ATS analyzer</strong> → get your score</li>
    <li><strong>Paste a job description</strong> → see exact keywords to add</li>
    <li><strong>Click "Rewrite for This Job"</strong> → AI rewrites your resume for that specific role</li>
    <li><strong>Generate a cover letter</strong> → takes 30 seconds</li>
    <li><strong>Apply</strong> → watch the callbacks come in</li>
  </ol>
  <a href="{SITE_URL}/app" style="display:inline-block;background:#2563eb;color:#fff;padding:14px 28px;border-radius:8px;font-weight:700;text-decoration:none;margin:16px 0">
    Open My Dashboard →
  </a>
  <p>Questions? Just reply. We usually respond in under 2 hours.</p>
  <p>Rooting for you,<br>— ResumeAI Pro Team</p>
</div>
""",
    # Add more templates as needed
    "day3_survey": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <p>Hey {name},</p>
  <p>Quick question — where are you in your job search right now?</p>
  <p>Just reply with a number:</p>
  <ol style="padding-left:20px;line-height:2.5">
    <li>Just starting — updating my resume</li>
    <li>Actively applying — not getting responses</li>
    <li>Getting some interviews — preparing now</li>
    <li>Just got a job offer — doing research</li>
  </ol>
  <p>I ask because I want to send you the most relevant tips for where you actually are right now.</p>
  <p>Takes 5 seconds — just reply "1", "2", "3", or "4".</p>
  <p>— The Team</p>
</div>
""",
    "day5_tips": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <h2 style="color:#111827;font-size:1.2rem">3 things successful candidates do differently</h2>
  <p>Hey {name},</p>
  <p>After analyzing thousands of resumes, here are the 3 things that consistently separate people who get interviews from those who don't:</p>
  <p><strong>1. They tailor every application.</strong> Not just the cover letter — the resume itself. They paste the job description, find keywords, and weave them in. This alone can 2x your callback rate.</p>
  <p><strong>2. They quantify everything.</strong> Not "improved sales" — "increased Q3 sales by 34% ($180k revenue)". Numbers make ATS systems and humans both pay attention.</p>
  <p><strong>3. They follow up.</strong> 48-72 hours after applying, they send a 2-sentence email to the hiring manager. Most candidates never do this. It's a huge differentiator.</p>
  <p>ResumeAI Pro automates #1 and #2. If you haven't upgraded yet: <a href="{SITE_URL}#pricing" style="color:#2563eb;font-weight:700">$29/month → Start here</a></p>
  <p>More tips Friday,<br>— ResumeAI Pro</p>
</div>
""",
    "day14_discount": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <h2 style="color:#111827;font-size:1.2rem">20% off — expires Friday, {name}</h2>
  <p>Still haven't landed interviews yet?</p>
  <p>I want to make it easier to try Pro. Use code <strong>GETJOB20</strong> for 20% off your first month — that's <strong>$23.20</strong> instead of $29.</p>
  <a href="{SITE_URL}#pricing" style="display:inline-block;background:#16a34a;color:#fff;padding:14px 28px;border-radius:8px;font-weight:700;text-decoration:none;margin:16px 0">
    Claim 20% Off → Use Code: GETJOB20
  </a>
  <p>Offer expires Friday at midnight. After that it's back to $29.</p>
  <p>30-day money back guarantee if it doesn't get you more interviews.</p>
</div>
""",
    "pro_feature_coverletter": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <p>Hey {name},</p>
  <p>Have you tried the cover letter generator yet?</p>
  <p>Here's how it works: paste the job description, click generate, and get a personalized cover letter in 30 seconds that references the specific role requirements.</p>
  <p>Most people skip cover letters or write generic ones. With AI, you can write a tailored one for every application in the time it takes to make coffee.</p>
  <a href="{SITE_URL}/app#coverletter" style="display:inline-block;background:#2563eb;color:#fff;padding:12px 24px;border-radius:8px;font-weight:700;text-decoration:none;margin:16px 0">
    Try Cover Letter Generator →
  </a>
  <p>Let me know how it goes!</p>
</div>
""",
    "pro_checkin": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <p>Hey {name},</p>
  <p>Just checking in — how's the job search going?</p>
  <p>If you've been getting interviews, amazing! Reply and let me know — I'd love to hear your story.</p>
  <p>If things are still slow, reply with a bit about your situation and I'll personally give you some targeted advice. No bots — I actually read these.</p>
  <p>— The Team</p>
</div>
""",
    "pro_success_tips": lambda name: f"""
<div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:40px 20px;color:#374151">
  <div style="font-size:1.4rem;font-weight:800;color:#2563eb;margin-bottom:24px">ResumeAI Pro</div>
  <h2 style="color:#111827;font-size:1.2rem">What got people hired this month</h2>
  <p>Hey {name},</p>
  <p>Three quick patterns from users who got hired in the last 30 days:</p>
  <p>🎯 <strong>They applied to 10-15 jobs/week</strong> (not 2-3). Volume matters when your conversion rate is improving.</p>
  <p>📝 <strong>They customized each resume</strong> using the Job Match feature — adding 3-5 keywords specific to each role.</p>
  <p>📞 <strong>They followed up within 48 hours</strong> — a simple "I wanted to reiterate my interest and ask if you need any additional info" email.</p>
  <p>Keep going — the callbacks are coming.</p>
  <p>— ResumeAI Pro Team</p>
</div>
""",
}


def send_email_resend(to: str, subject: str, html: str):
    if not USE_RESEND:
        print(f"[email_agent] MOCK SEND to {to}: {subject}")
        return {"id": "mock-id"}

    params = {
        "from": FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    return resend.Emails.send(params)


def enqueue_sequence(email: str, name: str, sequence: str = "free_signup"):
    """Add a user to an email sequence. Called on sign-up."""
    queue_file = Path("content/.email_queue.json")
    queue = json.loads(queue_file.read_text()) if queue_file.exists() else []

    now = datetime.now()
    for step in SEQUENCES[sequence]:
        send_at = (now + timedelta(days=step["delay_days"])).isoformat()
        queue.append({
            "email": email,
            "name": name,
            "sequence": sequence,
            "template": step["template"],
            "subject": step["subject"],
            "send_at": send_at,
            "sent": False,
        })

    queue_file.write_text(json.dumps(queue, indent=2))
    print(f"[email_agent] Queued {len(SEQUENCES[sequence])} emails for {email}")


def process_queue():
    """Send any emails that are due. Run this daily via cron."""
    queue_file = Path("content/.email_queue.json")
    if not queue_file.exists():
        print("[email_agent] No queue file found.")
        return

    queue = json.loads(queue_file.read_text())
    now = datetime.now()
    sent_count = 0

    for item in queue:
        if item["sent"]:
            continue
        if datetime.fromisoformat(item["send_at"]) > now:
            continue

        template_fn = TEMPLATES.get(item["template"])
        if not template_fn:
            print(f"[email_agent] Unknown template: {item['template']}")
            continue

        html = template_fn(item["name"])
        result = send_email_resend(item["email"], item["subject"], html)
        item["sent"] = True
        item["sent_at"] = now.isoformat()
        item["resend_id"] = result.get("id")
        sent_count += 1
        print(f"[email_agent] Sent: {item['subject']} → {item['email']}")

    queue_file.write_text(json.dumps(queue, indent=2))
    print(f"[email_agent] Processed queue. Sent {sent_count} emails.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test: enqueue a test user and immediately process
        enqueue_sequence("test@example.com", "Test User", "free_signup")
        process_queue()
    else:
        process_queue()
