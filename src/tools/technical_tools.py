from langchain_core.tools import tool
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_rsi(df, window=14):
    """Calculate Relative Strength Index (RSI)"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs)).replace([np.inf, -np.inf], np.nan).fillna(100) 
    return rsi

@tool
def get_technical_data(ticker: str) -> str:
    """
    Retrieves and calculates all available technical indicators (MA_20, MA_50, RSI_14, key levels) 
    for the last 6 months for the given stock ticker.
    Input should be a stock ticker symbol (e.g., 'TSM', 'NVDA').
    """
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="6mo", interval="1d")
        
        if history.empty:
            return f"No historical price data found for {ticker} for technical analysis."
            
        df = history.copy()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['RSI_14'] = calculate_rsi(df, window=14)
        
        # Key Levels (90-Day High/Low)
        recent_data = df['Close'].tail(90)
        resistance = recent_data.max()
        support = recent_data.min()
        
        latest = df.iloc[-1]
        
        output = f"""
        TECHNICAL DATA for {ticker}:
        --- Latest Metrics ---
        Close: {latest['Close']:.2f}
        SMA_20: {latest['SMA_20']:.2f}
        SMA_50: {latest['SMA_50']:.2f}
        RSI_14: {latest['RSI_14']:.2f}
        
        --- Key Price Levels (90-Day) ---
        Resistance: {resistance:.2f}
        Support: {support:.2f}
        
        --- Price History (Last 5 Days) ---
        {df['Close'].tail(5).to_string()}
        """
        return output
    except Exception as e:
        return f"Error fetching technical data for {ticker}: {str(e)}"