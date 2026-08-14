"""
Basic authentication using Supabase Auth (email + password).
Session is kept in st.session_state; Supabase handles password hashing,
tokens, etc. so we never touch raw passwords ourselves.
"""
import streamlit as st
from utils.db import get_anon_client, get_user_profile


def login(email: str, password: str) -> bool:
    client = get_anon_client()
    try:
        result = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        st.error(f"Login failed: {e}")
        return False

    user = result.user
    if not user:
        st.error("Invalid email or password.")
        return False

    profile = get_user_profile(user.id)
    if not profile:
        st.error("Your account has no profile record. Ask an admin to add you.")
        return False

    st.session_state["user_id"] = user.id
    st.session_state["email"] = user.email
    st.session_state["name"] = profile["name"]
    st.session_state["role"] = profile["role"]
    return True


def logout():
    for key in ("user_id", "email", "name", "role"):
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    return "user_id" in st.session_state


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"


def require_login():
    """Call at the top of every page. Stops the page if not logged in."""
    if not is_logged_in():
        st.warning("Please log in from the Home page first.")
        st.stop()


def require_admin():
    require_login()
    if not is_admin():
        st.error("This page is for admins only.")
        st.stop()
