
import streamlit as st
import pandas as pd
import sqlite3
from unidecode import unidecode

st.set_page_config(layout="wide")
st.title("🍷 Wine Listings")

# Load cleaned varietal mapping from CSV
varietal_map_df = pd.read_csv("raw_varietals_for_cleaning.csv").dropna(subset=["varietal", "Clean Varietal"])
varietal_map = dict(zip(varietal_map_df["varietal"].str.strip(), varietal_map_df["Clean Varietal"].str.strip()))

# Load data from SQLite
@st.cache_data
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
    
    # Apply cleaned varietal mapping to create clean_varietal column
    df["clean_varietal"] = df["varietal"].map(varietal_map).fillna(df["varietal"])
    df["clean_varietal"] = df["clean_varietal"].apply(lambda x: unidecode(str(x)).lower())


    # Wine type classifier
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

if "shortlist" not in st.session_state:
    st.session_state.shortlist = set()

# --- TOP FILTERS ---
with st.container():
    cols = st.columns([3, 2, 2])
    with cols[0]:
        wine_search = st.text_input("🔍 Search by Wine or Producer")
    with cols[1]:
        sort_option = st.selectbox("Sort By", ["Producer A-Z", "Producer Z-A", "Price Low-High", "Price High-Low"])
    with cols[2]:
        type_tags = st.multiselect("Wine Type", ["Red", "White", "Rosé", "Sparkling", "Fortified"])

# --- SIDEBAR ADVANCED FILTERS ---
with st.sidebar:
    st.header("⚙️ Advanced Filters")
    
    under_50 = st.checkbox("💲 Show only wines under $50")
    over_500 = st.checkbox("💰 Show only wines over $500")
    
    max_price = float(df["bottle_price"].max()) + 10  # add buffer for slider headroom
    price_min, price_max = st.slider("Price Range",0.0,max_price,(0.0, max_price))
    
    varietals = st.multiselect("Varietal", sorted(df["clean_varietal"].unique()))
    producers = st.multiselect("Producer", sorted(df["producer"].unique()))
    suppliers = st.multiselect("Supplier", sorted(df["supplier"].unique()))

filtered_df = df.copy()

if wine_search:
    wine_search_clean = unidecode(wine_search.lower())
    filtered_df = filtered_df[
        filtered_df["clean_wine_name"].str.contains(wine_search_clean, na=False) |
        filtered_df["clean_producer"].str.contains(wine_search_clean, na=False)
    ]

if under_50 and not over_500:
    filtered_df = filtered_df[filtered_df["bottle_price"] <= 50]
elif over_500 and not under_50:
    filtered_df = filtered_df[filtered_df["bottle_price"] > 500]
else:
    filtered_df = filtered_df[
        (filtered_df["bottle_price"] >= price_min) & (filtered_df["bottle_price"] <= price_max)
    ]

if varietals:
    varietals_clean = [unidecode(v.lower()) for v in varietals]
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

# Show how many wines matched
st.markdown(f"**Displaying {len(filtered_df)} of {len(df)} wines**")

# Display Grid - Responsive
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

    # Display wine card
    st.markdown(f"""
    <div class='card'>
        <div class='card-title'>{row['producer']} {row['wine_name']}</div>
        <div class='card-sub'>{row['vintage']}</div>
        <div class='card-sub'>{row['varietal']} – {row['region']}</div>
        <div class='card-sub'>Supplier: {row['supplier']}</div>
        <div class='price'>💰 ${row['bottle_price']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    # Unique shortlist button
    button_label = "✅ Shortlisted" if is_shortlisted else "➕ Shortlist"
    if st.button(button_label, key=f"shortlist_btn_{row['wine_id']}_{i}"):
        if is_shortlisted:
            st.session_state.shortlist.remove(row['wine_id'])
        else:
            st.session_state.shortlist.add(row['wine_id'])

st.markdown("</div>", unsafe_allow_html=True)

# Shortlist summary
with st.sidebar:
    if st.session_state.shortlist:
        st.markdown("### 📝 Shortlist")
        for sid in st.session_state.shortlist:
            wine = df[df['wine_id'] == sid].iloc[0]
            st.write(f"{wine['producer']} {wine['wine_name']} ({wine['vintage']}) – ${wine['bottle_price']:.2f}")
        st.button("Clear Shortlist", on_click=lambda: st.session_state.shortlist.clear())
