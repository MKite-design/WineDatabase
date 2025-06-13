
import streamlit as st
import sqlite3
import pandas as pd
import os

DB_FILE = 'wine_supplier_with_producer.db'

st.set_page_config(page_title="Wine Supplier Search", layout="wide")
st.title("Wine Supplier Search")

# JavaScript screen width detection
st.markdown(
    '''
    <script>
    const screenWidth = window.innerWidth;
    window.parent.postMessage({type: 'STREAMLIT:SET_SESSION_STATE', key: 'screen_width', value: screenWidth}, '*');
    </script>
    ''',
    unsafe_allow_html=True
)

# Default screen width if not set
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

        with st.expander("Filters", expanded=True):
            name_filter = st.text_input("Wine Name")
            varietal_filter = st.selectbox("Varietal", ["All"] + sorted(df['varietal'].dropna().unique()))
            region_filter = st.selectbox("Region", ["All"] + sorted(df['region'].dropna().unique()))
            vintage_filter = st.selectbox("Vintage", ["All"] + sorted(df['vintage'].dropna().astype(str).unique()))
            producer_filter = st.text_input("Producer")
            supplier_filter = st.text_input("Supplier")
            min_price = st.number_input("Min Bottle Price", value=0.0, step=1.0)
max_price = st.number_input("Max Bottle Price", value=20000.0, step=1.0)

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
        if supplier_filter:
            df = df[df['supplier'].str.contains(supplier_filter, case=False, na=False)]
        df = df[(df['bottle_price'] >= min_price) & (df['bottle_price'] <= max_price)]

        st.markdown(f"### {len(df)} wines found")

        if is_mobile:
            for _, row in df.iterrows():
                st.markdown(f"""
**{{row['producer']}}**  
{{row['wine_name']}} ({{row['vintage']}})  
*{{row['varietal']}} - {{row['region']}}*  
Supplier: {{row['supplier']}}  
Price: ${{row['bottle_price']:.2f}}  
---""")
        else:
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")
    finally:
        conn.close()
