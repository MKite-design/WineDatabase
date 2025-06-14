
import streamlit as st
import pandas as pd

# Load data
df = pd.read_excel("Wine_Master_Table_Scaffold.xlsx")

# Sidebar filters
st.sidebar.title("🔍 Refine Search")
wine_name = st.sidebar.text_input("Wine Name")
varietals = ["All"] + sorted(df["Varietal"].dropna().unique().tolist())
regions = ["All"] + sorted(df["Wine Region"].dropna().unique().tolist())
vintages = ["All"] + sorted(df["Vintage"].dropna().astype(str).unique().tolist())
producers = ["All"] + sorted(df["Producer"].dropna().unique().tolist())
suppliers = ["All"] + sorted(df["Supplier"].dropna().unique().tolist())

selected_varietal = st.sidebar.selectbox("Varietal", varietals)
selected_region = st.sidebar.selectbox("Region", regions)
selected_vintage = st.sidebar.selectbox("Vintage", vintages)
selected_producer = st.sidebar.text_input("Producer")
selected_supplier = st.sidebar.selectbox("Supplier", suppliers)

min_price = st.sidebar.number_input("Min Price", value=0.0, step=1.0)
max_price = st.sidebar.number_input("Max Price", value=20000.0, step=1.0)

if st.sidebar.button("Clear Filters"):
    st.experimental_rerun()

# Apply filters
filtered_df = df[
    (df["Wine Name"].str.contains(wine_name, case=False, na=False)) &
    ((df["Varietal"] == selected_varietal) | (selected_varietal == "All")) &
    ((df["Wine Region"] == selected_region) | (selected_region == "All")) &
    ((df["Vintage"].astype(str) == selected_vintage) | (selected_vintage == "All")) &
    (df["Producer"].str.contains(selected_producer, case=False, na=False)) &
    ((df["Supplier"] == selected_supplier) | (selected_supplier == "All")) &
    (df["Bottle Price"] >= min_price) & (df["Bottle Price"] <= max_price)
]

# Sort dropdown
sort_option = st.selectbox("Sort by", ["Name: A to Z", "Name: Z to A", "Price: Low to High", "Price: High to Low"])

if sort_option == "Name: A to Z":
    filtered_df = filtered_df.sort_values("Wine Name", ascending=True)
elif sort_option == "Name: Z to A":
    filtered_df = filtered_df.sort_values("Wine Name", ascending=False)
elif sort_option == "Price: Low to High":
    filtered_df = filtered_df.sort_values("Bottle Price", ascending=True)
elif sort_option == "Price: High to Low":
    filtered_df = filtered_df.sort_values("Bottle Price", ascending=False)

st.markdown(f"### {len(filtered_df)} wines found")

# Responsive card layout
cols = st.columns(3)
for idx, (_, row) in enumerate(filtered_df.iterrows()):
    col = cols[idx % 3]
    with col:
        st.markdown(f"**{row['Producer']}**")
        st.markdown(f"{row['Wine Name']} ({row['Vintage']})")
        st.markdown(f"*{row['Varietal']} – {row['Wine Region']}*")
        st.markdown(f"Supplier: {row['Supplier']}")
        st.markdown(f"Price: ${row['Bottle Price']:.2f}")
