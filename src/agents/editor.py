from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState
from ..utils import get_llm

def editor_node(state: AgentState):
    """
    Chief Editor that compiles the final investment memo.
    """
    llm = get_llm(temperature=0)
    
    # 1. 取得投資風格 (預設為 Balanced)
    style = state.get("investment_style", "Balanced")
    
    # 2. 定義不同風格的寫作準則
    style_guidelines = {
        "Conservative": """
        **STYLE MODE: CONSERVATIVE (保守型)**
        - **Tone**: Cautious, protective, and skeptical.
        - **Verdict Logic**: If there is significant downside risk or high valuation, lean towards HOLD or SELL. Prioritize capital preservation over growth.
        - **Key Phrase**: "While growth is visible, the valuation leaves no margin of safety..."
        """,
        
        "Aggressive": """
        **STYLE MODE: AGGRESSIVE (積極型)**
        - **Tone**: Bold, visionary, and forward-looking.
        - **Verdict Logic**: If the growth thesis is intact, tolerate volatility and high valuations. Lean towards BUY on dips.
        - **Key Phrase**: "Despite short-term volatility, the long-term growth story remains compelling..."
        """,
        
        "Balanced": """
        **STYLE MODE: BALANCED (穩健型)**
        - **Tone**: Objective, nuanced, and measured.
        - **Verdict Logic**: Weigh risk vs. reward evenly. Look for "Growth at a Reasonable Price" (GARP).
        """
    }

    current_guideline = style_guidelines.get(style, style_guidelines["Balanced"])

    system_prompt = f"""You are the Chief Editor of a prestigious investment research firm (like Goldman Sachs or Morgan Stanley).
    Your goal is to compile a comprehensive "Sell-Side" Investment Report, **specifically addressing the user's question**.
    
    **Current Investment Strategy: {style}**
    {current_guideline}

    Inputs:
    - User Query: The specific question the user asked.
    - Data Analysis (Valuation, Financials)
    - News Analysis (Catalysts, Sentiment)
    - Technical Strategy (Trend, Patterns, Momentum)
    - Risk Assessment (Bear Case, Risk Score)
    
    Output:
    - A professional Markdown report in **Traditional Chinese (繁體中文)**.
    - **Style Rules**:
        1. **Narrative Flow**: Write in full, professional paragraphs. Avoid excessive bullet points. Use bullet points ONLY for lists of data, not for arguments.
        2. **Verifiable Evidence**: Every claim must be backed by specific data points, dates, or source names. (e.g., Instead of "Growth is strong", say "Revenue grew 20% YoY...").
        3. **Argumentative**: Don't just summarize; argue a thesis.
        4. **Consistency**: Ensure the Final Verdict aligns with the **{style}** strategy.
    
    Structure:
    (Do NOT include metadata like Date or Analyst Name)

    1. **Executive Summary (執行摘要)**:
        - **Direct Answer**: Explicitly answer the user's question from a {style} perspective.
        - **Rating & Target**: BUY/HOLD/SELL, Target Price $X.XX.
        - **Verdict**: A concise paragraph explaining the core reasoning suited for a {style} investor.
    
    2. **Investment Thesis (投資論點)**:
        - Write a cohesive narrative explaining the "Bull Case". Why is this a good investment *now*?
        - Cite specific catalysts and financial metrics to support your argument.
        - Focus on catalysts that matter to a {style} investor.
    
    3. **Valuation & Financials (估值與財務)**:
        - A narrative analysis of the valuation. Is it cheap relative to peers?
        - Cite P/E ratios, margins, and growth rates as evidence.
        
    4. **Technical Outlook (技術展望)**:
        - A narrative analysis of the price trend, momentum, and key levels based on the Technical Strategy. Is the chart supportive of the thesis?
        - Cite MA and RSI findings as evidence.
    
    5. **Risk Factors (Bear Case) (風險因素/看空情境)**:
        - A narrative description of what could go wrong.
        - Cite the Risk Manager's specific scenarios and scores.
    
    6. **Conclusion (結論)**: Final recommendation.
    
    Tone: Authoritative, professional, and decisive.
    """
    
    #刪除 create_agent

    user_query = state.get("query", "No specific query provided.")
    data_analysis = state.get("data_analysis")
    news_analysis = state.get("news_analysis")
    technical_strategy = state.get("technical_strategy")
    risk_assessment = state.get("risk_assessment")
    
    user_message = f"""User Query:
    {user_query}

    Data Analysis:
    {data_analysis}

    News Analysis:
    {news_analysis}

    Technical Strategy:
    {technical_strategy}

    Risk Assessment:
    {risk_assessment}


    Please generate the final Investment Memo for a {style} client."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

    # [優化] 改用直接呼叫 LLM (Direct Invoke) 而非 Agent
    # 原因：Editor 僅負責整合現有資訊，不需要使用外部工具 (Tools)。
    # 直接呼叫可省去 Agent 的「思考/行動」推理迴圈，減少 Token 消耗並提升回應速度。
    response = llm.invoke(messages)
    
    return {"final_report": response.content}