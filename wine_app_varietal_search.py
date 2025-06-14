import streamlit as st
import pandas as pd
import sqlite3
from typing import List

st.set_page_config(layout="wide")

@st.cache_data

def load_data():
    conn = sqlite3.connect("wine_supplier_clean.db")
    df = pd.read_sql_query("SELECT * FROM wines", conn)
    conn.close()

    df.fillna("", inplace=True)
    df["display_name"] = df["wine_name"] + " (" + df["vintage"].astype(str) + ")"
    df["sort_name"] = df["producer"] + " " + df["wine_name"]

    # Cast price to numeric
    df["bottle_price"] = pd.to_numeric(df["bottle_price"], errors="coerce")

    return df.sort_values("sort_name").reset_index(drop=True)

df = load_data()

# Sidebar filters
st.sidebar.header("Search Filters")

varietals = sorted(df["varietal"].unique())
regions = sorted(df["region"].unique())
producers = sorted(df["producer"].unique())
suppliers = sorted(df["supplier"].unique())

tags = ["Red", "White", "Rosé", "Sparkling", "Orange", "Dessert", "Fortified", "Vegan"]
type_map = {
    "Red": ["Shiraz", "Cabernet Sauvignon", "Merlot", "Pinot Noir", "Grenache", "Cabernet Franc", "Red Blend", "Cabernet Blend"],
    "White": ["Chardonnay", "Sauvignon Blanc", "Riesling", "Pinot Gris", "Semillon", "White Blend"],
    "Rosé": ["Rosé", "Rose"],
    "Sparkling": ["Sparkling", "MCC", "Champagne", "Prosecco"],
    "Orange": ["Orange"],
    "Dessert": ["Dessert", "Sweet"],
    "Fortified": ["Fortified", "Port", "Sherry", "Madeira"],
    "Vegan": ["Vegan"]
}

selected_tags = st.sidebar.multiselect("Wine Type Tags", tags)

selected_varietals = st.sidebar.multiselect("Varietals", varietals)
selected_regions = st.sidebar.multiselect("Regions", regions)
selected_producers = st.sidebar.multiselect("Producers", producers)
selected_suppliers = st.sidebar.multiselect("Suppliers", suppliers)
price_range = st.sidebar.slider("Price Range ($)", 0, int(df["bottle_price"].max() or 1000), (0, 1000))
vintage_range = st.sidebar.slider("Vintage Range", int(df["vintage"].min()), int(df["vintage"].max()), (2010, 2025))

# Filtering logic
filtered_df = df.copy()

if selected_varietals:
    filtered_df = filtered_df[filtered_df["varietal"].isin(selected_varietals)]

if selected_regions:
    filtered_df = filtered_df[filtered_df["region"].isin(selected_regions)]

if selected_producers:
    filtered_df = filtered_df[filtered_df["producer"].isin(selected_producers)]

if selected_suppliers:
    filtered_df = filtered_df[filtered_df["supplier"].isin(selected_suppliers)]

if selected_tags:
    allowed_varietals = set()
    for tag in selected_tags:
        allowed_varietals.update(type_map.get(tag, []))
    filtered_df = filtered_df[filtered_df["varietal"].isin(allowed_varietals)]

filtered_df = filtered_df[(filtered_df["bottle_price"] >= price_range[0]) & (filtered_df["bottle_price"] <= price_range[1])]
filtered_df = filtered_df[(filtered_df["vintage"] >= vintage_range[0]) & (filtered_df["vintage"] <= vintage_range[1])]

# Display result count
st.markdown(f"### Displaying {len(filtered_df)} of {len(df)} wines")

# Grid display
columns = st.columns(4)

for idx, (_, row) in enumerate(filtered_df.iterrows()):
    with columns[idx % 4]:
        st.markdown(
            f"""
            **{row['producer']}**  
            *{row['wine_name']} ({row['vintage']})*  
            Varietal: {row['varietal']}  
            Region: {row['region']}  
            Supplier: {row['supplier']}  
            Price: ${row['bottle_price']:.2f}
            """
        )
        if st.button(f"Add to Shortlist {row['wine_id']}"):
            st.session_state.shortlist.add(row['wine_id'])

# Shortlist display
if st.session_state.get("shortlist"):
    st.markdown("## Shortlisted Wines")
    shortlisted_df = df[df["wine_id"].isin(st.session_state.shortlist)]
    st.dataframe(shortlisted_df[["producer", "wine_name", "vintage", "bottle_price"]])
