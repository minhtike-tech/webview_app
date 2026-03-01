import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Myanmar Market Sales Pro", page_icon="🇲🇲", layout="wide")

# --- AUTO CLEANUP OLD CACHED DATA ---
if 'sales_history' in st.session_state:
    df = st.session_state['sales_history']
    if 'Total Value (USD)' in df.columns:
        df.rename(columns={'Total Value (USD)': 'Total Value (MMK)'}, inplace=True)
    if 'Price (USD)' in df.columns:
        df.rename(columns={'Price (USD)': 'Unit Price (MMK)'}, inplace=True)
    if 'Sale Count' in df.columns:
        df.drop(columns=['Sale Count'], inplace=True)
    st.session_state['sales_history'] = df

if 'inventory' in st.session_state:
    df_inv = st.session_state['inventory']
    if 'Price (USD)' in df_inv.columns:
        df_inv.rename(columns={'Price (USD)': 'Price (MMK)'}, inplace=True)
    if 'Category' in df_inv.columns:
        df_inv.drop(columns=['Category'], inplace=True)
    st.session_state['inventory'] = df_inv

# --- MOCK DATABASE INITIALIZATION ---
if 'inventory' not in st.session_state:
    st.session_state['inventory'] = pd.DataFrame({
        'Product ID': ['P001', 'P002', 'P003'],
        'Product Name': ['ကော်ဖီထုပ်', 'Data Analytics Software', 'Enterprise Security Suite'],
        'Price (MMK)': [5000.0, 150000.0, 450000.0],
        'Stock': [1000, 50, 30]
    })

if 'sales_history' not in st.session_state:
    st.session_state['sales_history'] = pd.DataFrame(columns=[
        'Transaction ID', 'Date', 'Product Name', 'Unit Price (MMK)', 'Quantity', 'Sale Type', 'Total Value (MMK)'
    ])

# --- HELPER FUNCTIONS ---
def record_sale(product_name, qty, sale_type):
    price = st.session_state['inventory'].loc[
        st.session_state['inventory']['Product Name'] == product_name, 'Price (MMK)'
    ].values[0]
    
    total_value = 0.0 if sale_type == "Free (Promotional)" else price * qty
    
    new_sale = pd.DataFrame([{
        'Transaction ID': f"TRX-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        'Date': datetime.datetime.now().date(),
        'Product Name': product_name,
        'Unit Price (MMK)': price,
        'Quantity': qty,
        'Sale Type': sale_type,
        'Total Value (MMK)': total_value
    }])
    
    if st.session_state['sales_history'].empty:
        st.session_state['sales_history'] = new_sale
    else:
        st.session_state['sales_history'] = pd.concat([st.session_state['sales_history'], new_sale], ignore_index=True)
    
    st.session_state['inventory'].loc[
        st.session_state['inventory']['Product Name'] == product_name, 'Stock'
    ] -= qty

# --- APP NAVIGATION ---
st.sidebar.title("🇲🇲 Local Market Pro")
st.sidebar.markdown("---")
menu = ["🏠 Home / Dashboard", "🛒 Process Sales", "📦 Inventory Management", "📊 Market Analysis", "📜 Sales History"]
choice = st.sidebar.radio("Navigation", menu)

# --- 1. HOME / DASHBOARD ---
if choice == "🏠 Home / Dashboard":
    st.title("Business Dashboard Overview")
    
    df_sales = st.session_state['sales_history']
    today = datetime.datetime.now().date()
    
    total_sales_all_time = df_sales['Total Value (MMK)'].sum() if not df_sales.empty else 0.0
    daily_sales = df_sales[df_sales['Date'] == today]['Total Value (MMK)'].sum() if not df_sales.empty else 0.0
    total_items_sold = df_sales['Quantity'].sum() if not df_sales.empty else 0
    free_items_given = df_sales[df_sales['Sale Type'] == 'Free (Promotional)']['Quantity'].sum() if not df_sales.empty else 0
    
    free_sales_df = df_sales[df_sales['Sale Type'] == 'Free (Promotional)'] if not df_sales.empty else pd.DataFrame()
    promo_revenue = (free_sales_df['Unit Price (MMK)'] * free_sales_df['Quantity']).sum() if not free_sales_df.empty else 0.0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Revenue", f"{total_sales_all_time:,.0f} Ks")
    col2.metric("Today's Revenue", f"{daily_sales:,.0f} Ks")
    col3.metric("Promo/Free Revenue", f"{promo_revenue:,.0f} Ks")
    col4.metric("Total Units Sold", f"{total_items_sold}")
    col5.metric("Promo/Free Units", f"{free_items_given}")
    
    st.markdown("---")
    st.subheader("Current Inventory Snapshot")
    st.dataframe(st.session_state['inventory'], use_container_width=True, hide_index=True)

