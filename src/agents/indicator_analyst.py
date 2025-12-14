# lydd168/investment-agent/investment-agent-22c26258a839f24043bfdc542e6087bed11ba231/src/agents/indicator_analyst.py

from langchain.agents import create_agent
from ..state import AgentState
from ..tools.technical_tools import get_technical_data
from ..utils import get_llm

def indicator_analyst_node(state: AgentState):
    """
    Technical Indicator Analyst focusing on momentum and overbought/oversold conditions (e.g., RSI).
    """
    llm = get_llm(temperature=0)
    tools = [get_technical_data]
    
    system_prompt = """You are an analyst specializing in Quantitative Technical Indicators. (您是一位專注於量化技術指標的分析師。)
    Your goal is to provide a comprehensive momentum assessment, identify overbought/oversold conditions, and check for indicator divergence based on the technical data provided.
    
    1. Use the `get_technical_data` tool to retrieve indicator data for **RSI (14)** and **Momentum Index (MTM 10)**.
    2. **Momentum Assessment (動能評估 using MTM)**: MTM > 0 indicates strong upward momentum; MTM < 0 indicates strong downward momentum. Based on the value change of MTM and its relationship to the zero axis, determine if the current market momentum is strong, exhausted, or neutral.
    3. **Overbought/Oversold Check (超買/超賣判斷 using RSI)**: Determine if the RSI (14) is in the overbought (>70) or oversold (<30) zone, and explain its implication for short-term prices.
    4. **Integrated Judgment (綜合判斷)**: Combine the signals from both MTM and RSI to provide an overall conclusion on market momentum.
    
    Output a structured analysis report in **Traditional Chinese (繁體中文)**.
    
    **CRITICAL OUTPUT FORMAT**:
    - **Momentum Assessment (動能評估)**: This is your primary momentum judgment. You **MUST** clearly state the MTM (10) value and its significance for market momentum (e.g., MTM is +1.78, showing slight upward momentum), and provide an overall momentum conclusion.
    - **RSI Signal (RSI 訊號)**: Specific RSI value and its overbought/oversold level (e.g., 41.72, in the neutral zone).
    - **Divergence Check (指標背離)**: Briefly summarize if any indicator (RSI or MTM) shows divergence from the price action.
    
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
    instructions = state.get("indicator_analyst_instructions", "")
    
    user_message = f"""分析以下股票的技術指標狀況: {tickers}. 

        用戶的特定問題: {query}

        **來自主管的具體指示**:
        {instructions}
        """
        
    # Invoke the agent
    result = agent.invoke({"messages": [("human", user_message)]})
    
    last_message = result["messages"][-1]
    return {"indicator_analysis": last_message.content}