from config.mongodb import get_database

# MongoDBデータベース取得
db = get_database()

# analysis_resultsの操作例
def get_analysis_results(limit: int = 10):
    return list(db["analysis_results"].find().limit(limit))

def insert_analysis_result(data: dict):
    return db["analysis_results"].insert_one(data).inserted_id

# ast_collectionの読み出し
def get_ast_collection(query: dict, limit: int = 10):
    return list(db["ast_collection"].find(query).limit(limit))
