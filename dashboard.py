import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------------------------
# 1. Config & Setup
# ------------------------------------------------------------------------------
st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

st.title("📊 E-Commerce Sales Dashboard")
st.markdown("### Interactive Dashboard for Online Retail Analysis")
st.markdown("---")

# ------------------------------------------------------------------------------
# 2. Load & Clean Data (Updated)
# ------------------------------------------------------------------------------
@st.cache_data
def load_data():
    # Load Data
    try:
        df = pd.read_csv('online_retail_II.csv', encoding='unicode_escape')
    except FileNotFoundError:
        st.error("ไม่พบไฟล์ online_retail_II.csv กรุณาเช็คว่าไฟล์อยู่ในโฟลเดอร์เดียวกับ dashboard.py ครับ")
        return pd.DataFrame(), pd.DataFrame() # Return empty if fail
    
    # Cleaning Logic
    df_clean = df.dropna(subset=['Customer ID']).copy()
    df_clean['Customer ID'] = df_clean['Customer ID'].astype(float).astype(int).astype(str)
    df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
    df_clean['TotalAmount'] = df_clean['Quantity'] * df_clean['Price']
    
    # Helper Columns
    df_clean['MonthYear'] = df_clean['InvoiceDate'].dt.strftime('%Y-%m')
    df_clean['Hour'] = df_clean['InvoiceDate'].dt.hour
    df_clean['DayOfWeek'] = df_clean['InvoiceDate'].dt.day_name()
    
    # Split Sales vs Returns
    df_sales = df_clean[df_clean['Quantity'] > 0].copy()
    df_returns = df_clean[df_clean['Quantity'] < 0].copy()
    df_returns['Quantity'] = df_returns['Quantity'].abs() # Make positive
    
    return df_sales, df_returns

# Load data
with st.spinner('Loading Data...'):
    df_sales, df_returns = load_data()

# Check if data loaded correctly
if df_sales.empty:
    st.stop()

# ------------------------------------------------------------------------------
# 3. Sidebar (Filters)
# ------------------------------------------------------------------------------
st.sidebar.header("Filter Options")

# Filter by Country
all_countries = sorted(df_sales['Country'].unique())
# Default to United Kingdom (Since it's the main market)
selected_countries = st.sidebar.multiselect("Select Country", all_countries, default=['United Kingdom'])

# Apply Filter
if selected_countries:
    df_filtered = df_sales[df_sales['Country'].isin(selected_countries)]
    df_returns_filtered = df_returns[df_returns['Country'].isin(selected_countries)]
else:
    df_filtered = df_sales
    df_returns_filtered = df_returns
    
# Dataset download button    
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Download Data")

# 1. Filter data -> CSV
csv_data = df_filtered.to_csv(index=False).encode('utf-8')

# 2. Download button
st.sidebar.download_button(
    label="📥 Download Dataset(CSV)",
    data=csv_data,
    file_name='filtered_sales_data.csv',
    mime='text/csv',
    help="Click to download the data currently shown on dashboard"
)

# ------------------------------------------------------------------------------
# 4. KPI Metrics
# ------------------------------------------------------------------------------
total_revenue = df_filtered['TotalAmount'].sum()
total_orders = df_filtered['Invoice'].nunique()
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"£{total_revenue:,.2f}")
col2.metric("Total Orders", f"{total_orders:,}")
col3.metric("Avg Order Value", f"£{avg_order_value:,.2f}")

st.markdown("---")

# ------------------------------------------------------------------------------
# 5. Charts Area (All 10 Questions)
# ------------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📈 Phase 1: Overview", "🔍 Phase 2: Behavior", "💎 Phase 3: Strategy"])

# --- TAB 1: Overview (Q1-Q3) ---
with tab1:
    st.header("Business Overview")
    
    # Q1: Monthly Trend
    monthly_sales = df_filtered.groupby('MonthYear')['TotalAmount'].sum().reset_index()
    fig1 = px.line(monthly_sales, x='MonthYear', y='TotalAmount', markers=True, 
                   title='Q1: Monthly Revenue Trend')
    st.plotly_chart(fig1, use_container_width=True)
    
    col_q2, col_q3 = st.columns(2)
    
    with col_q2:
        # Q2: Top Products
        top_products = df_filtered.groupby('Description')['TotalAmount'].sum().reset_index().sort_values('TotalAmount', ascending=False).head(10)
        fig2 = px.bar(top_products, x='TotalAmount', y='Description', orientation='h', 
                      title='Q2: Top 10 Best Sellers')
        fig2.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)
        
    with col_q3:
        # Q3: Map (3D Globe Style)
        country_sales = df_sales.groupby('Country')['TotalAmount'].sum().reset_index()
        fig3 = px.choropleth(country_sales, locations='Country', locationmode='country names',
                             color='TotalAmount', title='Q3: Global Sales (3D)',
                             projection='orthographic', color_continuous_scale='Plasma')
        st.plotly_chart(fig3, use_container_width=True)

