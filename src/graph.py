# lydd168/investment-agent/investment-agent-22c26258a839f24043bfdc542e6087bed11ba231/src/graph.py

from langgraph.graph import StateGraph, END
from .state import AgentState
from .agents.router import router_node
from .agents.data_analyst import data_analyst_node
from .agents.news_analyst import news_analyst_node
from .agents.risk_manager import risk_manager_node
from .agents.editor import editor_node
from .agents.trend_analyst import trend_analyst_node
from .agents.pattern_analyst import pattern_analyst_node
from .agents.indicator_analyst import indicator_analyst_node
from .agents.technical_strategist import technical_strategist_node

def create_graph():
    """
    Creates the Multi-Agent Investment Research Graph.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("data_analyst", data_analyst_node)
    workflow.add_node("news_analyst", news_analyst_node)
    workflow.add_node("trend_analyst", trend_analyst_node)
    workflow.add_node("pattern_analyst", pattern_analyst_node)
    workflow.add_node("indicator_analyst", indicator_analyst_node)
    workflow.add_node("technical_strategist", technical_strategist_node)
    workflow.add_node("risk_manager", risk_manager_node)
    workflow.add_node("editor", editor_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Add edges
    # Router -> All Analysts (Parallel Fan-Out)
    workflow.add_edge("router", "data_analyst")
    workflow.add_edge("router", "news_analyst")
    workflow.add_edge("router", "trend_analyst")
    workflow.add_edge("router", "pattern_analyst")
    workflow.add_edge("router", "indicator_analyst")

    # Technical Analysts -> Technical Strategist (Join)
    workflow.add_edge("trend_analyst", "technical_strategist")
    workflow.add_edge("pattern_analyst", "technical_strategist")
    workflow.add_edge("indicator_analyst", "technical_strategist")
    
    # Parallel Branches Join into Risk Manager
    # Risk Manager waits for Data Analyst, News Analyst, AND Technical Strategist
    workflow.add_edge("data_analyst", "risk_manager")
    workflow.add_edge("news_analyst", "risk_manager")
    workflow.add_edge("technical_strategist", "risk_manager")

    # Risk Manager -> Editor
    workflow.add_edge("risk_manager", "editor")

    # Editor -> End
    workflow.add_edge("editor", END)

    return workflow.compile()