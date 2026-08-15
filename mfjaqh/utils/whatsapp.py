"""
WhatsApp Cloud API notifications (Meta, official, free API access + per-message cost).

Sends a message using an already-approved template. Works for ANY phone number
typed into the app -- no need to pre-register recipients. That "5 test number"
limit only applies to Meta's sandbox test number; once you register your own
business phone number, this sends to any number dynamically.

Requires these Streamlit secrets:
    WHATSAPP_PHONE_NUMBER_ID   - from Meta App Dashboard > WhatsApp > API Setup
    WHATSAPP_ACCESS_TOKEN      - permanent System User token (not the 24h temp one)
    WHATSAPP_TEMPLATE_NAME     - the approved template name, e.g. "donation_receipt"
"""
import re
import requests
import streamlit as st

GRAPH_API_VERSION = "v21.0"


def _normalize_phone(phone: str) -> str | None:
    """Converts a loosely-formatted Indian number into E.164 (+91XXXXXXXXXX).
    Returns None if it doesn't look like a valid 10-digit Indian mobile number."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        return f"91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return digits
    if len(digits) == 13 and digits.startswith("091"):
        return digits[1:]
    return None


def send_whatsapp_notification(phone: str, donor_name: str, txn_type: str,
                                 amount: float, receipt_number: str | None,
                                 category_name: str) -> tuple[bool, str]:
    """Sends the approval notification. Returns (success, message)."""
    if not phone:
        return False, "No phone number provided, skipped."

    normalized = _normalize_phone(phone)
    if not normalized:
        return False, f"Phone number '{phone}' doesn't look valid, skipped."

    phone_number_id = st.secrets.get("WHATSAPP_PHONE_NUMBER_ID")
    access_token = st.secrets.get("WHATSAPP_ACCESS_TOKEN")
    template_name = st.secrets.get("WHATSAPP_TEMPLATE_NAME", "donation_receipt")

    if not phone_number_id or not access_token:
        return False, "WhatsApp not configured (missing secrets), skipped."

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Template placeholders, in order: {{1}} name, {{2}} type+category, {{3}} amount, {{4}} receipt no.
    body_params = [
        {"type": "text", "text": donor_name or "Donor"},
        {"type": "text", "text": category_name},
        {"type": "text", "text": f"{amount:,.2f}"},
        {"type": "text", "text": receipt_number or "N/A"},
    ]

    payload = {
        "messaging_product": "whatsapp",
        "to": normalized,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": [{"type": "body", "parameters": body_params}],
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            return True, "Notification sent."
        return False, f"WhatsApp API error ({resp.status_code}): {resp.text}"
    except requests.RequestException as e:
        return False, f"Network error sending WhatsApp notification: {e}"
