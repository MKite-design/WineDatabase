import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide")
st.title("🍷 Wine Listings")

# Load data from SQLite
@st.cache_data

def load_data():
    conn = sqlite3.connect("wine_supplier_clean.db")
    df = pd.read_sql_query("SELECT * FROM wines", conn)
    conn.close()

    df.fillna({
        "wine_name": "",
        "vintage": "NV",
        "varietal": "Unknown",
        "region": "Unknown",
        "producer": "Unknown",
        "wine_type": "Unknown"
    }, inplace=True)

    df["sort_name"] = df["producer"].str.lower() + " " + df["wine_name"].str.lower()
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
        sort_option = st.selectbox("Sort By", ["Producer A-Z", "Producer Z-A"])
    with cols[2]:
        type_tags = st.multiselect("Wine Type", sorted(df["wine_type"].unique()))

# --- SIDEBAR ADVANCED FILTERS ---
with st.sidebar:
    st.header("⚙️ Advanced Filters")
    varietals = st.multiselect("Varietal", sorted(df["varietal"].unique()))
    producers = st.multiselect("Producer", sorted(df["producer"].unique()))
    regions = st.multiselect("Region", sorted(df["region"].unique()))

# Filter logic
filtered_df = df.copy()

if wine_search:
    wine_search_clean = wine_search.lower()
    filtered_df = filtered_df[
        filtered_df["wine_name"].str.lower().str.contains(wine_search_clean) |
        filtered_df["producer"].str.lower().str.contains(wine_search_clean)
    ]

if varietals:
    filtered_df = filtered_df[filtered_df["varietal"].isin(varietals)]
if producers:
    filtered_df = filtered_df[filtered_df["producer"].isin(producers)]
if regions:
    filtered_df = filtered_df[filtered_df["region"].isin(regions)]
if type_tags:
    filtered_df = filtered_df[filtered_df["wine_type"].isin(type_tags)]

if sort_option == "Producer A-Z":
    filtered_df = filtered_df.sort_values("sort_name")
elif sort_option == "Producer Z-A":
    filtered_df = filtered_df.sort_values("sort_name", ascending=False)

# --- DISPLAY ---
st.markdown(f"### Displaying {len(filtered_df)} of {len(df)} wines")

st.markdown("""<style>
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
  .card-title { font-size: 1rem; }
  .card-sub { font-size: 0.85rem; }
  .price { font-size: 0.95rem; }
}
</style>""", unsafe_allow_html=True)

st.markdown("<div class='grid'>", unsafe_allow_html=True)

for _, row in filtered_df.iterrows():
    is_shortlisted = row['wine_id'] in st.session_state.shortlist
    html_card = f"""
    <div class='card'>
        <div class='card-title'>{row['producer']} {row['wine_name']}</div>
        <div class='card-sub'>{row['vintage']}</div>
        <div class='card-sub'>{row['varietal']} – {row['region']}</div>
        <div class='card-sub'>Type: {row['wine_type']}</div>
        <div class='shortlist-button'>
            <form action="" method="post">
                <input type="submit" name="shortlist_{row['wine_id']}" value="{'✅ Shortlisted' if is_shortlisted else '➕ Shortlist'}">
            </form>
        </div>
    </div>
    """
    st.markdown(html_card, unsafe_allow_html=True)
    if st.session_state.get(f"shortlist_{row['wine_id']}"):
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
            st.write(f"{wine['producer']} {wine['wine_name']} ({wine['vintage']})")
        st.button("Clear Shortlist", on_click=lambda: st.session_state.shortlist.clear())
