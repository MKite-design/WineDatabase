import streamlit as st
import pandas as pd
import sqlite3
from unidecode import unidecode
import math
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(layout="wide")
st.title("🍇 Wine Listings")

# Authorize with Google Sheets using secrets.toml
gcp_creds = st.secrets["gcp_service_account"]
    
# Authenticate with proper scopes
scoped_creds = Credentials.from_service_account_info(
st.secrets["gcp_service_account"],
scopes=["https://www.googleapis.com/auth/spreadsheets", 
"https://www.googleapis.com/auth/drive"])
            
gc = gspread.authorize(scoped_creds)
            
            
# Use the key from your sheet URL
sheet_key = "1H6guq90INPuSk49BfweRJ8zpPUCBLmHLNtVpVX-vThU"
worksheet = gc.open_by_key(sheet_key).sheet1
            
            
# This pulls all rows of the Google Sheet as a list of dictionaries
data = worksheet.get_all_records()
            
# Convert it into a pandas DataFrame
df_sheet = pd.DataFrame(data)
            
# Ensure all values in 'vintage' are strings for Arrow compatibility
if 'vintage' in df_sheet.columns:
    df_sheet['vintage'] = df_sheet['vintage'].astype(str)

# Load cleaned varietal mapping from CSV
varietal_map_df = pd.read_csv("raw_varietals_for_cleaning.csv").dropna(subset=["varietal", "Clean Varietal"])
varietal_map = dict(zip(varietal_map_df["varietal"].str.strip(), varietal_map_df["Clean Varietal"].str.strip()))

# Load data from SQLite
@st.cache_data
def get_google_sheet_df():
    worksheet = gc.open_by_key(sheet_key).sheet1
    data = worksheet.get_all_records()
    df_sheet = pd.DataFrame(data)
    for col in df_sheet.columns:
        df_sheet[col] = df_sheet[col].astype(str)
    return df_sheet
    
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

    df.fillna({
        "wine_name": "",
        "vintage": "NV",
        "varietal": "Unknown",
        "region": "Unknown",
        "producer": "Unknown",
        "supplier": "Unknown",
        "bottle_price": 0.0
    }, inplace=True)

    df["sort_name"] = df["producer"].apply(lambda x: unidecode(x).lower()) + " " + df["wine_name"].apply(lambda x: unidecode(x).lower())

    df["clean_varietal"] = df["varietal"].map(varietal_map).fillna(df["varietal"])
    df["clean_varietal"] = df["clean_varietal"].apply(lambda x: unidecode(str(x)).lower())

    def classify_wine_type(varietal):
        varietal = varietal.lower()
        if any(x in varietal for x in ["shiraz", "pinot noir", "merlot", "cabernet", "tempranillo", "malbec"]):
            return "Red"
        elif any(x in varietal for x in ["chardonnay", "sauvignon", "riesling", "semillon", "pinot gris", "vermentino"]):
            return "White"
        elif "rosé" in varietal or "rose" in varietal:
            return "Rosé"
        elif any(x in varietal for x in ["sparkling", "champagne", "prosecco", "methode", "cava"]):
            return "Sparkling"
        elif any(x in varietal for x in ["port", "sherry", "vermouth"]):
            return "Fortified"
        return "Other"

    df["wine_type"] = df["clean_varietal"].apply(classify_wine_type)
    df["clean_producer"] = df["producer"].apply(lambda x: unidecode(x).lower())
    df["clean_wine_name"] = df["wine_name"].apply(lambda x: unidecode(x).lower())
    df = df.sort_values("sort_name")
    return df.reset_index(drop=True)

df = load_data()

