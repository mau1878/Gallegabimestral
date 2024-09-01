import streamlit as st
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.title('Price Increase Heatmap for GGAL and GGAL.BA')

# Function to find the 4th Monday of an even month
def fourth_monday(year, month):
    first_day = pd.Timestamp(year, month, 1)
    first_monday = first_day + pd.offsets.Week(weekday=0) - pd.offsets.Week(weekday=first_day.weekday())
    fourth_monday = first_monday + pd.DateOffset(weeks=3)
    return fourth_monday

# Function to find the 3rd Friday of the next even month
def third_friday(year, month):
    next_even_month = month + 2
    if next_even_month > 12:
        next_even_month -= 12
        year += 1
    month_start = pd.Timestamp(year, next_even_month, 1)
    third_friday = month_start + pd.DateOffset(days=(14 + (4 - month_start.weekday()) % 7))
    return third_friday

# Function to get the periods
def get_periods(start_date, end_date):
    periods = []
    current_year = start_date.year
    current_month = start_date.month
    
    # Adjust to the nearest even month
    if current_month % 2 != 0:
        current_month += 1
        if current_month > 12:
            current_month = 2
            current_year += 1
    
    while True:
        start_period = fourth_monday(current_year, current_month)
        end_period = third_friday(current_year, current_month)
        
        # Convert periods to timezone-naive if needed
        if start_period.tzinfo is not None:
            start_period = start_period.tz_localize(None)
        if end_period.tzinfo is not None:
            end_period = end_period.tz_localize(None)
        if start_date.tzinfo is not None:
            start_date = start_date.tz_localize(None)
        if end_date.tzinfo is not None:
            end_date = end_date.tz_localize(None)
        
        if start_period > end_date:
            break
        
        periods.append((start_period, end_period))
        
        current_month += 2
        if current_month > 12:
            current_month = 2
            current_year += 1
    
    return periods

# Function to fetch stock data
def fetch_data(tickers, start_date, end_date):
    try:
        data = yf.download(tickers, start=start_date, end=end_date, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data = data['Adj Close'] if 'Adj Close' in data.columns.levels[1] else data['Close']
        else:
            data = data['Adj Close'] if 'Adj Close' in data.columns else data['Close']
        if data.empty:
            st.error("No data available for the selected tickers.")
            st.stop()
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()

# Fetch data
tickers = ['GGAL', 'GGAL.BA']
data = fetch_data(tickers, '2010-01-01', pd.Timestamp.today())

# Ensure that the data index is timezone-naive
if data.index.tzinfo is not None:
    data.index = data.index.tz_localize(None)

# Get periods
start_date = data.index.min()
end_date = data.index.max()
periods = get_periods(start_date, end_date)

# Calculate price increase percentage for each period
price_increases = []

for start, end in periods:
    period_data = data.loc[start:end]
    if not period_data.empty:
        start_prices = period_data.iloc[0]
        end_prices = period_data.iloc[-1]
        percentage_increase = (end_prices / start_prices - 1) * 100
        percentage_increase['Period'] = f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
        price_increases.append(percentage_increase)

price_increase_df = pd.DataFrame(price_increases).set_index('Period')

# Ensure data is available for plotting
if price_increase_df.empty:
    st.error("No price increase data available for the specified periods.")
    st.stop()

# Plotting heatmap with seaborn
plt.figure(figsize=(12, 8))
sns.heatmap(price_increase_df.T, annot=True, fmt=".1f", cmap='RdYlGn', center=0,
            cbar_kws={'label': 'Price Increase (%)'}, linewidths=.5, linecolor='gray')

plt.title("Price Increase Heatmap for GGAL and GGAL.BA", fontsize=16)
plt.xlabel("Period", fontsize=14)
plt.ylabel("Ticker", fontsize=14)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)

# Display the plot in Streamlit
st.pyplot(plt)
