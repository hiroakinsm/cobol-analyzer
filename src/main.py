# src/main.py

from fastapi import FastAPI
from services.mongo_service import get_analysis_results, get_ast_collection

app = FastAPI()

# analysis_resultsからデータを取得
@app.get("/mongo/analysis_results/")
def fetch_analysis_results(limit: int = 10):
    results = get_analysis_results(limit=limit)
    return {"data": results}

# ast_collectionからデータを取得
@app.get("/mongo/ast_collection/")
def fetch_ast_collection(limit: int = 10):
    results = get_ast_collection({}, limit=limit)
    return {"data": results}
