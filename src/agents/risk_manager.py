from langchain.agents import create_agent
from ..state import AgentState
from ..utils import get_llm

def risk_manager_node(state: AgentState):
    """
    Risk Manager that assesses risks based on data and news analysis.
    """
    llm = get_llm(temperature=0)
    
    system_prompt = """You are a Chief Risk Officer at a major investment fund.
    Your job is to play "Devil's Advocate" and identify the downside risks that others might miss, **specifically regarding the user's question**.
    
    Input:
    - User Query: The specific question or hypothesis the user has.
    - Data Analysis (Valuation, Financials)
    - News Analysis (Catalysts, Sentiment)
    - **Technical Strategy (Technical Outlook)**: The combined view of chart trends, patterns, and indicators.
    
    Output in **Traditional Chinese (繁體中文)**:
    1. **Stress Test User's Hypothesis (壓力測試用戶假設)**: If the user is asking "Is X a bottleneck?", explore "What if X is NOT a bottleneck?" or "What if X gets worse?".
    2. **Bear Case Scenario (看空情境)**: Describe a specific scenario where the stock could drop 20%+. Highlight *Technical Breakdowns* (e.g., breaking major moving average or support) as a primary risk.
    3. **Risk Categorization (風險分類)**: Macro, Sector, Company.
    4. **Risk Score (風險評分)**: Assign a score (1-10) with justification.
    
    Be conservative. If the stock is "priced for perfection," highlight that as a major risk.
    
    **IMPORTANT**: Start directly with the analysis. Do NOT use introductory phrases like "As a Chief Risk Officer..." or "Here is my assessment...". Go straight to the first section.
    """
    
    # Create the agent
    agent = create_agent(
        model=llm,
        tools=[],
        system_prompt=system_prompt
    )
    
    user_query = state.get("query", "No specific query provided.")
    data_analysis = state.get("data_analysis", "No data analysis provided.")
    news_analysis = state.get("news_analysis", "No news analysis provided.")
    technical_strategy = state.get("technical_strategy", "No technical strategy provided.")
    
    user_message = f"""User Query:
{user_query}

Data Analysis:
{data_analysis}

News Analysis:
{news_analysis}

Technical Strategy:
{technical_strategy}

Please provide your risk assessment."""
    
    # Invoke the agent
    result = agent.invoke({"messages": [("human", user_message)]})
    
    # The result contains the full state of the agent, including messages.
    last_message = result["messages"][-1]
    
    return {"risk_assessment": last_message.content}
