import streamlit as st
import pandas as pd
from utils.auth import require_login
from utils.db import get_transactions

require_login()
st.title("📊 Dashboard")

data = get_transactions(status="approved")

if not data:
    st.info("No approved transactions yet.")
    st.stop()

df = pd.DataFrame(data)
df["category_name"] = df["categories"].apply(lambda c: c["name"] if c else "Uncategorized")
df["amount"] = df["amount"].astype(float)

total_income = df.loc[df["type"] == "income", "amount"].sum()
total_expense = df.loc[df["type"] == "expense", "amount"].sum()
balance = total_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"₹{total_income:,.2f}")
col2.metric("Total Expense", f"₹{total_expense:,.2f}")
col3.metric("Balance", f"₹{balance:,.2f}")

st.subheader("By Category")
by_cat = df.groupby(["type", "category_name"])["amount"].sum().reset_index()
st.dataframe(by_cat, use_container_width=True, hide_index=True)

st.subheader("Recent Transactions")
recent = df[["txn_date", "type", "category_name", "amount", "receipt_number", "description"]].head(20)
st.dataframe(recent, use_container_width=True, hide_index=True)
