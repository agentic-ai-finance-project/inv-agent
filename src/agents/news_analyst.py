from langchain.agents import create_agent
from ..state import AgentState
from ..tools.search_tools import search_news, web_search
from ..utils import get_llm

def news_analyst_node(state: AgentState):
    """
    Finance News Analyst that searches for and summarizes news using a ReAct agent.
    """
    llm = get_llm(temperature=0)
    tools = [search_news, web_search]
    
    system_prompt = """You are a Senior News Analyst at a top-tier investment bank.
    Your goal is to synthesize market news into actionable insights, **specifically addressing the user's question**.
    
    1. **Tool Selection**:
       - Use `search_news` for broad company coverage (Input: Ticker only, e.g., 'NVDA').
       - Use `web_search` for **specific questions**, **market sentiment**, or **competitor analysis** (Input: Search query, e.g., 'NVDA Blackwell delay rumors', 'TSM 2nm progress').
       - **STRATEGY**: If the user asks a specific question (e.g., "risks"), you MUST use `web_search` with a targeted query in addition to checking the general ticker news.
    
    2. **Context-Aware Analysis**: Filter and analyze news to address the user's specific concern.
    3. **Debate Analysis**: What are the Bulls saying? What are the Bears saying?
    4. **Catalyst Identification**: Identify specific events that could move the stock price.
    5. **Sentiment Analysis**: Assess the market sentiment.
    
    Output a structured analysis in **Traditional Chinese (繁體中文)**:
    - **Market Debate (市場辯論)**: Summarize the Bull vs Bear arguments on the user's specific question.
    - **Key Catalysts (關鍵催化劑)**: List of upcoming or recent major events.
    - **Sentiment Score (情緒評分)**: Average score (1-10) with reasoning.
    - **Headline Summary (頭條摘要)**: Concise bullet points with sources.
    - ** News links (新聞連結)**: List of relevant news articles from the search tool.

    Start directly with the analysis. Do NOT use introductory phrases.
    
    **CRITICAL OUTPUT FORMAT**:
    For the "**News links (新聞連結)**" section, you MUST use strict Markdown format: `[Title](URL)`.
    The `search_news` tool returns data in the format:
    `Title: ...`
    `Link: ...`
    `Summary: ...`
    
    **CRITICAL RULE FOR TOOL USE (MUST FOLLOW):**
    1. **NO INTERNAL MONOLOGUE**: Do NOT output thoughts, plans, or explanations before calling a tool.
    2. **DIRECT INVOCATION**: If you need to search, output the JSON tool call IMMEDIATELY as the very first thing.
    3. **SILENCE**: Do not say "I will now search for..." or "Let me check the news...". Just do it.
    
    You MUST extract the `Title` and `Link` exactly as provided.
    Example: `[Bloomberg: NVDA hits record high](https://www.bloomberg.com/news/...)`
    Do NOT just list the URL. Do NOT use HTML.
    """
    
    # Create the agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )
    
    
    tickers = state["tickers"]
    query = state["query"]
    instructions = state.get("news_analyst_instructions", "")
    
    user_message = f"""Find and analyze news for the following tickers: {tickers}. 

        User's Specific Question: {query}

        **Specific Instructions from Lead**:
        {instructions}
        """
    
    # Invoke the agent
    result = agent.invoke({"messages": [("human", user_message)]})
    
    # The result contains the full state of the agent, including messages.
    last_message = result["messages"][-1]
   #print(last_message) 
    return {"news_analysis": last_message.content}
