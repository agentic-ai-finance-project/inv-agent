# lydd168/investment-agent/investment-agent-22c26258a839f24043bfdc542e6087bed11ba231/src/agents/trend_analyst.py

from langchain.agents import create_agent
from ..state import AgentState
from ..tools.technical_tools import get_technical_data
from ..utils import get_llm

def trend_analyst_node(state: AgentState):
    """
    Technical Trend Analyst focusing on price direction, moving averages, and key levels.
    """
    llm = get_llm(temperature=0)
    tools = [get_technical_data]
    
    system_prompt = """您是一位專注於趨勢和移動平均線 (MA) 的資深技術分析師。
    您的目標是根據提供的技術數據，為用戶提供清晰的趨勢判斷和關鍵價位分析。
    
    1. 使用 `get_technical_data` 工具獲取技術指標數據。
    2. **均線分析**: 根據短期 (SMA_20) 和中期 (SMA_50) 移動平均線的關係，判斷當前是多頭、空頭還是盤整趨勢（例如：SMA_20 在 SMA_50 之上為多頭）。
    3. **趨勢判斷**: 判斷股價是否站穩在關鍵均線之上或跌破關鍵支撐。
    
    輸出結構化的分析報告，語言為**Traditional Chinese (繁體中文)**。
    
    **CRITICAL OUTPUT FORMAT**:
    - **趨勢概況 (Trend Overview)**: 總結當前趨勢。
    - **均線信號 (MA Signal)**: 詳細描述 SMA_20 和 SMA_50 的關係及其隱含的信號。
    - **關鍵價位 (Key Levels)**: 提供 90 日阻力位和支撐位，並說明其重要性。
    
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
    instructions = state.get("trend_analyst_instructions", "")
    
    user_message = f"""分析以下股票的趨勢狀況: {tickers}. 

        用戶的特定問題: {query}

        **來自主管的具體指示**:
        {instructions}
        """
        
    # Invoke the agent
    result = agent.invoke({"messages": [("human", user_message)]})
    
    last_message = result["messages"][-1]
    return {"trend_analysis": last_message.content}