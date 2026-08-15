import streamlit as st
from utils.auth import require_admin
from utils.db import get_transactions, approve_transaction, reject_transaction
from utils.whatsapp import send_whatsapp_notification

require_admin()
st.title("✅ Pending Approvals")

# Show feedback from the previous action (stored before rerun, since rerun
# would otherwise wipe out st.success/st.warning before you could see it)
if "approval_feedback" in st.session_state:
    level, text = st.session_state.pop("approval_feedback")
    getattr(st, level)(text)

pending = get_transactions(status="pending")

if not pending:
    st.info("No pending transactions. All caught up!")
    st.stop()

for txn in pending:
    cat_name = txn["categories"]["name"] if txn["categories"] else "Uncategorized"
    submitter = txn["users"]["name"] if txn.get("users") else "Unknown"

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{txn['type'].upper()} — {cat_name}**")
            st.write(f"Amount: ₹{float(txn['amount']):,.2f}")
            st.write(f"Date: {txn['txn_date']}")
            if txn.get("receipt_number"):
                st.write(f"Receipt #: {txn['receipt_number']}")
            if txn.get("donor_name"):
                st.write(f"Donor: {txn['donor_name']} ({txn.get('donor_phone', 'no phone')})")
            st.write(f"Submitted by: {submitter}")
            if txn.get("description"):
                st.write(f"Notes: {txn['description']}")
        with col2:
            if txn.get("photo_url"):
                st.image(txn["photo_url"], width=150)

        c1, c2 = st.columns(2)
        if c1.button("Approve", key=f"approve_{txn['id']}"):
            approve_transaction(txn["id"], st.session_state["user_id"])
            if txn["type"] == "income" and txn.get("donor_phone"):
                sent, msg = send_whatsapp_notification(
                    phone=txn["donor_phone"],
                    donor_name=txn.get("donor_name"),
                    txn_type=txn["type"],
                    amount=float(txn["amount"]),
                    receipt_number=txn.get("receipt_number"),
                    category_name=cat_name,
                )
                if sent:
                    st.session_state["approval_feedback"] = ("success", "Approved and WhatsApp confirmation sent to donor.")
                else:
                    st.session_state["approval_feedback"] = ("warning", f"Approved, but WhatsApp notification failed: {msg}")
            else:
                st.session_state["approval_feedback"] = ("success", "Approved.")
            st.rerun()
        if c2.button("Reject", key=f"reject_{txn['id']}"):
            reject_transaction(txn["id"], st.session_state["user_id"])
            st.session_state["approval_feedback"] = ("info", "Rejected.")
            st.rerun()
