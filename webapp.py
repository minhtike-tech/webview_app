import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import time  # နှောင့်နှေးချိန်လေးထည့်ရန် ထပ်တိုးထားသည်

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Khaing's Market Sales", page_icon="🇲🇲", layout="wide")
# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Khaing's Market Sales", page_icon="🇲🇲", layout="wide")

# --- HIDE STREAMLIT UI ---
hide_st_style = """
            <style>
            /* အပေါ်ညာဘက်ထောင့်ရှိ ခလုတ်များ အားလုံးကို အတင်းဖျောက်ရန် */
            [data-testid="stHeaderActionElements"] {display: none !important;}
            .stAppDeployButton {display: none !important;}
            #MainMenu {visibility: hidden !important;}
            /* အောက်ခြေရှိ Streamlit Footer ကို ဖျောက်ရန် */
            footer {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_db_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        import os
        import json
        if os.path.exists("secrets.json"):
            creds = Credentials.from_service_account_file("secrets.json", scopes=scopes)
        else:
            secret_str = st.secrets["google_credentials"]
            creds_dict = json.loads(secret_str)
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            
        client = gspread.authorize(creds)
        return client.open("Market Database")
    except Exception as e:
        st.error(f"⚠️ Database ချိတ်ဆက်မှု မအောင်မြင်ပါ။\nError: {e}")
        return None

db = get_db_connection()
if db:
    inv_sheet = db.worksheet("Inventory")
    sales_sheet = db.worksheet("Sales")

    # --- HELPER FUNCTIONS FOR GOOGLE SHEETS ---
    def load_inventory():
        records = inv_sheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=['Product ID', 'Product Name', 'Price (MMK)', 'Stock'])
        df = pd.DataFrame(records)
        # Google Sheet မှ စာသားများကို ဂဏန်းအဖြစ် ပြောင်းလဲပေးခြင်း
        df['Price (MMK)'] = pd.to_numeric(df['Price (MMK)'], errors='coerce').fillna(0.0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df

    def load_sales():
        records = sales_sheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=['Transaction ID', 'Date', 'Product Name', 'Unit Price (MMK)', 'Quantity', 'Sale Type', 'Total Value (MMK)'])
        df = pd.DataFrame(records)
        
        # Error မတက်စေရန် ကော်လံများ ရှိမရှိ စစ်ဆေးပြီး မရှိပါက အသစ်ဖန်တီးပေးခြင်း
        expected_cols = ['Transaction ID', 'Date', 'Product Name', 'Unit Price (MMK)', 'Quantity', 'Sale Type', 'Total Value (MMK)']
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "Standard Sale" if col == 'Sale Type' else 0
                
        # Google Sheet မှ စာသားများကို ဂဏန်းအဖြစ် ပြောင်းလဲပေးခြင်း (Chart များပေါ်လာစေရန်)
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0).astype(int)
        df['Total Value (MMK)'] = pd.to_numeric(df['Total Value (MMK)'], errors='coerce').fillna(0.0)
        df['Unit Price (MMK)'] = pd.to_numeric(df['Unit Price (MMK)'], errors='coerce').fillna(0.0)
        return df

    def update_inventory_db(df):
        inv_sheet.clear()
        inv_sheet.update([df.columns.values.tolist()] + df.values.tolist())

    # [အသစ်] Sales Sheet ပါ ရှင်းလင်းပေးမည့် Function
    def clear_sales_db():
        sales_sheet.clear()
        # ခေါင်းစဉ်များကို ပြန်ထည့်ပေးခြင်း
        headers = ['Transaction ID', 'Date', 'Product Name', 'Unit Price (MMK)', 'Quantity', 'Sale Type', 'Total Value (MMK)']
        sales_sheet.append_row(headers)

    def record_sale(product_name, qty, sale_type, current_inventory):
        price = float(current_inventory.loc[current_inventory['Product Name'] == product_name, 'Price (MMK)'].values[0])
        total_value = 0.0 if sale_type == "Free (Promotional)" else float(price * qty)
        
        transaction_id = f"TRX-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        date_str = str(datetime.datetime.now().date())
        
        sale_data = [transaction_id, date_str, product_name, price, int(qty), sale_type, total_value]
        sales_sheet.append_row(sale_data)
        
        current_inventory.loc[current_inventory['Product Name'] == product_name, 'Stock'] -= qty
        update_inventory_db(current_inventory)

    # Load Data from Database
    df_inventory = load_inventory()
    df_sales = load_sales()

    # --- APP NAVIGATION ---
    st.sidebar.title("Khaing Market❣️")
    st.sidebar.markdown("---")
    menu = ["🏠 Home / Dashboard", "🛒 Process Sales", "📦 Inventory Management", "📊 Market Analysis", "📜 Sales History"]
    choice = st.sidebar.radio("Navigation", menu)

    # --- 1. HOME / DASHBOARD ---
    if choice == "🏠 Home / Dashboard":
        st.title("Business Dashboard Overview")
        today = str(datetime.datetime.now().date())
        
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
        st.dataframe(df_inventory, use_container_width=True, hide_index=True)

    # --- 2. PROCESS SALES ---
    elif choice == "🛒 Process Sales":
        st.title("Point of Sale")
        st.markdown("အရောင်းမှတ်တမ်း (သို့မဟုတ်) အခမဲ့ Promotion ပေးမှုများကို မှတ်သားပါ။")
        
        with st.form("sales_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            product_list = df_inventory['Product Name'].tolist() if not df_inventory.empty else []
            
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
                    current_stock = int(df_inventory.loc[df_inventory['Product Name'] == sel_product, 'Stock'].values[0])
                    
                    if qty > current_stock:
                        st.error(f"Stock မလောက်တော့ပါ! {sel_product} အတွက် {current_stock} ခုသာ ကျန်ပါတော့တယ်။")
                    else:
                        record_sale(sel_product, qty, sale_type, df_inventory.copy())
                        st.success(f"အရောင်းမှတ်တမ်း အောင်မြင်ပါတယ်။ {qty}x {sel_product} ကို Database သို့ သိမ်းဆည်းပြီးပါပြီ။")
                        st.rerun()

    # --- 3. INVENTORY MANAGEMENT ---
    elif choice == "📦 Inventory Management":
        st.title("Inventory Management")
        tab1, tab2, tab3 = st.tabs(["➕ Add New Product", "🔄 Update Price/Stock", "❌ Delete / Reset"])
        
        with tab1:
            with st.form("add_product"):
                new_id = st.text_input("Product ID (e.g., P001)")
                new_name = st.text_input("Product Name")
                new_price = st.number_input("Price (MMK)", min_value=0.0, step=1000.0, value=None, placeholder="0.00")
                new_stock = st.number_input("Initial Stock", min_value=0, step=1, value=None, placeholder="0")
                
                if st.form_submit_button("Add Product"):
                    if new_name == "" or new_price is None or new_stock is None:
                        st.error("ကျေးဇူးပြု၍ Product အမည်၊ စျေးနှုန်း နှင့် အရေအတွက် အားလုံးကို ဖြည့်သွင်းပါ။")
                    elif not df_inventory.empty and new_name in df_inventory['Product Name'].values:
                        st.error("ဒီ Product က ရှိပြီးသားပါ!")
                    else:
                        new_item = pd.DataFrame([[new_id, new_name, float(new_price), int(new_stock)]], columns=df_inventory.columns)
                        updated_df = pd.concat([df_inventory, new_item], ignore_index=True)
                        update_inventory_db(updated_df)
                        st.success("Product အသစ်ကို Database သို့ ထည့်သွင်းပြီးပါပြီ!")
                        st.rerun()

        with tab2:
            product_list_to_update = df_inventory['Product Name'].tolist() if not df_inventory.empty else []
            if not product_list_to_update:
                st.info("Update လုပ်ရန် Product မရှိသေးပါ။")
            else:
                prod_to_update = st.selectbox("Select Product to Update", product_list_to_update)
                current_price = float(df_inventory.loc[df_inventory['Product Name'] == prod_to_update, 'Price (MMK)'].values[0])
                
                col1, col2 = st.columns(2)
                with col1:
                    updated_price = st.number_input("New Price (MMK)", value=current_price, step=1000.0)
                with col2:
                    add_stock = st.number_input("Add Stock (Quantity)", value=None, placeholder="0", step=1)
                    
                if st.button("Update Product"):
                    df_to_update = df_inventory.copy()
                    df_to_update.loc[df_to_update['Product Name'] == prod_to_update, 'Price (MMK)'] = float(updated_price)
                    if add_stock is not None:
                        df_to_update.loc[df_to_update['Product Name'] == prod_to_update, 'Stock'] += int(add_stock)
                    update_inventory_db(df_to_update)
                    st.success("Database တွင် Product ကို Update လုပ်ပြီးပါပြီ!")
                    st.rerun()

        with tab3:
            st.markdown("#### တစ်ခုချင်းစီ ဖျက်ရန်")
            product_list_to_delete = df_inventory['Product Name'].tolist() if not df_inventory.empty else []
            
            if not product_list_to_delete:
                st.info("ဖျက်ရန် Product မရှိတော့ပါ။")
            else:
                prod_to_delete = st.selectbox("Select Product to Delete", product_list_to_delete, key="del_single")
                if st.button("Delete Selected Product"):
                    df_after_delete = df_inventory[df_inventory['Product Name'] != prod_to_delete]
                    update_inventory_db(df_after_delete)
                    st.success(f"{prod_to_delete} ကို Database မှ ဖျက်လိုက်ပါပြီ။")
                    st.rerun()
                    
            st.markdown("---")
            st.markdown("#### အားလုံးကို ဖျက်ရန် (Clear All Data)")
            st.warning("သတိပြုရန်: ဤခလုတ်ကိုနှိပ်ပါက Inventory (ကုန်ပစ္စည်းများ) နှင့် Sales History (အရောင်းမှတ်တမ်းများ) အားလုံးကို Google Sheet မှ အပြီးတိုင် ဖျက်ပစ်ပါမည်။ Dashboard ရှိ စာရင်းများလည်း သုည ဖြစ်သွားပါမည်။")
            
            if st.button("🚨 Reset Entire System & Clear ALL Data 🚨", type="primary", use_container_width=True):
                with st.spinner("Database တစ်ခုလုံးကို ရှင်းလင်းနေပါသည်။ ခေတ္တစောင့်ပါ..."):
                    # 1. Inventory ကို ရှင်းလင်းခြင်း
                    empty_df = pd.DataFrame(columns=['Product ID', 'Product Name', 'Price (MMK)', 'Stock'])
                    update_inventory_db(empty_df)
                    
                    # 2. Sales History ကို ရှင်းလင်းခြင်း
                    clear_sales_db()
                    
                st.success("စနစ်တစ်ခုလုံးရှိ ဒေတာအားလုံးကို အောင်မြင်စွာ ရှင်းလင်းလိုက်ပါပြီ။")
                time.sleep(2)
                st.rerun()

    # --- 4. MARKET ANALYSIS ---
    elif choice == "📊 Market Analysis":
        st.title("Market Analysis & Insights")
        
        if df_sales.empty or df_sales['Total Value (MMK)'].sum() == 0:
            st.info("Analysis လုပ်ရန် Data မရှိသေးပါ (သို့မဟုတ်) ရောင်းရငွေ သုည ဖြစ်နေပါသည်။")
        else:
            # Sales Data များကို ပေါင်းရုံးပြီး Chart ဆွဲခြင်း
            revenue_by_product = df_sales.groupby('Product Name')['Total Value (MMK)'].sum().reset_index()
            # 0 ထက်ကြီးသော Data များကိုသာ Chart တွင်ပြမည်
            revenue_by_product = revenue_by_product[revenue_by_product['Total Value (MMK)'] > 0]
            
            if not revenue_by_product.empty:
                fig1 = px.pie(revenue_by_product, values='Total Value (MMK)', names='Product Name', 
                              title="Market Share: Revenue by Product", hole=0.3)
                st.plotly_chart(fig1, use_container_width=True)
            
            trend_data = df_sales.groupby('Date')['Total Value (MMK)'].sum().reset_index()
            if not trend_data.empty:
                fig2 = px.line(trend_data, x='Date', y='Total Value (MMK)', 
                               title="Daily Revenue Trend", markers=True)
                st.plotly_chart(fig2, use_container_width=True)

    # --- 5. SALES HISTORY ---
    elif choice == "📜 Sales History":
        st.title("Comprehensive Sales History")
        st.markdown("အရောင်းမှတ်တမ်း အားလုံးကို ဤနေရာတွင် ကြည့်ရှုနိုင်ပါသည်။")
        
        if not df_sales.empty:
            display_df = df_sales.drop(columns=['Sale Type'], errors='ignore')
        else:
            display_df = df_sales
            
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        if not display_df.empty:
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Data as CSV", data=csv, file_name='local_sales_history.csv', mime='text/csv')

else:
    st.error("Database နှင့် မချိတ်ဆက်နိုင်သေးပါ။")




