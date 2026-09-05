import streamlit as st
from utils.auth import require_login
from utils.db import verify_password, update_own_password

require_login()
st.title("🔑 Change Password")

if "password_change_feedback" in st.session_state:
    st.success(st.session_state.pop("password_change_feedback"))

with st.form("change_password_form", clear_on_submit=True):
    current_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    submitted = st.form_submit_button("Update Password")

    if submitted:
        if len(new_password) < 6:
            st.error("New password must be at least 6 characters.")
            st.stop()
        if new_password != confirm_password:
            st.error("New password and confirmation don't match.")
            st.stop()

        if not verify_password(st.session_state["email"], current_password):
            st.error("Current password is incorrect.")
            st.stop()

        success, message = update_own_password(st.session_state["user_id"], new_password)
        if success:
            st.session_state["password_change_feedback"] = "Password updated successfully."
            st.rerun()
        else:
            st.error(message)
