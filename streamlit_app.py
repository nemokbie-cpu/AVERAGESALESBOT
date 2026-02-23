import streamlit as st
import re
from datetime import datetime, timedelta
from statistics import mean

def calculate_net(price):
    """Calculate net payout after StockX fees"""
    if price < 57:
        return price * 0.97 - 8.5
    else:
        return price * 0.89 - 4

def get_target_roi(avg_days):
    """Target ROI based on average days to sell"""
    if avg_days < 5:
        return 0.30
    elif 10 <= avg_days <= 15:
        return 0.40
    else:
        return 0.45

def parse_sales(raw_text):
    """Parse StockX sales data exactly as you paste it"""
    sales = []
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        # Find date
        date_match = re.search(r'(\d{2}/\d{2}/\d{2})', line)
        if date_match:
            try:
                date = datetime.strptime(date_match.group(1), '%m/%d/%y')
                if date > datetime.now():
                    date = date.replace(year=date.year - 100)
                
                # Find price on this line or next few lines
                price = None
                for j in range(i, min(i + 5, len(lines))):
                    price_match = re.search(r'£\s*([\d,]+)', lines[j])
                    if price_match:
                        price = float(price_match.group(1).replace(',', ''))
                        i = j
                        break
                
                if price is not None:
                    sales.append({'date': date, 'price': price})
            except:
                pass
        i += 1
    return sales

def calculate_avg_days(sales_list):
    """Calculate average days between consecutive sales (manual method we use)"""
    if len(sales_list) < 2:
        return None
    # Sort oldest → newest
    sorted_sales = sorted(sales_list, key=lambda x: x['date'])
    days_list = []
    for i in range(1, len(sorted_sales)):
        delta = (sorted_sales[i]['date'] - sorted_sales[i-1]['date']).days
        days_list.append(delta)  # 0 for same-day sales (exact match to our manual calc)
    
    return round(mean(days_list), 2)

# ====================== STREAMLIT APP ======================
st.set_page_config(page_title="Sneaker Analyzer", layout="wide")
st.title("🚀 Sneaker Sales Analyzer")
st.write("Paste your StockX sales data below (same format as always)")

# Session state for text area so Clear works perfectly
if "sales_data" not in st.session_state:
    st.session_state.sales_data = ""

# Sidebar filters
st.sidebar.header("Filters & Settings")
min_price = st.sidebar.number_input("Min Price (£)", value=0, step=5)
max_price = st.sidebar.number_input("Max Price (£)", value=300, step=5)

velocity_x = st.sidebar.number_input(
    "Calculate avg days using last ___ sales",
    min_value=5,
    max_value=100,
    value=20,
    step=5,
    help="Leave at 20 or change to any number"
)

# Main input area
col1, col2 = st.columns([6, 1])
with col1:
    data = st.text_area(
        "Sales Data",
        value=st.session_state.sales_data,
        height=520,
        placeholder="Paste your sales here...",
        key="text_area"
    )
with col2:
    if st.button("🗑️ Clear Data", use_container_width=True):
        st.session_state.sales_data = ""
        st.rerun()

if st.button("Analyze", type="primary", use_container_width=True):
    if not data.strip():
        st.warning("Paste your sales data first!")
    else:
        # Save current data to session
        st.session_state.sales_data = data
        
        sales = parse_sales(data)
        
        # Apply price filter
        filtered_sales = [s for s in sales if min_price <= s['price'] <= max_price]
        
        if not filtered_sales:
            st.error("No sales match the price filter.")
        else:
            # 120-day cutoff
            cutoff = datetime.now() - timedelta(days=120)
            recent_sales = [s for s in filtered_sales if s['date'] >= cutoff]
            
            if len(recent_sales) < 2:
                st.warning("Not enough sales to calculate average days.")
            else:
                n = len(recent_sales)
                prices = [s['price'] for s in recent_sales]
                
                avg_price = mean(prices)
                avg_net = mean(calculate_net(p) for p in prices)
                
                # Last 10 sales net average
                last_10_net = mean(calculate_net(s['price']) for s in recent_sales[:10]) \
                              if len(recent_sales) >= 10 else avg_net
                
                # Full average days (all filtered sales in 120d)
                avg_days_all = calculate_avg_days(recent_sales)
                
                # Average days using only last X sales
                recent_x = sorted(recent_sales, key=lambda x: x['date'], reverse=True)[:velocity_x]
                avg_days_x = calculate_avg_days(recent_x)
                
                # Use the X-sales velocity for ROI (most practical)
                target_roi = get_target_roi(avg_days_x)
                max_pay = round(last_10_net / (1 + target_roi), 2)
                
                st.success("✅ Analysis Complete")
                st.markdown(f"""
**📊 120-Day Sneaker Analysis**

**Sales Analyzed**: {n}  
**Price Filter**: £{min_price} – £{max_price}

**Avg Sold Price**: £{avg_price:.2f}  
**Avg Net Payout**: £{avg_net:.2f}  
**Avg Net (Last 10 Sales)**: £{last_10_net:.2f}

**Avg Days Between Sales** (all filtered): **{avg_days_all} days**  
**Velocity (Last {velocity_x} sales)**: **{avg_days_x} days**

**Target ROI**: {target_roi:.0%}  
**Recommended Max Price to Pay**: **£{max_pay}**
                """)
