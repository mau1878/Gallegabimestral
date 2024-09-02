import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Set the ticker to GGAL (ADR)
ticker = "GGAL"  # ADR for Grupo Financiero Galicia

# User input for date range with default start date set to January 1, 2000
start_date = st.date_input("Select the start date", value=pd.to_datetime('2000-01-01'))
end_date = st.date_input("Select the end date", value=pd.to_datetime('today'))

# User input for close price type
close_price_type = st.selectbox("Select Close Price Type", ["Unadjusted", "Adjusted"])

# Fetch historical data for GGAL
data = yf.download(ticker, start=start_date, end=end_date)

# Select close price based on user input
if close_price_type == "Adjusted":
    price_column = 'Adj Close'
else:
    price_column = 'Close'

# Calculate 21-day SMA
data['21_SMA'] = data[price_column].rolling(window=21).mean()

# Calculate the dispersion (price - SMA)
data['Dispersion'] = data[price_column] - data['21_SMA']

# Calculate the dispersion percentage
data['Dispersion_Percent'] = data['Dispersion'] / data['21_SMA'] * 100

# Plotly Line Plot: Historical Price with 21 SMA
fig = go.Figure()

# Plot the historical close price
fig.add_trace(go.Scatter(x=data.index, y=data[price_column], mode='lines', name='Close Price'))

# Plot the 21-day SMA
fig.add_trace(go.Scatter(x=data.index, y=data['21_SMA'], mode='lines', name='21 SMA'))

# Update layout
fig.update_layout(
    title=f"Historical {close_price_type} Price of {ticker} with 21-day SMA",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    legend_title="Legend",
    template="plotly_dark"
)

# Show the Plotly chart
st.plotly_chart(fig)

# Plotly Line Plot: Historical Dispersion Percentage
fig_dispersion = go.Figure()

# Plot the dispersion percentage
fig_dispersion.add_trace(go.Scatter(x=data.index, y=data['Dispersion_Percent'], mode='lines', name='Dispersion %'))

# Add a red horizontal line at y=0
fig_dispersion.add_shape(
    go.layout.Shape(
        type="line",
        x0=data.index.min(),
        x1=data.index.max(),
        y0=0,
        y1=0,
        line=dict(color="red", width=2)
    )
)

# Update layout
fig_dispersion.update_layout(
    title=f"Historical Dispersion Percentage of {ticker} ({close_price_type})",
    xaxis_title="Date",
    yaxis_title="Dispersion (%)",
    legend_title="Legend",
    template="plotly_dark"
)

# Show the Plotly chart for dispersion percentage
st.plotly_chart(fig_dispersion)

# Seaborn/Matplotlib Histogram: Dispersion Percent without Gaussian fit
percentiles = [95, 75, 50, 25, 5]
percentile_values = np.percentile(data['Dispersion_Percent'].dropna(), percentiles)

plt.figure(figsize=(10, 6))
sns.histplot(data['Dispersion_Percent'].dropna(), color='blue', bins=30)

# Add percentile lines
for percentile, value in zip(percentiles, percentile_values):
    plt.axvline(value, color='red', linestyle='--')
    plt.text(value, plt.ylim()[1]*0.9, f'{percentile}th', color='red')

plt.title(f'Dispersion Percentage of {ticker} ({close_price_type}) Close Price from 21-day SMA')
plt.xlabel('Dispersion (%)')
plt.ylabel('Frequency')

# Rotate Y labels
plt.yticks(rotation=45)

st.pyplot(plt)
