import pytest
from unittest.mock import MagicMock, patch
from src.state import AgentState
from src.agents.data_analyst import data_analyst_node
from src.agents.news_analyst import news_analyst_node
from src.agents.risk_manager import risk_manager_node
from src.agents.editor import editor_node

# Mock the LLM to avoid actual API calls during testing
@pytest.fixture(autouse=True)
def mock_llm():
    with patch('src.agents.data_analyst.get_llm') as mock1, \
         patch('src.agents.news_analyst.get_llm') as mock2, \
         patch('src.agents.risk_manager.get_llm') as mock3, \
         patch('src.agents.editor.get_llm') as mock4:
        
        mock_instance = MagicMock()
        mock1.return_value = mock_instance
        mock2.return_value = mock_instance
        mock3.return_value = mock_instance
        mock4.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_create_agent():
    with patch('src.agents.data_analyst.create_agent') as mock:
        yield mock

@pytest.fixture
def mock_create_agent_news():
    with patch('src.agents.news_analyst.create_agent') as mock:
        yield mock

def test_data_analyst_node(mock_create_agent):
    # Setup mock agent
    mock_agent_executor = MagicMock()
    mock_create_agent.return_value = mock_agent_executor
    
    # Mock the invoke response
    mock_response = {
        "messages": [
            MagicMock(content="Analysis of AAPL: Undervalued based on P/E.")
        ]
    }
    mock_agent_executor.invoke.return_value = mock_response

    # Input state
    state = {
        "tickers": ["AAPL"],
        "query": "Is AAPL undervalued?"
    }

    # Run the node
    result = data_analyst_node(state)

    # Verify
    assert "data_analysis" in result
    assert "Analysis of AAPL" in result["data_analysis"]
    mock_create_agent.assert_called_once()

def test_news_analyst_node(mock_create_agent_news):
    # Setup mock agent
    mock_agent_executor = MagicMock()
    mock_create_agent_news.return_value = mock_agent_executor
    
    # Mock the invoke response
    mock_response = {
        "messages": [
            MagicMock(content="News for AAPL: Positive sentiment due to new product launch.")
        ]
    }
    mock_agent_executor.invoke.return_value = mock_response

    # Input state
    state = {
        "tickers": ["AAPL"],
        "query": "Any recent news?"
    }

    # Run the node
    result = news_analyst_node(state)

    # Verify
    assert "news_analysis" in result
    assert "News for AAPL" in result["news_analysis"]
    mock_create_agent_news.assert_called_once()

@pytest.fixture
def mock_create_agent_risk():
    with patch('src.agents.risk_manager.create_agent') as mock:
        yield mock

@pytest.fixture
def mock_create_agent_editor():
    with patch('src.agents.editor.create_agent') as mock:
        yield mock

def test_risk_manager_node(mock_create_agent_risk):
    # Setup mock agent
    mock_agent_executor = MagicMock()
    mock_create_agent_risk.return_value = mock_agent_executor
    
    # Mock the invoke response
    mock_response = {
        "messages": [
            MagicMock(content="Risk Assessment: Moderate risk.")
        ]
    }
    mock_agent_executor.invoke.return_value = mock_response
    
    state = {
        "query": "Risks?",
        "data_analysis": "Data...",
        "news_analysis": "News..."
    }
    
    result = risk_manager_node(state)
    
    assert "risk_assessment" in result
    assert "Risk Assessment" in result["risk_assessment"]
    mock_create_agent_risk.assert_called_once()

def test_editor_node(mock_create_agent_editor):
    # Setup mock agent
    mock_agent_executor = MagicMock()
    mock_create_agent_editor.return_value = mock_agent_executor
    
    # Mock the invoke response
    mock_response = {
        "messages": [
            MagicMock(content="Final Report: Buy AAPL.")
        ]
    }
    mock_agent_executor.invoke.return_value = mock_response
    
    state = {
        "query": "Report?",
        "data_analysis": "Data...",
        "news_analysis": "News...",
        "risk_assessment": "Risks..."
    }
    
    result = editor_node(state)
    
    assert "final_report" in result
    assert "Final Report" in result["final_report"]
    mock_create_agent_editor.assert_called_once()
