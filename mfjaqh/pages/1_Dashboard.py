import streamlit as st
import pandas as pd
from utils.auth import require_login
from utils.db import get_transactions
from utils.style import apply_soft_theme, styled_metric

st.set_page_config(page_title="Dashboard", page_icon="📊")
apply_soft_theme()
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

method_filter = st.selectbox("Payment Method", ["All", "Cash", "Bank"], index=0)
if method_filter != "All":
    df = df[df["payment_method"] == method_filter.lower()]

if df.empty:
    st.info(f"No approved transactions for {method_filter}.")
    st.stop()

total_income = df.loc[df["type"] == "income", "amount"].sum()
total_expense = df.loc[df["type"] == "expense", "amount"].sum()
balance = total_income - total_expense


def amount_for(txn_type: str, method: str) -> float:
    subset = df[(df["type"] == txn_type) & (df["payment_method"] == method)]
    return subset["amount"].sum()


income_cash = amount_for("income", "cash")
income_bank = amount_for("income", "bank")
expense_cash = amount_for("expense", "cash")
expense_bank = amount_for("expense", "bank")
cash_balance = income_cash - expense_cash
bank_balance = income_bank - expense_bank

GREEN = "#146C43"
RED = "#C0392B"

st.subheader("Overall")
col1, col2 = st.columns(2)
with col1:
    styled_metric("Total Income (Cash + Bank)", f"₹{total_income:,.2f}", GREEN)
with col2:
    styled_metric("Total Expense (Cash + Bank)", f"₹{total_expense:,.2f}", RED)

st.subheader("Income by Payment Method")
icol1, icol2 = st.columns(2)
with icol1:
    styled_metric("💵 Income - Cash", f"₹{income_cash:,.2f}", GREEN)
with icol2:
    styled_metric("🏦 Income - Bank/GPay", f"₹{income_bank:,.2f}", GREEN)

st.subheader("Expense by Payment Method")
ecol1, ecol2 = st.columns(2)
with ecol1:
    styled_metric("💵 Expense - Cash", f"₹{expense_cash:,.2f}", RED)
with ecol2:
    styled_metric("🏦 Expense - Bank/GPay", f"₹{expense_bank:,.2f}", RED)

st.subheader("💰 Balance Summary")
with st.container(border=True, key="balance_summary"):
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        styled_metric("Net Balance", f"₹{balance:,.2f}", GREEN if balance >= 0 else RED)
    with bcol2:
        styled_metric("💵 Cash in Hand", f"₹{cash_balance:,.2f}", GREEN if cash_balance >= 0 else RED)
    with bcol3:
        styled_metric("🏦 Cash in Bank", f"₹{bank_balance:,.2f}", GREEN if bank_balance >= 0 else RED)

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