tab1, tab2 = st.tabs(["🍷 Wine Browser", "📋 Sheet Preview"])
with tab1:

    price_tiers = [0, 5, 10, 15, 25, 35, 50, 60, 70, 80, 90, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 700]
    bottle_multipliers = [3, 2.5, 2.5, 2.25, 2.15, 2.0, 1.9, 1.8, 1.7, 1.6, 1.6, 1.6, 1.6, 1.55, 1.5, 1.5, 1.45, 1.4, 1.4, 1.3, 1.3, 1.3, 1.3, 1.3]
    glass_multipliers = [2.2, 2.1, 2.05, 2.00, 1.95, 1.85, 1.80, 1.75, 1.70, 1.65, 1.6, 1.6, 1.6]  # Glass price multiplier only for <= $200
    takeaway_multipliers = [2, 1.8, 1.7, 1.65, 1.57, 1.54, 1.50, 1.48, 1.45, 1.42, 1.39, 1.36, 1.33, 1.3, 1.2, 1.2, 1.2, 1.2, 1.15, 1.15, 1.15, 1.15]
    
    def calculate_bottle_price(luc):
        if np.isnan(luc) or luc <= 0:
            return "N/A"
        inc_price = luc * 1.1
        idx = np.searchsorted(price_tiers, luc, side="right") - 1
        idx = min(idx, len(bottle_multipliers) - 1)
        multiplier = bottle_multipliers[idx]
        result = math.ceil(inc_price * multiplier / 10.0) * 10
        return int(result)
    
    def calculate_glass_price(luc):
        if np.isnan(luc) or luc <= 0 or luc * 1.1 > 200:
            return "N/A"
        inc_price = luc * 1.1
        idx = np.searchsorted(price_tiers, luc, side="left") - 1
        idx = min(idx, len(glass_multipliers) - 1)
        multiplier = glass_multipliers[idx]
        rounded_bottle_price = math.ceil(inc_price * multiplier / 10.0) * 10
        glass_price = max(rounded_bottle_price / 4, 14)
        return round(glass_price, 2)
    
    def calculate_takeaway_price(luc):
        if np.isnan(luc) or luc <= 0:
            return "N/A"
        inc_price = luc * 1.1
        idx = np.searchsorted(price_tiers, luc, side="left") - 1
        idx = min(idx, len(takeaway_multipliers) - 1)
        multiplier = takeaway_multipliers[idx]
        result = math.ceil(inc_price * multiplier / 10.0) * 10
        return int(result)
    
    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def safe_float_str(value):
        try:
            return f"${float(value):.2f}"
        except (ValueError, TypeError):
            return "N/A"
    
    
    df["calculated_bottle_price"] = df["bottle_price"].apply(calculate_bottle_price)
    df["calculated_glass_price"] = df["bottle_price"].apply(calculate_glass_price)
    df["calculated_takeaway_price"] = df["bottle_price"].apply(calculate_takeaway_price)
    
    # PAGE NAVIGATION
    page = st.sidebar.radio("Select Page", ["🍷 Wine Browser", "✏️ Edit Wines"])
    
    if page == "🍷 Wine Browser":
        # all existing filtering + display logic remains here (unchanged)
        pass
    
    elif page == "✏️ Edit Wines":
        st.header("✏️ Edit Existing Wine")
        df["display_name"] = df["wine_name"] + " (" + df["producer"] + ")"
        wine_to_edit = st.selectbox("Select wine", df["display_name"].tolist())
        selected_row = df[df["display_name"] == wine_to_edit]
        if not selected_row.empty:
            selected_row = selected_row.iloc[0]
            with st.form("edit_wine_form"):
                new_name = st.text_input("Wine Name", selected_row["wine_name"])
                new_vintage = st.text_input("Vintage", selected_row["vintage"])
                new_varietal = st.text_input("Varietal", selected_row["varietal"])
                new_region = st.text_input("Region", selected_row["region"])
                new_producer = st.text_input("Producer", selected_row["producer"])
                new_price = st.number_input("LUC Price ($)", value=selected_row["bottle_price"], step=0.1)
    
                submitted = st.form_submit_button("Update Wine")
                if submitted:
                    conn = sqlite3.connect("wine_supplier_with_producer.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE wines
                        SET wine_name = ?, vintage = ?, varietal = ?, region = ?, producer = ?
                        WHERE wine_id = ?
                    """, (new_name, new_vintage, new_varietal, new_region, new_producer, selected_row["wine_id"]))
    
                    cursor.execute("""
                        UPDATE wine_prices
                        SET bottle_price = ?
                        WHERE wine_id = ?
                    """, (new_price, selected_row["wine_id"]))
    
                    conn.commit()
                    conn.close()
                    st.success("✅ Wine updated successfully!")
                    st.cache_data.clear()
        else:
            st.warning("⚠️ Could not find selected wine.")
    
    if "shortlist" not in st.session_state:
        st.session_state.shortlist = set()
    
    with st.container():
        cols = st.columns([3, 2, 2])
        with cols[0]:
            wine_search = st.text_input("🔍 Search by Wine or Producer")
        with cols[1]:
            sort_option = st.selectbox("Sort By", ["Producer A-Z", "Producer Z-A", "Price Low-High", "Price High-Low"])
        with cols[2]:
            type_tags = st.multiselect("Wine Type", ["Red", "White", "Rosé", "Sparkling", "Fortified"])
    
    with st.sidebar:
        st.header("⚙️ Advanced Filters")
    
        under_50 = st.checkbox("💲 Show only wines under $50")
        over_500 = st.checkbox("💰 Show only wines over $500")
with st.sidebar:
    pretty_varietals = sorted(set(v.title() for v in df["clean_varietal"].unique()))
    varietal_selection = st.multiselect("Varietal", pretty_varietals)
    producers = st.multiselect("Producer", sorted(df["producer"].unique()))
    suppliers = st.multiselect("Supplier", sorted(df["supplier"].unique()))
        
    filtered_df = df.copy()
        
        if wine_search:
            wine_search_clean = unidecode(wine_search.lower())
            filtered_df = filtered_df[
                filtered_df["clean_wine_name"].str.contains(wine_search_clean, na=False) |
                filtered_df["clean_producer"].str.contains(wine_search_clean, na=False)
            ]
        
    
    st.markdown("**Price Range (LUC $)**")
    col_min, col_max = st.columns(2)
    
    with col_min:
        price_min = st.number_input(
            "Min", min_value=0.0, value=0.0, step=1.0, format="%.2f"
        )
    
    with col_max:
        price_max = st.number_input(
            "Max", min_value=0.0, value=float(df["bottle_price"].max() + 10), step=1.0, format="%.2f"
        )
        
        
    # Apply checkbox filters
    if under_50:
        filtered_df = filtered_df[filtered_df["bottle_price"] <= 50]
    
    if over_500:
        filtered_df = filtered_df[filtered_df["bottle_price"] > 500]
    
    # Apply box-based price range filter
    filtered_df = filtered_df[
        (filtered_df["bottle_price"] >= price_min) &
        (filtered_df["bottle_price"] <= price_max)
    ]

    
if varietal_selection:
        varietals_clean = [unidecode(v.lower()) for v in varietal_selection]
        filtered_df = filtered_df[filtered_df["clean_varietal"].isin(varietals_clean)]
if producers:
        filtered_df = filtered_df[filtered_df["producer"].isin(producers)]
if suppliers:
        filtered_df = filtered_df[filtered_df["supplier"].isin(suppliers)]
if type_tags:
        filtered_df = filtered_df[filtered_df["wine_type"].isin(type_tags)]
    
if sort_option == "Producer A-Z":
        filtered_df = filtered_df.sort_values("sort_name")
elif sort_option == "Producer Z-A":
        filtered_df = filtered_df.sort_values("sort_name", ascending=False)
elif sort_option == "Price Low-High":
        filtered_df = filtered_df.sort_values("bottle_price")
elif sort_option == "Price High-Low":
        filtered_df = filtered_df.sort_values("bottle_price", ascending=False)
    
st.markdown(f"**Displaying {len(filtered_df)} of {len(df)} wines**")
    
st.markdown("""
    <style>
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 1rem;
      padding: 1rem 0.5rem;
    }
    .card {
      background: white;
      border-radius: 12px;
      padding: 1rem;
      box-shadow: 0 2px 6px rgba(0,0,0,0.08);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 100%;
    }
    .card-title {
      font-weight: 700;
      font-size: 1.1rem;
      margin-bottom: 0.3rem;
      color: #111;
    }
    .card-sub {
      font-style: italic;
      color: #555;
      font-size: 0.9rem;
      margin-bottom: 0.3rem;
    }
    .price {
      margin-top: 0.6rem;
      font-weight: bold;
      color: #222;
      font-size: 1rem;
    }
    .shortlist-button {
      margin-top: 0.6rem;
      text-align: right;
    }
    @media only screen and (max-width: 768px) {
      .card-title {
        font-size: 1rem;
      }
      .card-sub {
        font-size: 0.85rem;
      }
      .price {
        font-size: 0.95rem;
      }
    }
    </style>
    """, unsafe_allow_html=True)
    
st.markdown("<div class='grid'>", unsafe_allow_html=True)
    
for i, row in filtered_df.iterrows():
        is_shortlisted = row['wine_id'] in st.session_state.shortlist
    
st.markdown(f"""
        <div class='card'>
            <div class='card-title'>{row['producer']} {row['wine_name']}</div>
            <div class='card-sub'>{row['vintage']}</div>
            <div class='card-sub'>{row['varietal']} – {row['region']}</div>
            <div class='card-sub'>Supplier: {row['supplier']}</div>
            <div class='price'>
                💲 <strong>LUC:</strong> {safe_float_str(row.get('bottle_price'))}<br>
                🍾 <strong>Bottle Price:</strong> {safe_float_str(row.get('calculated_bottle_price'))}<br>
                🥂 <strong>Glass Price:</strong> {safe_float_str(row.get('calculated_glass_price'))}<br>
                📦 <strong>Takeaway Price:</strong> {safe_float_str(row.get('calculated_takeaway_price'))}
    </div>
    
    
    
        """, unsafe_allow_html=True)
    
button_label = "✅ Shortlisted" if is_shortlisted else "➕ Shortlist"
if st.button(button_label, key=f"shortlist_btn_{row['wine_id']}_{i}"):
        if is_shortlisted:
            st.session_state.shortlist.remove(row['wine_id'])
        else:
            st.session_state.shortlist.add(row['wine_id'])
    
st.markdown("</div>", unsafe_allow_html=True)
    
with st.sidebar:
    if st.session_state.shortlist:
        st.markdown("### 📝 Shortlist")
        for sid in st.session_state.shortlist:
            wine = df[df['wine_id'] == sid].iloc[0]
            st.write(f"{wine['producer']} {wine['wine_name']} ({wine['vintage']}) – ${wine['bottle_price']:.2f}")
        st.button("Clear Shortlist", on_click=lambda: st.session_state.shortlist.clear())
    
    columns_to_export = [
                "wine_name", "vintage", "clean_varietal", "region", "producer", "supplier", "bottle_price"
            ]
    
    export_df = df[df["wine_id"].isin(st.session_state.shortlist)].copy()
    export_df = export_df[columns_to_export]
    export_df = export_df.rename(columns={
                "wine_name": "Wine Name",
                "vintage": "Vintage",
                "clean_varietal": "Varietal",
                "region": "Region",
                "producer": "Producer",
                "supplier": "Supplier",
                "bottle_price": "Price ($)"
            })
    
    export_csv = export_df.to_csv(index=False)
    
    st.download_button(
            label="📅 Download Shortlist (CSV)",
            data=export_csv,
            file_name="wine_shortlist.csv",
            mime="text/csv"
        )
with tab2:
    with tab2:
        st.subheader("📋 Wines from Google Sheet")

    with st.spinner("Loading sheet..."):
        df_sheet = get_google_sheet_df()

    # Ensure all object columns are safely converted to string
    for col in df_sheet.select_dtypes(include=["object", "int", "float"]).columns:
        df_sheet[col] = df_sheet[col].astype(str)

    st.dataframe(df_sheet, use_container_width=True)