# --- 2. PROCESS SALES ---
elif choice == "🛒 Process Sales":
    st.title("Point of Sale")
    st.markdown("အရောင်းမှတ်တမ်း (သို့မဟုတ်) အခမဲ့ Promotion ပေးမှုများကို မှတ်သားပါ။")
    
    with st.form("sales_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        product_list = st.session_state['inventory']['Product Name'].tolist()
        
        with col1:
            if not product_list:
                st.warning("Product မရှိသေးပါ။ အရင်ဆုံး ထည့်သွင်းပေးပါ။")
                sel_product = None
            else:
                sel_product = st.selectbox("Select Product", product_list)
            sale_type = st.radio("Sale Type", ["Standard Sale", "Free (Promotional)"])
        with col2:
            qty = st.number_input("Quantity", min_value=1, step=1)
            
        submit_sale = st.form_submit_button("Complete Transaction")
        
        if submit_sale:
            if sel_product is None:
                st.error("ရောင်းချရန် Product မရှိပါ။")
            else:
                current_stock = st.session_state['inventory'].loc[
                    st.session_state['inventory']['Product Name'] == sel_product, 'Stock'
                ].values[0]
                
                if qty > current_stock:
                    st.error(f"Stock မလောက်တော့ပါ! {sel_product} အတွက် {current_stock} ခုသာ ကျန်ပါတော့တယ်။")
                else:
                    record_sale(sel_product, qty, sale_type)
                    st.success(f"အရောင်းမှတ်တမ်း အောင်မြင်ပါတယ်။ {qty}x {sel_product} မှတ်သားပြီးပါပြီ။")

# --- 3. INVENTORY MANAGEMENT ---
elif choice == "📦 Inventory Management":
    st.title("Inventory Management")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add New Product", "🔄 Update Price/Stock", "❌ Delete Product"])
    
    # Add Product
    with tab1:
        with st.form("add_product"):
            new_id = st.text_input("Product ID (e.g., P004)")
            new_name = st.text_input("Product Name")
            
            new_price = st.number_input("Price (MMK)", min_value=0.0, step=1000.0, value=None, placeholder="0.00")
            new_stock = st.number_input("Initial Stock", min_value=0, step=1, value=None, placeholder="0")
            
            if st.form_submit_button("Add Product"):
                if new_name == "" or new_price is None or new_stock is None:
                    st.error("ကျေးဇူးပြု၍ Product အမည်၊ စျေးနှုန်း နှင့် အရေအတွက် အားလုံးကို ဖြည့်သွင်းပါ။")
                elif new_name in st.session_state['inventory']['Product Name'].values:
                    st.error("ဒီ Product က ရှိပြီးသားပါ!")
                else:
                    new_item = pd.DataFrame([[new_id, new_name, new_price, new_stock]], 
                                            columns=st.session_state['inventory'].columns)
                    st.session_state['inventory'] = pd.concat([st.session_state['inventory'], new_item], ignore_index=True)
                    st.success("Product အသစ် ထည့်သွင်းပြီးပါပြီ!")

    # Update Product
    with tab2:
        product_list_to_update = st.session_state['inventory']['Product Name'].tolist()
        if not product_list_to_update:
            st.info("Update လုပ်ရန် Product မရှိသေးပါ။")
        else:
            prod_to_update = st.selectbox("Select Product to Update", product_list_to_update)
            current_price = st.session_state['inventory'].loc[st.session_state['inventory']['Product Name'] == prod_to_update, 'Price (MMK)'].values[0]
            
            col1, col2 = st.columns(2)
            with col1:
                updated_price = st.number_input("New Price (MMK)", value=float(current_price), step=1000.0)
            with col2:
                add_stock = st.number_input("Add Stock (Quantity)", value=None, placeholder="0", step=1)
                
            if st.button("Update Product"):
                st.session_state['inventory'].loc[st.session_state['inventory']['Product Name'] == prod_to_update, 'Price (MMK)'] = updated_price
                if add_stock is not None:
                    st.session_state['inventory'].loc[st.session_state['inventory']['Product Name'] == prod_to_update, 'Stock'] += add_stock
                st.success("Product ကို Update လုပ်ပြီးပါပြီ!")

    # Delete Product
    with tab3:
        st.markdown("#### တစ်ခုချင်းစီ ဖျက်ရန်")
        product_list_to_delete = st.session_state['inventory']['Product Name'].tolist()
        
        if not product_list_to_delete:
            st.info("ဖျက်ရန် Product မရှိတော့ပါ။")
        else:
            prod_to_delete = st.selectbox("Select Product to Delete", product_list_to_delete, key="del_single")
            if st.button("Delete Selected Product", type="primary"):
                st.session_state['inventory'] = st.session_state['inventory'][st.session_state['inventory']['Product Name'] != prod_to_delete]
                st.success(f"{prod_to_delete} ကို ဖျက်လိုက်ပါပြီ။")
                
        st.markdown("---")
        st.markdown("#### အားလုံးကို ဖျက်ရန် (Clear All)")
        st.warning("သတိပြုရန်: ဤခလုတ်ကို နှိပ်ပါက Inventory အတွင်းရှိ Product အားလုံး အပြီးတိုင် ဖျက်ပစ်ပါမည်။ (Sales History မပျက်ပါ)")
        if st.button("Delete ALL Products", type="primary", use_container_width=True):
            # Column တွေကို ချန်ထားပြီး Row တွေအကုန်ဖျက်ပစ်မယ်
            st.session_state['inventory'] = pd.DataFrame(columns=['Product ID', 'Product Name', 'Price (MMK)', 'Stock'])
            st.success("Product အားလုံးကို အပြီးတိုင် ရှင်းလင်းလိုက်ပါပြီ။")

# --- 4. MARKET ANALYSIS ---
elif choice == "📊 Market Analysis":
    st.title("Market Analysis & Insights")
    df_sales = st.session_state['sales_history']
    
    if df_sales.empty:
        st.info("Analysis လုပ်ရန် Data မရှိသေးပါ။ အရောင်းအဝယ် အရင်ပြုလုပ်ပေးပါ!")
    else:
        revenue_by_product = df_sales.groupby('Product Name')['Total Value (MMK)'].sum().reset_index()
        fig1 = px.pie(revenue_by_product, values='Total Value (MMK)', names='Product Name', 
                      title="Market Share: Revenue by Product", hole=0.3)
        st.plotly_chart(fig1, use_container_width=True)
        
        trend_data = df_sales.groupby('Date')['Total Value (MMK)'].sum().reset_index()
        fig2 = px.line(trend_data, x='Date', y='Total Value (MMK)', 
                       title="Daily Revenue Trend", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

# --- 5. SALES HISTORY ---
elif choice == "📜 Sales History":
    st.title("Comprehensive Sales History")
    st.markdown("အရောင်းမှတ်တမ်း အားလုံးကို ဤနေရာတွင် ကြည့်ရှုနိုင်ပါသည်။")
    
    df_sales = st.session_state['sales_history']
    
    if not df_sales.empty:
        display_df = df_sales.drop(columns=['Sale Type'], errors='ignore')
    else:
        display_df = df_sales.drop(columns=['Sale Type'], errors='ignore') if 'Sale Type' in df_sales.columns else df_sales
        
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    if not display_df.empty:
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name='local_sales_history.csv',
            mime='text/csv',
        )