import streamlit as st
import secrets
import string
from utils.auth import require_admin
from utils.db import create_user_account, get_all_users

require_admin()
st.title("👤 Create User")
st.caption("Create a login for a new admin or member. Share the password with them directly (WhatsApp, in person, etc.) - they can use it as-is or change it later.")

if "created_user_feedback" in st.session_state:
    st.success(st.session_state.pop("created_user_feedback"))


def generate_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


with st.form("create_user_form"):
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
            st.session_state["created_user_feedback"] = (
                f"User created: **{name}** ({role}). "
                f"Login email: `{email}` — Password: `{password}` "
                f"— share this with them now, it won't be shown again."
            )
            st.rerun()
        else:
            st.error(message)

st.divider()
st.subheader("Existing Users")
users = get_all_users()
if users:
    st.dataframe(
        [{"Name": u["name"], "Role": u["role"], "Phone": u.get("phone") or "-"} for u in users],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No users found.")
