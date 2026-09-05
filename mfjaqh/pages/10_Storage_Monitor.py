import streamlit as st
from utils.auth import require_admin
from utils.db import get_database_size_bytes, get_storage_size_bytes

require_admin()
st.title("📦 Storage Monitor")
st.caption("Tracks usage against Supabase's free tier limits (500MB database, 1GB file storage).")

DB_LIMIT_BYTES = 500 * 1024 * 1024      # 500 MB
STORAGE_LIMIT_BYTES = 1024 * 1024 * 1024  # 1 GB


def format_size(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    return f"{num_bytes / 1024:.1f} KB"


def show_usage_bar(label: str, used_bytes: int, limit_bytes: int):
    pct = min(used_bytes / limit_bytes, 1.0)
    st.write(f"**{label}**: {format_size(used_bytes)} of {format_size(limit_bytes)} used ({pct * 100:.1f}%)")
    st.progress(pct)
    if pct >= 0.9:
        st.error("⚠️ Over 90% full — consider cleaning up old records/photos or upgrading soon.")
    elif pct >= 0.75:
        st.warning("⚠️ Over 75% full — worth keeping an eye on this.")


# --- Database size ---
db_size = get_database_size_bytes()
if db_size is None:
    st.warning(
        "Database size check isn't set up yet. Run the `get_database_size_bytes()` "
        "SQL function from the bottom of schema.sql in Supabase's SQL Editor, then refresh this page."
    )
else:
    show_usage_bar("Database Storage", db_size, DB_LIMIT_BYTES)

st.divider()

# --- File (photo) storage size ---
with st.spinner("Calculating photo storage usage..."):
    storage_size = get_storage_size_bytes()
show_usage_bar("Photo Storage (receipts bucket)", storage_size, STORAGE_LIMIT_BYTES)

st.divider()
st.caption(
    "If either of these gets close to full: delete old/unneeded records and photos via "
    "Manage Records, or consider Supabase's Pro plan ($25/month) if the masjid's usage "
    "has genuinely outgrown the free tier."
)
