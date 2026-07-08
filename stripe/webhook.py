#!/usr/bin/env python3
"""
stripe/webhook.py — Handles Stripe payment events.
Deploy this as a Flask/FastAPI endpoint or use a serverless function.

SETUP:
  pip install flask stripe
  export STRIPE_SECRET_KEY=sk_live_xxx
  export STRIPE_WEBHOOK_SECRET=whsec_xxx  (from Stripe Dashboard > Webhooks)

  Run locally: python webhook.py
  Deploy: Vercel (free), Railway ($5/mo), or any VPS

  Stripe Dashboard: Set webhook URL to https://yourdomain.com/webhook
  Events to listen for:
    - checkout.session.completed
    - customer.subscription.deleted
    - customer.subscription.updated
    - invoice.payment_failed
"""

import os
import json
import sys
from pathlib import Path

# Add parent to path for agents
sys.path.insert(0, str(Path(__file__).parent.parent))

import stripe
from flask import Flask, request, jsonify

# Import our agents
from agents.email_agent import enqueue_sequence

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

app = Flask(__name__)

# Map Stripe price IDs to plan names
PRICE_PLANS = {
    os.environ.get("STRIPE_PRICE_PRO", "price_pro_id"): "pro_subscriber",
    os.environ.get("STRIPE_PRICE_CAREER", "price_career_id"): "pro_subscriber",
}

CUSTOMERS_FILE = Path("content/.customers.json")


def load_customers() -> list:
    return json.loads(CUSTOMERS_FILE.read_text()) if CUSTOMERS_FILE.exists() else []


def save_customer(customer: dict):
    customers = load_customers()
    # Update if exists
    existing = next((c for c in customers if c["email"] == customer["email"]), None)
    if existing:
        existing.update(customer)
    else:
        customers.append(customer)
    CUSTOMERS_FILE.write_text(json.dumps(customers, indent=2))


def get_mrr() -> float:
    """Calculate current MRR from active subscribers."""
    customers = load_customers()
    plan_prices = {"pro": 29.0, "career": 49.0}
    mrr = sum(plan_prices.get(c.get("plan", ""), 0) for c in customers if c.get("status") == "active")
    return mrr


@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError:
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400

    event_type = event["type"]
    data = event["data"]["object"]

    print(f"[webhook] Event: {event_type}")

    if event_type == "checkout.session.completed":
        handle_new_subscriber(data)

    elif event_type == "customer.subscription.deleted":
        handle_cancellation(data)

    elif event_type == "invoice.payment_failed":
        handle_payment_failed(data)

    elif event_type == "customer.subscription.updated":
        handle_subscription_updated(data)

    return jsonify({"status": "ok"}), 200


def handle_new_subscriber(session: dict):
    """Called when someone completes checkout."""
    email = session.get("customer_email") or session.get("customer_details", {}).get("email", "")
    customer_id = session.get("customer")
    name = session.get("customer_details", {}).get("name", "").split()[0] or "there"

    # Look up which plan they bought
    line_items = stripe.checkout.Session.list_line_items(session["id"])
    price_id = line_items.data[0].price.id if line_items.data else ""
    sequence = PRICE_PLANS.get(price_id, "pro_subscriber")
    plan = "pro" if "pro" in price_id.lower() else "career"

    print(f"[webhook] New subscriber: {email} → {plan}")

    # Save customer
    save_customer({
        "email": email,
        "name": name,
        "customer_id": customer_id,
        "plan": plan,
        "status": "active",
        "subscribed_at": session.get("created"),
    })

    # Start email sequence
    enqueue_sequence(email, name, sequence)

    # Log MRR
    mrr = get_mrr()
    print(f"[webhook] 💰 Current MRR: ${mrr:.2f} / Target: $5000")


def handle_cancellation(subscription: dict):
    customer_id = subscription.get("customer")
    customers = load_customers()
    customer = next((c for c in customers if c.get("customer_id") == customer_id), None)
    if customer:
        customer["status"] = "cancelled"
        CUSTOMERS_FILE.write_text(json.dumps(customers, indent=2))
        print(f"[webhook] Cancelled: {customer.get('email')}")


def handle_payment_failed(invoice: dict):
    customer_id = invoice.get("customer")
    customers = load_customers()
    customer = next((c for c in customers if c.get("customer_id") == customer_id), None)
    if customer:
        email = customer.get("email", "")
        name = customer.get("name", "there")
        print(f"[webhook] Payment failed: {email}")
        # Enqueue dunning email (add to email_agent sequences if needed)


def handle_subscription_updated(subscription: dict):
    pass  # Handle plan upgrades/downgrades if needed


@app.route("/mrr", methods=["GET"])
def show_mrr():
    """Quick MRR dashboard endpoint."""
    customers = load_customers()
    active = [c for c in customers if c.get("status") == "active"]
    mrr = get_mrr()
    target = 5000
    return jsonify({
        "mrr": mrr,
        "target": target,
        "progress_pct": round(mrr / target * 100, 1),
        "active_subscribers": len(active),
        "needed_to_target": max(0, target - mrr),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[webhook] Starting on port {port}")
    print(f"[webhook] Webhook URL: http://localhost:{port}/webhook")
    app.run(host="0.0.0.0", port=port, debug=False)
