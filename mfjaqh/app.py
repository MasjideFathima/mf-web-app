import streamlit as st
from utils.auth import login, logout, is_logged_in

st.set_page_config(page_title="Masjid-e-Fathima JAQH Tracker", page_icon="🕌", layout="centered")

st.title("🕌 Masjid-e-Fathima JAQH, Salem-1")
st.caption("Income & Expense Tracker")

if is_logged_in():
    st.success(f"Logged in as **{st.session_state['name']}** ({st.session_state['role']})")
    st.info("Use the sidebar to navigate: Dashboard, Add Transaction, Pending Approvals (admin), Reports.")
    if st.button("Log out"):
        logout()
        st.rerun()
else:
    st.subheader("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
        if submitted:
            if login(email, password):
                st.rerun()

    st.caption(
        "Don't have an account? Ask an admin to create one for you in Supabase "
        "(Authentication tab) and add a matching row in the `users` table."
    )
