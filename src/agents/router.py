# lydd168/investment-agent/investment-agent-22c26258a839f24043bfdc542e6087bed11ba231/src/agents/router.py

from typing import List
from langchain.agents import create_agent
from langchain_core.tools import tool
from ..state import AgentState
from ..utils import get_llm

@tool
def submit_routing_instructions(tickers: List[str], data_analyst_instructions: str, news_analyst_instructions: str, trend_analyst_instructions: str, pattern_analyst_instructions: str, indicator_analyst_instructions: str):
    """
    Submit the extracted tickers and specific instructions for the Data Analyst, News Analyst, Trend Analyst, Pattern Analyst, and Indicator Analyst.
    
    Args:
        tickers: List of stock tickers found in the query.
        data_analyst_instructions: Specific instructions for the Data Analyst (financials, valuation).
        news_analyst_instructions: Specific instructions for the News Analyst (news, sentiment, events).
        trend_analyst_instructions: Specific instructions for the Trend Analyst (MA, trend lines, direction).
        pattern_analyst_instructions: Specific instructions for the Pattern Analyst (candlestick and chart patterns).
        indicator_analyst_instructions: Specific instructions for the Indicator Analyst (RSI, MACD, Stochastic).
    """
    return "Instructions submitted."

def router_node(state: AgentState):
    """
    Router agent that extracts tickers and generates specific instructions for analysts.
    """
    llm = get_llm(temperature=0)
    
    system_prompt = """You are a Senior Financial Research Lead.
    您的工作是透過分析用戶的查詢並分配任務來協調研究流程。
    
    1. **分析用戶查詢**: 了解核心問題、假設或關注點。
    2. **提取股票代碼**: 識別所有提及或暗示的股票代碼。
    3. **分配給數據分析師**: 為數據分析師創建具體指令。
       - 應該尋找哪些具體的財務指標？（例如: 「如果用戶詢問盈利能力，請檢查毛利率。」）
       - 哪些估值倍數是相關的？
    4. **分配給新聞分析師**: 為新聞分析師創建具體指令。
       - 應搜索哪些具體的關鍵詞或主題？（例如: 「如果用戶詢問延誤，請搜索『供應鏈問題』。」）
       - 哪些情緒或事件最重要？
    5. **分配給趨勢分析師**: 創建具體指令，著重於移動平均線、價格方向和時間框架（例如: 「分析 20 日和 50 日移動平均線之間的關係。」）。
    6. **分配給型態分析師**: 創建具體指令，著重於 K 線或圖表型態（例如: 「尋找頭肩底或旗形型態。」）。
    7. **分配給指標分析師**: 創建具體指令，著重於動能（RSI, MACD）和波動性指標（例如: 「使用 14 週期 RSI 評估動能。」）。
       
    **目標**: 不要只傳遞一般的查詢。將用戶的意圖轉化為精確、可執行的技術指令。
    
    您**必須**調用 `submit_routing_instructions` 工具來輸出您的決策。
    """
    
    # Create the agent
    agent = create_agent(
        model=llm,
        tools=[submit_routing_instructions],
        system_prompt=system_prompt
    )
    
    # Invoke the agent
    result = agent.invoke({"messages": [("human", state["query"])]})
    
    # Extract the tool call from the last message (or the one before if the last is a tool message)
    messages = result["messages"]
    tool_call = None
    
    # Iterate backwards to find the tool call
    for msg in reversed(messages):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_call = msg.tool_calls[0]
            break
            
    if tool_call and tool_call["name"] == "submit_routing_instructions":
        args = tool_call["args"]
        return {
            "tickers": args.get("tickers", []),
            "data_analyst_instructions": args.get("data_analyst_instructions", ""),
            "news_analyst_instructions": args.get("news_analyst_instructions", ""),
            "trend_analyst_instructions": args.get("trend_analyst_instructions", ""),
            "pattern_analyst_instructions": args.get("pattern_analyst_instructions", ""),
            "indicator_analyst_instructions": args.get("indicator_analyst_instructions", "")
        }
    
    # Fallback if no tool call (shouldn't happen with good LLM)
    default_instruction = state["query"]
    return {
        "tickers": [], 
        "data_analyst_instructions": default_instruction, 
        "news_analyst_instructions": default_instruction,
        "trend_analyst_instructions": default_instruction,
        "pattern_analyst_instructions": default_instruction,
        "indicator_analyst_instructions": default_instruction
    }