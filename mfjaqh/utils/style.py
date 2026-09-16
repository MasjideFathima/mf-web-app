"""
Shared visual polish, applied on every page via apply_soft_theme().
Keeps the look consistent without repeating CSS in each file.
"""
import streamlit as st


def apply_soft_theme():
    st.markdown(
        """
        <style>
        /* Softer, rounded containers (used for record cards throughout the app) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
            border: 1px solid #E4E0D6 !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
            padding: 4px 2px;
        }

        /* Buttons: rounded, gentle hover */
        div.stButton > button {
            border-radius: 10px !important;
            transition: all 0.15s ease-in-out;
        }
        div.stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
        }

        /* Text inputs, number inputs, selectboxes, textareas: rounded */
        div[data-baseweb="input"], div[data-baseweb="select"], textarea {
            border-radius: 10px !important;
        }

        /* Metrics: a little breathing room and a soft card feel */
        div[data-testid="stMetric"] {
            background-color: #F5F3EC;
            border-radius: 12px;
            padding: 12px 16px;
            border: 1px solid #EAE6DA;
        }

        /* Reduce harsh top padding so content feels less cramped */
        .block-container {
            padding-top: 2.5rem;
        }

        /* Softer section dividers */
        hr {
            border-color: #E9E5D9 !important;
        }

        /* Sidebar: slightly warmer background to match the palette */
        section[data-testid="stSidebar"] {
            background-color: #F3F1EA;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
