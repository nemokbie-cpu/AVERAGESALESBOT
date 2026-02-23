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

# Your exact average days calculation
def calculate_avg_days(sales_list):
    if len(sales_list) < 2:
        return None
    
    date_list = [s['date'] for s in sales_list]
    date_list.sort(reverse=True)  # newest → oldest
    
    intervals = []
    for i in range(1, len(date_list)):
        delta = (date_list[i-1] - date_list[i]).days
        intervals.append(delta)
    
    avg = sum(intervals) / len(intervals)
    return round(avg, 1)

# ────────────────────────────────────────────────
#                  STREAMLIT APP
# ────────────────────────────────────────────────

st.set_page_config(page_title="Sneaker Analyzer", layout="wide")
st.title("🚀 Sneaker Sales Analyzer")
st.caption("Paste your StockX sales data exactly as before")

# Session state for paste area
if "sales_input" not in st.session_state:
    st.session_state.sales_input = ""

def clear_data():
    st.session_state.sales_input = ""

# Sidebar (advanced settings)
st.sidebar.header("Advanced Settings")
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

# Main page
data = st.text_area(
    "📋 Paste Sales Data Here",
    height=520,
    key="sales_input",
    placeholder="02/19/26, 6:58 PMUK 8.5\n£98\n..."
)

# Filter section – BEFORE analyze button
st.subheader("🔍 Filter BEFORE Analysis")
min_price = st.number_input(
    "Only include sales **at or above** this price (£)",
    value=0,
    step=5,
    min_value=0,
    help="Example: set to 110 → includes £110 and higher"
)

# Buttons
col_clear, col_analyze = st.columns([1, 3])
with col_clear:
    st.button("🗑️ Clear Data", on_click=clear_data, use_container_width=True, type="secondary")
with col_analyze:
    analyze_clicked = st.button("🔍 Analyze Data", type="primary", use_container_width=True)

if analyze_clicked:
    if not data.strip():
        st.warning("Paste your sales data first!")
    else:
        all_sales = parse_sales(data)
        
        # Changed: ≥ instead of >
        filtered_sales = [s for s in all_sales if s['price'] >= min_price]
        
        if len(filtered_sales) < 2:
            st.error(f"No sales at or above £{min_price}")
        else:
            cutoff = datetime.now() - timedelta(days=120)
            recent_sales = [s for s in filtered_sales if s['date'] >= cutoff]
            
            n = len(recent_sales)
            if n < 2:
                st.warning("Not enough sales after filtering.")
            else:
                avg_price = mean(s['price'] for s in recent_sales)
                avg_net = mean(calculate_net(s['price']) for s in recent_sales)
                
                last_10 = sorted(recent_sales, key=lambda x: x['date'], reverse=True)[:10]
                avg_net_last10 = mean(calculate_net(s['price']) for s in last_10)
                
                sorted_recent = sorted(recent_sales, key=lambda x: x['date'], reverse=True)
                avg_days_x   = calculate_avg_days(sorted_recent[:velocity_x])
                avg_days_10  = calculate_avg_days(sorted_recent[:10])
                avg_days_50  = calculate_avg_days(sorted_recent[:50]) if len(sorted_recent) >= 50 else None
                
                target_roi = get_target_roi(avg_days_x)
                max_pay = round(avg_net_last10 / (1 + target_roi), 2)
                
                st.success("✅ Analysis Complete")
                
                st.markdown(f"""
**📊 120-Day Analysis (Sales ≥ £{min_price})**

**Valid Sales**: {n}  
**Avg Sold Price**: £{avg_price:.2f}  
**Avg Net Payout**: £{avg_net:.2f}  
**Avg Net (Last 10)**: £{avg_net_last10:.2f}

**Average Days Between Sales** (your exact method):
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
