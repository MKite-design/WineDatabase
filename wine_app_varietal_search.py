
import streamlit as st
import sqlite3
import pandas as pd
import os

DB_FILE = 'wine_supplier_with_producer.db'

st.set_page_config(page_title="Wine Supplier Explorer", layout="wide")
st.title("🍷 Wine Supplier Explorer")

# Detect screen size
st.markdown(
    '''
    <script>
    const screenWidth = window.innerWidth;
    window.parent.postMessage({type: 'STREAMLIT:SET_SESSION_STATE', key: 'screen_width', value: screenWidth}, '*');
    </script>
    ''',
    unsafe_allow_html=True
)

if "screen_width" not in st.session_state:
    st.session_state["screen_width"] = 1000

is_mobile = st.session_state["screen_width"] < 768

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
            wine_prices.bottle_price
        FROM wine_prices
        JOIN wines ON wine_prices.wine_id = wines.wine_id
        JOIN suppliers ON wine_prices.supplier_id = suppliers.supplier_id
        '''
        df = pd.read_sql_query(query, conn)

        # Sidebar filters
        with st.sidebar:
            st.header("🔎 Refine Search")
            name_filter = st.text_input("Wine Name")
            varietal_filter = st.selectbox("Varietal", ["All"] + sorted(df['varietal'].dropna().unique()))
            region_filter = st.selectbox("Region", ["All"] + sorted(df['region'].dropna().unique()))
            vintage_filter = st.selectbox("Vintage", ["All"] + sorted(df['vintage'].dropna().astype(str).unique()))
            producer_filter = st.text_input("Producer")
            supplier_filter = st.selectbox("Supplier", ["All"] + sorted(df["supplier"].dropna().unique()))
            min_price = st.number_input("Min Price", value=0.0, step=1.0)
            max_price = st.number_input("Max Price", value=20000.0, step=1.0)
            if st.button("Clear Filters"):
                st.experimental_rerun()

        sort_options = {
            "Name: A to Z": ("wine_name", True),
            "Name: Z to A": ("wine_name", False),
            "Price: Low to High": ("bottle_price", True),
            "Price: High to Low": ("bottle_price", False),
            "Vintage: New to Old": ("vintage", False),
            "Vintage: Old to New": ("vintage", True),
        }

        selected_sort = st.selectbox("Sort by", list(sort_options.keys()))

        # Apply filters
        if name_filter:
            df = df[df['wine_name'].str.contains(name_filter, case=False, na=False)]
        if varietal_filter != "All":
            df = df[df['varietal'] == varietal_filter]
        if region_filter != "All":
            df = df[df['region'] == region_filter]
        if vintage_filter != "All":
            df = df[df['vintage'].astype(str) == vintage_filter]
        if producer_filter:
            df = df[df['producer'].str.contains(producer_filter, case=False, na=False)]
        if supplier_filter != "All":
            df = df[df['supplier'].str.contains(supplier_filter, case=False, na=False)]
        df = df[(df['bottle_price'] >= min_price) & (df['bottle_price'] <= max_price)]

        # Sort
        sort_field, ascending = sort_options[selected_sort]
        df = df.sort_values(by=sort_field, ascending=ascending)

        st.markdown(f"### {len(df)} wines found")

        # Styling
        st.markdown("""<style>
            .wine-card {
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #fff;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                font-size: 0.95rem;
            }
        </style>""", unsafe_allow_html=True)

        if is_mobile:
            for _, row in df.iterrows():
                st.markdown(f'''
<div class="wine-card">
<strong>{row["producer"]}</strong><br>
{row["wine_name"]} ({row["vintage"]})<br>
<em>{row["varietal"]} – {row["region"]}</em><br>
Supplier: {row["supplier"]}<br>
Price: ${row["bottle_price"]:.2f}
</div>
''', unsafe_allow_html=True)
        else:
            cols = st.columns(3)
            for i, (_, row) in enumerate(df.iterrows()):
                with cols[i % 3]:
                    st.markdown(f'''
<div class="wine-card">
<strong>{row["producer"]}</strong><br>
{row["wine_name"]} ({row["vintage"]})<br>
<em>{row["varietal"]} – {row["region"]}</em><br>
Supplier: {row["supplier"]}<br>
Price: ${row["bottle_price"]:.2f}
</div>
''', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")
    finally:
        conn.close()
