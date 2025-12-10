from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from src.graph import create_graph
import json  
import os  

import pandas
load_dotenv()

app = FastAPI(title="Investment Agent API")

class ResearchRequest(BaseModel):
    query: str
    style: str = "Balanced"  # 新增風格參數，預設為穩健型

@app.post("/research")
async def research(request: ResearchRequest):
    try:
        graph = create_graph()
        # Initialize state with all fields required by the new architecture
        initial_state = {
            "query": request.query,
            "investment_style": request.style,  # <--- 關鍵修改：將參數傳入 State
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
