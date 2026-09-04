import streamlit as st
import pandas as pd
from utils.auth import require_admin
from utils.db import get_transactions, delete_transaction, delete_transactions

require_admin()
st.title("🗑️ Manage Records")
st.caption("Delete income/expense records. This is permanent and cannot be undone.")

# Feedback from the previous action survives the rerun below.
if "manage_feedback" in st.session_state:
    level, text = st.session_state.pop("manage_feedback")
    getattr(st, level)(text)

# --- Filters ---
col1, col2 = st.columns(2)
status_filter = col1.selectbox("Status", ["approved", "pending", "rejected"], index=0)
type_filter = col2.selectbox("Type", ["All", "income", "expense"])

records = get_transactions(status=status_filter)
if type_filter != "All":
    records = [r for r in records if r["type"] == type_filter]

if not records:
    st.info("No records match this filter.")
    st.stop()

st.divider()

# --- Bulk delete controls ---
if "selected_ids" not in st.session_state:
    st.session_state["selected_ids"] = set()

top_col1, top_col2 = st.columns([3, 1])
select_all = top_col1.checkbox("Select all shown below")
if select_all:
    st.session_state["selected_ids"] = {r["id"] for r in records}
elif not select_all and st.session_state.get("_prev_select_all"):
    st.session_state["selected_ids"] = set()
st.session_state["_prev_select_all"] = select_all

selected_count = len(st.session_state["selected_ids"])
bulk_delete_clicked = top_col2.button(
    f"Delete Selected ({selected_count})",
    disabled=selected_count == 0,
    type="primary" if selected_count else "secondary",
)

if bulk_delete_clicked:
    st.session_state["confirm_bulk_delete"] = True

if st.session_state.get("confirm_bulk_delete"):
    st.warning(f"Permanently delete {selected_count} record(s)? This cannot be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Yes, delete them", type="primary"):
        delete_transactions(list(st.session_state["selected_ids"]))
        st.session_state["selected_ids"] = set()
        st.session_state["confirm_bulk_delete"] = False
        st.session_state["manage_feedback"] = ("success", f"Deleted {selected_count} record(s).")
        st.rerun()
    if c2.button("Cancel"):
        st.session_state["confirm_bulk_delete"] = False
        st.rerun()

st.divider()

# --- Record list ---
for txn in records:
    cat_name = txn["categories"]["name"] if txn["categories"] else "Uncategorized"

    with st.container(border=True):
        c1, c2, c3 = st.columns([0.4, 3, 1])

        checked = c1.checkbox(
            "Select",
            value=txn["id"] in st.session_state["selected_ids"],
            key=f"select_{txn['id']}",
            label_visibility="collapsed",
        )
        if checked:
            st.session_state["selected_ids"].add(txn["id"])
        else:
            st.session_state["selected_ids"].discard(txn["id"])

        with c2:
            st.markdown(f"**{txn['type'].upper()} — {cat_name}**")
            st.write(f"₹{float(txn['amount']):,.2f}  •  {txn['txn_date']}")
            if txn.get("receipt_number"):
                st.caption(f"Receipt #: {txn['receipt_number']}")
            if txn.get("donor_name"):
                st.caption(f"Donor: {txn['donor_name']}")
            if txn.get("description"):
                st.caption(txn["description"])

        with c3:
            if txn.get("photo_url"):
                st.image(txn["photo_url"], width=80)
            if st.button("Delete", key=f"delete_{txn['id']}"):
                st.session_state["confirm_single_delete"] = txn["id"]

        if st.session_state.get("confirm_single_delete") == txn["id"]:
            st.warning("Permanently delete this record? This cannot be undone.")
            cc1, cc2 = st.columns(2)
            if cc1.button("Yes, delete", key=f"confirm_yes_{txn['id']}", type="primary"):
                delete_transaction(txn["id"])
                st.session_state["confirm_single_delete"] = None
                st.session_state["manage_feedback"] = ("success", "Record deleted.")
                st.rerun()
            if cc2.button("Cancel", key=f"confirm_no_{txn['id']}"):
                st.session_state["confirm_single_delete"] = None
                st.rerun()
