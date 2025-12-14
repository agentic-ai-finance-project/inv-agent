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
    
    # New: Get investment style and define rating rules
    style = state.get("investment_style", "Balanced")

    style_rules = {
        "Conservative": """
        **RATING RULES: CONSERVATIVE (保守型)**
        - **BUY Condition**: Must have all (Trend, Pattern, Indicator) signals **strongly Bullish**, and the price must be far from the 90-day resistance level.
        - **SELL Condition**: Consider SELL or HOLD if even one major signal is Bearish (e.g., breaking below a key MA), or if indicators show **Overbought** conditions.
        - **Recommendation Tendency**: Leans towards NEUTRAL or BEARISH, avoids chasing highs.
        """,
        "Aggressive": """
        **RATING RULES: AGGRESSIVE (積極型)**
        - **BUY Condition**: As long as the trend is clearly upward, a BUY recommendation is justified, even if indicators are temporarily overbought or a short-term consolidation pattern appears.
        - **SELL Condition**: Only consider SELL if the price breaks below the long-term trend line or a **decisive reversal pattern** emerges.
        - **Recommendation Tendency**: Leans towards BULLISH, provided there are no decisive bearish technical signals.
        """,
        "Balanced": """
        **RATING RULES: BALANCED (穩健型)**
        - **BUY/HOLD Condition**: At least two out of the three (Trend, Pattern, Indicator) signals must be Bullish, and indicator signals must not diverge from the price.
        """
    }
    current_rule = style_rules.get(style, style_rules["Balanced"])

    # Modified system_prompt to be in English and include the style rule
    system_prompt = f"""You are a Senior Technical Strategist, responsible for integrating various technical analyses (Trend, Pattern, Indicator) into a coherent and actionable trading view. (您是一位資深技術策略師，負責將各項技術分析整合為一個連貫且具有行動力的交易觀點。)
    Your goal is to provide a clear technical summary for the user's investment decision based on all technical analysis results.
    
    **Current Investment Strategy: {style}**
    {current_rule}

    Inputs include:
    - Trend Analysis (趨勢分析)
    - Pattern Analysis (型態分析)
    - Indicator Analysis (指標分析)
    
    Integrate this information and answer the following key questions:
    1. **Overall Technical Rating**: What is the short-term (1 week) and medium-term (1 month) technical rating: Bullish (看漲), Bearish (看跌), or Neutral (中性)? (**Must strictly adhere to the {style} rating rules**).
    2. **Trading Strategy**: What is the recommended trading strategy? (e.g., Buy on dips, Wait for breakout, Observe, Reduce position).
    3. **Technical Summary**: Organize the most consistent and most contradictory technical signals.
    
    Output a structured analysis report in **Traditional Chinese (繁體中文)**.
    
    **CRITICAL OUTPUT FORMAT**:
    - **Technical Summary (技術總結)**: A paragraph summarizing whether the technical outlook is bullish or bearish.
    - **Short-Term Technical Rating (短線技術評級)**: BULLISH / NEUTRAL / BEARISH, with main justifications.
    - **Recommended Strategy (建議策略)**: Specific trading action advice.
    - **Signal Consistency (技術信號一致性)**: List bullish and bearish signals.
    
    **IMPORTANT**: 
    Start directly with the analysis.
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