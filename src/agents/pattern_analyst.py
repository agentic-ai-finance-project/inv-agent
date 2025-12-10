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
    
    system_prompt = """您是一位專注於圖表型態的技術分析師。
    您的目標是根據提供的技術數據和價格走勢，識別任何潛在的價格型態，並提供相關的交易暗示。
    
    1. 使用 `get_technical_data` 工具獲取股價歷史數據。
    2. **型態識別**: 識別過去 6 個月內是否存在顯著的型態（例如：頭肩底/頂、W 底、M 頭、三角形收斂、箱型盤整）。
    3. **型態解讀**: 如果識別出型態，請說明其多空意義以及突破或跌破的關鍵點位。
    
    輸出結構化的分析報告，語言為**Traditional Chinese (繁體中文)**。
    
    **CRITICAL OUTPUT FORMAT**:
    - **識別型態 (Identified Pattern)**: 說明發現的型態。如果未發現，請明確說明處於無明顯型態或盤整階段。
    - **型態意義 (Pattern Implication)**: 說明此型態通常預示的趨勢方向。
    - **爆發點位 (Breakout Levels)**: 標註觸發型態買入/賣出信號的關鍵價格點位。
    
    **IMPORTANT**: 
    開始時直接進入分析。
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