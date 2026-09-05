import streamlit as st
import pandas as pd
from datetime import date
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
if "payment_method" not in df.columns:
    df["payment_method"] = "cash"
else:
    df["payment_method"] = df["payment_method"].fillna("cash")
df["txn_date"] = pd.to_datetime(df["txn_date"])
df["donor_name"] = df.get("donor_name", "").fillna("") if "donor_name" in df.columns else ""
df["donor_phone"] = df.get("donor_phone", "").fillna("") if "donor_phone" in df.columns else ""

if "report_filters" not in st.session_state:
    st.session_state["report_filters"] = {
        "start_date": date.today(),
        "end_date": date.today(),
        "search": "",
        "type": "All",
    }
elif "type" not in st.session_state["report_filters"]:
    st.session_state["report_filters"]["type"] = "All"

with st.form("report_filter_form"):
    col1, col2, col3 = st.columns([1, 1, 1])
    start_date_input = col1.date_input("From", value=st.session_state["report_filters"]["start_date"])
    end_date_input = col2.date_input("To", value=st.session_state["report_filters"]["end_date"])
    type_options = ["All", "income", "expense"]
    type_input = col3.selectbox(
        "Type", type_options,
        index=type_options.index(st.session_state["report_filters"]["type"]),
    )
    search_input = st.text_input(
        "Search (donor name, receipt number)",
        value=st.session_state["report_filters"]["search"],
        placeholder="e.g. Ahmed or R-1023",
    )
    apply_clicked = st.form_submit_button("Search", type="primary")

    if apply_clicked:
        st.session_state["report_filters"] = {
            "start_date": start_date_input,
            "end_date": end_date_input,
            "search": search_input,
            "type": type_input,
        }

filters = st.session_state["report_filters"]
start_date = filters["start_date"]
end_date = filters["end_date"]
search = filters["search"]
type_filter = filters["type"]

mask = (df["txn_date"] >= pd.Timestamp(start_date)) & (df["txn_date"] <= pd.Timestamp(end_date))
filtered = df.loc[mask, ["txn_date", "type", "category_name", "amount", "payment_method",
                          "receipt_number", "donor_name", "donor_phone", "description"]]

if type_filter != "All":
    filtered = filtered[filtered["type"] == type_filter]

if search:
    search_lower = search.lower()
    filtered = filtered[
        filtered["donor_name"].str.lower().str.contains(search_lower, na=False)
        | filtered["receipt_number"].fillna("").str.lower().str.contains(search_lower, na=False)
    ]

filtered = filtered.sort_values("txn_date")

st.dataframe(filtered, use_container_width=True, hide_index=True)

income_total = filtered.loc[filtered["type"] == "income", "amount"].sum()
expense_total = filtered.loc[filtered["type"] == "expense", "amount"].sum()
st.write(f"**Income:** ₹{income_total:,.2f}  |  **Expense:** ₹{expense_total:,.2f}  |  **Net:** ₹{income_total - expense_total:,.2f}")

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download as CSV", csv, file_name=f"masjid_report_{start_date}_{end_date}.csv", mime="text/csv")
