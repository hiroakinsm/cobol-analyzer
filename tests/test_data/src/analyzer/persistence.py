from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
from .analysis_engine import AnalysisResult

logger = logging.getLogger(__name__)

class AnalysisPersistence:
    """解析結果の永続化を管理するクラス"""
    
    def __init__(self, pg_config: Dict[str, Any], mongo_config: Dict[str, Any]):
        self.pg_config = pg_config
        self.mongo_config = mongo_config
        self.pg_pool = None
        self.mongo_client = None

    async def initialize(self):
        """データベース接続の初期化"""
        try:
            # PostgreSQL接続プールの作成
            self.pg_pool = await asyncpg.create_pool(**self.pg_config)
            
            # MongoDB接続の作成
            self.mongo_client = AsyncIOMotorClient(self.mongo_config['uri'])
            
            # 必要なテーブルとインデックスの作成
            await self._ensure_database_structure()
            
            logger.info("データベース接続を初期化しました")
        except Exception as e:
            logger.error(f"データベース初期化でエラー: {str(e)}")
            raise

    async def close(self):
        """データベース接続のクローズ"""
        try:
            if self.pg_pool:
                await self.pg_pool.close()
            if self.mongo_client:
                self.mongo_client.close()
            logger.info("データベース接続をクローズしました")
        except Exception as e:
            logger.error(f"データベースクローズでエラー: {str(e)}")
            raise

    async def save_analysis_result(self, result: AnalysisResult) -> bool:
        """解析結果の保存"""
        try:
            # 基本メトリクスをPostgreSQLに保存
            await self._save_metrics_to_postgres(result)
            
            # 詳細な解析結果をMongoDBに保存
            await self._save_details_to_mongodb(result)
            
            return True
        except Exception as e:
            logger.error(f"解析結果の保存でエラー: {str(e)}")
            return False

    async def _ensure_database_structure(self):
        """必要なデータベース構造の確保"""
        try:
            async with self.pg_pool.acquire() as conn:
                # メトリクステーブルの作成
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_metrics (
                        id SERIAL PRIMARY KEY,
                        source_id TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        total_lines INTEGER,
                        code_lines INTEGER,
                        comment_lines INTEGER,
                        cyclomatic_complexity INTEGER,
                        maintainability_index FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # インデックスの作成
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_metrics_source_id 
                    ON analysis_metrics(source_id)
                ''')
                
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_metrics_timestamp 
                    ON analysis_metrics(timestamp)
                ''')

            # MongoDBのインデックス作成
            db = self.mongo_client.cobol_analysis
            await db.analysis_details.create_index([("source_id", 1)])
            await db.analysis_details.create_index([("timestamp", -1)])
            
        except Exception as e:
            logger.error(f"データベース構造作成でエラー: {str(e)}")
            raise

    async def _save_metrics_to_postgres(self, result: AnalysisResult):
        """基本メトリクスをPostgreSQLに保存"""
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO analysis_metrics (
                        source_id, analysis_type, timestamp,
                        total_lines, code_lines, comment_lines,
                        cyclomatic_complexity, maintainability_index
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ''',
                    result.source_id,
                    result.analysis_type,
                    result.timestamp,
                    result.metrics.get('total_lines'),
                    result.metrics.get('code_lines'),
                    result.metrics.get('comment_lines'),
                    result.metrics.get('complexity_metrics', {}).get('cyclomatic_complexity'),
                    result.metrics.get('complexity_metrics', {}).get('maintainability_index')
                )
        except Exception as e:
            logger.error(f"PostgreSQLへの保存でエラー: {str(e)}")
            raise

    async def _save_details_to_mongodb(self, result: AnalysisResult):
        """詳細な解析結果をMongoDBに保存"""
        try:
            db = self.mongo_client.cobol_analysis
            
            # 解析結果ドキュメントの作成
            document = {
                'source_id': result.source_id,
                'analysis_type': result.analysis_type,
                'timestamp': result.timestamp,
                'metrics': result.metrics,
                'details': result.details,
                'created_at': datetime.now()
            }
            
            # MongoDBに保存
            await db.analysis_details.insert_one(document)
            
        except Exception as e:
            logger.error(f"MongoDBへの保存でエラー: {str(e)}")
            raise

    async def get_analysis_history(self, source_id: str) -> List[Dict[str, Any]]:
        """解析履歴の取得"""
        try:
            history = []
            
            # PostgreSQLからメトリクス履歴を取得
            async with self.pg_pool.acquire() as conn:
                metrics = await conn.fetch('''
                    SELECT * FROM analysis_metrics 
                    WHERE source_id = $1 
                    ORDER BY timestamp DESC
                ''', source_id)
            
            # MongoDBから詳細情報を取得
            db = self.mongo_client.cobol_analysis
            details = await db.analysis_details.find(
                {'source_id': source_id}
            ).sort('timestamp', -1).to_list(length=None)
            
            # 結果のマージ
            for metric in metrics:
                history_item = dict(metric)
                
                # 対応する詳細情報を検索
                detail = next(
                    (d for d in details if d['timestamp'] == metric['timestamp']),
                    None
                )
                
                if detail:
                    history_item['details'] = detail
                
                history.append(history_item)
            
            return history
        except Exception as e:
            logger.error(f"解析履歴の取得でエラー: {str(e)}")
            return [] 