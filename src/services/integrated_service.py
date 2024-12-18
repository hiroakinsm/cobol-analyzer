# src/services/integrated_service.py

from sqlalchemy.orm import Session
from config.mongodb import get_database
from models.analysis_logs import AnalysisLogs

db_mongo = get_database()

def get_cross_references_from_postgres(db: Session, log_id: int):
    # PostgreSQLからデータ取得
    log_entry = db.query(AnalysisLogs).filter(AnalysisLogs.id == log_id).first()
    if not log_entry:
        return None

    # MongoDBで関連データを検索
    cross_refs = db_mongo["cross_reference"].find({"log_id": log_id})
    return {"log_entry": log_entry, "cross_references": list(cross_refs)}

