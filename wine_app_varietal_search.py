
import streamlit as st
import pandas as pd
import sqlite3

# Load data
@st.cache_data
def load_data():
    conn = sqlite3.connect("wine_supplier_with_producer (1).db")
    query = '''
        SELECT w.wine_id, w.wine_name, w.vintage, w.varietal, w.region, w.producer,
               s.name AS supplier, p.bottle_price
        FROM wines w
        JOIN wine_prices p ON w.wine_id = p.wine_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("🔍 Refine Search")

name_filter = st.sidebar.text_input("Search Wine Name")
selected_varietals = st.sidebar.multiselect("Varietal", sorted(df['varietal'].dropna().unique()))
selected_regions = st.sidebar.multiselect("Region", sorted(df['region'].dropna().unique()))
selected_producers = st.sidebar.multiselect("Producer", sorted(df['producer'].dropna().unique()))
selected_suppliers = st.sidebar.multiselect("Supplier", sorted(df['supplier'].dropna().unique()))

min_price, max_price = st.sidebar.slider("Price Range", 
    float(df['bottle_price'].min()), float(df['bottle_price'].max()), 
    (float(df['bottle_price'].min()), float(df['bottle_price'].max()))
)

sort_option = st.sidebar.selectbox("Sort by", [
    "Name (A-Z)", "Name (Z-A)", "Price (Low to High)", "Price (High to Low)"
])

# Apply Filters
if name_filter:
    df = df[df['wine_name'].str.contains(name_filter, case=False)]

if selected_varietals:
    df = df[df['varietal'].isin(selected_varietals)]

if selected_regions:
    df = df[df['region'].isin(selected_regions)]

if selected_producers:
    df = df[df['producer'].isin(selected_producers)]

if selected_suppliers:
    df = df[df['supplier'].isin(selected_suppliers)]

df = df[(df['bottle_price'] >= min_price) & (df['bottle_price'] <= max_price)]

# Sorting Logic
if sort_option == "Name (A-Z)":
    df = df.sort_values(by="wine_name")
elif sort_option == "Name (Z-A)":
    df = df.sort_values(by="wine_name", ascending=False)
elif sort_option == "Price (Low to High)":
    df = df.sort_values(by="bottle_price")
elif sort_option == "Price (High to Low)":
    df = df.sort_values(by="bottle_price", ascending=False)

# Display Results in a Grid
st.markdown("### 🍷 Matching Wines")
cols = st.columns(3)
for idx, (_, row) in enumerate(df.iterrows()):
    with cols[idx % 3]:
        st.markdown(f"**{row['wine_name']}**")
        st.markdown(f"*{row['varietal']} – {row['region']}*")
        st.markdown(f"*{row['vintage']}*  
**${row['bottle_price']:.2f}**")
        st.markdown(f"Supplier: `{row['supplier']}`")
