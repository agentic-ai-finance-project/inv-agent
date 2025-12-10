from typing import TypedDict, List, Optional, Annotated
import operator

class AgentState(TypedDict):
    query: str
    tickers: List[str]
    investment_style: Optional[str] # e.g., "growth", "value", "dividend"
    data_analyst_instructions: Optional[str]
    news_analyst_instructions: Optional[str]
    # NEW Technical Instructions
    trend_analyst_instructions: Optional[str]
    pattern_analyst_instructions: Optional[str]
    indicator_analyst_instructions: Optional[str]
    data_analysis: Optional[str]
    news_analysis: Optional[str]
    # NEW Technical Analysis Reports
    trend_analysis: Optional[str]
    pattern_analysis: Optional[str]
    indicator_analysis: Optional[str]
    technical_strategy: Optional[str]
    
    risk_assessment: Optional[str]
    final_report: Optional[str]
