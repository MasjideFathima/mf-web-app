import streamlit as st
import uuid
from datetime import date
from utils.auth import require_login, is_admin
from utils.db import get_categories, insert_transaction, upload_photo, receipt_number_exists
from utils.whatsapp import send_whatsapp_notification

require_login()
st.title("➕ Add Transaction")

txn_type = st.radio("Type", ["income", "expense"], horizontal=True)
categories = get_categories(txn_type)
cat_names = [c["name"] for c in categories]

with st.form("add_txn_form", clear_on_submit=True):
    category_name = st.selectbox("Category", cat_names)
    amount = st.number_input("Amount (₹)", min_value=0.0, step=1.0)
    txn_date = st.date_input("Date", value=date.today())
    payment_method = st.radio("Payment Method", ["Cash", "GPay/Bank"], horizontal=True, index=0)
    receipt_number = ""
    donor_name = ""
    donor_phone = ""
    if txn_type == "income":
        receipt_number = st.text_input(
            "Receipt Number (as written on the physical receipt book)"
        )
        donor_name = st.text_input("Donor Name")
        donor_phone = st.text_input(
            "Donor Mobile Number (for WhatsApp confirmation once approved)",
            placeholder="e.g. 9876543210"
        )
    description = st.text_area("Description / Notes", placeholder="e.g. Purpose, etc.")
    photo = st.file_uploader("Upload photo of receipt/item (optional)", type=["jpg", "jpeg", "png"])

    submitted = st.form_submit_button("Submit")

    if submitted:
        if amount <= 0:
            st.error("Amount must be greater than 0.")
            st.stop()
        if txn_type == "income" and receipt_number and receipt_number_exists(receipt_number):
            st.error(f"Receipt number '{receipt_number}' has already been recorded. Check for duplicate entry.")
            st.stop()

        photo_url = None
        if photo is not None:
            ext = photo.name.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            photo_url = upload_photo(photo.getvalue(), filename, photo.type)

        category_id = next(c["id"] for c in categories if c["name"] == category_name)

        record = {
            "type": txn_type,
            "category_id": category_id,
            "amount": amount,
            "txn_date": txn_date.isoformat(),
            "receipt_number": receipt_number or None,
            "donor_name": donor_name or None,
            "donor_phone": donor_phone or None,
            "payment_method": "bank" if payment_method == "GPay/Bank" else "cash",
            "description": description,
            "photo_url": photo_url,
            "submitted_by": st.session_state["user_id"],
            "status": "approved" if is_admin() else "pending",
        }
        insert_transaction(record)

        if is_admin():
            st.success("Transaction recorded and approved.")
            if txn_type == "income" and donor_phone:
                sent, msg = send_whatsapp_notification(
                    phone=donor_phone,
                    donor_name=donor_name,
                    txn_type=txn_type,
                    amount=amount,
                    receipt_number=receipt_number,
                    category_name=category_name,
                )
                if sent:
                    st.info("WhatsApp confirmation sent to donor.")
                else:
                    st.warning(f"Recorded, but WhatsApp notification failed: {msg}")
        else:
            st.success("Submitted! An admin will review and approve it.")
