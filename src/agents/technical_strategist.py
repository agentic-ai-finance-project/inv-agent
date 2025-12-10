# lydd168/investment-agent/investment-agent-22c26258a839f24043bfdc542e6087bed11ba231/src/agents/technical_strategist.py

from langchain.agents import create_agent
from ..state import AgentState
from ..utils import get_llm

def technical_strategist_node(state: AgentState):
    """
    Technical Strategist that synthesizes inputs from Trend, Pattern, and Indicator Analysts 
    to form a cohesive Technical Outlook and trading recommendation.
    """
    llm = get_llm(temperature=0)
    
    system_prompt = """您是一位資深技術策略師，負責將各項技術分析 (趨勢、型態、指標) 整合為一個連貫且具有行動力的交易觀點。
    您的目標是根據所有技術分析的結果，為用戶的投資決策提供一個清晰的技術總結。
    
    輸入包含：
    - Trend Analysis (趨勢分析)
    - Pattern Analysis (型態分析)
    - Indicator Analysis (指標分析)
    
    整合這些資訊，並回答以下關鍵問題：
    1. **整體技術評級**: 當前短線 (1週) 和中線 (1個月) 的技術評級是看漲 (Bullish)、看跌 (Bearish) 還是中性 (Neutral)?
    2. **交易策略**: 建議的交易策略是什麼？(例如：逢低買入、等待突破、觀望、減碼)。
    3. **技術總結**: 整理最一致和最矛盾的技術信號。
    
    輸出結構化的分析報告，語言為**Traditional Chinese (繁體中文)**。
    
    **CRITICAL OUTPUT FORMAT**:
    - **技術總結 (Technical Summary)**: 一個段落總結技術面是看漲還是看跌。
    - **短線技術評級 (Short-Term Rating)**: BULLISH / NEUTRAL / BEARISH，並附上主要理由。
    - **建議策略 (Recommended Strategy)**: 具體的交易行動建議。
    - **技術信號一致性 (Signal Consistency)**: 列出多頭和空頭信號。
    
    **IMPORTANT**: 
    開始時直接進入分析。
    """
    
    # Create the agent
    agent = create_agent(
        model=llm,
        tools=[],
        system_prompt=system_prompt
    )
    
    user_query = state.get("query", "No specific query provided.")
    trend_analysis = state.get("trend_analysis", "No trend analysis provided.")
    pattern_analysis = state.get("pattern_analysis", "No pattern analysis provided.")
    indicator_analysis = state.get("indicator_analysis", "No indicator analysis provided.")
    
    user_message = f"""User Query:
{user_query}

Trend Analysis:
{trend_analysis}

Pattern Analysis:
{pattern_analysis}

Indicator Analysis:
{indicator_analysis}

請根據上述輸入，產生一個技術策略總結報告。"""
    
    # Invoke the agent
    result = agent.invoke({"messages": [("human", user_message)]})
    
    last_message = result["messages"][-1]
    return {"technical_strategy": last_message.content}