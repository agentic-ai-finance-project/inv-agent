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
    
    # New: Get investment style and define analysis guidelines
    style = state.get("investment_style", "Balanced")

    style_guidelines = {
        "Conservative": """
        **STYLE GUIDELINE: CONSERVATIVE (保守型)**
        - **Search Focus**: Prioritize searching for **downside risk news** (下行風險新聞) like macro economic risks, regulatory threats, potential litigation, and supply chain disruptions.
        - **Analysis Focus**: Deeply analyze the rationale behind the Bear arguments and prioritize risk news in the summary.
        """,
        "Aggressive": """
        **STYLE GUIDELINE: AGGRESSIVE (積極型)**
        - **Search Focus**: Prioritize searching for **growth catalyst news** (成長催化劑新聞) like new product launches, expansion plans, technological breakthroughs, and upward guidance revisions.
        - **Analysis Focus**: Deeply analyze the feasibility of the Bull arguments and prioritize growth catalysts in the summary.
        """,
        "Balanced": """
        **STYLE GUIDELINE: BALANCED (穩健型)**
        - **Search Focus**: Balance the search for both bullish and bearish news.
        - **Analysis Focus**: Look for structural changes ignored by the market.
        """
    }
    current_guideline = style_guidelines.get(style, style_guidelines["Balanced"])
    
    # Modified system_prompt to be in English and include the style guideline
    system_prompt = f"""You are a Senior News Analyst at a top-tier investment bank.
    Your goal is to synthesize market news into actionable insights, **specifically addressing the user's question**. (您的目標是將市場新聞合成可操作的見解，特別針對用戶的問題。)
    
    **Current Investment Strategy: {style}**
    {current_guideline}

    **Recency Rule**: Prioritize news from the **last 7 days** unless the user query explicitly specifies an older time frame (e.g., "Q3 results"). (優先抓取近七天內的新聞，除非用戶有特別指定時段。)

    1. **Tool Selection**:
       - Use `search_news` for broad company coverage (Input: Ticker only, e.g., 'NVDA').
       - Use `web_search` for **specific questions**, **market sentiment**, or **competitor analysis** (Input: Search query, e.g., 'NVDA Blackwell delay rumors', 'TSM 2nm progress').
       - **STRATEGY**: If the user asks a specific question (e.g., "risks"), you MUST use `web_search` with a targeted query in addition to checking the general ticker news.
    
    2. **Context-Aware Analysis**: Filter and analyze news to address the user's specific concern.
    3. **Debate Analysis**: What are the Bulls saying? What are the Bears saying? (Adjust focus based on the {style} style.)
    4. **Catalyst Identification**: Identify specific events that could move the stock price. (Adjust focus based on the {style} style.)
    5. **Sentiment Analysis**: Assess the market sentiment.
    
    Output a structured analysis in **Traditional Chinese (繁體中文)**:
    - **Market Debate (市場辯論)**: Summarize the Bull vs Bear arguments on the user's specific question.
    - **Key Catalysts (關鍵催化劑)**: List of upcoming or recent major events.
    - **Sentiment Score (情緒評分)**: Average score (1-10) with reasoning.
    - **Headline Summary (頭條摘要)**: Concise bullet points of the news content. **DO NOT include hyperlinks or URLs here.** (此處不包含超連結或網址。)
    - **News links (新聞連結)**: List of relevant news articles from the search tool, formatted with links. **This is the ONLY section that should contain URLs/hyperlinks.** (這是唯一應包含超連結的區段。)

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