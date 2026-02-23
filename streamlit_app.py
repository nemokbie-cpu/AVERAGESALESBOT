import streamlit as st
import re
from datetime import datetime, timedelta
from statistics import mean

def calculate_net(price):
    if price < 57:
        return price * 0.97 - 8.5
    else:
        return price * 0.89 - 4

def get_target_roi(avg_days):
    if avg_days < 5:
        return 0.30
    elif 10 <= avg_days <= 15:
        return 0.40
    else:
        return 0.45

def parse_sales(raw_text):
    sales = []
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        date_match = re.search(r'(\d{2}/\d{2}/\d{2})', line)
        if date_match:
            try:
                date = datetime.strptime(date_match.group(1), '%m/%d/%y')
                if date > datetime.now():
                    date = date.replace(year=date.year - 100)
                
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
    if len(sales_list) < 2:
        return None
    sorted_sales = sorted(sales_list, key=lambda x: x['date'])
    days_list = []
    for i in range(1, len(sorted_sales)):
        delta = (sorted_sales[i]['date'] - sorted_sales[i-1]['date']).days
        days_list.append(delta)
    return round(mean(days_list), 2)

# ====================== STREAMLIT APP ======================
st.set_page_config(page_title="Sneaker Analyzer", layout="wide")
st.title("🚀 Sneaker Sales Analyzer")
st.caption("Paste your StockX sales data exactly as before")

# Session state for input
if "sales_input" not in st.session_state:
    st.session_state.sales_input = ""

# Sidebar Filters
st.sidebar.header("🔧 Filters")
min_price_filter = st.sidebar.number_input(
    "**Only include sales ABOVE this price (£)**",
    value=0,
    step=5,
    min_value=0,
    help="e.g. set to 90 to ignore all sales below £90"
)

velocity_x = st.sidebar.number_input(
    "**Calculate avg days using last ___ sales**",
    min_value=5,
    max_value=100,
    value=20,
    step=5,
    help="This controls the velocity/ROI calculation (last X sales after min price filter)"
)

# Main input + Clear button
col1, col2 = st.columns([5, 1])
with col1:
    data = st.text_area(
        "Paste Sales Data Here",
        height=520,
        key="sales_input",          # ← ONLY key (no value=) → Clear works 100%
        placeholder="02/15/26, 10:54 PMUK 11.5\n£110\n..."
    )
with col2:
    if st.button("🗑️ Clear Data", use_container_width=True, type="secondary"):
        st.session_state.sales_input = ""
        st.rerun()

if st.button("🔍 Analyze", type="primary", use_container_width=True):
    if not data.strip():
        st.warning("Paste your sales data first!")
    else:
        sales = parse_sales(data)
        
        # Apply lowest price filter
        filtered_sales = [s for s in sales if s['price'] >= min_price_filter]
        
        if not filtered_sales:
            st.error(f"No sales ≥ £{min_price_filter}")
        else:
            cutoff = datetime.now() - timedelta(days=120)
            recent_sales = [s for s in filtered_sales if s['date'] >= cutoff]
            
            if len(recent_sales) < 2:
                st.warning("Not enough sales after filter to calculate average days.")
            else:
                n = len(recent_sales)
                prices = [s['price'] for s in recent_sales]
                
                avg_price = mean(prices)
                avg_net = mean(calculate_net(p) for p in prices)
                
                # Last 10 net (after filter)
                last_10_sales = sorted(recent_sales, key=lambda x: x['date'], reverse=True)[:10]
                avg_net_last10 = mean(calculate_net(s['price']) for s in last_10_sales)
                
                # Average days on last X sales (after min price filter)
                last_x_sales = sorted(recent_sales, key=lambda x: x['date'], reverse=True)[:velocity_x]
                avg_days_x = calculate_avg_days(last_x_sales)
                
                target_roi = get_target_roi(avg_days_x)
                max_pay = round(avg_net_last10 / (1 + target_roi), 2)
                
                st.success("✅ Done!")
                
                st.markdown(f"""
**📊 120-Day Analysis (Sales ≥ £{min_price_filter})**

**Valid Sales**: {n}  
**Avg Sold Price**: £{avg_price:.2f}  
**Avg Net Payout**: £{avg_net:.2f}  
**Avg Net (Last 10)**: £{avg_net_last10:.2f}

**Avg Days Between Sales** (last {velocity_x} sales): **{avg_days_x} days**

**Target ROI**: {target_roi:.0%}  
**Recommended Max Price to Pay**: **£{max_pay}**
                """)  
**Recommended Max Price to Pay**: **£{max_pay}**
                """)
