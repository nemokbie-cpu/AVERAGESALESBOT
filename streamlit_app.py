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
                for j in range(i, min(i + 6, len(lines))):
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
    days_list = [(sorted_sales[i]['date'] - sorted_sales[i-1]['date']).days for i in range(1, len(sorted_sales))]
    return round(mean(days_list), 2)

# ====================== STREAMLIT APP ======================
st.set_page_config(page_title="Sneaker Analyzer", layout="wide")
st.title("🚀 Sneaker Sales Analyzer")
st.caption("Paste your StockX sales data exactly as before")

# Session state
if "sales_input" not in st.session_state:
    st.session_state.sales_input = ""

def clear_data():
    st.session_state.sales_input = ""

# Sidebar Filters
st.sidebar.header("🔧 Filters")
min_price = st.sidebar.number_input(
    "Only include sales **OVER** this price (£)",
    value=0,
    step=5,
    min_value=0,
    help="e.g. 90 = ignore everything below £90"
)

velocity_x = st.sidebar.number_input(
    "Use LAST ___ sales for ROI calculation",
    min_value=5,
    max_value=100,
    value=20,
    step=5
)

show_comparison = st.sidebar.checkbox(
    "Also show Last 10 & Last 50 velocity",
    value=True
)

# Main layout
col1, col2 = st.columns([6, 1.2])
with col1:
    data = st.text_area(
        "Paste Sales Data Here",
        height=520,
        key="sales_input",
        placeholder="02/10/26, 1:47 AMUK 7.5\n£109\n..."
    )
with col2:
    st.button("🗑️ Clear Data", on_click=clear_data, use_container_width=True, type="secondary")

if st.button("🔍 Analyze Data", type="primary", use_container_width=True):
    if not data.strip():
        st.warning("Paste your sales data first!")
    else:
        all_sales = parse_sales(data)
        
        # Price filter
        filtered_sales = [s for s in all_sales if s['price'] >= min_price]
        
        if len(filtered_sales) < 2:
            st.error(f"No sales ≥ £{min_price}")
        else:
            cutoff = datetime.now() - timedelta(days=120)
            recent_sales = [s for s in filtered_sales if s['date'] >= cutoff]
            
            n = len(recent_sales)
            if n < 2:
                st.warning("Not enough sales after filtering.")
            else:
                avg_price = mean(s['price'] for s in recent_sales)
                avg_net = mean(calculate_net(s['price']) for s in recent_sales)
                
                # Last 10 net
                last_10 = sorted(recent_sales, key=lambda x: x['date'], reverse=True)[:10]
                avg_net_last10 = mean(calculate_net(s['price']) for s in last_10)
                
                # Velocities
                sorted_recent = sorted(recent_sales, key=lambda x: x['date'], reverse=True)
                avg_days_x = calculate_avg_days(sorted_recent[:velocity_x])
                avg_days_10 = calculate_avg_days(sorted_recent[:10])
                avg_days_50 = calculate_avg_days(sorted_recent[:50]) if len(sorted_recent) >= 50 else None
                
                target_roi = get_target_roi(avg_days_x)
                max_pay = round(avg_net_last10 / (1 + target_roi), 2)
                
                st.success("✅ Analysis Complete")
                
                st.markdown(f"""
**📊 120-Day Analysis (Sales ≥ £{min_price})**

**Valid Sales**: {n}  
**Avg Sold Price**: £{avg_price:.2f}  
**Avg Net Payout**: £{avg_net:.2f}  
**Avg Net (Last 10)**: £{avg_net_last10:.2f}

**Average Days Between Sales:**
- Last **{velocity_x}** sales → **{avg_days_x} days** (used for ROI)
                """)
                
                if show_comparison:
                    st.markdown(f"""
- Last **10** sales → **{avg_days_10} days**
- Last **50** sales → **{avg_days_50} days** (if available)
                    """)
                
                st.markdown(f"""
**Target ROI**: {target_roi:.0%}  
**Recommended Max Buy Price**: **£{max_pay}**
                """)
