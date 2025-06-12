
import streamlit as st
import sqlite3
import pandas as pd
import os

DB_FILE = 'wine_supplier_with_producer.db'

st.set_page_config(page_title="Wine Supplier Explorer", layout="wide")
st.title("🍷 Wine Supplier Search")

if not os.path.exists(DB_FILE):
    st.error(f"Database file '{DB_FILE}' not found.")
else:
    conn = sqlite3.connect(DB_FILE)
    try:
        query = '''
        SELECT 
            wines.producer,
            wines.wine_name,
            wines.vintage,
            wines.varietal,
            wines.region,
            suppliers.name AS supplier,
            wine_prices.bottle_price,
            wine_prices.case_price,
            wine_prices.case_size,
            wine_prices.availability
        FROM wine_prices
        JOIN wines ON wine_prices.wine_id = wines.wine_id
        JOIN suppliers ON wine_prices.supplier_id = suppliers.supplier_id
        '''
        df = pd.read_sql_query(query, conn)

        # Sidebar filters
        st.sidebar.header("🔎 Filter Wines")

        name_filter = st.sidebar.text_input("Wine Name")

        # Filter varietal options dynamically
        all_varietals = sorted(df['varietal'].dropna().unique())
        varietal_search = st.sidebar.text_input("Search Varietal").strip().lower()
        filtered_varietals = ['All'] + [v for v in all_varietals if varietal_search in v.lower()]
        varietal_filter = st.sidebar.selectbox("Select Varietal", filtered_varietals)

        st.sidebar.markdown("**Bottle Price Range**")
        min_price = st.sidebar.number_input("Min", value=0.0, step=1.0)
        max_price = st.sidebar.number_input("Max", value=500.0, step=1.0)

        with st.sidebar.expander("Advanced Filters"):
            producer_filter = st.text_input("Producer")
            supplier_filter = st.text_input("Supplier")

        # Apply filters
        if name_filter:
            df = df[df['wine_name'].str.contains(name_filter, case=False, na=False)]

        if varietal_filter and varietal_filter != 'All':
            df = df[df['varietal'] == varietal_filter]

        if producer_filter:
            df = df[df['producer'].str.contains(producer_filter, case=False, na=False)]

        if supplier_filter:
            df = df[df['supplier'].str.contains(supplier_filter, case=False, na=False)]

        df = df[(df['bottle_price'] >= min_price) & (df['bottle_price'] <= max_price)]

        st.markdown(f"### 📋 {len(df)} wines found")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")
    finally:
        conn.close()
