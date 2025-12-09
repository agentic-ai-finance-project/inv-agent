from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from src.graph import create_graph
import json  
import os  

load_dotenv()

app = FastAPI(title="Investment Agent API")

class ResearchRequest(BaseModel):
    query: str

@app.post("/research")
async def research(request: ResearchRequest):
    try:
        graph = create_graph()
        # Initialize state with just the query, other fields will be populated by agents
        initial_state = {
            "query": request.query,
            "tickers": [],
            "data_analysis": None,
            "news_analysis": None,
            "risk_assessment": None,
            "final_report": None
        }
        result = graph.invoke(initial_state)
        # =========== 【請組員加入這段程式碼】 ===========
        # 將結果存成 JSON 檔案，方便前端 (UI) 開發者測試
        output_filename = "real_data_snapshot.json"
        
        # 使用 default=str 處理 datetime 等無法序列化的物件
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4, default=str)
            
        print(f"✅ 測試資料已匯出至: {os.path.abspath(output_filename)}")
        # ==============================================
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
