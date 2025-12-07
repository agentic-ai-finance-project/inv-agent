# lydd168/investment-agent/investment-agent-22c26258a839f24043bfdc542e6087bed11ba231/src/api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from src.graph import create_graph

load_dotenv()

app = FastAPI(title="Investment Agent API")

class ResearchRequest(BaseModel):
    query: str

@app.post("/research")
async def research(request: ResearchRequest):
    try:
        graph = create_graph()
        # Initialize state with all fields required by the new architecture
        initial_state = {
            "query": request.query,
            "tickers": [],
            "data_analyst_instructions": None,
            "news_analyst_instructions": None,
            "trend_analyst_instructions": None,
            "pattern_analyst_instructions": None,
            "indicator_analyst_instructions": None,
            "data_analysis": None,
            "news_analysis": None,
            "trend_analysis": None,
            "pattern_analysis": None,
            "indicator_analysis": None,
            "technical_strategy": None,
            "risk_assessment": None,
            "final_report": None
        }
        result = graph.invoke(initial_state)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
