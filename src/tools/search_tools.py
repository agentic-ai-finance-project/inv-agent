from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults

@tool
def search_news(query: str) -> str:
    """
    Searches for news about a company using Yahoo Finance.
    Input should be a stock ticker symbol (e.g., 'TSM', 'NVDA', '2330.TW').
    """
    # Set User-Agent to avoid 403 errors from Yahoo Finance
    import os
    import yfinance as yf
    os.environ["USER_AGENT"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    try:
        print(f"DEBUG: Searching Yahoo Finance for '{query}'")
        ticker = yf.Ticker(query)
        news = ticker.news
        
        # Format the results for the LLM
        formatted_results = ""
        if news:
            for item in news:
                if not item:
                    continue
                # Handle nested content structure if present
                # Use try-except for safety if item is not a dict
                try:
                    content = item.get('content', item)
                except AttributeError:
                    print(f"DEBUG: Item is not a dict: {item}")
                    continue
                    
                if content is None:
                    content = item
                
                title = content.get('title', 'No Title')
                
                # Link might be in clickThroughUrl or link
                link = content.get('link')
                if not link and 'clickThroughUrl' in content:
                    click_through = content['clickThroughUrl']
                    if click_through:
                        link = click_through.get('url')
                if not link:
                    link = 'No Link'
                    
                summary = content.get('summary', 'No Summary')
                
                formatted_results += f"Title: {title}\nLink: {link}\nSummary: {summary}\n---\n"
        else:
            formatted_results = "No news found."
            
        print(f"DEBUG: Found {len(formatted_results)} characters of results.")
        return formatted_results
    except Exception as e:
        print(f"DEBUG: Error in search_news: {e}")
        return f"Error searching news for {query}: {str(e)}"

@tool
def web_search(query: str) -> str:
    """
    Performs a general web search using DuckDuckGo.
    Use this for specific questions, market sentiment, or when company-specific news is insufficient.
    Input should be a search query string (e.g., 'NVDA supply chain issues', 'TSM vs Intel 3nm').
    """
    try:
        print(f"DEBUG: Performing web search for '{query}'")
        search = DuckDuckGoSearchResults(backend="news")
        results = search.run(query)
        return results
    except Exception as e:
        print(f"DEBUG: Error in web_search: {e}")
        return f"Error performing web search for {query}: {str(e)}"
