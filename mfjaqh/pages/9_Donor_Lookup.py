import streamlit as st
import pandas as pd
from utils.auth import require_login
from utils.db import search_donor_transactions

require_login()
st.title("🔍 Donor Lookup")
st.caption("Search by donor name or phone number to see their donation history.")

query = st.text_input("Search", placeholder="e.g. Ahmed or 9876543210")

if query:
    results = search_donor_transactions(query)

    if not results:
        st.info("No matching donations found.")
    else:
        df = pd.DataFrame(results)
        df["category_name"] = df["categories"].apply(lambda c: c["name"] if c else "Uncategorized")
        df["amount"] = df["amount"].astype(float)

        total = df["amount"].sum()
        st.metric(f"Total donated ({len(df)} record(s))", f"₹{total:,.2f}")

        display_df = df[["txn_date", "donor_name", "donor_phone", "category_name",
                          "amount", "payment_method", "receipt_number"]].sort_values(
            "txn_date", ascending=False
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
