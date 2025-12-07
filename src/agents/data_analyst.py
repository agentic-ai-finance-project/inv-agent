from langchain.agents import create_agent
from ..state import AgentState
from ..tools.finance_tools import get_stock_data
from ..utils import get_llm

def data_analyst_node(state: AgentState):
    """
    Finance Data Analyst that gathers and analyzes market data using a ReAct agent.
    """
    llm = get_llm(temperature=0)
    tools = [get_stock_data]
    
    system_prompt = """You are a Senior Financial Data Analyst at a top-tier investment bank.
    Your goal is to provide a rigorous quantitative analysis of the provided tickers, **specifically addressing the user's question**.
    
    1. Use the `get_stock_data` tool to fetch comprehensive data.
    2. **Context-Aware Analysis**: Look for data points that specifically support or refute the user's hypothesis (e.g., if they ask about "margins", focus on that).
    3. **Valuation Analysis**: Compare P/E, PEG, and EV/EBITDA to historical norms or general market benchmarks. Is the stock cheap or expensive?
    4. **Financial Health**: Analyze margins (Gross/Operating), growth rates (Revenue/Earnings), and balance sheet strength (Cash vs Debt).
    5. **Analyst Consensus**: Summarize the street's view (Target Prices, Recommendations).
    
    Output a structured analysis in **Traditional Chinese (繁體中文)**. Do not just list numbers; interpret them.
    
    **CRITICAL OUTPUT FORMAT**:
    - **Valuation Analysis (估值分析)**: Detailed breakdown of P/E, PEG, etc. with a verdict (Undervalued/Fair/Overvalued).
    - **Financial Health (財務健康)**: Analysis of Margins, ROE, and Balance Sheet strength.
    - **Growth Prospects (成長前景)**: Assessment of Revenue and Earnings growth rates.
    - **Analyst Consensus (分析師共識)**: Summary of target prices and buy/sell recommendations.
    - **Key Metrics Summary (關鍵指標摘要)**: A clear table or bulleted list of the most critical numbers (e.g., P/E, EPS, Revenue Growth).
    
    **IMPORTANT**: 
    Start directly with the analysis. Do NOT use introductory phrases.
    Ensure numbers are formatted legibly (e.g., 1.2B, 35%).
    If comparing multiple tickers, a comparison table is highly recommended.
    """
    
    # Create the agent
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
        
    # Invoke the agent
    # The agent expects a list of messages. We pass the task as a human message.
    result = agent.invoke({"messages": [("human", user_message)]})
    
    # The result contains the full state of the agent, including messages.
    # The last message should be the AI's final response.
    last_message = result["messages"][-1]
    print(last_message) 
    return {"data_analysis": last_message.content}
