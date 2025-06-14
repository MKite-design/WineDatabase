import sqlite3
import pandas as pd
import streamlit as st

@st.cache_data

def load_data():
    conn = sqlite3.connect("wine_supplier_with_producer.db")
    query = '''
        SELECT 
            w.wine_id, w.wine_name, w.vintage, w.varietal, w.region, 
            w.producer, w.type, s.name AS supplier, p.bottle_price
        FROM wines w
        JOIN wine_prices p ON w.wine_id = p.wine_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    df.fillna("", inplace=True)
    df["sort_name"] = df["wine_name"].str.lower()
    return df.sort_values("sort_name").reset_index(drop=True)

df = load_data()

# --- Sidebar filters ---
st.sidebar.header("Search Filters")

# Type filter (Red, White, Rosé, etc.)
types = sorted(df["type"].unique())
type_filter = st.sidebar.multiselect("Wine Type", types, default=types)

# Varietal filter
varietals = sorted(df["varietal"].unique())
varietal_filter = st.sidebar.multiselect("Varietal", varietals, default=varietals)

# Region filter
regions = sorted(df["region"].unique())
region_filter = st.sidebar.multiselect("Region", regions, default=regions)

# Producer filter
producers = sorted(df["producer"].unique())
producer_filter = st.sidebar.multiselect("Producer", producers, default=producers)

# Supplier filter
suppliers = sorted(df["supplier"].unique())
supplier_filter = st.sidebar.multiselect("Supplier", suppliers, default=suppliers)

# Price filter
min_price, max_price = int(df["bottle_price"].min()), int(df["bottle_price"].max())
price_range = st.sidebar.slider("Bottle Price Range", min_value=0, max_value=max(1000, max_price),
                                value=(min_price, max_price))

# --- Filtered DataFrame ---
filtered_df = df[
    (df["type"].isin(type_filter)) &
    (df["varietal"].isin(varietal_filter)) &
    (df["region"].isin(region_filter)) &
    (df["producer"].isin(producer_filter)) &
    (df["supplier"].isin(supplier_filter)) &
    (df["bottle_price"] >= price_range[0]) &
    (df["bottle_price"] <= price_range[1])
]

st.markdown(f"### Displaying {len(filtered_df)} of {len(df)} wines")

# --- Display Grid ---
for _, row in filtered_df.iterrows():
    with st.container():
        st.markdown(f"**{row['wine_name']} ({row['vintage']})**")
        st.markdown(f"*{row['producer']} — {row['region']}*  ")
        st.markdown(f"Varietal: {row['varietal']} | Type: {row['type']} | Supplier: {row['supplier']}")
        st.markdown(f"**${row['bottle_price']:.2f}**")
        st.markdown("---")
