
import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide")

# Load data from the SQLite database
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
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Refine Search")

wine_name = st.sidebar.text_input("Search Wine Name")
selected_varietals = st.sidebar.multiselect("Varietal", sorted(df["varietal"].dropna().unique()))
selected_producers = st.sidebar.multiselect("Producer", sorted(df["producer"].dropna().unique()))
selected_suppliers = st.sidebar.multiselect("Supplier", sorted(df["supplier"].dropna().unique()))
min_price, max_price = st.sidebar.slider("Bottle Price Range", 0, 20000, (0, 20000))

sort_option = st.sidebar.selectbox("Sort By", ["Name (A-Z)", "Name (Z-A)", "Price (Low to High)", "Price (High to Low)"])

# Filter the DataFrame
filtered_df = df.copy()

if wine_name:
    filtered_df = filtered_df[filtered_df["wine_name"].str.contains(wine_name, case=False, na=False)]

if selected_varietals:
    filtered_df = filtered_df[filtered_df["varietal"].isin(selected_varietals)]

if selected_producers:
    filtered_df = filtered_df[filtered_df["producer"].isin(selected_producers)]

if selected_suppliers:
    filtered_df = filtered_df[filtered_df["supplier"].isin(selected_suppliers)]

filtered_df = filtered_df[
    (filtered_df["bottle_price"] >= min_price) &
    (filtered_df["bottle_price"] <= max_price)
]

# Sort
if sort_option == "Name (A-Z)":
    filtered_df = filtered_df.sort_values(by="wine_name", ascending=True)
elif sort_option == "Name (Z-A)":
    filtered_df = filtered_df.sort_values(by="wine_name", ascending=False)
elif sort_option == "Price (Low to High)":
    filtered_df = filtered_df.sort_values(by="bottle_price", ascending=True)
elif sort_option == "Price (High to Low)":
    filtered_df = filtered_df.sort_values(by="bottle_price", ascending=False)

# Grid display
st.markdown("## 🍷 Wine Results")

if filtered_df.empty:
    st.warning("No wines match your filters.")
else:
    num_cols = 3
    rows = filtered_df.shape[0] // num_cols + int(filtered_df.shape[0] % num_cols > 0)
    for i in range(rows):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            idx = i * num_cols + j
            if idx < filtered_df.shape[0]:
                row = filtered_df.iloc[idx]
                with cols[j]:
                    st.markdown(f"### {row['producer']}")
                    st.markdown(f"**{row['wine_name']}**")
                    st.markdown(f"*{row['vintage']}*  
_{row['varietal']} – {row['region']}_", unsafe_allow_html=True)
                    st.markdown(f"**Supplier:** {row['supplier']}")
                    st.markdown(f"**Price:** ${row['bottle_price']:.2f}")
