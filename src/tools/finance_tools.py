from langchain_core.tools import tool
import yfinance as yf
import pandas as pd

# 讓表格對齊中文
pd.set_option('display.unicode.east_asian_width', True)

@tool
def get_stock_analysis_data(ticker: str) -> str:
    """
    Retrieves comprehensive stock data for a given ticker.
    Includes Real-time valuation, Analyst estimates, and 5-year Financial trends.
    """
    try:
        stock = yf.Ticker(ticker)
        
        # ... (Part 1: Real-Time Snapshot 保持不變) ...
        info = stock.info
        
        def fmt_num(num):
            if isinstance(num, (int, float)):
                if abs(num) >= 1e12: return f"{num/1e12:.2f}T"
                if abs(num) >= 1e9: return f"{num/1e9:.2f}B"
                if abs(num) >= 1e6: return f"{num/1e6:.2f}M"
                return f"{num:.2f}"
            return num

        valuation = {
            "Market Cap": fmt_num(info.get("marketCap")),
            "Trailing P/E": fmt_num(info.get("trailingPE")),
            "Forward P/E": fmt_num(info.get("forwardPE")),
            "PEG Ratio": fmt_num(info.get("pegRatio")),
            "Price/Book": fmt_num(info.get("priceToBook")),
            "Dividend Yield": fmt_num(info.get("dividendYield")),
            "Current ROE": fmt_num(info.get("returnOnEquity")),
            "Current Op Margin": fmt_num(info.get("operatingMargins")) # 稍微縮短 key 名稱
        }

        estimates = {
            "Target Mean": info.get("targetMeanPrice"), # 縮短 key 名稱
            "Target High": info.get("targetHighPrice"),
            "Recommendation": info.get("recommendationKey"),
            "Num Analysts": info.get("numberOfAnalystOpinions")
        }

        # ... (Part 2: Long-Term Trends) ...
        history = stock.history(period="5y", interval="1mo")
        if history.empty:
            price_trend = "No price data."
        else:
            start_price = history.iloc[0]['Close']
            curr_price = history.iloc[-1]['Close']
            total_return = ((curr_price - start_price) / start_price) * 100
            
            price_trend = {
                "Period": "Last 5 Years",
                "Start": round(start_price, 2),
                "Current": round(curr_price, 2),
                "Return": f"{total_return:.2f}%",
                "High": round(history['High'].max(), 2),
                "Low": round(history['Low'].min(), 2)
            }

        # 2. Financial Statements Helper (改用 to_string + east_asian_width)
        def format_financials(df, key_metrics):
            if df is None or df.empty:
                return "Data not available"
            
            existing = [m for m in key_metrics if m in df.index]
            if not existing:
                return "Key metrics not found"
            
            selected = df.loc[existing]
            # 欄位轉為年份
            selected.columns = [col.strftime('%Y') if hasattr(col, 'strftime') else str(col) for col in selected.columns]
            
            # 數值格式化
            for col in selected.columns:
                selected[col] = selected[col].apply(lambda x: fmt_num(x) if isinstance(x, (int, float)) else x)
            
            # --- 這裡改用 to_string()，配合最上面的 pd.set_option，中文就會對齊了 ---
            return selected.to_string()

        # A. Income Statement
        income_metrics = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "Diluted EPS"]
        income_str = format_financials(stock.financials, income_metrics)

        # B. Balance Sheet
        balance_metrics = ["Stockholders Equity", "Total Assets", "Total Debt"]
        balance_str = format_financials(stock.balance_sheet, balance_metrics)

        return f"""
        REPORT FOR: {ticker}
        
        --- 1. VALUATION ---
        {valuation}
        
        --- 2. ANALYST ---
        {estimates}
        
        --- 3. PRICE (5y) ---
        {price_trend}
        
        --- 4. INCOME TRENDS ---
        {income_str}
        
        --- 5. BALANCE SHEET ---
        {balance_str}
        
        --- 6. RECENT DATA ---
        {history[['Close', 'Volume']].tail(5).to_string()}
        """

    except Exception as e:
        return f"Error: {str(e)}"
