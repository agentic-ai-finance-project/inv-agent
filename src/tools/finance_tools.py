from langchain_core.tools import tool
import yfinance as yf

@tool
def get_stock_data(ticker: str) -> str:
    """
    Retrieves stock data for a given ticker symbol using yfinance.
    Returns a summary of price history (last 1 month) and basic info.
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get history (extended to 1 year for better trend analysis)
        history = stock.history(period="1y")
        if history.empty:
            return f"No price data found for {ticker}."
            
        # Get info
        info = stock.info
        
        # 1. Valuation Metrics
        valuation = {
            "Market Cap": info.get("marketCap"),
            "Enterprise Value": info.get("enterpriseValue"),
            "Trailing P/E": info.get("trailingPE"),
            "Forward P/E": info.get("forwardPE"),
            "PEG Ratio": info.get("pegRatio"),
            "Price/Book": info.get("priceToBook"),
            "Price/Sales": info.get("priceToSalesTrailing12Months"),
            "EV/EBITDA": info.get("enterpriseToEbitda"),
        }
        
        # 2. Financial Health & Performance
        financials = {
            "Revenue Growth (YoY)": info.get("revenueGrowth"),
            "Earnings Growth (YoY)": info.get("earningsGrowth"),
            "Gross Margins": info.get("grossMargins"),
            "Operating Margins": info.get("operatingMargins"),
            "Return on Equity (ROE)": info.get("returnOnEquity"),
            "Total Cash": info.get("totalCash"),
            "Total Debt": info.get("totalDebt"),
            "Free Cash Flow": info.get("freeCashflow"),
        }
        
        # 3. Analyst Estimates & Targets
        estimates = {
            "Target Mean Price": info.get("targetMeanPrice"),
            "Target High": info.get("targetHighPrice"),
            "Target Low": info.get("targetLowPrice"),
            "Recommendation": info.get("recommendationKey"),
            "Number of Analyst Opinions": info.get("numberOfAnalystOpinions")
        }
        
        # 4. Price Performance Summary
        current_price = history.iloc[-1]["Close"]
        price_1mo_ago = history.iloc[-22]["Close"] if len(history) > 22 else history.iloc[0]["Close"]
        price_6mo_ago = history.iloc[-126]["Close"] if len(history) > 126 else history.iloc[0]["Close"]
        
        performance = {
            "Current Price": current_price,
            "52 Week High": info.get("fiftyTwoWeekHigh"),
            "52 Week Low": info.get("fiftyTwoWeekLow"),
            "1 Month Return": f"{((current_price - price_1mo_ago) / price_1mo_ago) * 100:.2f}%",
            "6 Month Return": f"{((current_price - price_6mo_ago) / price_6mo_ago) * 100:.2f}%",
            "YTD Return": f"{((current_price - history.iloc[0]['Close']) / history.iloc[0]['Close']) * 100:.2f}%" # Approx YTD if 1y period
        }
        
        return f"""
        Ticker: {ticker}
        
        --- VALUATION ---
        {valuation}
        
        --- FINANCIALS ---
        {financials}
        
        --- ANALYST ESTIMATES ---
        {estimates}
        
        --- PRICE PERFORMANCE ---
        {performance}
        
        --- RECENT PRICE DATA (Last 5 Days) ---
        {history.tail(5)[['Open', 'High', 'Low', 'Close', 'Volume']].to_string()}
        """
    except Exception as e:
        return f"Error fetching data for {ticker}: {str(e)}"
