# lydd168/investment-agent/investment-agent-22c26258a839f24043bfdc542e6087bed11ba231/src/agents/pattern_analyst.py

from langchain.agents import create_agent
from ..state import AgentState
from ..tools.technical_tools import get_technical_data
from ..utils import get_llm

def pattern_analyst_node(state: AgentState):
    """
    Technical Pattern Analyst focusing on chart patterns (e.g., consolidation, reversals).
    """
    llm = get_llm(temperature=0)
    tools = [get_technical_data]
    
    system_prompt = """You are a Technical Analyst specializing in Chart Patterns. (您是一位專注於圖表型態的技術分析師。)
    Your goal is to identify any potential price patterns based on the technical data and price action provided, and offer related trading implications.
    
    1. Use the `get_technical_data` tool to retrieve historical stock price data.
    2. **Pattern Identification (型態識別)**: Identify if any significant patterns (e.g., Head and Shoulders Bottom/Top, Double Bottom, Double Top, Triangle Consolidation, Box Consolidation) exist within the last 6 months.
    3. **Pattern Interpretation (型態解讀)**: If a pattern is identified, explain its bullish/bearish implication and the key breakout/breakdown levels.
    
    Output a structured analysis report in **Traditional Chinese (繁體中文)**.
    
    **CRITICAL OUTPUT FORMAT**:
    - **Identified Pattern (識別型態)**: State the pattern found. If no clear pattern is found, explicitly state that the price is in a no-obvious-pattern or consolidation phase.
    - **Pattern Implication (型態意義)**: Explain the trend direction typically suggested by this pattern.
    - **Breakout Levels (爆發點位)**: Note the key price levels that trigger buy/sell signals for the pattern.
    
    **IMPORTANT**: 
    Start directly with the analysis.
    """
    
    # Create the agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )
    
    tickers = state["tickers"]
    query = state["query"]
    instructions = state.get("pattern_analyst_instructions", "")
    
    user_message = f"""分析以下股票的型態狀況: {tickers}. 

        用戶的特定問題: {query}

        **來自主管的具體指示**:
        {instructions}
        """
        
    # Invoke the agent
    result = agent.invoke({"messages": [("human", user_message)]})
    
    last_message = result["messages"][-1]
    return {"pattern_analysis": last_message.content}