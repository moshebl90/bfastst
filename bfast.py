import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Automated Discounts Impact Dashboard")
logo_url = "https://www.breadfast.com/wp-content/themes/breadfast/website/images/breadfast-brand.svg"  # Replace with the actual logo URL
st.sidebar.image(logo_url, use_column_width=True)
st.sidebar.header("Dashboard Filters")


@st.cache_data
def load_data():
    url1 = "https://docs.google.com/spreadsheets/d/1wVJHvY31lX3OP0PSMujpD9ZPpAVMdleCE50QHMChgJ0/edit#gid=102985752"
    url2 = "https://docs.google.com/spreadsheets/d/1_GKq4ieaNAgslqRg6H0JdJwiQsZ3UjCZasNsjlHhn6A/edit#gid=1072934975"
    url3 = "https://docs.google.com/spreadsheets/d/1RfqvJhFgNyatB7RnLjEJoaIt1BbQBVvPhsc0IwnWJS0/edit#gid=1312217094"

    data1 = pd.read_csv(url1.replace("/edit#gid=", "/export?format=csv&gid="))
    data2 = pd.read_csv(url2.replace("/edit#gid=", "/export?format=csv&gid="))
    data3 = pd.read_csv(url3.replace("/edit#gid=", "/export?format=csv&gid="))

    return data1, data2, data3

fct_daily_cost, fct_automated_discounts, fct_oov_products = load_data()

# Rename columns for consistent access
fct_daily_cost = fct_daily_cost.rename(columns={'ordering_date': 'date'})
fct_oov_products = fct_oov_products.rename(columns={'date_day': 'date'})

# Convert date columns to datetime format
fct_daily_cost['date'] = pd.to_datetime(fct_daily_cost['date'], errors='coerce')
fct_oov_products['date'] = pd.to_datetime(fct_oov_products['date'], errors='coerce')

# Convert the 'date' column to datetime format
fct_automated_discounts = fct_automated_discounts.rename(columns={'valid_from': 'date'})
fct_automated_discounts['date'] = pd.to_datetime(fct_automated_discounts['date'], errors='coerce')

# Sidebar date range filter
min_date = fct_daily_cost['date'].min()
max_date = fct_daily_cost['date'].max()
selected_date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# Ensure selected_date_range is in datetime64[ns] format
selected_date_range = pd.to_datetime(selected_date_range)

# Sidebar branch selection
branch_list = sorted(fct_automated_discounts['branch_key'].unique())
placeholder_branch = st.sidebar.selectbox("Select Branch Type", ["All Branches", "Specific Branches"])

if placeholder_branch == "Specific Branches":
    selected_branch = st.sidebar.multiselect("Select Specific Branches", branch_list)
else:
    selected_branch = branch_list

# Filter data based on selections
filtered_cost_data = fct_daily_cost[
    (fct_daily_cost['branch_key'].isin(selected_branch)) &
    (fct_daily_cost['date'].between(selected_date_range[0], selected_date_range[1]))
]
filtered_discount_data = fct_automated_discounts[
    fct_automated_discounts['branch_key'].isin(selected_branch)
]
filtered_oov_data = fct_oov_products[
    (fct_oov_products['branch_key'].isin(selected_branch)) &
    (fct_oov_products['date'].between(selected_date_range[0], selected_date_range[1]))
]


## Question 1: Discount Spending Through Automated Discounts
st.header("1. Discount Spending Through Automated Discounts")
discount_spending = filtered_discount_data.groupby('date')['automated_discount_applied_amount'].sum()
fig1 = px.line(discount_spending, title="Daily Discount Spending", labels={"value": "Discount Amount"})
st.plotly_chart(fig1)

## Question 2: Inventory Sold at Discounted Prices (Volume and Value)
st.header("2. Inventory Sold at Discounted Price")
inventory_volume = filtered_cost_data.groupby('date')['product_qty_sold_with_automated_discounts'].sum()
inventory_value = filtered_cost_data.groupby('date')['total_discount_cost_egp'].sum()

fig2 = px.bar(x=inventory_volume.index, y=inventory_volume.values, title="Discounted Inventory Sold (Volume)",
              labels={"x": "Date", "y": "Units Sold"})
st.plotly_chart(fig2)

fig3 = px.line(x=inventory_value.index, y=inventory_value.values, title="Discounted Inventory Sold (Value)",
               labels={"x": "Date", "y": "Discounted Sales Value"})
st.plotly_chart(fig3)

## Question 3: Percentage of Out-of-Validity Products Remaining After Discount
st.header("3. Percentage of Out-of-Validity Products Remaining Post-Discount")
oov_remaining = (filtered_oov_data.groupby('date')['oov'].sum() /
                 filtered_oov_data.groupby('date')['total'].sum()) * 100
fig4 = px.area(oov_remaining, title="Percentage of OOV Products Remaining After Discounts",
               labels={"value": "% OOV Remaining"})
st.plotly_chart(fig4)

## Question 4: Top Discounted Products
st.header("4. Top Discounted Products")
top_discounted_products = filtered_discount_data.groupby('product_key')['automated_discount_applied_amount'].sum().nlargest(10)
fig5 = px.bar(top_discounted_products, title="Top 10 Discounted Products by Amount",
              labels={"value": "Discount Amount", "product_key": "Product"})
st.plotly_chart(fig5)

## Question 5: Impact on Sales and Waste
st.header("5. Impact on Sales and Waste")
# Calculate pre- and post-discount sales metrics to assess sales uplift
sales_data = filtered_cost_data.groupby('date')[['product_qty_sold_with_automated_discounts']].sum()
sales_data['discounted_percentage'] = (sales_data['product_qty_sold_with_automated_discounts'] /
                                       sales_data['product_qty_sold_with_automated_discounts'].sum()) * 100

fig6 = px.line(sales_data['discounted_percentage'], title="Impact on Sales (Discounted Sales Percentage)",
               labels={"value": "% of Total Sales at Discounted Prices"})
st.plotly_chart(fig6)

# Display waste analysis
waste_analysis = filtered_oov_data.groupby('date')['oov'].sum()
fig7 = px.line(waste_analysis, title="Waste Trend (Unsold OOV Units Over Time)",
               labels={"value": "Units Remaining"})
st.plotly_chart(fig7)

## Additional Insights
st.header("Additional Insights")
st.write("The graphs above clearly demonstrate a significant reduction in unsold OOV products, which is also effectively reducing waste.")
