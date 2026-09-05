import streamlit as st
import secrets
import string
from utils.auth import require_admin
from utils.db import create_user_account, get_all_users, delete_user_account, count_admins

require_admin()
st.title("👥 User Management")
st.caption("Create logins for admins/members, and remove access when someone no longer needs it.")

if "user_mgmt_feedback" in st.session_state:
    level, text = st.session_state.pop("user_mgmt_feedback")
    getattr(st, level)(text)


def generate_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


st.subheader("Create User")
with st.form("create_user_form", clear_on_submit=True):
    name = st.text_input("Full Name")
    email = st.text_input("Email (used to log in)")
    phone = st.text_input("Phone Number (optional)")
    role = st.radio("Role", ["member", "admin"], horizontal=True, index=0)

    use_generated = st.checkbox("Auto-generate a random password", value=True)
    manual_password = ""
    if not use_generated:
        manual_password = st.text_input("Set Password (min 6 characters)", type="password")

    submitted = st.form_submit_button("Create User")

    if submitted:
        if not name or not email:
            st.error("Name and email are required.")
            st.stop()

        password = generate_password() if use_generated else manual_password
        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            st.stop()

        success, message = create_user_account(
            email=email.strip(),
            password=password,
            name=name.strip(),
            phone=phone.strip(),
            role=role,
        )

        if success:
            st.session_state["user_mgmt_feedback"] = (
                "success",
                f"User created: **{name}** ({role}). "
                f"Login email: `{email}` — Password: `{password}` "
                f"— share this with them now, it won't be shown again.",
            )
            st.rerun()
        else:
            st.error(message)

st.divider()
st.subheader("Existing Users")

users = get_all_users()
if not users:
    st.info("No users found.")
else:
    admin_count = count_admins()
    current_user_id = st.session_state.get("user_id")

    for u in users:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{u['name']}** — {u['role']}")
                st.caption(u.get("phone") or "No phone on file")
                if u["id"] == current_user_id:
                    st.caption("_(this is you)_")

            with c2:
                is_last_admin = u["role"] == "admin" and admin_count <= 1
                is_self = u["id"] == current_user_id
                disabled = is_last_admin or is_self
                if st.button("Delete", key=f"delete_user_{u['id']}", disabled=disabled):
                    st.session_state["confirm_delete_user"] = u["id"]

                if is_self:
                    st.caption("Can't delete your own account.")
                elif is_last_admin:
                    st.caption("Can't delete the last admin.")

        if st.session_state.get("confirm_delete_user") == u["id"]:
            st.warning(
                f"Permanently delete **{u['name']}**'s login? They will no longer be able to log in. "
                "Their past transaction history is kept, but will show as submitted/approved by \"Unknown\"."
            )
            cc1, cc2 = st.columns(2)
            if cc1.button("Yes, delete", key=f"confirm_yes_user_{u['id']}", type="primary"):
                success, message = delete_user_account(u["id"])
                st.session_state["confirm_delete_user"] = None
                if success:
                    st.session_state["user_mgmt_feedback"] = ("success", message)
                else:
                    st.session_state["user_mgmt_feedback"] = ("error", message)
                st.rerun()
            if cc2.button("Cancel", key=f"confirm_no_user_{u['id']}"):
                st.session_state["confirm_delete_user"] = None
                st.rerun()
