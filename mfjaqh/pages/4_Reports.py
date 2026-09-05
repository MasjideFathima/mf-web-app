import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils.auth import require_login
from utils.db import get_transactions

require_login()
st.title("📄 Reports")

data = get_transactions(status="approved")
if not data:
    st.info("No approved transactions yet.")
    st.stop()

df = pd.DataFrame(data)
df["category_name"] = df["categories"].apply(lambda c: c["name"] if c else "Uncategorized")
df["amount"] = df["amount"].astype(float)
df["payment_method"] = df.get("payment_method", "cash").fillna("cash")
df["txn_date"] = pd.to_datetime(df["txn_date"])

col1, col2 = st.columns(2)
start_date = col1.date_input("From", value=date.today() - timedelta(days=30))
end_date = col2.date_input("To", value=date.today())

mask = (df["txn_date"] >= pd.Timestamp(start_date)) & (df["txn_date"] <= pd.Timestamp(end_date))
filtered = df.loc[mask, ["txn_date", "type", "category_name", "amount", "payment_method", "receipt_number", "description"]]
filtered = filtered.sort_values("txn_date")

st.dataframe(filtered, use_container_width=True, hide_index=True)

income_total = filtered.loc[filtered["type"] == "income", "amount"].sum()
expense_total = filtered.loc[filtered["type"] == "expense", "amount"].sum()
st.write(f"**Income:** ₹{income_total:,.2f}  |  **Expense:** ₹{expense_total:,.2f}  |  **Net:** ₹{income_total - expense_total:,.2f}")

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download as CSV", csv, file_name=f"masjid_report_{start_date}_{end_date}.csv", mime="text/csv")
