import streamlit as st
import pandas as pd
import plotly.express as px

# Set wide layout
st.set_page_config(layout="wide")

# Cache file loading for better performance
@st.cache_data
def load_data(uploaded_file):
    return pd.read_excel(uploaded_file)

# Cache computation-heavy functions
@st.cache_data
def compute_shipment_counts(df):
    return df.groupby(pd.Grouper(key='SB DATE', freq='D')).size().reset_index(name='Shipments')

@st.cache_data
def compute_port_trends(df):
    return df.groupby(['SB DATE', 'PORT OF LOADING'])['FOB'].sum().reset_index()

@st.cache_data
def compute_product_fob(df):
    return df.groupby('HSN_DESCRIPTION')['FOB'].sum().nlargest(10)

@st.cache_data
def compute_product_trends(df):
    return df.groupby(['SB DATE', 'HSN_DESCRIPTION']).size().reset_index(name='Shipments')

@st.cache_data
def compute_product_counts(df):
    return df['HSN_DESCRIPTION'].value_counts().nlargest(10)

@st.cache_data
def compute_total_products(df):
    return df['HSN_DESCRIPTION'].nunique()

# Main app function
def main():
    st.title("📊 Export Data Analysis Dashboard")
    
    # File Upload
    uploaded_file = st.file_uploader("📂 Upload an Excel File", type=["xlsx"])
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        
        # Convert SB DATE to datetime
        if 'SB DATE' in df.columns:
            df['SB DATE'] = pd.to_datetime(df['SB DATE'])
            
        # Sidebar Filters
        st.sidebar.header("🔍 Filters")
        
        # Date Range Filter
        if 'SB DATE' in df.columns:
            start_date = st.sidebar.date_input("Start Date", df['SB DATE'].min())
            end_date = st.sidebar.date_input("End Date", df['SB DATE'].max())
            df = df[(df['SB DATE'] >= pd.to_datetime(start_date)) & 
                    (df['SB DATE'] <= pd.to_datetime(end_date))]
        
        # Port of Loading Filter
        if 'PORT OF LOADING' in df.columns:
            ports = st.sidebar.multiselect("Port of Loading", options=df['PORT OF LOADING'].unique())
            if ports:
                df = df[df['PORT OF LOADING'].isin(ports)]
        
        # Country of Destination Filter
        if 'COUNTRY OF DESTINATION' in df.columns:
            countries = st.sidebar.multiselect("Destination Countries", options=df['COUNTRY OF DESTINATION'].unique())
            if countries:
                df = df[df['COUNTRY OF DESTINATION'].isin(countries)]
        
        # Port of Discharge Filter
        if 'PORT OF DISCHARGE' in df.columns:
            discharge_ports = st.sidebar.multiselect("Port of Discharge", options=df['PORT OF DISCHARGE'].unique())
            if discharge_ports:
                df = df[df['PORT OF DISCHARGE'].isin(discharge_ports)]
        
        
        # Tabs for better organization
        tab1, tab2, tab3, tab4 = st.tabs(["📜 Data", "📈 Charts", "📊 Summary", "📦 Product Analysis"])
        
        with tab1:
            st.subheader("📜 Filtered Data")
            st.dataframe(df.head(1000))  # Limiting displayed rows for performance
            
            st.download_button(label="⬇ Download Filtered Data as CSV", data=df.to_csv(index=False),
                               file_name="filtered_export_data.csv", mime="text/csv")
        
        with tab2:
            st.subheader("📈 Data Visualizations")
            
            st.subheader("📦 Shipments Count Over Time (Daily)")
            shipment_counts = compute_shipment_counts(df)
            
            fig = px.bar(shipment_counts, x='SB DATE', y='Shipments', labels={'SB DATE': 'Date', 'Shipments': 'Total Shipments'},
                         title="Daily Shipments Count")
            
            # Add trend line
            fig.add_scatter(x=shipment_counts['SB DATE'], y=shipment_counts['Shipments'], mode='lines', name='Trend Line')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # FOB Trends by Port
            if 'PORT OF LOADING' in df.columns:
                st.subheader("⚓ FOB Trends by Port")
                port_trends = compute_port_trends(df)
                fig = px.line(port_trends, x='SB DATE', y='FOB', color='PORT OF LOADING', markers=True,
                              labels={'SB DATE': 'Date', 'FOB': 'Total FOB'})
                st.plotly_chart(fig, use_container_width=True)
                
        with tab3:
            st.subheader("📊 Summary & Insights")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Shipments", df.shape[0])
                st.metric("Average FOB per Shipment", f"${df['FOB'].mean():,.2f}")
            
            with col2:
                st.metric("Total FOB Value", f"${df['FOB'].sum():,.2f}")
            
        with tab4:
            st.subheader("📦 Product Analysis (HSN_DESCRIPTION)")
            
            if 'HSN_DESCRIPTION' in df.columns:
                total_products = compute_total_products(df)
                st.metric("Total Unique Products", total_products)
                
                st.subheader("💰 Top Products by FOB Value")
                product_fob = compute_product_fob(df)
                fig = px.bar(product_fob, x=product_fob.values, y=product_fob.index, orientation='h',
                             labels={'x': 'Total FOB', 'y': 'Product'})
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📊 Products vs Quantity")
                if 'QUANTITY' in df.columns:
                    quantity_data = df.groupby('HSN_DESCRIPTION')['QUANTITY'].sum().nlargest(10).reset_index()
                    fig = px.pie(quantity_data, names='HSN_DESCRIPTION', values='QUANTITY', title="Top Products by Quantity")
                    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
