"""
Supabase client wrapper.

Two clients are used on purpose:
- `anon_client`    -> used for login and for a MEMBER's own actions (respects RLS)
- `service_client` -> used ONLY for admin actions (approve/reject/view-all).
                       This key must never be sent to the browser; since Streamlit
                       Community Cloud runs the whole app server-side, that's safe
                       as long as it only ever lives in st.secrets.
"""
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]

BUCKET_NAME = "receipts"


@st.cache_resource
def get_anon_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


@st.cache_resource
def get_service_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
def get_categories(txn_type: str | None = None):
    client = get_service_client()
    query = client.table("categories").select("*")
    if txn_type:
        query = query.eq("type", txn_type)
    return query.order("name").execute().data


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------
def insert_transaction(data: dict):
    """data must include: type, category_id, amount, txn_date, description,
    submitted_by, and optionally receipt_number, photo_url, status."""
    client = get_service_client()
    return client.table("transactions").insert(data).execute()


def get_transactions(status: str | None = None, submitted_by: str | None = None):
    client = get_service_client()
    query = client.table("transactions").select("*, categories(name, type), users!transactions_submitted_by_fkey(name)")
    if status:
        query = query.eq("status", status)
    if submitted_by:
        query = query.eq("submitted_by", submitted_by)
    return query.order("txn_date", desc=True).execute().data


def get_transaction(txn_id: str):
    client = get_service_client()
    result = client.table("transactions").select("*, categories(name, type)").eq("id", txn_id).execute()
    return result.data[0] if result.data else None


def approve_transaction(txn_id: str, approver_id: str):
    client = get_service_client()
    return client.table("transactions").update({
        "status": "approved",
        "approved_by": approver_id,
        "approved_at": "now()"
    }).eq("id", txn_id).execute()


def reject_transaction(txn_id: str, approver_id: str):
    client = get_service_client()
    return client.table("transactions").update({
        "status": "rejected",
        "approved_by": approver_id,
        "approved_at": "now()"
    }).eq("id", txn_id).execute()


def receipt_number_exists(receipt_number: str) -> bool:
    if not receipt_number:
        return False
    client = get_service_client()
    result = client.table("transactions").select("id").eq("receipt_number", receipt_number).execute()
    return len(result.data) > 0


def delete_transaction(txn_id: str):
    """Deletes a single transaction. Also attempts to remove its photo from
    storage if one exists (best-effort - won't fail the delete if it can't)."""
    client = get_service_client()
    txn = get_transaction(txn_id)
    if txn and txn.get("photo_url"):
        _delete_photo_by_url(txn["photo_url"])
    return client.table("transactions").delete().eq("id", txn_id).execute()


def delete_transactions(txn_ids: list[str]):
    """Bulk delete. Cleans up each photo first, then deletes all rows in one call."""
    if not txn_ids:
        return None
    client = get_service_client()
    for txn_id in txn_ids:
        txn = get_transaction(txn_id)
        if txn and txn.get("photo_url"):
            _delete_photo_by_url(txn["photo_url"])
    return client.table("transactions").delete().in_("id", txn_ids).execute()


def _delete_photo_by_url(photo_url: str):
    """Best-effort removal of a photo from the receipts bucket given its public URL."""
    try:
        client = get_service_client()
        path = photo_url.split(f"/{BUCKET_NAME}/")[-1]
        client.storage.from_(BUCKET_NAME).remove([path])
    except Exception:
        pass  # Non-fatal - the DB row delete should still proceed.


# ---------------------------------------------------------------------------
# Photo storage (Supabase Storage bucket, not DB blobs)
# ---------------------------------------------------------------------------
def upload_photo(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Uploads to the 'receipts' bucket and returns a public URL."""
    client = get_service_client()
    path = f"{filename}"
    client.storage.from_(BUCKET_NAME).upload(
        path, file_bytes, {"content-type": content_type, "upsert": "true"}
    )
    return client.storage.from_(BUCKET_NAME).get_public_url(path)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def get_user_profile(auth_id: str):
    client = get_service_client()
    result = client.table("users").select("*").eq("id", auth_id).execute()
    return result.data[0] if result.data else None


def get_all_users():
    client = get_service_client()
    return client.table("users").select("*").order("name").execute().data


def email_exists_in_users_table(email: str) -> bool:
    """Best-effort duplicate check against auth users by listing them.
    (Supabase Admin API has no direct get-by-email in supabase-py, so we
    rely on the create_user call itself to reject true duplicates too.)"""
    client = get_service_client()
    try:
        result = client.auth.admin.list_users()
        return any(u.email == email for u in result)
    except Exception:
        return False


def create_user_account(email: str, password: str, name: str, phone: str, role: str):
    """Creates the auth user (Supabase Admin API, bypasses email confirmation)
    and a matching row in public.users. Returns (success, message)."""
    client = get_service_client()
    try:
        auth_result = client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # skip confirmation email - admin is vouching for this user
        })
    except Exception as e:
        return False, f"Could not create login: {e}"

    new_user = auth_result.user
    if not new_user:
        return False, "Account creation failed for an unknown reason."

    try:
        client.table("users").insert({
            "id": new_user.id,
            "name": name,
            "phone": phone or None,
            "role": role,
        }).execute()
    except Exception as e:
        # Roll back the auth user so we don't end up with an orphaned login
        # that has no profile row.
        try:
            client.auth.admin.delete_user(new_user.id)
        except Exception:
            pass
        return False, f"Login was created but profile setup failed, so it was rolled back: {e}"

    return True, "User created successfully."
