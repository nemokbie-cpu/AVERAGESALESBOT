import streamlit as st
import re
from datetime import datetime, timedelta

def calculate_net(price):
    if price < 57:
        return price * 0.97 - 8.5
    else:
        return price * 0.89 - 4

def get_target_roi(days):
    if days < 5:
        return 0.30
    elif 10 <= days <= 15:
        return 0.40
    else:
        return 0.45

def analyze(raw_text):
    today = datetime.now()
    cutoff = today - timedelta(days=120)
    prices = []

    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        date_match = re.search(r'(\d{2}/\d{2}/\d{2})', line)
        if date_match:
            try:
                date = datetime.strptime(date_match.group(1), '%m/%d/%y')
                if date > today:
                    date = date.replace(year=date.year - 100)
                i += 1
                while i < len(lines):
                    price_match = re.search(r'£\s*([\d,]+)', lines[i])
                    if price_match:
                        price = float(price_match.group(1).replace(',', ''))
                        if date >= cutoff:
                            prices.append(price)
                        break
                    i += 1
                continue
            except:
                pass
        i += 1

    if not prices:
        return "No valid sales in last 120 days."

    n = len(prices)
    avg_price = sum(prices) / n
    avg_net = sum(calculate_net(p) for p in prices) / n
    days_to_sell = 120 / n if n > 0 else float('inf')
    target_roi = get_target_roi(days_to_sell)
    max_pay = avg_net / (1 + target_roi)

    return f"""
**120-Day Sneaker Analysis**

# Sales (120D): {n}
Avg Sold Price: £{avg_price:.2f}
Avg Net Payout: £{avg_net:.2f}
Est. Days to Sell: {days_to_sell:.2f}

Target ROI: {target_roi:.0%}
**Recommended Max Price to Pay: £{max_pay:.2f}**
    """

st.title("Sneaker 120-Day Analyzer")
st.write("Paste raw StockX sales data (same format as always)")

data = st.text_area("Sales Data", height=400)
if st.button("Analyze"):
    if data.strip():
        result = analyze(data)
        st.markdown(result)
    else:
        st.warning("Paste data first!")
