import streamlit as st
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

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

# Function to get the nearest available date
def get_nearest_date(date, data_index, direction='forward'):
    if direction == 'forward':
        available_dates = data_index[data_index >= date]
        if not available_dates.empty:
            return available_dates[0]
    elif direction == 'backward':
        available_dates = data_index[data_index <= date]
        if not available_dates.empty:
            return available_dates[-1]
    return None

# Function to get periods
def get_periods(start_date, end_date, data_index):
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
        
        # Find nearest available dates if exact dates are missing
        start_period = get_nearest_date(start_period, data_index, 'forward')
        end_period = get_nearest_date(end_period, data_index, 'backward')
        
        if start_period is None or end_period is None or start_period > end_date:
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
periods = get_periods(start_date, end_date, data.index)

# Calculate price increase percentage for each period
price_increases = []

for start, end in periods:
    # Ensure we have data available for the period
    start = get_nearest_date(start, data.index, 'forward')
    end = get_nearest_date(end, data.index, 'backward')
    
    if start and end:
        period_data = data.loc[start:end]
        if not period_data.empty:
            start_prices = period_data.iloc[0]
            end_prices = period_data.iloc[-1]
            percentage_increase = (end_prices / start_prices - 1) * 100
            percentage_increase['Period'] = f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
            price_increases.append(percentage_increase)

price_increase_df = pd.DataFrame(price_increases).set_index('Period')

# Ensure that all tickers are included and fill missing values
all_tickers = [ticker for ticker in tickers if ticker in price_increase_df.columns]
price_increase_df = price_increase_df.reindex(columns=all_tickers, fill_value=np.nan)

# Fill missing values by forward filling and backward filling
price_increase_df = price_increase_df.fillna(method='ffill').fillna(method='bfill')

# Ensure that the index is a DatetimeIndex
if not isinstance(price_increase_df.index, pd.DatetimeIndex):
    price_increase_df.index = pd.to_datetime(price_increase_df.index)

# Plotting heatmap with seaborn
plt.figure(figsize=(14, 18))  # Adjusting size for better visibility
heatmap = sns.heatmap(price_increase_df, annot=True, fmt=".1f", cmap='RdYlGn', center=0,
                     cbar_kws={'label': 'Price Increase (%)'}, linewidths=.5, linecolor='gray')

# Customize plot
plt.title("Price Increase Heatmap for GGAL and GGAL.BA", fontsize=18)
plt.xlabel("Ticker", fontsize=14)
plt.ylabel("Period", fontsize=14)
plt.xticks(rotation=0, fontsize=12)
plt.yticks(rotation=0, fontsize=12)

# Draw red horizontal lines for new years
years = pd.DatetimeIndex(price_increase_df.index).year.unique()
for year in years:
    year_start = pd.Timestamp(f'{year}-01-01')
    if year_start in price_increase_df.index:
        year_start_index = price_increase_df.index.get_loc(year_start)
        plt.axhline(y=year_start_index - 0.5, color='red', linestyle='--', linewidth=1)

# Display the plot in Streamlit
st.pyplot(plt)

# Define colors for percentiles
percentile_colors = {
    5: 'blue',
    25: 'green',
    50: 'orange',
    75: 'purple',
    95: 'red'
}

# Calculate percentiles
def plot_histogram_with_gaussian(data, ticker, ax):
    # Dropna to ensure clean data
    data = data.dropna()
    
    # Plot histogram
    sns.histplot(data, kde=True, stat="density", linewidth=0, color='skyblue', ax=ax)
    
    # Plot Gaussian curve
    mu, std = data.mean(), data.std()
    xmin, xmax = ax.get_xlim()
    x = np.linspace(xmin, xmax, 100)
    p = np.exp(-0.5 * ((x - mu) / std) ** 2) / (std * np.sqrt(2 * np.pi))
    ax.plot(x, p, 'k--', linewidth=2, label='Gaussian Fit')
    
    # Plot percentile lines with different colors
    percentiles = [5, 25, 50, 75, 95]
    for perc in percentiles:
        percentile_value = np.percentile(data, perc)
        ax.axvline(percentile_value, color=percentile_colors[perc], linestyle='--', linewidth=2)
        ax.text(percentile_value, ax.get_ylim()[1] * 0.9, f'{perc}th', color=percentile_colors[perc])

    # Customize plot
    ax.set_title(f'Histogram with Gaussian Fit for {ticker}', fontsize=16)
    ax.set_xlabel('Price Increase (%)', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)
    ax.legend()

# Create histograms for each ticker
fig, axes = plt.subplots(len(tickers), 1, figsize=(10, 5 * len(tickers)))

for i, ticker in enumerate(tickers):
    plot_histogram_with_gaussian(price_increase_df[ticker], ticker, axes[i])

# Display the histograms in Streamlit
st.pyplot(fig)
