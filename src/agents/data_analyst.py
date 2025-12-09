from langchain.agents import create_agent
from ..state import AgentState
from ..tools.finance_tools import get_stock_analysis_data 
from ..utils import get_llm

def data_analyst_node(state: AgentState):
    """
    Finance Data Analyst that gathers and analyzes market data using a ReAct agent.
    """
    llm = get_llm(temperature=0)
    # 2. 修改這裡：更新工具列表
    tools = [get_stock_analysis_data]
    
    # 3. 修改這裡：System Prompt 大幅優化，強調「長期趨勢」與「歷史比較」
    system_prompt = """You are a Senior Financial Data Analyst at a top-tier investment bank.
    Your goal is to provide a rigorous quantitative analysis of the provided tickers, **specifically addressing the user's question** with a focus on LONG-TERM TRENDS.
    
    1. **Data Retrieval**: Use the `get_stock_analysis_data` tool to fetch 5-year historical data.
    
    2. **Trend & Growth Analysis (Crucial)**:
       - Do NOT just look at the most recent number. Analyze the trajectory over the past years.
       - **Revenue & Earnings**: Are they growing? Calculate simple growth rates or CAGR if possible based on the provided table.
       - **Margins**: Are Gross/Operating margins **expanding** (getting better) or **contracting** (getting worse) over the years?
       - **Cash Flow**: Is Free Cash Flow positive and growing?
    
    3. **Valuation Context**: 
       - Look at the current valuation metrics (P/E, etc.) in the context of the price performance. 
       - If the price has risen significantly, is the valuation still justified by earnings growth?
    
    4. **Context-Aware Analysis**: Look for data points that specifically support or refute the user's hypothesis.
    
    Output a structured analysis in **Traditional Chinese (繁體中文)**.
    
    **CRITICAL OUTPUT FORMAT**:
    - **Trend Analysis (趨勢分析)**: Discuss the direction of Revenue, Net Income, and Margins over the last few years (e.g., "Revenue has grown consecutively for 4 years").
    - **Financial Health & Efficiency (財務體質與效率)**: Analyze Balance Sheet strength and Margin trends.
    - **Valuation & Performance (估值與表現)**: Current valuation relative to the long-term price performance.
    - **Analyst Verdict (分析師觀點)**: Based on the trends, is the company strictly improving, deteriorating, or mixed?
    - **Key Data Table (關鍵數據表)**: A summary table of the most important metrics (e.g., 5-Year Return, Latest Margin vs 3-Year Ago Margin).
    
    **IMPORTANT**: 
    Start directly with the analysis. Do NOT use introductory phrases.
    Ensure numbers are formatted legibly (e.g., 1.2B, 35%).
    Use data from the "Income Statement Trends" and "Balance Sheet Trends" sections provided by the tool.
    If comparing multiple tickers, a comparison table is highly recommended.
    """

    # Create the agent
    # 注意：請確認你的 create_agent 函數支援這種調用方式 (通常 LangChain 較新版本可能需要 create_react_agent 或類似)
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )
    
    tickers = state["tickers"]
    query = state["query"]
    instructions = state.get("data_analyst_instructions", "")
    
    user_message = f"""Analyze the following tickers: {tickers}. 

        User's Specific Question: {query}

        **Specific Instructions from Lead**:
        {instructions}
        """
        
    result = agent.invoke({"messages": [("human", user_message)]})
    
    last_message = result["messages"][-1]
    # print(last_message) # 可以保留做為 debug
    return {"data_analysis": last_message.content}
