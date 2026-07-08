# External Provider Connections — What I Need From You

## What's Already Built (Zero Setup)
The app works RIGHT NOW with your Anthropic API key. The full 4-feature dashboard (Analyzer, Rewriter, Cover Letter, LinkedIn) calls Claude directly from the browser.

---

## 1. ANTHROPIC (The AI Brain) — REQUIRED FIRST
**Cost:** ~$5–20/month (Haiku model is cheap)
**Get key:** https://console.anthropic.com → API Keys → Create Key

1. Go to `app.html` → Settings tab
2. Paste your key: `sk-ant-api03-...`
3. Everything works immediately

**Or for production:** Set as environment variable `ANTHROPIC_API_KEY`

---

## 2. STRIPE (Taking Payments) — REQUIRED FOR REVENUE
**Cost:** 2.9% + 30¢ per transaction (no monthly fee)
**Get started:** https://stripe.com

### Steps:
1. Create Stripe account, add bank account
2. **Stripe Dashboard → Products → Add Product:**
   - "ResumeAI Pro" → $29/month recurring → Save → Copy `price_xxx` ID
   - "Career Boost" → $49/month recurring → Save → Copy `price_xxx` ID
3. **Payment Links → Create Link** for each product
4. In `index.html` find `checkout()` function → replace Stripe URLs:
   ```javascript
   const links = {
     pro: 'https://buy.stripe.com/YOUR_ACTUAL_PRO_LINK',
     career: 'https://buy.stripe.com/YOUR_ACTUAL_CAREER_LINK'
   };
   // Remove the alert(), uncomment: window.location.href = links[plan];
   ```
5. **Webhooks → Add Endpoint:**
   - URL: `https://your-railway-app.railway.app/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`
   - Copy Webhook Secret → set as `STRIPE_WEBHOOK_SECRET` env var

**Give me:** Your Price IDs and Payment Links → I'll wire them in automatically.

---

## 3. RESEND (Email Delivery) — REQUIRED FOR EMAIL SEQUENCES
**Cost:** Free up to 3,000 emails/month. $20/month for 50,000.
**Get started:** https://resend.com

### Steps:
1. Create account → Add Domain → Add DNS records (they give you 3 records to add)
2. API Keys → Create Key → Copy it
3. Set environment variable: `RESEND_API_KEY=re_xxx`
4. Set `FROM_EMAIL=hello@yourdomain.com`

**Why:** Every new sign-up triggers a 6-email sequence. Without this, you lose most of your free-to-paid conversions.

---

## 4. REDDIT API (Marketing Agent) — OPTIONAL BUT HIGH ROI
**Cost:** Free
**Get credentials:** https://www.reddit.com/prefs/apps

### Steps:
1. Click "Create App" → Type: **script**
2. Name: "ResumeAI Content Bot"
3. Redirect: http://localhost
4. Copy `client_id` (under app name) and `secret`
5. Set env vars:
   ```
   REDDIT_CLIENT_ID=xxx
   REDDIT_CLIENT_SECRET=xxx
   REDDIT_USERNAME=YourActualUsername
   REDDIT_PASSWORD=YourActualPassword
   ```

**Important:** Create a separate Reddit account for posting. Don't use your personal one.

---

## 5. DEPLOYMENT (Making It Live) — REQUIRED
**Recommended: Vercel (Free)**

### Landing Page + App:
```bash
# Install Vercel CLI
npm i -g vercel

# In your project directory:
vercel

# Follow prompts → get URL like: https://resumeaipro.vercel.app
# Add custom domain in Vercel dashboard
```

### Webhook Server (Python):
**Railway.app** — $5/month, easiest Python hosting

```bash
# Install Railway CLI
npm i -g @railway/cli

# In stripe/ directory:
railway login
railway init
railway up

# Set env vars in Railway dashboard:
# STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, RESEND_API_KEY, etc.
```

---

## 6. DOMAIN (Professional Credibility) — STRONGLY RECOMMENDED
**Cost:** $12–15/year
**Where:** Namecheap or Porkbun

**Best available names:**
- resumeaipro.com (~$12)
- airesumepro.com (~$12)
- atsoptimizer.com (~$12)
- beatthebots.com (~$15, memorable)

---

## Give Me These and I'll Wire Everything In:

| What | Where to get it | I need |
|------|----------------|--------|
| Anthropic API key | console.anthropic.com | `sk-ant-api03-...` |
| Stripe Pro Price ID | stripe.com/products | `price_xxx` |
| Stripe Career Price ID | stripe.com/products | `price_xxx` |
| Stripe Pro Payment Link | stripe.com/payment-links | `https://buy.stripe.com/xxx` |
| Stripe Career Payment Link | stripe.com/payment-links | `https://buy.stripe.com/xxx` |
| Stripe Webhook Secret | stripe.com/webhooks | `whsec_xxx` |
| Resend API Key | resend.com | `re_xxx` |
| Your domain | namecheap.com | e.g. resumeaipro.com |
| Reddit credentials | reddit.com/prefs/apps | client_id + secret |

**Once you give me these, I will:**
1. Wire Stripe payment links into index.html
2. Configure all environment variables
3. Deploy webhook server
4. Set up cron jobs for all agents
5. Test the full payment flow end-to-end

---

## Full System Architecture (When All Connected)

```
Visitor → index.html (landing) → Stripe checkout → payment
                                                        ↓
                                              webhook.py receives event
                                                        ↓
                                              email_agent.py → welcome email sequence
                                                        ↓
                                              customer added to .customers.json
                                                        ↓
                                              MRR dashboard updates

Daily (automated):
content_agent.py → blog post → WordPress/GitHub Pages (SEO traffic)
reddit_agent.py → value post → r/resumes, r/jobsearch (social traffic)
email_agent.py → nurture emails → free→paid conversion
scheduler.py → MRR report → your terminal
```
