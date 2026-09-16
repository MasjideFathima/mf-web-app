"""
Shared visual polish (green & gold theme), applied on every page via
apply_soft_theme(). Keeps the look consistent without repeating CSS in each file.
"""
import streamlit as st


def apply_soft_theme():
    st.markdown(
        """
        <style>
        /* Softer, rounded containers (used for record cards throughout the app) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
            border: 1px solid #E6D9B8 !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
            padding: 4px 2px;
        }

        /* Buttons: rounded, gentle hover with a warm gold-tinted shadow */
        div.stButton > button {
            border-radius: 10px !important;
            transition: all 0.15s ease-in-out;
        }
        div.stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(201, 162, 39, 0.25);
        }

        /* Text inputs, number inputs, selectboxes, textareas: rounded */
        div[data-baseweb="input"], div[data-baseweb="select"], textarea {
            border-radius: 10px !important;
        }

        /* Metrics: soft card with a gold accent border, like the approved mockup */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 12px 16px;
            border: 1px solid #E6D9B8;
            border-left: 4px solid #C9A227;
        }

        /* Reduce harsh top padding so content feels less cramped */
        .block-container {
            padding-top: 2.5rem;
        }

        /* Softer, gold-tinted section dividers */
        hr {
            border-color: #E8D9A0 !important;
        }

        /* Sidebar: warm gold-cream background matching the theme */
        section[data-testid="stSidebar"] {
            background-color: #F3ECDA;
        }

        /* Sidebar page links: gold highlight on hover, green when active */
        section[data-testid="stSidebar"] a:hover {
            background-color: #E8D9A0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
