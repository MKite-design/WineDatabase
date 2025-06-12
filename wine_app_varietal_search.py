
import streamlit as st
import sqlite3
import pandas as pd
import os

DB_FILE = 'wine_supplier_with_producer.db'

st.set_page_config(page_title="Wine Supplier Search", layout="wide")
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

        # Varietal filter
        all_varietals = sorted(df['varietal'].dropna().unique())
        varietal_search = st.sidebar.text_input("Search Varietal").strip().lower()
        filtered_varietals = ['All'] + [v for v in all_varietals if varietal_search in v.lower()]
        varietal_filter = st.sidebar.selectbox("Select Varietal", filtered_varietals)

        # Region filter
        all_regions = sorted(df['region'].dropna().unique())
        region_search = st.sidebar.text_input("Search Region").strip().lower()
        filtered_regions = ['All'] + [r for r in all_regions if region_search in r.lower()]
        region_filter = st.sidebar.selectbox("Select Region", filtered_regions)

        # Vintage filter
        all_vintages = sorted(df['vintage'].dropna().astype(str).unique())
        vintage_search = st.sidebar.text_input("Search Vintage").strip()
        filtered_vintages = ['All'] + [v for v in all_vintages if vintage_search in v]
        vintage_filter = st.sidebar.selectbox("Select Vintage", filtered_vintages)

        # Price range
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
            df = df[df['varietal'].str.lower() == varietal_filter.lower()]
        elif varietal_search:
            df = df[df['varietal'].str.lower().str.contains(varietal_search)]

        if region_filter and region_filter != 'All':
            df = df[df['region'].str.lower() == region_filter.lower()]
        elif region_search:
            df = df[df['region'].str.lower().str.contains(region_search)]

        if vintage_filter and vintage_filter != 'All':
            df = df[df['vintage'].astype(str) == vintage_filter]
        elif vintage_search:
            df = df[df['vintage'].astype(str).str.contains(vintage_search)]

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
