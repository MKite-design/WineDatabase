import streamlit as st
import pandas as pd
import sqlite3
import re
import math

st.set_page_config(page_title="Wine Varietal Search", layout="wide")

@st.cache_data
def load_data():
    conn = sqlite3.connect('wine_supplier_with_producer (1).db')
    query = """
        SELECT w.wine_id, w.wine_name, w.vintage, w.varietal, w.region, w.producer,
               s.name AS supplier, p.bottle_price
        FROM wines w
        JOIN wine_prices p ON w.wine_id = p.wine_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Pick lowest price entry for each wine to avoid duplicates
    idx_min = df.groupby('wine_id')['bottle_price'].idxmin()
    df = df.loc[idx_min].reset_index(drop=True)
    # Clean and prepare columns
    df['vintage'] = df['vintage'].fillna('NV')
    df['vintage'] = df['vintage'].replace({'300cl - NV': 'NV', '9': '2009'})
    # Derive broad wine type (Red, White, Rosé, Sparkling, Fortified) from varietal and name
    def derive_type(varietal, name):
        v = varietal.lower() if pd.notna(varietal) else ""
        n = name.lower()
        if 'sparkling' in v or 'sparkling' in n or 'champagne' in n:
            return 'Sparkling'
        fort_keys = ['fortified', 'port', 'sherry', 'tokay', 'tawny']
        if any(key in v for key in fort_keys) or any(key in n for key in fort_keys):
            return 'Fortified'
        sweet_keys = ['late harvest', 'ice wine', 'icewine', 'trockenbeerenauslese',
                      'beerenauslese', 'auslese', 'noble', 'dessert']
        if any(key in v for key in sweet_keys) or any(key in n for key in sweet_keys):
            # If it's a sweet wine (not fortified), classify as Red or White based on grape context
            red_indicators = ['shiraz', 'cabernet', 'merlot', 'pinot noir', 'grenache',
                               'malbec', 'sangiovese', 'nebbiolo', 'tempranillo',
                               'montepulciano', 'zinfandel', 'barbera']
            if any(grape in v for grape in red_indicators) or any(grape in n for grape in red_indicators):
                return 'Red'
            else:
                return 'White'
        if 'rosé' in v or 'rosé' in n or 'rose' in v or 'rose' in n:
            return 'Rosé'
        red_grapes = ['shiraz', 'cabernet', 'merlot', 'pinot noir', 'nebbiolo', 'grenache',
                      'malbec', 'tempranillo', 'sangiovese', 'zinfandel', 'barbera',
                      'gamay', 'touriga', 'petit verdot', 'mourvèdre', 'mataro', 'carignan']
        white_grapes = ['chardonnay', 'sauvignon', 'riesling', 'semillon', 'chenin', 'viognier',
                        'pinot gris', 'pinot grigio', 'muscat', 'gewurz', 'grüner', 'gruner',
                        'albarino', 'verdelho', 'marsanne', 'roussanne']
        if any(grape in v for grape in red_grapes):
            return 'Red'
        if any(grape in v for grape in white_grapes):
            return 'White'
        return 'Red'
    df['type'] = df.apply(lambda row: derive_type(str(row['varietal']), str(row['wine_name'])), axis=1)
    # Create tag flags from wine_name text
    df['tag_vegan'] = df['wine_name'].str.contains('vegan', case=False, na=False)
    df['tag_organic'] = df['wine_name'].str.contains('organic', case=False, na=False)
    df['tag_biodynamic'] = df['wine_name'].str.contains('biodynamic', case=False, na=False)
    df['tag_preservative_free'] = df['wine_name'].str.contains('preservative', case=False, na=False)
    df['tag_sustainable'] = df['wine_name'].str.contains('sustainable', case=False, na=False)
    # Classify style (body/sweetness categories) for still wines
    def classify_style(row):
        t = row['type']
        v = str(row['varietal']).lower()
        n = str(row['wine_name']).lower()
        sweet_keys = ['late harvest', 'ice wine', 'icewine', 'trockenbeerenauslese',
                      'beerenauslese', 'auslese', 'noble', 'dessert']
        if t == 'Fortified' or any(key in v for key in sweet_keys) or any(key in n for key in sweet_keys):
            return 'Desserts & Fortifieds'
        if t == 'Red':
            light_red = ['pinot noir', 'gamay', 'cinsault', 'zweigelt', 'grenache']
            if any(grape in v for grape in light_red):
                return 'Red (Light/Medium Bodied)'
            else:
                return 'Red (Full Bodied)'
        if t == 'White':
            full_white = ['chardonnay', 'viognier', 'marsanne', 'roussanne', 'semillon', 'gewurz']
            if any(grape in v for grape in full_white):
                return 'White (Full Bodied)'
            else:
                return 'White (Light/Medium Bodied)'
        if t == 'Rosé':
            return 'Rosé'
        return None
    df['style'] = df.apply(classify_style, axis=1)
    # Derive country from region string
    known_countries = ["Australia", "France", "Italy", "Spain", "Portugal", "Germany",
                       "Austria", "Greece", "Argentina", "Chile", "New Zealand",
                       "USA", "United States", "South Africa", "Lebanon", "Hungary",
                       "England", "Scotland"]
    aus_states = ["NSW", "VIC", "WA", "SA", "QLD", "TAS", "ACT", "NT",
                  "Western Australia", "South Australia", "New South Wales",
                  "Queensland", "Victoria", "Tasmania"]
    us_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
                 "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
                 "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
                 "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WI",
                 "WV", "WY", "Oregon", "Washington", "California"]
    def get_country(region):
        if pd.isna(region):
            return "Other"
        r = region.strip()
        # Check for an explicit country name
        for country in known_countries:
            if country in r:
                return "USA" if country in ["USA", "United States"] else country
        # Check trailing part of region (after last comma)
        parts = [p.strip() for p in r.split(",")]
        if parts[-1] in ["USA", "United States"]:
            return "USA"
        if parts[-1] in known_countries:
            return parts[-1]
        if parts[-1] in aus_states or parts[-1] == "AUS":
            return "Australia"
        if parts[-1] in us_states:
            return "USA"
        if parts[-1] == "NZ":
            return "New Zealand"
        # Country code abbreviations
        code_map = {"FR": "France", "IT": "Italy", "ES": "Spain", "DE": "Germany",
                    "AT": "Austria", "GR": "Greece", "PT": "Portugal",
                    "CL": "Chile", "CHL": "Chile", "HU": "Hungary"}
        if parts[-1] in code_map:
            return code_map[parts[-1]]
        # If second last part is a country
        if len(parts) > 1 and parts[-2] in known_countries:
            return "USA" if parts[-2] in ["USA", "United States"] else parts[-2]
        # Region keywords for specific countries
        fr_regions = ["Burgundy", "Champagne", "Bordeaux", "Bourgogne", "Provence", "Loire", "Rhône", "Rhone", "Alsace"]
        if any(fr in r for fr in fr_regions):
            return "France"
        it_regions = ["Tuscany", "Piedmont", "Veneto", "Sicily", "Liguria", "Lombardy", "Trentino"]
        if any(it in r for it in it_regions):
            return "Italy"
        es_regions = ["Rioja", "Andalucia", "Catalonia", "Galicia", "Jerez"]
        if any(es in r for es in es_regions):
            return "Spain"
        pt_regions = ["Douro", "Alentejo", "Vinho Verde"]
        if any(pt in r for pt in pt_regions):
            return "Portugal"
        de_regions = ["Mosel", "Rheingau", "Pfalz", "Franken"]
        if any(de in r for de in de_regions):
            return "Germany"
        nz_regions = ["Marlborough", "Central Otago", "Hawke", "Martinborough", "Wairarapa"]
        if any(nz in r for nz in nz_regions):
            return "New Zealand"
        us_regions = ["California", "Napa", "Sonoma", "Oregon", "Washington", "Columbia Valley", "Russian River"]
        if any(us in r for us in us_regions):
            return "USA"
        if "South Africa" in r:
            return "South Africa"
        if "Hungary" in r or "Tokaj" in r:
            return "Hungary"
        return "Other"
    df['country'] = df['region'].apply(get_country)
    # Extract bottle size in ml from wine_name (assume 750ml if not specified)
    def extract_ml(name):
        match = re.search(r'(\d+)\s?[mM][lL]', str(name))
        return int(match.group(1)) if match else 750
    df['bottle_size'] = df['wine_name'].apply(extract_ml)
    # Compute a numeric sort key for vintage (for sorting by vintage year)
    def get_sort_year(vint):
        if pd.isna(vint):
            return 9999
        s = str(vint).upper()
        if "NV" in s or "MV" in s:
            return 9999
        nums = re.findall(r'\d+', s)
        years = []
        for num in nums:
            if len(num) == 2:
                year = int(num)
                year += 2000 if year <= 24 else 1900
                years.append(year)
            elif len(num) == 4:
                years.append(int(num))
        return min(years) if years else 9999
    df['sort_year'] = df['vintage'].apply(get_sort_year)
    return df

# Load data (cached to improve performance)
df = load_data()

# Define filter options
type_options = ["Red", "White", "Rosé", "Sparkling", "Fortified"]
tags_options = ["Vegan", "Organic", "Biodynamic", "Preservative Free", "Sustainable"]
style_options = ["Red (Full Bodied)", "Red (Light/Medium Bodied)",
                 "White (Full Bodied)", "White (Light/Medium Bodied)",
                 "Rosé", "Desserts & Fortifieds"]
country_options = sorted([c for c in df['country'].unique() if c and c != "Other"])
varietal_options = sorted(df['varietal'].dropna().unique().tolist())
brand_options = sorted(df['producer'].dropna().unique().tolist())
region_options = sorted(df['region'].dropna().unique().tolist())
# Compile distinct vintage filter options (individual years, NV, MV)
vintage_set = set()
for vint in df['vintage'].dropna().astype(str):
    s = vint.upper()
    if "NV" in s:
        vintage_set.add("NV")
    if "MV" in s:
        vintage_set.add("MV")
    nums = re.findall(r'\d+', s)
    for num in nums:
        if len(num) == 2:
            year = int(num)
            year = year + 2000 if year <= 24 else year + 1900
            vintage_set.add(str(year))
        elif len(num) == 4:
            vintage_set.add(num)
vintage_years = sorted([int(y) for y in vintage_set if y.isdigit()])
vintage_options = [str(y) for y in vintage_years]
if "NV" in vintage_set:
    vintage_options.append("NV")
if "MV" in vintage_set:
    vintage_options.append("MV")

# Sidebar Filters
st.sidebar.markdown("**Price Range (AU$)**")
min_price = math.floor(df['bottle_price'].min())
max_price = math.ceil(df['bottle_price'].max())
price_slider = st.sidebar.slider("", min_value=min_price, max_value=max_price, value=(min_price, max_price))

# Filter category expanders
type_selected = []
with st.sidebar.expander("Type", expanded=True):
    for t in type_options:
        if st.checkbox(t, key=f"type_{t}"):
            type_selected.append(t)
tag_selected = []
with st.sidebar.expander("Tags", expanded=True):
    for tag in tags_options:
        if st.checkbox(tag, key=f"tag_{tag}"):
            tag_selected.append(tag)
varietal_selected = st.sidebar.multiselect("Varietal", varietal_options)
brand_selected = st.sidebar.multiselect("Brand/Producer", brand_options)
with st.sidebar.expander("Style", expanded=True):
    style_selected = [s for s in style_options if st.checkbox(s, key=f"style_{s}")]
with st.sidebar.expander("Country", expanded=True):
    country_selected = [c for c in country_options if st.checkbox(c, key=f"country_{c}")]
region_selected = st.sidebar.multiselect("Region", region_options)
with st.sidebar.expander("Vintage", expanded=False):
    vintage_selected = [v for v in vintage_options if st.checkbox(v, key=f"vintage_{v}")]
with st.sidebar.expander("Bottle Size", expanded=True):
    size_selected = [size for size in sorted(df['bottle_size'].unique()) if st.checkbox(f"{size} ml", key=f"size_{size}")]

# Apply filters to dataframe
filtered = df.copy()
low_price, high_price = price_slider
filtered = filtered[(filtered['bottle_price'] >= low_price) & (filtered['bottle_price'] <= high_price)]
if type_selected:
    filtered = filtered[filtered['type'].isin(type_selected)]
if tag_selected:
    mask = pd.Series(False, index=filtered.index)
    if "Vegan" in tag_selected:
        mask |= filtered['tag_vegan']
    if "Organic" in tag_selected:
        mask |= filtered['tag_organic']
    if "Biodynamic" in tag_selected:
        mask |= filtered['tag_biodynamic']
    if "Preservative Free" in tag_selected:
        mask |= filtered['tag_preservative_free']
    if "Sustainable" in tag_selected:
        mask |= filtered['tag_sustainable']
    filtered = filtered[mask]
if varietal_selected:
    filtered = filtered[filtered['varietal'].isin(varietal_selected)]
if brand_selected:
    filtered = filtered[filtered['producer'].isin(brand_selected)]
if style_selected:
    filtered = filtered[filtered['style'].isin(style_selected)]
if country_selected:
    filtered = filtered[filtered['country'].isin(country_selected)]
if region_selected:
    filtered = filtered[filtered['region'].isin(region_selected)]
if vintage_selected:
    mask_v = pd.Series(False, index=filtered.index)
    for vint in vintage_selected:
        mask_v |= filtered['vintage'].astype(str).str.contains(vint, case=False, na=False)
    filtered = filtered[mask_v]
if size_selected:
    filtered = filtered[filtered['bottle_size'].isin(size_selected)]

# Sorting
sort_options = ["Name: A to Z", "Price: Low to High", "Vintage"]
sort_choice = st.selectbox("Sort By", sort_options, index=0)
if sort_choice == "Name: A to Z":
    filtered = filtered.sort_values(by=['producer', 'wine_name'])
elif sort_choice == "Price: Low to High":
    filtered = filtered.sort_values(by='bottle_price')
elif sort_choice == "Vintage":
    filtered = filtered.sort_values(by='sort_year')

# Display results header
total_count = len(filtered)
total_all = len(df)
col1, col2 = st.columns([1, 1])
col1.write(f"**Showing {total_count} of {total_all} products**")
col2.write("")  # spacer
col2.selectbox("Sort", sort_options, index=sort_options.index(sort_choice), key="sort_display", disabled=True)

# Display products in a responsive grid
cols = st.columns(4)
for idx, row in filtered.reset_index(drop=True).iterrows():
    col = cols[idx % 4]
    producer = row['producer'] if pd.notna(row['producer']) else ""
    wine_name = row['wine_name']
    vintage = row['vintage']
    varietal = row['varietal'] if pd.notna(row['varietal']) else ""
    region = row['region'] if pd.notna(row['region']) else ""
    supplier = row['supplier'] if pd.notna(row['supplier']) else ""
    price = row['bottle_price']
    # Format card content
    card_md = f"**{producer}**  \n"
    card_md += f"{wine_name} ({vintage})  \n"
    card_md += f"*{varietal} – {region}*  \n"
    card_md += f"Supplier: {supplier}  \n"
    card_md += f"Price: ${price:,.2f}"
    col.markdown(f"<div style='border:1px solid #ddd; padding:10px; border-radius:5px; margin:5px 0;'>{card_md}</div>",
                 unsafe_allow_html=True)
