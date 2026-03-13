# core/paywall.py
"""
Paywall / feature-gate module for qwhizz.

Access tiers (stored on user MongoDB document):
  is_admin  → full access to all features
  is_pro    → paid tier, access to AI deck generation
  (neither) → free tier, basic study only
"""

from __future__ import annotations
import streamlit as st
from data.user_store import get_user

# ── Feature definitions ───────────────────────────────────────────────────────

FEATURE_TIERS: dict[str, str] = {
    "ai_deck_gen":      "admin",   # Change to "pro" when ready to sell
    "bulk_import":      "admin",
    "manage_decks":     "admin",
    "duplicate_detect": "admin",
    "export":           "pro",
    "study":            "free",
}

UPGRADE_MESSAGES: dict[str, str] = {
    "ai_deck_gen": (
        "🤖 **AI Deck Generation** is a Pro feature. "
        "Upgrade to Pro to generate flashcard decks from PDFs, documents, and URLs."
    ),
    "bulk_import":   "📥 **Bulk Import** is an Admin feature.",
    "manage_decks":  "🗂️ **Deck Management** is restricted to administrators.",
    "export": (
        "📤 **Export** is a Pro feature. Upgrade to Pro to download your decks."
    ),
}


# ── Tier resolution ───────────────────────────────────────────────────────────

def _get_user_tier(username: str) -> str:
    user = get_user(username)
    if not user:
        return "free"
    if user.get("is_admin"):
        return "admin"
    if user.get("is_pro"):
        return "pro"
    return "free"


def _tier_rank(tier: str) -> int:
    return {"free": 0, "pro": 1, "admin": 2}.get(tier, 0)


def has_access(feature: str, username: str) -> bool:
    required  = FEATURE_TIERS.get(feature, "admin")
    user_tier = _get_user_tier(username)
    return _tier_rank(user_tier) >= _tier_rank(required)


def require_feature(feature: str, username: str) -> bool:
    """Return True if allowed. If denied, render upgrade banner and return False."""
    if has_access(feature, username):
        return True
    msg = UPGRADE_MESSAGES.get(feature, "🔒 This feature requires a higher access tier.")
    st.warning(msg)
    _render_upgrade_cta(feature, username)
    return False


# ── Stripe Checkout ───────────────────────────────────────────────────────────

def _create_checkout_url(username: str, email: str) -> str | None:
    """
    Create a Stripe Checkout session and return the URL.
    Requires STRIPE_SECRET_KEY and STRIPE_PRICE_ID in st.secrets.
    """
    try:
        import stripe
        stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=email,               # used by webhook to match user
            line_items=[{
                "price": st.secrets["STRIPE_PRICE_ID"],  # your monthly price ID
                "quantity": 1,
            }],
            success_url=st.secrets.get(
                "STRIPE_SUCCESS_URL",
                "https://yourapp.streamlit.app/?upgrade=success"
            ),
            cancel_url=st.secrets.get(
                "STRIPE_CANCEL_URL",
                "https://yourapp.streamlit.app/?upgrade=cancelled"
            ),
            metadata={"username": username},
        )
        return session.url
    except Exception as e:
        st.error(f"Could not create checkout session: {e}")
        return None


def _render_upgrade_cta(feature: str, username: str):
    required = FEATURE_TIERS.get(feature, "admin")

    if required == "admin":
        st.info("Contact your administrator to enable this feature.")
        return

    # Pro upgrade flow
    user = get_user(username)
    email = user.get("email", "") if user else ""

    if not email:
        st.info("Add an email address to your profile to upgrade to Pro.")
        return

    st.markdown("---")
    st.markdown("### ⭐ Upgrade to Pro")
    st.markdown("Unlock AI deck generation, exports, and more.")

    if st.button("💳 Subscribe — $X/month", key=f"upgrade_btn_{feature}", type="primary"):
        with st.spinner("Creating checkout session…"):
            url = _create_checkout_url(username, email)
        if url:
            st.markdown(
                f'<meta http-equiv="refresh" content="0; url={url}">',
                unsafe_allow_html=True
            )
            st.markdown(f"[Click here if not redirected]({url})")

    # Handle return from Stripe
    params = st.query_params
    if params.get("upgrade") == "success":
        st.success("🎉 Payment successful! Your Pro access will activate within a minute.")
    elif params.get("upgrade") == "cancelled":
        st.info("Upgrade cancelled. You can subscribe any time.")


# ── Admin helpers ─────────────────────────────────────────────────────────────

def grant_pro(username: str) -> bool:
    try:
        from data.db import get_database
        get_database().users.update_one({"_id": username}, {"$set": {"is_pro": True}})
        return True
    except Exception:
        return False


def revoke_pro(username: str) -> bool:
    try:
        from data.db import get_database
        get_database().users.update_one({"_id": username}, {"$set": {"is_pro": False}})
        return True
    except Exception:
        return False