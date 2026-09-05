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
if "payment_method" not in df.columns:
    df["payment_method"] = "cash"
else:
    df["payment_method"] = df["payment_method"].fillna("cash")

total_income = df.loc[df["type"] == "income", "amount"].sum()
total_expense = df.loc[df["type"] == "expense", "amount"].sum()
balance = total_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"₹{total_income:,.2f}")
col2.metric("Total Expense", f"₹{total_expense:,.2f}")
col3.metric("Balance", f"₹{balance:,.2f}")

st.subheader("Balance by Payment Method")


def method_balance(method: str) -> float:
    subset = df[df["payment_method"] == method]
    income = subset.loc[subset["type"] == "income", "amount"].sum()
    expense = subset.loc[subset["type"] == "expense", "amount"].sum()
    return income - expense


cash_balance = method_balance("cash")
bank_balance = method_balance("bank")

pcol1, pcol2, pcol3 = st.columns(3)
pcol1.metric("💵 Cash in Hand", f"₹{cash_balance:,.2f}")
pcol2.metric("🏦 Bank / GPay", f"₹{bank_balance:,.2f}")
pcol3.metric("Total (Cash + Bank)", f"₹{cash_balance + bank_balance:,.2f}")

st.subheader("By Category")
by_cat = df.groupby(["type", "category_name"])["amount"].sum().reset_index()
st.dataframe(by_cat, use_container_width=True, hide_index=True)

st.subheader("Monthly Trend")
df["txn_date"] = pd.to_datetime(df["txn_date"])
df["month"] = df["txn_date"].dt.to_period("M").astype(str)
monthly = df.groupby(["month", "type"])["amount"].sum().unstack(fill_value=0)
for col in ("income", "expense"):
    if col not in monthly.columns:
        monthly[col] = 0
monthly = monthly.sort_index()
st.bar_chart(monthly[["income", "expense"]])

st.subheader("Recent Transactions")
recent = df[["txn_date", "type", "category_name", "amount", "payment_method", "receipt_number", "description"]].head(20).copy()
recent["txn_date"] = recent["txn_date"].dt.date
st.dataframe(recent, use_container_width=True, hide_index=True)
