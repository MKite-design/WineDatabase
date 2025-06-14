
import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide", page_title="Wine Database")

@st.cache_data
def load_data():
    conn = sqlite3.connect("wine_supplier_with_producer.db")
    query = '''
        SELECT w.wine_id, w.wine_name, w.vintage, w.varietal, w.region, w.producer,
               s.name AS supplier, p.bottle_price
        FROM wines w
        JOIN wine_prices p ON w.wine_id = p.wine_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    idx_min = df.groupby('wine_id')['bottle_price'].idxmin()
    return df.loc[idx_min].reset_index(drop=True)

df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Refine Search")
wine_name = st.sidebar.text_input("Search by Wine Name")
selected_varietal = st.sidebar.selectbox("Filter by Varietal", ["All"] + sorted(df['varietal'].dropna().unique().tolist()))
selected_region = st.sidebar.selectbox("Filter by Region", ["All"] + sorted(df['region'].dropna().unique().tolist()))
selected_producer = st.sidebar.selectbox("Filter by Producer", ["All"] + sorted(df['producer'].dropna().unique().tolist()))
selected_supplier = st.sidebar.selectbox("Filter by Supplier", ["All"] + sorted(df['supplier'].dropna().unique().tolist()))
min_price = st.sidebar.number_input("Min Bottle Price", min_value=0.0, value=0.0, step=1.0)
max_price = st.sidebar.number_input("Max Bottle Price", min_value=0.0, value=20000.0, step=1.0)
sort_order = st.sidebar.selectbox("Sort By", ["Name A-Z", "Name Z-A", "Price Low-High", "Price High-Low"])

# Apply filters
filtered_df = df.copy()
if wine_name:
    filtered_df = filtered_df[filtered_df["wine_name"].str.contains(wine_name, case=False, na=False)]
if selected_varietal != "All":
    filtered_df = filtered_df[filtered_df["varietal"] == selected_varietal]
if selected_region != "All":
    filtered_df = filtered_df[filtered_df["region"] == selected_region]
if selected_producer != "All":
    filtered_df = filtered_df[filtered_df["producer"] == selected_producer]
if selected_supplier != "All":
    filtered_df = filtered_df[filtered_df["supplier"] == selected_supplier]
filtered_df = filtered_df[(filtered_df["bottle_price"] >= min_price) & (filtered_df["bottle_price"] <= max_price)]

# Sorting
if sort_order == "Name A-Z":
    filtered_df = filtered_df.sort_values(by="wine_name")
elif sort_order == "Name Z-A":
    filtered_df = filtered_df.sort_values(by="wine_name", ascending=False)
elif sort_order == "Price Low-High":
    filtered_df = filtered_df.sort_values(by="bottle_price")
elif sort_order == "Price High-Low":
    filtered_df = filtered_df.sort_values(by="bottle_price", ascending=False)

# Display results
st.title("🍷 Wine Listings")
cols = st.columns(3)
for idx, row in filtered_df.iterrows():
    with cols[idx % 3]:
        st.markdown(f"**{row['wine_name']}**")
        st.markdown(f"*{row['producer']}*")
        st.markdown(f"*{row['vintage']}*")
        st.markdown(f"{row['varietal']} – {row['region']}")
        st.markdown(f"💰 ${row['bottle_price']:,.2f}")
        st.markdown(f"📦 {row['supplier']}")
        st.markdown("---")
