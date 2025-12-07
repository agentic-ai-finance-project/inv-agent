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
    
    system_prompt = """您是一位專注於量化技術指標的分析師。
    您的目標是根據提供的技術數據，評估市場動能和超買/超賣狀況。
    
    1. 使用 `get_technical_data` 工具獲取 RSI 等指標數據。
    2. **RSI 分析**: 判斷 RSI (14) 是否處於超買 (>70) 或超賣 (<30) 區域，並說明其對短線價格的暗示。
    3. **動能判斷**: 根據指標的數值變化，判斷目前市場是處於強勢動能還是動能衰竭。
    
    輸出結構化的分析報告，語言為**Traditional Chinese (繁體中文)**。
    
    **CRITICAL OUTPUT FORMAT**:
    - **動能評估 (Momentum Assessment)**: 總結市場動能狀況。
    - **RSI 訊號 (RSI Signal)**: 具體 RSI 數值及其超買/超賣等級（例如：75.2，高位超買）。
    - **指標背離 (Divergence Check)**: 簡述是否有指標與價格走勢出現背離。
    
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