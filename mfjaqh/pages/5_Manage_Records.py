import streamlit as st
import pandas as pd
from datetime import date as date_cls, timedelta
from utils.auth import require_admin
from utils.db import get_transactions, delete_transaction, delete_transactions, update_transaction, get_categories

require_admin()
st.title("🗑️ Manage Records")
st.caption("Edit or delete income/expense records. Deletion is permanent and cannot be undone.")

# Feedback from the previous action survives the rerun below.
if "manage_feedback" in st.session_state:
    level, text = st.session_state.pop("manage_feedback")
    getattr(st, level)(text)

# --- Filters ---
col1, col2, col3, col4 = st.columns(4)
status_filter = col1.selectbox("Status", ["approved", "pending", "rejected"], index=0)
type_filter = col2.selectbox("Type", ["All", "income", "expense"])
start_date = col3.date_input("From", value=date_cls.today() - timedelta(days=90))
end_date = col4.date_input("To", value=date_cls.today())

records = get_transactions(status=status_filter)
if type_filter != "All":
    records = [r for r in records if r["type"] == type_filter]
records = [
    r for r in records
    if r.get("txn_date") and start_date.isoformat() <= r["txn_date"] <= end_date.isoformat()
]

if not records:
    st.info("No records match this filter.")
    st.stop()

# Drop any selected id that no longer exists in the current results (e.g. it
# was deleted individually while also checked for bulk delete) - prevents a
# stale "Delete Selected" confirmation from lingering for a record that's
# already gone.
if "selected_ids" in st.session_state:
    existing_ids = {r["id"] for r in records}
    st.session_state["selected_ids"] &= existing_ids
    if not st.session_state["selected_ids"]:
        st.session_state["confirm_bulk_delete"] = False

# Reset pagination back to the first page whenever any filter changes.
current_filter_key = (status_filter, type_filter, start_date, end_date)
if st.session_state.get("manage_records_filter_key") != current_filter_key:
    st.session_state["manage_records_filter_key"] = current_filter_key
    st.session_state["manage_records_page_size"] = 10

if "manage_records_page_size" not in st.session_state:
    st.session_state["manage_records_page_size"] = 10

st.caption(f"{len(records)} record(s) match this filter.")

st.divider()

visible_records = records[: st.session_state["manage_records_page_size"]]

# --- Bulk delete controls ---
if "selected_ids" not in st.session_state:
    st.session_state["selected_ids"] = set()

top_col1, top_col2 = st.columns([3, 1])
select_all = top_col1.checkbox("Select all shown below")
if select_all:
    st.session_state["selected_ids"] = {r["id"] for r in visible_records}
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
for txn in visible_records:
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
            st.write(f"₹{float(txn['amount']):,.2f}  •  {txn['txn_date']}  •  {txn.get('payment_method', 'cash').title()}")
            if txn.get("receipt_number"):
                st.caption(f"Receipt #: {txn['receipt_number']}")
            if txn.get("donor_name"):
                st.caption(f"Donor: {txn['donor_name']}")
            if txn.get("description"):
                st.caption(txn["description"])

        with c3:
            if txn.get("photo_url"):
                st.image(txn["photo_url"], width=80)
            ec1, ec2 = st.columns(2)
            if ec1.button("Edit", key=f"edit_{txn['id']}"):
                st.session_state["editing_id"] = (
                    None if st.session_state.get("editing_id") == txn["id"] else txn["id"]
                )
                st.rerun()
            if ec2.button("Delete", key=f"delete_{txn['id']}"):
                st.session_state["confirm_single_delete"] = txn["id"]

        if st.session_state.get("editing_id") == txn["id"]:
            categories = get_categories(txn["type"])
            cat_names = [c["name"] for c in categories]
            current_cat_index = next(
                (i for i, c in enumerate(categories) if c["id"] == txn["category_id"]), 0
            )

            with st.form(f"edit_form_{txn['id']}"):
                st.write("**Edit Record**")
                new_category_name = st.selectbox("Category", cat_names, index=current_cat_index)
                new_amount = st.number_input("Amount (₹)", min_value=0.0, value=float(txn["amount"]), step=1.0)
                new_date = st.date_input(
                    "Date",
                    value=pd.to_datetime(txn["txn_date"]).date() if txn.get("txn_date") else date_cls.today(),
                )
                new_payment_method = st.radio(
                    "Payment Method", ["Cash", "GPay/Bank"], horizontal=True,
                    index=0 if txn.get("payment_method", "cash") == "cash" else 1,
                )
                new_receipt_number = st.text_input("Receipt Number", value=txn.get("receipt_number") or "")
                new_donor_name = st.text_input("Donor Name", value=txn.get("donor_name") or "")
                new_donor_phone = st.text_input("Donor Phone", value=txn.get("donor_phone") or "")
                new_description = st.text_area("Description", value=txn.get("description") or "")

                save_col, cancel_col = st.columns(2)
                if save_col.form_submit_button("Save Changes", type="primary"):
                    new_category_id = next(c["id"] for c in categories if c["name"] == new_category_name)
                    update_transaction(txn["id"], {
                        "category_id": new_category_id,
                        "amount": new_amount,
                        "txn_date": new_date.isoformat(),
                        "payment_method": "bank" if new_payment_method == "GPay/Bank" else "cash",
                        "receipt_number": new_receipt_number or None,
                        "donor_name": new_donor_name or None,
                        "donor_phone": new_donor_phone or None,
                        "description": new_description,
                    })
                    st.session_state["editing_id"] = None
                    st.session_state["manage_feedback"] = ("success", "Record updated.")
                    st.rerun()
                if cancel_col.form_submit_button("Cancel"):
                    st.session_state["editing_id"] = None
                    st.rerun()

        if st.session_state.get("confirm_single_delete") == txn["id"]:
            st.warning("Permanently delete this record? This cannot be undone.")
            cc1, cc2 = st.columns(2)
            if cc1.button("Yes, delete", key=f"confirm_yes_{txn['id']}", type="primary"):
                delete_transaction(txn["id"])
                st.session_state["confirm_single_delete"] = None
                st.session_state["selected_ids"].discard(txn["id"])
                if not st.session_state["selected_ids"]:
                    st.session_state["confirm_bulk_delete"] = False
                st.session_state["manage_feedback"] = ("success", "Record deleted.")
                st.rerun()
            if cc2.button("Cancel", key=f"confirm_no_{txn['id']}"):
                st.session_state["confirm_single_delete"] = None
                st.rerun()

if len(records) > len(visible_records):
    st.divider()
    remaining = len(records) - len(visible_records)
    if st.button(f"Show More ({remaining} remaining)"):
        st.session_state["manage_records_page_size"] += 10
        st.rerun()
