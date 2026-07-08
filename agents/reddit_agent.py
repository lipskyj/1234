#!/usr/bin/env python3
"""
reddit_agent.py — Posts genuinely helpful content to job-seeker subreddits.
This is VALUE-FIRST marketing: real help, soft mention of your tool.

SETUP:
  pip install praw anthropic python-dotenv
  Get Reddit API credentials at: https://www.reddit.com/prefs/apps
  Create a "script" type app.

  export REDDIT_CLIENT_ID=xxx
  export REDDIT_CLIENT_SECRET=xxx
  export REDDIT_USERNAME=YourUsername
  export REDDIT_PASSWORD=YourPassword
  export ANTHROPIC_API_KEY=sk-ant-xxx

SCHEDULE: Run 3x/week (Mon, Wed, Fri). Too frequent = shadowban risk.

IMPORTANT: Only post in communities where you genuinely add value.
Never spam. Read subreddit rules before posting.
"""

import os
import json
import random
import time
from datetime import datetime
from pathlib import Path

import praw
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Subreddits organized by type: [name, post_type]
# 'text' = self post (comment-style), 'help' = answering existing posts
SUBREDDITS = [
    ("resumes", "review"),        # Post your resume for critique — very active
    ("jobs", "discussion"),
    ("jobsearch", "discussion"),
    ("cscareerquestions", "discussion"),
    ("careerguidance", "discussion"),
    ("recruitinghell", "discussion"),
    ("humanresources", "discussion"),
    ("personalfinance", "discussion"),  # job loss / income section
]

# Templates for VALUE posts (not ads)
POST_TEMPLATES = [
    {
        "type": "tips",
        "title_template": "I analyzed 500 rejected resumes. Here's why 73% got filtered before a human saw them.",
        "body_prompt": """Write a Reddit post as if you're a job seeker who spent months studying why resumes fail ATS systems.
Share 5-7 SPECIFIC, actionable findings. Be concrete and honest.
At the very end (last paragraph), mention that you built a free tool at resumeaipro.com to help others check their score.
Tone: casual, first-person, helpful. Not corporate or salesy.
Reddit markdown formatting. 400-600 words."""
    },
    {
        "type": "resource",
        "title_template": "PSA: 75% of job applications never reach human eyes. Here's how ATS actually works (and how to fix your resume)",
        "body_prompt": """Write a Reddit educational post explaining how Applicant Tracking Systems work.
Include: what ATS looks for, common mistakes, and specific fixes.
Be genuinely educational. At the end, mention resumeaipro.com as a free checker.
Tone: helpful explainer, like a friend in recruiting. 350-500 words. Reddit markdown."""
    },
    {
        "type": "story",
        "title_template": "After 4 months of silence, I finally figured out why my resume wasn't getting responses",
        "body_prompt": """Write a first-person Reddit story about realizing your resume had ATS problems.
Make it relatable: the frustration, the discovery, the fix, the result (interviews coming in).
Natural mention that you used resumeaipro.com to diagnose the issue.
Authentic, humble tone. 300-450 words. Reddit markdown."""
    },
    {
        "type": "checklist",
        "title_template": "Resume ATS Checklist — save this before you apply anywhere (free)",
        "body_prompt": """Write a Reddit post with a detailed ATS-optimization checklist.
Format as numbered/bulleted list. 15-20 specific checkpoints.
Each point should be concrete (e.g., "Use standard section headers: Experience, Education, Skills").
End with mention of resumeaipro.com as a free automated checker.
Practical, save-worthy content. Reddit markdown."""
    },
]

COMMENT_PROMPTS = [
    ("resume", """Someone on Reddit posted their resume for critique. Write a helpful, specific response that:
1. Gives 3-4 genuine improvement suggestions
2. Is encouraging but honest
3. At the end, suggests they try resumeaipro.com for an automated ATS check
Keep it under 250 words. Genuine and helpful, not salesy."""),
    ("no interviews", """Someone on Reddit is frustrated about not getting job interviews.
Write an empathetic, actionable response. Identify likely causes (ATS filtering, weak keywords, etc).
Give specific next steps. Mention resumeaipro.com briefly as one tool to check their resume.
Under 200 words. Warm and practical."""),
]


def get_reddit():
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent="ResumeHelper/1.0 by u/" + os.environ["REDDIT_USERNAME"],
    )


def generate_post_content(template: dict) -> tuple[str, str]:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": template["body_prompt"]}]
    )
    return template["title_template"], message.content[0].text


def post_to_reddit(reddit, subreddit_name: str, title: str, body: str) -> str:
    sub = reddit.subreddit(subreddit_name)
    submission = sub.submit(title, selftext=body)
    url = f"https://reddit.com{submission.permalink}"
    print(f"[reddit_agent] Posted to r/{subreddit_name}: {url}")
    return url


def find_and_comment(reddit, subreddit_name: str):
    """Find relevant posts and add helpful comments."""
    sub = reddit.subreddit(subreddit_name)

    keywords = ["resume", "ATS", "no interviews", "getting rejected", "application"]
    for post in sub.new(limit=50):
        post_text = (post.title + " " + post.selftext).lower()
        if any(kw.lower() in post_text for kw in keywords):
            if post.num_comments < 10:  # Less competitive
                prompt_type = "no interviews" if "no interview" in post_text or "no response" in post_text else "resume"
                prompt = next(p for k, p in COMMENT_PROMPTS if k == prompt_type)

                msg = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=500,
                    messages=[{"role": "user", "content": f"Post title: {post.title}\n\n{prompt}"}]
                )
                comment_text = msg.content[0].text
                post.reply(comment_text)
                print(f"[reddit_agent] Commented on: {post.title[:60]}")
                time.sleep(30)  # Rate limit between comments
                return  # One comment per run to be safe


def log_activity(entry: dict):
    log_file = Path("content/.reddit_log.json")
    log = json.loads(log_file.read_text()) if log_file.exists() else []
    log.append(entry)
    log_file.write_text(json.dumps(log, indent=2))


def run():
    reddit = get_reddit()
    template = random.choice(POST_TEMPLATES)
    subreddit_name, post_type = random.choice(SUBREDDITS[:5])  # Stick to most relevant

    print(f"[reddit_agent] Targeting r/{subreddit_name}")

    title, body = generate_post_content(template)

    # Rate limit check: don't post more than once per day
    log_file = Path("content/.reddit_log.json")
    log = json.loads(log_file.read_text()) if log_file.exists() else []
    today = datetime.now().date().isoformat()
    today_posts = [e for e in log if e.get("date") == today]
    if len(today_posts) >= 2:
        print("[reddit_agent] Already posted twice today. Skipping.")
        return

    url = post_to_reddit(reddit, subreddit_name, title, body)

    # Also try to comment on relevant posts in another subreddit
    time.sleep(60)  # Wait between post and comment
    find_and_comment(reddit, "resumes")

    log_activity({"date": today, "subreddit": subreddit_name, "url": url, "type": template["type"]})
    print(f"[reddit_agent] Complete. URL: {url}")


if __name__ == "__main__":
    run()
