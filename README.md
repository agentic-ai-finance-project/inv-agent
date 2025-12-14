# 🤖 Multi-Agent Investment Research Assistant

**A professional, agentic AI system for comprehensive investment analysis.**

Built with the latest **LangChain v1.0+** and **LangGraph v1.0+**, this assistant orchestrates a team of specialized AI agents to perform deep-dive research, analyze financial data, synthesize news sentiment, conduct technical analysis, and assess risks—delivering a professional-grade investment memo in **Traditional Chinese (繁體中文)**.

---

## 🚀 Features

-   **Multi-Agent Architecture**: Leverages a supervisor-worker pattern with specialized roles (Router, Data Analyst, News Analyst, Technical Analysts, Risk Manager, Chief Editor).
-   **Traditional Chinese Output**: All reports and analysis are generated in Traditional Chinese (繁體中文) for local context.
-   **Structured Reports**: Agents produce highly structured outputs (Valuation, Financial Health, Market Debate, Catalysts, Technical Outlook) rather than generic summaries.
-   **Real-time Data**: Fetches live market data using `yfinance`.
-   **News Analysis**: Searches and summarizes recent news using `duckduckgo-search`.
-   **Technical Analysis**: Comprehensive technical analysis including trend analysis, pattern recognition, and technical indicators (RSI, MTM, Moving Averages).
-   **Risk Assessment**: Dedicated agent for identifying downside risks, volatility, and "bear cases".
-   **Modern Tech Stack**: Built on the latest LangChain and LangGraph APIs (v1.0+), using `uv` for lightning-fast package management.

## 📸 Screenshots

| Input Interface | Market Dashboard | Investment Report |
| :---: | :---: | :---: |
| ![Input Interface](assets/input_interface.png) | ![Market Dashboard](assets/market_dashboard.png) | ![Investment Report](assets/investment_report.png) |

## 📊 Workflow

```mermaid
graph TD
    start([Start]) --> router[Router]
    router --> data_analyst[Finance Data Analyst]
    router --> news_analyst[Finance News Analyst]
    router --> trend_analyst[Trend Analyst]
    router --> pattern_analyst[Pattern Analyst]
    router --> indicator_analyst[Indicator Analyst]
    trend_analyst --> technical_strategist[Technical Strategist]
    pattern_analyst --> technical_strategist
    indicator_analyst --> technical_strategist
    data_analyst --> risk_manager[Risk Manager]
    news_analyst --> risk_manager
    technical_strategist --> risk_manager
    risk_manager --> editor[Chief Editor]
    editor --> final([End])
```

## 🤖 Agent Roles

1.  **Router**: Analyzes your query to identify stock tickers and user intent.
2.  **Finance Data Analyst**: Performs rigorous quantitative analysis:
    -   **Valuation**: P/E, PEG, EV/EBITDA, DCF hints.
    -   **Financial Health**: Margins, ROE, Balance Sheet strength.
    -   **Growth**: Revenue and Earnings growth trajectories.
3.  **Finance News Analyst**: Scours the web for qualitative insights:
    -   **Market Debate**: Bull vs. Bear arguments.
    -   **Catalysts**: Upcoming product launches, earnings, or regulatory events.
    -   **Sentiment**: Market sentiment scoring.
4.  **Trend Analyst**: Analyzes price trends and moving averages to identify market direction.
5.  **Pattern Analyst**: Identifies technical chart patterns and price action signals.
6.  **Indicator Analyst**: Evaluates technical indicators like RSI and Momentum (MTM) for trading signals.
7.  **Technical Strategist**: Synthesizes all technical analysis into a cohesive technical outlook and trading recommendation.
8.  **Risk Manager**: Acts as the "Devil's Advocate", synthesizing data to flag potential downside risks, macro headwinds, and competitive threats.
9.  **Chief Editor**: Compiles all insights into a structured, narrative-driven Investment Memo, ensuring professional tone and clarity.

## 🛠️ Prerequisites

-   **Python 3.11+**
-   **[uv](https://github.com/astral-sh/uv)** (Fast Python package installer and resolver)
-   **OpenAI API Key**, **Google Gemini API Key**, or **Groq API Key**

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd agent_investment_sup
    ```

2.  **Install dependencies using `uv`**:
    ```bash
    uv sync
    ```
    This creates a virtual environment in `.venv`.

3.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```bash
    # OpenAI (Default)
    OPENAI_API_KEY=sk-...
    LLM_PROVIDER=openai
    LLM_MODEL=gpt-4o-mini

    # Google Gemini (Optional)
    # GOOGLE_API_KEY=AI...
    # LLM_PROVIDER=google
    # LLM_MODEL=gemini-1.5-pro

    # Groq (Optional)
    # GROQ_API_KEY=gsk_...
    # LLM_PROVIDER=groq
    # LLM_MODEL=llama-3.3-70b-versatile
    ```

## ⚙️ Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `openai`, `google`, or `groq` | `openai` |
| `LLM_MODEL` | Model name (e.g., `gpt-4o`, `gemini-1.5-pro`, `llama-3.3-70b-versatile`) | `gpt-4o-mini` (OpenAI) / `gemini-2.0-flash-exp` (Google) / `llama-3.3-70b-versatile` (Groq) |
| `OPENAI_API_KEY` | Required if using OpenAI | - |
| `GOOGLE_API_KEY` | Required if using Google | - |
| `GROQ_API_KEY` | Required if using Groq | - |

## 🏃‍♂️ Usage

Activate the virtual environment:
- **Mac/Linux**: `source .venv/bin/activate`
- **Windows**: `.venv\Scripts\activate`

### Method 1: Command Line Interface (CLI)
Run the assistant directly from the terminal:

```bash
# Analyze specific tickers
uv run python -m src.main "Analyze NVDA and AMD"

# Ask a general question
uv run python -m src.main "What are the risks of investing in TSLA right now?"
```

### Method 2: User Interface

#### Method 2.1: REST API
Run the backend API server for integration with other apps:

```bash
uv run uvicorn src.api:app --reload
```
API Docs: `http://localhost:8000/docs`

#### Method 2.2: Web UI (Streamlit)
For a rich, interactive experience with charts and formatted reports:

```bash
uv run streamlit run src/ui/app.py
```
Open your browser at `http://localhost:8501`.

## 🔧 Customization

-   **Modify System Prompts**: Edit `src/agents/*.py` to change how agents behave or format their output.
-   **Add New Tools**: Create new tool functions in `src/tools/` and register them in the agent definitions.
-   **Change Graph Logic**: Update `src/graph.py` to modify the workflow (e.g., add a "Human in the Loop" step).

## ❓ Troubleshooting

-   **`Address already in use`**: The port 8000 or 8501 is busy. Kill the existing process or specify a different port.
-   **`API Key not found`**: Ensure your `.env` file is correctly formatted and loaded.
-   **`Module not found`**: Make sure you are running commands with `uv run` or have activated the virtual environment.

## 📄 License

MIT