# --- TAB 2: Behavior (Q4-Q6) ---
with tab2:
    st.header("Customer Behavior & Returns")
    
    col_q4, col_q5 = st.columns(2)
    
    with col_q4:
        # Q4: Hourly Sales (Custom Colors)
        hourly_sales = df_filtered.groupby('Hour')['TotalAmount'].sum().reset_index()
        fig4 = px.bar(hourly_sales, x='Hour', y='TotalAmount', title='Q4: Sales by Hour',
                      # สีที่คุณเลือกไว้: ทอง -> ส้ม -> แดง
                      color='TotalAmount', color_continuous_scale=['#FFD700', '#FF8C00', '#8B0000'])
        st.plotly_chart(fig4, use_container_width=True)
        
    with col_q5:
        # Q5: Top Returns
        top_returns = df_returns_filtered.groupby('Description')['Quantity'].sum().reset_index().sort_values('Quantity', ascending=False).head(10)
        fig5 = px.bar(top_returns, x='Quantity', y='Description', orientation='h', 
                      title='Q5: Top 10 Returned Items', color_discrete_sequence=['#FF4B4B'])
        fig5.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig5, use_container_width=True)
        
    # Q6: AOV by Country
    st.subheader("Q6: Average Order Value (AOV)")
    country_stats = df_filtered.groupby('Country').agg({'TotalAmount': 'sum', 'Invoice': 'nunique'}).reset_index()
    country_stats['AOV'] = country_stats['TotalAmount'] / country_stats['Invoice']
    top_aov = country_stats.sort_values(by='AOV', ascending=False).head(10)
    
    fig6 = px.bar(top_aov, x='Country', y='AOV', title='Average Spend per Order by Country',
                  text_auto='.2f', color='AOV', color_continuous_scale='Blues')
    st.plotly_chart(fig6, use_container_width=True)

# --- TAB 3: Strategy (Q7-Q10) ---
with tab3:
    st.header("Strategic Analysis (RFM & Pareto)")
    
    # Q7: RFM Segmentation
    snapshot_date = df_filtered['InvoiceDate'].max() + pd.Timedelta(days=1)
    rfm = df_filtered.groupby('Customer ID').agg({
        'InvoiceDate': lambda x: (snapshot_date - x.max()).days,
        'Invoice': 'nunique',
        'TotalAmount': 'sum'
    }).reset_index()
    rfm.columns = ['Customer ID', 'Recency', 'Frequency', 'Monetary']
    
    # RFM Plot
    rfm['Segment'] = pd.qcut(rfm['Monetary'], q=4, labels=['Low', 'Mid', 'High', 'VIP'], duplicates='drop')
    fig7 = px.scatter(rfm, x='Recency', y='Monetary', color='Segment', size='Frequency',
                      log_y=True, title='Q7: Customer Segmentation (RFM)',
                      hover_data=['Customer ID'], color_discrete_sequence=px.colors.qualitative.Safe)
    st.plotly_chart(fig7, use_container_width=True)
    
    col_q8, col_q9 = st.columns(2)
    
    with col_q8:
        # Q8: Retention
        monthly_active = df_filtered.groupby('MonthYear')['Customer ID'].nunique().reset_index()
        fig8 = px.line(monthly_active, x='MonthYear', y='Customer ID', markers=True,
                       title='Q8: Monthly Active Customers')
        fig8.update_traces(line_color='green')
        st.plotly_chart(fig8, use_container_width=True)
        
    with col_q9:
        # Q10: Best Working Day
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Sunday']
        weekday_sales = df_filtered.groupby('DayOfWeek')['TotalAmount'].mean().reindex(days_order).reset_index()
        fig10 = px.bar(weekday_sales, x='DayOfWeek', y='TotalAmount', title='Q10: Best Working Day',
                       color='TotalAmount', color_continuous_scale='Teal')
        st.plotly_chart(fig10, use_container_width=True)

    # Q9: Pareto Principle
    st.subheader("Q9: Pareto Principle (80/20 Rule)")
    rfm_sorted = rfm.sort_values(by='Monetary', ascending=False)
    rfm_sorted['Cumulative_Revenue'] = rfm_sorted['Monetary'].cumsum()
    rfm_sorted['Revenue_Pct'] = 100 * rfm_sorted['Cumulative_Revenue'] / rfm_sorted['Monetary'].sum()
    rfm_sorted['Customer_Rank_Pct'] = 100 * (pd.Series(range(len(rfm_sorted))) + 1) / len(rfm_sorted)
    
    fig9 = px.line(rfm_sorted, x='Customer_Rank_Pct', y='Revenue_Pct', title='Pareto Analysis',
                   labels={'Customer_Rank_Pct': '% Customers', 'Revenue_Pct': '% Revenue'})
    fig9.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80% Revenue")
    fig9.add_vline(x=20, line_dash="dash", line_color="red", annotation_text="20% Customers")
    st.plotly_chart(fig9, use_container_width=True)