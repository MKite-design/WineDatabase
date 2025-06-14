
import streamlit as st
import sqlite3
import pandas as pd

@st.cache_data
def load_data():
    conn = sqlite3.connect("wine_supplier_with_producer (1).db")
    query = """
        SELECT w.wine_id, w.wine_name, w.vintage, w.varietal, w.region, w.producer,
               s.name AS supplier, p.bottle_price
        FROM wines w
        JOIN wine_prices p ON w.wine_id = p.wine_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Keep only the lowest price for each wine
    idx_min = df.groupby('wine_id')['bottle_price'].idxmin()
    return df.loc[idx_min].reset_index(drop=True)

df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Refine Search")

wine_name = st.sidebar.text_input("Search Wine Name")
varietal = st.sidebar.selectbox("Varietal", ["All"] + sorted(df["varietal"].dropna().unique().tolist()))
region = st.sidebar.selectbox("Region", ["All"] + sorted(df["region"].dropna().unique().tolist()))
vintage = st.sidebar.selectbox("Vintage", ["All"] + sorted(df["vintage"].dropna().astype(str).unique().tolist()))
producer = st.sidebar.selectbox("Producer", ["All"] + sorted(df["producer"].dropna().unique().tolist()))
supplier = st.sidebar.selectbox("Supplier", ["All"] + sorted(df["supplier"].dropna().unique().tolist()))

min_price = st.sidebar.number_input("Min Price", min_value=0.0, value=0.0, step=1.0)
max_price = st.sidebar.number_input("Max Price", min_value=0.0, value=20000.0, step=1.0)

sort_by = st.sidebar.selectbox("Sort by", ["Name (A-Z)", "Price (Low to High)", "Price (High to Low)"])

# Apply filters
filtered_df = df.copy()

if wine_name:
    filtered_df = filtered_df[filtered_df['wine_name'].str.contains(wine_name, case=False)]

if varietal != "All":
    filtered_df = filtered_df[filtered_df["varietal"] == varietal]

if region != "All":
    filtered_df = filtered_df[filtered_df["region"] == region]

if vintage != "All":
    filtered_df = filtered_df[filtered_df["vintage"].astype(str) == vintage]

if producer != "All":
    filtered_df = filtered_df[filtered_df["producer"] == producer]

if supplier != "All":
    filtered_df = filtered_df[filtered_df["supplier"] == supplier]

filtered_df = filtered_df[(filtered_df["bottle_price"] >= min_price) & (filtered_df["bottle_price"] <= max_price)]

# Sort
if sort_by == "Name (A-Z)":
    filtered_df = filtered_df.sort_values(by="wine_name")
elif sort_by == "Price (Low to High)":
    filtered_df = filtered_df.sort_values(by="bottle_price")
elif sort_by == "Price (High to Low)":
    filtered_df = filtered_df.sort_values(by="bottle_price", ascending=False)

# Display results
st.markdown(f"### Showing {len(filtered_df)} result(s)")

for _, row in filtered_df.iterrows():
    st.markdown(f"""
    <div style='padding: 10px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 10px;'>
        <strong>{row['wine_name']} ({row['vintage']})</strong><br>
        <em>{row['varietal']} – {row['region']}</em><br>
        <span style='font-size: 0.9em;'>Producer: {row['producer']}<br>
        Supplier: {row['supplier']}<br>
        <strong>Price: ${row['bottle_price']:.2f}</strong></span>
    </div>
    """, unsafe_allow_html=True)
