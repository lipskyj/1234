#!/usr/bin/env python3
"""
content_agent.py — Generates SEO blog posts targeting job-seeker keywords.
Schedule: Run daily via cron. Publishes to your blog via API or saves as HTML files.

SETUP:
  pip install anthropic python-dotenv requests
  export ANTHROPIC_API_KEY=sk-ant-...
  export WORDPRESS_URL=https://yourblog.com (optional)
  export WORDPRESS_USER=admin
  export WORDPRESS_APP_PASSWORD=xxxx-xxxx-xxxx
"""

import anthropic
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# High-volume, low-competition SEO targets
SEO_TOPICS = [
    ("how to beat ATS resume scanner 2026", "ats-resume-scanner-tips"),
    ("resume keywords for software engineer", "software-engineer-resume-keywords"),
    ("why am i not getting job interviews", "not-getting-job-interviews"),
    ("how to write a cover letter that gets read", "cover-letter-tips"),
    ("resume action verbs that impress ATS", "resume-action-verbs"),
    ("how to tailor resume for each job application", "tailor-resume-job-application"),
    ("linkedin profile tips for job seekers 2026", "linkedin-profile-job-search"),
    ("how long should a resume be in 2026", "resume-length-guide"),
    ("resume summary vs objective which is better", "resume-summary-vs-objective"),
    ("how to get a job with no experience", "get-job-no-experience"),
    ("best resume format for career change", "career-change-resume-format"),
    ("salary negotiation email template", "salary-negotiation-email"),
    ("how to follow up after job application", "follow-up-job-application"),
    ("common resume mistakes that cost you the job", "resume-mistakes"),
    ("how to get past applicant tracking system", "get-past-ats"),
]

BLOG_SYSTEM_PROMPT = """You are an expert career coach and SEO content writer.
Write detailed, helpful blog posts for job seekers.
Tone: friendly, authoritative, practical.
Always include real actionable advice, not fluff.
Include the target keyword naturally 4-6 times.
At the end, include a soft CTA to ResumeAI Pro."""

def generate_blog_post(topic: str, slug: str) -> dict:
    print(f"[content_agent] Generating post: '{topic}'")

    prompt = f"""Write a comprehensive, SEO-optimized blog post targeting the keyword: "{topic}"

Structure:
1. Compelling H1 title (include the keyword)
2. Brief intro (2-3 sentences) with hook
3. 5-7 main sections with H2 headers
4. Bullet points or numbered lists where appropriate
5. Conclusion with summary
6. CTA paragraph mentioning ResumeAI Pro (resumeaipro.com) as a tool that helps with this

Requirements:
- 900-1200 words
- Include 2-3 statistics (real or plausible)
- Practical, specific advice
- Natural keyword usage (not stuffed)
- Output as clean HTML (h1, h2, p, ul, li tags only)

Do NOT include the outer html/body/head tags. Just the article content."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ],
        system=BLOG_SYSTEM_PROMPT
    )

    content = message.content[0].text

    return {
        "title": topic.title(),
        "slug": slug,
        "content": content,
        "generated_at": datetime.now().isoformat(),
        "keyword": topic,
        "word_count": len(content.split()),
    }


def save_post_locally(post: dict) -> str:
    output_dir = Path("content/blog")
    output_dir.mkdir(parents=True, exist_ok=True)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{post['title']} | ResumeAI Pro Blog</title>
  <meta name="description" content="Learn {post['keyword']} with expert tips from ResumeAI Pro.">
  <style>
    body{{font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:40px 20px;line-height:1.7;color:#374151}}
    h1{{font-size:2rem;color:#111827;margin-bottom:8px}}
    h2{{font-size:1.3rem;color:#1d4ed8;margin-top:32px}}
    p{{margin-bottom:16px}}
    ul,ol{{margin-bottom:16px;padding-left:24px}}
    li{{margin-bottom:6px}}
    .cta-box{{background:linear-gradient(135deg,#eff6ff,#f0fdf4);border:1px solid #bfdbfe;border-radius:12px;padding:28px;margin-top:40px;text-align:center}}
    .cta-btn{{background:#2563eb;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;display:inline-block;margin-top:12px}}
  </style>
</head>
<body>
<article>
{post['content']}
</article>
<div class="cta-box">
  <strong>Ready to beat ATS and get more interviews?</strong><br>
  ResumeAI Pro analyzes your resume in 60 seconds and shows you exactly what to fix.
  <br><a href="/" class="cta-btn">Try Free Now →</a>
</div>
</body>
</html>"""

    filepath = output_dir / f"{post['slug']}.html"
    filepath.write_text(html_template)
    print(f"[content_agent] Saved: {filepath}")
    return str(filepath)


def publish_to_wordpress(post: dict):
    """Optional: publish directly to WordPress REST API."""
    wp_url = os.environ.get("WORDPRESS_URL")
    if not wp_url:
        return

    import requests
    from requests.auth import HTTPBasicAuth

    endpoint = f"{wp_url}/wp-json/wp/v2/posts"
    auth = HTTPBasicAuth(os.environ["WORDPRESS_USER"], os.environ["WORDPRESS_APP_PASSWORD"])

    payload = {
        "title": post["title"],
        "content": post["content"],
        "slug": post["slug"],
        "status": "publish",
        "meta": {"rank_math_focus_keyword": post["keyword"]},
    }

    resp = requests.post(endpoint, json=payload, auth=auth, timeout=30)
    if resp.status_code in (200, 201):
        data = resp.json()
        print(f"[content_agent] Published to WordPress: {data.get('link')}")
    else:
        print(f"[content_agent] WordPress error {resp.status_code}: {resp.text[:200]}")


def run_daily():
    """Pick a random unused topic and generate + save the post."""
    log_file = Path("content/.published_slugs.json")
    published = json.loads(log_file.read_text()) if log_file.exists() else []

    remaining = [t for t in SEO_TOPICS if t[1] not in published]
    if not remaining:
        print("[content_agent] All topics published! Resetting queue.")
        published = []
        remaining = SEO_TOPICS

    topic, slug = random.choice(remaining)

    post = generate_blog_post(topic, slug)
    save_post_locally(post)
    publish_to_wordpress(post)

    published.append(slug)
    log_file.write_text(json.dumps(published))

    print(f"[content_agent] Done. {len(remaining)-1} topics remaining.")
    return post


if __name__ == "__main__":
    run_daily()
