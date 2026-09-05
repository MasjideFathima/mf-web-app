import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import datetime
from utils.auth import require_admin
from utils.db import get_all_transactions_for_backup, get_all_users

require_admin()
st.title("💾 Backup / Export")
st.caption(
    "Supabase's free tier does not include automatic backups. "
    "Download a full copy periodically (e.g. monthly) and save it somewhere safe "
    "(Google Drive, email to yourself, etc.)."
)

transactions = get_all_transactions_for_backup()
users = get_all_users()

if not transactions:
    st.info("No transactions to back up yet.")
else:
    txn_df = pd.DataFrame(transactions)
    txn_df["category_name"] = txn_df["categories"].apply(lambda c: c["name"] if c else "Uncategorized")
    txn_df["submitted_by_name"] = txn_df["users"].apply(lambda u: u["name"] if u else "Unknown")
    txn_df = txn_df.drop(columns=["categories", "users"])

    users_df = pd.DataFrame(users)

    st.subheader("Preview")
    st.write(f"{len(txn_df)} transaction(s), {len(users_df)} user(s)")
    st.dataframe(txn_df.head(10), use_container_width=True, hide_index=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")

    # Build an in-memory zip containing both CSVs, so it's one download.
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("transactions.csv", txn_df.to_csv(index=False))
        zf.writestr("users.csv", users_df.to_csv(index=False))
    zip_buffer.seek(0)

    st.download_button(
        "Download Full Backup (.zip)",
        data=zip_buffer,
        file_name=f"masjid_backup_{timestamp}.zip",
        mime="application/zip",
        type="primary",
    )

    st.caption(
        "Note: this backs up transaction and user profile data. It does NOT "
        "include uploaded photos - those stay safe in Supabase Storage "
        "separately unless you delete them."
    )
