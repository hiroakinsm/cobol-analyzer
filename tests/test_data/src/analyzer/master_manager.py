from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import logging
import json
import os
import shutil
import psutil
from pathlib import Path
import psycopg2
from psycopg2.extras import DictCursor, Json
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import uuid
import traceback
import subprocess
import time
from .rag_engine import RAGEngine  # RAGエンジンのインポート

logger = logging.getLogger(__name__)

@dataclass
class EnvironmentMaster:
    """環境マスタ情報"""
    env_id: str
    env_name: str
    os_type: str
    compiler_info: Dict[str, str]
    character_set: str
    file_system: str
    configurations: Dict[str, Any]

@dataclass
class SingleAnalysisMaster:
    """単一解析マスタ情報"""
    analysis_type: str
    target_elements: List[str]
    analysis_rules: Dict[str, Any]
    output_format: str
    thresholds: Dict[str, float]

@dataclass
class SummaryAnalysisMaster:
    """サマリ解析マスタ情報"""
    summary_type: str
    aggregation_rules: Dict[str, Any]
    grouping_keys: List[str]
    calculation_methods: Dict[str, str]
    report_format: str

@dataclass
class DashboardMaster:
    """ダッシュボードマスタ情報"""
    dashboard_id: str
    title: str
    layout: Dict[str, Any]
    components: List[Dict[str, Any]]
    refresh_interval: int
    access_control: Dict[str, List[str]]

@dataclass
class DocumentMaster:
    """ドキュメントマスタ情報"""
    doc_type: str
    template_path: str
    variables: Dict[str, str]
    format_rules: Dict[str, Any]
    output_settings: Dict[str, Any]

class MasterManager:
    """統合マスタ管理"""
    
    def __init__(self, master_dir: str = "masters", db_config: Dict[str, Any] = None):
        self._master_dir = Path(master_dir)
        self._env_masters: Dict[str, EnvironmentMaster] = {}
        self._single_analysis_masters: Dict[str, SingleAnalysisMaster] = {}
        self._summary_analysis_masters: Dict[str, SummaryAnalysisMaster] = {}
        self._dashboard_masters: Dict[str, DashboardMaster] = {}
        self._document_masters: Dict[str, DocumentMaster] = {}
        self._load_all_masters()
        
        # データベース接続設定
        self._db_config = db_config or {
            'postgresql': {
                'host': '172.16.0.13',
                'database': 'cobol_analysis_db',
                'user': 'cobana_admin',
                'password': 'your_password'
            },
            'mongodb': {
                'host': '172.16.0.17',
                'database': 'cobol_ast_db'
            }
        }
        
        # DB接続の初期化
        self._pg_conn = None
        self._mongo_client = None
        self._init_db_connections()

    def _load_all_masters(self):
        """全マスタの読み込み"""
        try:
            self._load_environment_masters()
            self._load_single_analysis_masters()
            self._load_summary_analysis_masters()
            self._load_dashboard_masters()
            self._load_document_masters()
        except Exception as e:
            logger.error(f"マスタ読み込みでエラー: {str(e)}")
            raise

    def _load_environment_masters(self):
        """環境マスタの読み込み"""
        env_file = self._master_dir / "environment" / "environment_master.json"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for env_data in data['environments']:
                    env = EnvironmentMaster(**env_data)
                    self._env_masters[env.env_id] = env

    def _load_single_analysis_masters(self):
        """単一解析マスタの読み込み"""
        analysis_file = self._master_dir / "analysis" / "single_analysis_master.json"
        if analysis_file.exists():
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for analysis_data in data['analysis_types']:
                    analysis = SingleAnalysisMaster(**analysis_data)
                    self._single_analysis_masters[analysis.analysis_type] = analysis

    def _load_summary_analysis_masters(self):
        """サマリ解析マスタの読み込み"""
        summary_file = self._master_dir / "analysis" / "summary_analysis_master.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for summary_data in data['summary_types']:
                    summary = SummaryAnalysisMaster(**summary_data)
                    self._summary_analysis_masters[summary.summary_type] = summary

    def _load_dashboard_masters(self):
        """ダッシュボードマスタの読み込み"""
        dashboard_file = self._master_dir / "dashboard" / "dashboard_master.json"
        if dashboard_file.exists():
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for dashboard_data in data['dashboards']:
                    dashboard = DashboardMaster(**dashboard_data)
                    self._dashboard_masters[dashboard.dashboard_id] = dashboard

    def _load_document_masters(self):
        """ドキュメントマスタの読み込み"""
        doc_file = self._master_dir / "document" / "document_master.json"
        if doc_file.exists():
            with open(doc_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for doc_data in data['document_types']:
                    doc = DocumentMaster(**doc_data)
                    self._document_masters[doc.doc_type] = doc

    # 各マスタの取得メソッド
    def get_environment(self, env_id: str) -> Optional[EnvironmentMaster]:
        return self._env_masters.get(env_id)

    def get_single_analysis(self, analysis_type: str) -> Optional[SingleAnalysisMaster]:
        return self._single_analysis_masters.get(analysis_type)

    def get_summary_analysis(self, summary_type: str) -> Optional[SummaryAnalysisMaster]:
        return self._summary_analysis_masters.get(summary_type)

    def get_dashboard(self, dashboard_id: str) -> Optional[DashboardMaster]:
        return self._dashboard_masters.get(dashboard_id)

    def get_document(self, doc_type: str) -> Optional[DocumentMaster]:
        return self._document_masters.get(doc_type)

    # マスタ情報の検証メソッド
    def validate_environment(self, env_id: str) -> Dict[str, Any]:
        """環境設定の検証"""
        env = self.get_environment(env_id)
        if not env:
            return {'valid': False, 'message': '環境定義が見つかりません'}
        
        # 検証ロジックの実装
        return {'valid': True, 'environment': env}

    def validate_analysis_config(self, analysis_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析設定の検証"""
        analysis = self.get_single_analysis(analysis_type)
        if not analysis:
            return {'valid': False, 'message': '解析定義が見つかりません'}
        
        # 検証ロジックの実装
        return {'valid': True, 'analysis': analysis}

    def _init_db_connections(self):
        """データベース接続の初期化"""
        try:
            # PostgreSQL接続
            self._pg_conn = psycopg2.connect(**self._db_config['postgresql'])
            
            # MongoDB接続
            self._mongo_client = MongoClient(self._db_config['mongodb']['host'])
            self._mongo_db = self._mongo_client[self._db_config['mongodb']['database']]
            
        except Exception as e:
            logger.error(f"データベース接続でエラー: {str(e)}")
            raise

    def create_analysis_task(self, source_path: str, analysis_config: Dict[str, Any], 
                           priority: int = 0) -> str:
        """解析タスクの作成"""
        try:
            task_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_tasks_partitioned (
                        task_id, source_id, task_type, status, priority,
                        source_path, analysis_config, created_by, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING task_id
                """, (
                    task_id,
                    str(uuid.uuid4()),  # source_id
                    'source_analysis',
                    'pending',
                    priority,
                    source_path,
                    psycopg2.extras.Json(analysis_config),
                    'system',
                    now,
                    now
                ))
                self._pg_conn.commit()
                
            return task_id
            
        except Exception as e:
            self._pg_conn.rollback()
            logger.error(f"解析タスク作成でエラー: {str(e)}")
            raise

    def store_analysis_result(self, task_id: str, source_id: str, 
                            analysis_type: str, ast_data: Dict[str, Any]) -> str:
        """解析結果の保存"""
        try:
            # MongoDBにAST情報を保存
            mongo_result = self._mongo_db.ast_collection.insert_one({
                'task_id': task_id,
                'source_id': source_id,
                'ast_type': analysis_type,
                'ast_data': ast_data,
                'created_at': datetime.now(timezone.utc)
            })
            
            # PostgreSQLに結果メタデータを保存
            result_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_results_partitioned (
                        result_id, task_id, source_id, analysis_type,
                        status, mongodb_collection, mongodb_document_id,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    result_id,
                    task_id,
                    source_id,
                    analysis_type,
                    'completed',
                    'ast_collection',
                    str(mongo_result.inserted_id),
                    now,
                    now
                ))
                self._pg_conn.commit()
                
            return result_id
            
        except Exception as e:
            self._pg_conn.rollback()
            logger.error(f"解析結果保存でエラー: {str(e)}")
            raise

    def get_analysis_results(self, source_id: str) -> List[Dict[str, Any]]:
        """解析結果の取得"""
        try:
            results: List[Dict[str, Any]] = []
            # 実装内容
            return results
        except Exception as e:
            logger.error(f"解析結果取得でエラー: {str(e)}")
            raise

    def store_ast(self, source_id: str, task_id: str, ast_type: str, 
                  ast_data: Dict[str, Any], source_mapping: Dict[str, Any]) -> str:
        """AST情報の保存"""
        try:
            ast_doc = {
                'source_id': source_id,
                'task_id': task_id,
                'ast_type': ast_type,
                'ast_version': '1.0',  # バージョン管理
                'created_at': datetime.now(timezone.utc),
                'ast_data': {
                    'root': ast_data,
                    'metadata': {
                        'generator': 'cobol-analyzer',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                },
                'source_mapping': source_mapping
            }
            
            result = self._mongo_db.ast_collection.insert_one(ast_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"AST保存でエラー: {str(e)}")
            raise

    def store_analysis_details(self, result_id: str, source_id: str, task_id: str,
                             analysis_type: str, details: Dict[str, Any], 
                             metrics: Dict[str, Any], issues: List[Dict[str, Any]]) -> str:
        """詳細な解析結果の保存"""
        try:
            result_doc = {
                'result_id': result_id,
                'source_id': source_id,
                'task_id': task_id,
                'analysis_type': analysis_type,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'details': details,
                'metrics': metrics,
                'issues': issues,
                'references': {
                    'ast_id': None,  # 関連するASTのID
                    'metrics_id': None  # 関連するメトリクスのID
                }
            }
            
            result = self._mongo_db.analysis_results.insert_one(result_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"解析結果詳細保存でエラー: {str(e)}")
            raise

    def store_metrics_data(self, source_id: str, task_id: str, metrics_type: str,
                          metrics_data: Dict[str, Any], trend_data: Dict[str, Any] = None) -> str:
        """メトリクスデータの保存"""
        try:
            metrics_doc = {
                'source_id': source_id,
                'task_id': task_id,
                'created_at': datetime.now(timezone.utc),
                'metrics_type': metrics_type,
                'metrics_data': metrics_data,
                'trend_data': trend_data or {},
                'analysis_details': {
                    'analyzer_version': '1.0',
                    'analysis_timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            result = self._mongo_db.metrics_data.insert_one(metrics_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"メトリクスデータ保存でエラー: {str(e)}")
            raise

    def store_document_data(self, task_id: str, document_type: str,
                          content: Dict[str, Any], formatting: Dict[str, Any]) -> str:
        """ドキュメント生成データの保存"""
        try:
            doc_data = {
                'task_id': task_id,
                'document_type': document_type,
                'created_at': datetime.now(timezone.utc),
                'content': content,
                'formatting': formatting,
                'references': {
                    'analysis_results': [],  # 関連する解析結果のID
                    'metrics_data': []  # 関連するメトリクスデータのID
                }
            }
            
            result = self._mongo_db.document_data.insert_one(doc_data)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"ドキュメントデータ保存でエラー: {str(e)}")
            raise

    def store_cross_reference(self, task_id: str, reference_type: str,
                            references: Dict[str, Any], dependencies: Dict[str, Any],
                            impact_analysis: Dict[str, Any]) -> str:
        """クロスリファレンス情報の保存"""
        try:
            xref_doc = {
                'task_id': task_id,
                'reference_type': reference_type,
                'created_at': datetime.now(timezone.utc),
                'references': references,
                'dependencies': dependencies,
                'impact_analysis': impact_analysis
            }
            
            result = self._mongo_db.cross_references.insert_one(xref_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"クロスリファレンス保存でエラー: {str(e)}")
            raise

    def get_ast_by_source(self, source_id: str, ast_type: str = None) -> List[Dict[str, Any]]:
        """ソースIDに基づくAST情報の取得"""
        try:
            query = {'source_id': source_id}
            if ast_type:
                query['ast_type'] = ast_type
                
            return list(self._mongo_db.ast_collection.find(query))
            
        except Exception as e:
            logger.error(f"AST取得でエラー: {str(e)}")
            raise

    def get_metrics_history(self, source_id: str, metrics_type: str) -> List[Dict[str, Any]]:
        """メトリクスの履歴データ取得"""
        try:
            return list(self._mongo_db.metrics_data.find({
                'source_id': source_id,
                'metrics_type': metrics_type
            }).sort('created_at', -1))
            
        except Exception as e:
            logger.error(f"メトリクス履歴取得でエラー: {str(e)}")
            raise

    def create_source_entry(self, task_id: str, file_path: str, file_type: str,
                          file_hash: str, file_size: int, encoding: str = None,
                          line_count: int = None, metadata: Dict[str, Any] = None) -> str:
        """解析対象ソースファイルのエントリ作成"""
        try:
            source_id = str(uuid.uuid4())
            
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_sources (
                        source_id, task_id, file_path, file_type, file_hash,
                        file_size, encoding, line_count, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING source_id
                """, (
                    source_id,
                    task_id,
                    file_path,
                    file_type,
                    file_hash,
                    file_size,
                    encoding,
                    line_count,
                    psycopg2.extras.Json(metadata) if metadata else None
                ))
                self._pg_conn.commit()
                
            return source_id
            
        except Exception as e:
            self._pg_conn.rollback()
            logger.error(f"ソースエントリ作成でエラー: {str(e)}")
            raise

    def log_analysis_event(self, task_id: str, source_id: str, level: str,
                          component: str, message: str, details: Dict[str, Any] = None) -> int:
        """解析ログの記録"""
        try:
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_logs (
                        task_id, source_id, log_level, component,
                        message, details
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING log_id
                """, (
                    task_id,
                    source_id,
                    level.upper(),
                    component,
                    message,
                    psycopg2.extras.Json(details) if details else None
                ))
                log_id = cur.fetchone()[0]
                self._pg_conn.commit()
                
            return log_id
            
        except Exception as e:
            self._pg_conn.rollback()
            logger.error(f"ログ記録でエラー: {str(e)}")
            raise

    def store_benchmark_result(self, task_id: str, source_id: str, benchmark_id: int,
                             measured_value: float, evaluation_result: str,
                             score: float, details: Dict[str, Any]) -> str:
        """ベンチマーク結果の保存"""
        try:
            result_id = str(uuid.uuid4())
            
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO benchmark_results (
                        benchmark_result_id, task_id, source_id, benchmark_id,
                        measured_value, evaluation_result, score, details
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING benchmark_result_id
                """, (
                    result_id,
                    task_id,
                    source_id,
                    benchmark_id,
                    measured_value,
                    evaluation_result,
                    score,
                    psycopg2.extras.Json(details)
                ))
                self._pg_conn.commit()
                
            return result_id
            
        except Exception as e:
            self._pg_conn.rollback()
            logger.error(f"ベンチマーク結果保存でエラー: {str(e)}")
            raise

    def store_security_result(self, task_id: str, source_id: str,
                            vulnerability_type: str, severity: str,
                            cvss_score: float, cve_ids: List[str],
                            description: str, recommendation: str,
                            details: Dict[str, Any]) -> str:
        """セキュリティ評価結果の保存"""
        try:
            result_id = str(uuid.uuid4())
            
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO security_results (
                        security_result_id, task_id, source_id, vulnerability_type,
                        severity, cvss_score, cve_ids, description,
                        recommendation, details
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING security_result_id
                """, (
                    result_id,
                    task_id,
                    source_id,
                    vulnerability_type,
                    severity,
                    cvss_score,
                    cve_ids,
                    description,
                    recommendation,
                    psycopg2.extras.Json(details)
                ))
                self._pg_conn.commit()
                
            return result_id
            
        except Exception as e:
            self._pg_conn.rollback()
            logger.error(f"セキュリティ結果保存でエラー: {str(e)}")
            raise

    def add_task_dependency(self, task_id: str, dependent_task_id: str,
                          dependency_type: str) -> str:
        """タスク依存関係の追加"""
        try:
            dependency_id = str(uuid.uuid4())
            
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO task_dependencies (
                        dependency_id, task_id, dependent_task_id, dependency_type
                    ) VALUES (%s, %s, %s, %s)
                    RETURNING dependency_id
                """, (
                    dependency_id,
                    task_id,
                    dependent_task_id,
                    dependency_type
                ))
                self._pg_conn.commit()
                
            return dependency_id
            
        except Exception as e:
            self._pg_conn.rollback()
            logger.error(f"タスク依存関係追加でエラー: {str(e)}")
            raise

    def get_task_dependencies(self, task_id: str) -> List[Dict[str, Any]]:
        """タスク依存関係の取得"""
        try:
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT d.*, t.status as dependent_status
                    FROM task_dependencies d
                    JOIN analysis_tasks t ON d.dependent_task_id = t.task_id
                    WHERE d.task_id = %s
                """, (task_id,))
                
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"タスク依存関係取得でエラー: {str(e)}")
            raise

    def store_ast_base(self, source_id: str, task_id: str, ast_type: str,
                      metadata: Dict[str, Any], source_mapping: Dict[str, Any]) -> str:
        """基本AST情報の保存"""
        try:
            ast_doc = {
                'source_id': source_id,
                'task_id': task_id,
                'ast_type': ast_type,
                'ast_version': '1.0',
                'created_at': datetime.now(timezone.utc),
                'metadata': metadata,
                'source_mapping': source_mapping
            }
            
            result = self._mongo_db.ast_base_collection.insert_one(ast_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"基本AST保存でエラー: {str(e)}")
            raise

    def store_ast_jcl(self, source_id: str, procedures: Dict[str, Any],
                     step_defs: Dict[str, Any], dd_statements: Dict[str, Any],
                     job_control: Dict[str, Any], dependencies: Dict[str, Any]) -> str:
        """JCL AST情報の保存"""
        try:
            jcl_doc = {
                'source_id': source_id,
                'jcl_procedures': procedures,
                'step_definitions': step_defs,
                'dd_statements': dd_statements,
                'job_control': job_control,
                'resource_dependencies': dependencies
            }
            
            result = self._mongo_db.ast_jcl_collection.insert_one(jcl_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"JCL AST保存でエラー: {str(e)}")
            raise

    def store_ast_db(self, source_id: str, sql_statements: Dict[str, Any],
                    db_operations: Dict[str, Any], transaction_control: Dict[str, Any],
                    cursor_mgmt: Dict[str, Any], connection_info: Dict[str, Any]) -> str:
        """データベースAST情報の保存"""
        try:
            db_doc = {
                'source_id': source_id,
                'sql_statements': sql_statements,
                'db_operations': db_operations,
                'transaction_control': transaction_control,
                'cursor_management': cursor_mgmt,
                'connection_info': connection_info
            }
            
            result = self._mongo_db.ast_db_collection.insert_one(db_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"DB AST保存でエラー: {str(e)}")
            raise

    def store_ast_dialect(self, source_id: str, vendor: str,
                         special_features: Dict[str, Any], extensions: Dict[str, Any],
                         compatibility: Dict[str, Any], syntax: Dict[str, Any]) -> str:
        """方言AST情報の保存"""
        try:
            dialect_doc = {
                'source_id': source_id,
                'vendor': vendor,
                'special_features': special_features,
                'extensions': extensions,
                'compatibility_info': compatibility,
                'dialect_specific_syntax': syntax
            }
            
            result = self._mongo_db.ast_dialect_collection.insert_one(dialect_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"方言AST保存でエラー: {str(e)}")
            raise

    def store_integrated_analysis(self, source_id: str, ast_refs: List[str],
                                combined_metrics: Dict[str, Any],
                                integration_analysis: Dict[str, Any],
                                impact_assessment: Dict[str, Any]) -> str:
        """統合解析情報の保存"""
        try:
            analysis_doc = {
                'source_id': source_id,
                'ast_references': ast_refs,
                'combined_metrics': combined_metrics,
                'integration_analysis': integration_analysis,
                'impact_assessment': impact_assessment
            }
            
            result = self._mongo_db.integrated_analysis_collection.insert_one(analysis_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"統合解析保存でエラー: {str(e)}")
            raise

    def get_ast_chain(self, source_id: str) -> Dict[str, Any]:
        """AST関連情報の連鎖取得"""
        try:
            # 基本AST情報の取得
            base_ast = self._mongo_db.ast_base_collection.find_one({'source_id': source_id})
            if not base_ast:
                return {}

            # AST種別に応じた詳細情報の取得
            ast_type = base_ast.get('ast_type')
            details = None
            
            if ast_type == 'JCL':
                details = self._mongo_db.ast_jcl_collection.find_one({'source_id': source_id})
            elif ast_type == 'DB':
                details = self._mongo_db.ast_db_collection.find_one({'source_id': source_id})
            elif ast_type.startswith('DIALECT_'):
                details = self._mongo_db.ast_dialect_collection.find_one({'source_id': source_id})

            # クロスリファレンス情報の取得
            xrefs = list(self._mongo_db.cross_reference_collection.find({'source_id': source_id}))

            # 統合解析情報の取得
            integrated = self._mongo_db.integrated_analysis_collection.find_one({'source_id': source_id})

            return {
                'base': base_ast,
                'details': details,
                'cross_references': xrefs,
                'integrated_analysis': integrated
            }
            
        except Exception as e:
            logger.error(f"AST連鎖取得でエラー: {str(e)}")
            raise

    def update_ast_metadata(self, source_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """AST メタデータの更新"""
        try:
            result = self._mongo_db.ast_base_collection.update_one(
                {'source_id': source_id},
                {'$set': {'metadata': metadata_updates}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"メタデータ更新でエラー: {str(e)}")
            raise

    def __del__(self):
        """クリーンアップ処理"""
        try:
            if self._pg_conn:
                self._pg_conn.close()
            if self._mongo_client:
                self._mongo_client.close()
        except Exception as e:
            logger.error(f"DB接続クローズでエラー: {str(e)}") 

    def get_environment_settings(self, category: str, sub_category: str = None) -> List[Dict[str, Any]]:
        """環境設定の取得"""
        try:
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                    SELECT * FROM environment_master
                    WHERE category = %s AND is_active = true
                """
                params = [category]
                
                if sub_category:
                    query += " AND sub_category = %s"
                    params.append(sub_category)
                    
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"環境設定取得でエラー: {str(e)}")
            raise

    def get_analysis_parameters(self, analysis_type: str, process_type: str) -> List[Dict[str, Any]]:
        """解析パラメータの取得"""
        try:
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM single_analysis_master
                    WHERE analysis_type = %s 
                    AND process_type = %s
                    AND is_active = true
                    ORDER BY parameter_name
                """, (analysis_type, process_type))
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"解析パラメータ取得でエラー: {str(e)}")
            raise

    def get_summary_parameters(self, analysis_type: str) -> List[Dict[str, Any]]:
        """サマリ解析パラメータの取得"""
        try:
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM summary_analysis_master
                    WHERE analysis_type = %s
                    AND is_active = true
                    ORDER BY parameter_name
                """, (analysis_type,))
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"サマリパラメータ取得でエラー: {str(e)}")
            raise

    def get_dashboard_components(self, dashboard_type: str) -> List[Dict[str, Any]]:
        """ダッシュボードコンポーネントの取得"""
        try:
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM dashboard_master
                    WHERE dashboard_type = %s
                    AND is_active = true
                    ORDER BY display_order
                """, (dashboard_type,))
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"ダッシュボードコンポーネント取得でエラー: {str(e)}")
            raise

    def get_document_template(self, document_type: str) -> List[Dict[str, Any]]:
        """ドキュメントテンプレートの取得"""
        try:
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM document_master
                    WHERE document_type = %s
                    AND is_active = true
                    ORDER BY display_order
                """, (document_type,))
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"ドキュメントテンプレート取得でエラー: {str(e)}")
            raise

    def get_benchmark_metrics(self, category: str, sub_category: str = None) -> List[Dict[str, Any]]:
        """ベンチマークメトリクスの取得"""
        try:
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                    SELECT * FROM benchmark_master
                    WHERE category = %s AND is_active = true
                """
                params = [category]
                
                if sub_category:
                    query += " AND sub_category = %s"
                    params.append(sub_category)
                    
                query += " ORDER BY metric_name"
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"ベンチマークメトリクス取得でエラー: {str(e)}")
            raise

    def validate_analysis_parameters(self, analysis_type: str, 
                                  parameters: Dict[str, Any]) -> Dict[str, Any]:
        """解析パラメータの検証"""
        try:
            master_params = self.get_analysis_parameters(analysis_type, 'validation')
            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            for param in master_params:
                param_name = param['parameter_name']
                if param['is_required'] and param_name not in parameters:
                    validation_results['valid'] = False
                    validation_results['errors'].append(
                        f"必須パラメータ {param_name} が未指定です"
                    )
                    continue
                    
                if param_name in parameters:
                    value = parameters[param_name]
                    validation_rule = param['validation_rule']
                    
                    if validation_rule and not eval(validation_rule, {'value': value}):
                        validation_results['valid'] = False
                        validation_results['errors'].append(
                            f"パラメータ {param_name} の値が不正です"
                        )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"パラメータ検証でエラー: {str(e)}")
            raise

    def update_environment_setting(self, setting_id: int, 
                                 updates: Dict[str, Any]) -> bool:
        """環境設定の更新"""
        try:
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    UPDATE environment_master
                    SET value = %s,
                        description = %s,
                        is_encrypted = %s,
                        is_active = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE environment_id = %s
                    RETURNING environment_id
                """, (
                    updates.get('value'),
                    updates.get('description'),
                    updates.get('is_encrypted', False),
                    updates.get('is_active', True),
                    setting_id
                ))
                self._pg_conn.commit()
                return cur.rowcount > 0
                
        except Exception as e:
            self._pg_conn.rollback()
            logger.error(f"環境設定更新でエラー: {str(e)}")
            raise 

    def store_analysis_chain(self, source_id: str, task_id: str,
                           ast_data: Dict[str, Any], 
                           analysis_results: Dict[str, Any],
                           metrics: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """解析チェーンの永続的保存"""
        try:
            with self._mongo_client.start_session() as session:
                with session.start_transaction():
                    # 1. 不変なASTデータの保存
                    ast_doc = {
                        'source_id': source_id,
                        'task_id': task_id,
                        'ast_type': ast_data.get('type', 'unknown'),
                        'ast_version': '1.0',
                        'created_at': datetime.now(timezone.utc),
                        'ast_data': ast_data,
                        'metadata': {
                            'generator': 'cobol-analyzer',
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'immutable': True,  # 不変フラグ
                            'retention': 'permanent'  # 永続保持フラグ
                        },
                        'source_mapping': ast_data.get('source_mapping', {})
                    }
                    ast_result = self._mongo_db.ast_collection.insert_one(ast_doc, session=session)

                    # 2. 解析結果の永続保存
                    result_doc = {
                        'result_id': str(uuid.uuid4()),
                        'source_id': source_id,
                        'task_id': task_id,
                        'analysis_type': analysis_results.get('type', 'general'),
                        'created_at': datetime.now(timezone.utc),
                        'immutable': True,  # 不変フラグ
                        'retention': 'permanent',  # 永続保持フラグ
                        'details': analysis_results.get('details', {}),
                        'metrics': analysis_results.get('metrics', {}),
                        'issues': analysis_results.get('issues', []),
                        'references': {
                            'ast_id': ast_result.inserted_id,
                            'metrics_id': None
                        }
                    }
                    result = self._mongo_db.analysis_results_collection.insert_one(
                        result_doc, session=session
                    )

                    # 3. PostgreSQLメタデータの永続保存
                    with self._pg_conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO analysis_results_partitioned (
                                result_id, task_id, source_id, result_type,
                                status, mongodb_collection, mongodb_document_id,
                                retention_policy, immutable,
                                created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            result_doc['result_id'],
                            task_id,
                            source_id,
                            'analysis',
                            'completed',
                            'analysis_results_collection',
                            str(result.inserted_id),
                            'permanent',
                            True,
                            datetime.now(timezone.utc),
                            datetime.now(timezone.utc)
                        ))
                        self._pg_conn.commit()

                    return {
                        'ast_id': str(ast_result.inserted_id),
                        'result_id': result_doc['result_id']
                    }

        except Exception as e:
            if self._pg_conn:
                self._pg_conn.rollback()
            logger.error(f"解析チェーン保存でエラー: {str(e)}")
            raise

    def get_analysis_data(self, source_id: str) -> Dict[str, Any]:
        """解析データの読み取り専用取得"""
        try:
            # 1. PostgreSQLメタデータの読み取り専用取得
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM analysis_results_partitioned
                    WHERE source_id = %s
                    AND deleted_at IS NULL
                    ORDER BY created_at DESC
                    FOR SHARE  -- 読み取り専用ロック
                """, (source_id,))
                metadata = [dict(row) for row in cur.fetchall()]

            # 2. MongoDBデータの読み取り専用取得
            ast_data = list(self._mongo_db.ast_collection.find(
                {
                    'source_id': source_id,
                    'deleted_at': {'$exists': False}
                },
                {'_id': 0}  # IDを除外
            ))

            # 3. 解析結果の読み取り専用取得
            analysis_results = list(self._mongo_db.analysis_results_collection.find(
                {
                    'source_id': source_id,
                    'deleted_at': {'$exists': False}
                },
                {'_id': 0}  # IDを除外
            ))

            return {
                'metadata': metadata,
                'ast_data': ast_data,
                'analysis_results': analysis_results
            }

        except Exception as e:
            logger.error(f"解析データ取得でエラー: {str(e)}")
            raise

    def delete_analysis_data(self, source_id: str, admin_key: str) -> bool:
        """解析データの管理者による論理削除"""
        try:
            # 1. 管理者権限の検証
            if not self._verify_admin_access(admin_key):
                raise PermissionError("管理者権限が必要です")

            now = datetime.now(timezone.utc)

            # 2. PostgreSQLデータの論理削除
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    UPDATE analysis_results_partitioned
                    SET deleted_at = %s,
                        deleted_by = %s
                    WHERE source_id = %s
                    AND deleted_at IS NULL
                """, (now, 'admin', source_id))
                self._pg_conn.commit()

            # 3. MongoDBデータの論理削除
            update_data = {
                '$set': {
                    'deleted_at': now,
                    'deleted_by': 'admin'
                }
            }

            self._mongo_db.ast_collection.update_many(
                {'source_id': source_id, 'deleted_at': {'$exists': False}},
                update_data
            )

            self._mongo_db.analysis_results_collection.update_many(
                {'source_id': source_id, 'deleted_at': {'$exists': False}},
                update_data
            )

            return True

        except Exception as e:
            if self._pg_conn:
                self._pg_conn.rollback()
            logger.error(f"解析データ削除でエラー: {str(e)}")
            raise

    def _verify_admin_access(self, admin_key: str) -> bool:
        """管理者権限の検証"""
        try:
            # 環境設定から管理者キーを取得
            admin_settings = self.get_environment_settings('security', 'admin')
            if not admin_settings:
                return False

            # キーの検証
            return any(
                setting['value'] == admin_key
                for setting in admin_settings
                if setting['name'] == 'admin_key' and setting['is_active']
            )

        except Exception as e:
            logger.error(f"管理者権限検証でエラー: {str(e)}")
            return False

    def process_analysis_output(self, analysis_results: Dict[str, Any],
                              output_format: str = 'json') -> Dict[str, Any]:
        """解析結果の出力処理"""
        try:
            # 1. 出力フォーマットの検証
            format_config = self.get_output_format_config(output_format)
            if not format_config:
                raise ValueError(f"未対応の出力フォーマット: {output_format}")

            # 2. 結果の正規化
            normalized_results = self._normalize_results(analysis_results)

            # 3. メトリクス計算
            metrics = self._calculate_metrics(normalized_results)

            # 4. 品質評価
            quality_assessment = self._assess_quality(metrics)

            # 5. 出力データの構築
            output_data = {
                'summary': {
                    'total_lines': metrics['total_lines'],
                    'complexity_score': metrics['complexity_score'],
                    'quality_score': quality_assessment['overall_score']
                },
                'details': normalized_results,
                'metrics': metrics,
                'quality': quality_assessment,
                'recommendations': self._generate_recommendations(quality_assessment)
            }

            # 6. フォーマット変換
            return self._format_output(output_data, format_config)

        except Exception as e:
            logger.error(f"出力処理でエラー: {str(e)}")
            raise

    def _normalize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """結果の正規化処理"""
        normalized = {
            'source_analysis': {},
            'structural_analysis': {},
            'dependency_analysis': {},
            'quality_metrics': {}
        }

        # 各分析結果の正規化
        for category, data in results.items():
            if category == 'source':
                normalized['source_analysis'] = self._normalize_source_data(data)
            elif category == 'structure':
                normalized['structural_analysis'] = self._normalize_structure_data(data)
            elif category == 'dependencies':
                normalized['dependency_analysis'] = self._normalize_dependency_data(data)
            elif category == 'metrics':
                normalized['quality_metrics'] = self._normalize_metrics_data(data)

        return normalized

    def _calculate_metrics(self, normalized_results: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスの計算"""
        metrics = {
            'total_lines': 0,
            'comment_lines': 0,
            'code_lines': 0,
            'complexity_score': 0,
            'maintainability_index': 0,
            'dependency_count': 0
        }

        # ソース分析メトリクス
        source_data = normalized_results['source_analysis']
        metrics['total_lines'] = source_data.get('total_lines', 0)
        metrics['comment_lines'] = source_data.get('comment_lines', 0)
        metrics['code_lines'] = source_data.get('code_lines', 0)

        # 構造分析メトリクス
        structure_data = normalized_results['structural_analysis']
        metrics['complexity_score'] = self._calculate_complexity(structure_data)
        metrics['maintainability_index'] = self._calculate_maintainability(structure_data)

        # 依存関係メトリクス
        dependency_data = normalized_results['dependency_analysis']
        metrics['dependency_count'] = len(dependency_data.get('dependencies', []))

        return metrics

    def _assess_quality(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """品質評価の実施"""
        assessment = {
            'overall_score': 0,
            'categories': {
                'complexity': {
                    'score': 0,
                    'issues': []
                },
                'maintainability': {
                    'score': 0,
                    'issues': []
                },
                'reliability': {
                    'score': 0,
                    'issues': []
                }
            }
        }

        # 複雑度評価
        complexity_score = self._evaluate_complexity(metrics)
        assessment['categories']['complexity']['score'] = complexity_score

        # 保守性評価
        maintainability_score = self._evaluate_maintainability(metrics)
        assessment['categories']['maintainability']['score'] = maintainability_score

        # 信頼性評価
        reliability_score = self._evaluate_reliability(metrics)
        assessment['categories']['reliability']['score'] = reliability_score

        # 総合評価
        assessment['overall_score'] = (
            complexity_score * 0.4 +
            maintainability_score * 0.4 +
            reliability_score * 0.2
        )

        return assessment

    def _generate_recommendations(self, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """改善推奨事項の生成"""
        recommendations = []

        # 複雑度に関する推奨事項
        if assessment['categories']['complexity']['score'] < 70:
            recommendations.append({
                'category': 'complexity',
                'severity': 'high',
                'description': '複雑度が高すぎます。以下の改善を検討してください：',
                'suggestions': [
                    'メソッドの分割',
                    '条件分岐の簡素化',
                    'ループ構造の見直し'
                ]
            })

        # 保守性に関する推奨事項
        if assessment['categories']['maintainability']['score'] < 70:
            recommendations.append({
                'category': 'maintainability',
                'severity': 'medium',
                'description': '保守性の改善が必要です：',
                'suggestions': [
                    'コメントの追加',
                    '命名規則の見直し',
                    'コードの構造化'
                ]
            })

        return recommendations 

    def analyze_single_source(self, source_path: str, analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """単一ソース解析の実行"""
        try:
            # 1. 解析タスクの作成
            task_id = self.create_analysis_task(source_path, analysis_config)
            
            # 2. ソース情報の登録
            source_id = self.create_source_entry(
                task_id=task_id,
                file_path=source_path,
                file_type=self._detect_file_type(source_path),
                file_hash=self._calculate_file_hash(source_path),
                file_size=os.path.getsize(source_path)
            )

            # 3. 各種解析の実行
            analysis_results = {
                'source': self._analyze_source_code(source_path),
                'structure': self._analyze_structure(source_path),
                'dependencies': self._analyze_dependencies(source_path),
                'metrics': self._analyze_metrics(source_path)
            }

            # 4. 解析チェーンの保存
            chain_ids = self.store_analysis_chain(
                source_id=source_id,
                task_id=task_id,
                ast_data=analysis_results['structure'].get('ast', {}),
                analysis_results=analysis_results,
                metrics=analysis_results['metrics']
            )

            # 5. 出力処理
            output_data = self.process_analysis_output(
                analysis_results,
                output_format=analysis_config.get('output_format', 'json')
            )

            # 6. ダッシュボードデータの生成
            dashboard_data = self.generate_dashboard_data(
                source_id=source_id,
                analysis_results=output_data
            )

            # 7. PDF報告書の生成
            pdf_data = self.generate_pdf_report(
                source_id=source_id,
                analysis_results=output_data,
                template_type='single_source'
            )

            return {
                'task_id': task_id,
                'source_id': source_id,
                'chain_ids': chain_ids,
                'output_data': output_data,
                'dashboard_url': dashboard_data['url'],
                'pdf_url': pdf_data['url']
            }

        except Exception as e:
            logger.error(f"単一ソース解析でエラー: {str(e)}")
            raise

    def analyze_multiple_sources(self, source_paths: List[str], 
                               analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """複数ソースのサマリ解析実行"""
        try:
            # 1. 親タスクの作成
            parent_task_id = self.create_analysis_task(
                source_path="multiple_sources",
                analysis_config={**analysis_config, 'type': 'summary'}
            )

            # 2. 各ソースの個別解析
            individual_results = []
            source_ids = []
            for source_path in source_paths:
                result = self.analyze_single_source(
                    source_path=source_path,
                    analysis_config={**analysis_config, 'parent_task_id': parent_task_id}
                )
                individual_results.append(result)
                source_ids.append(result['source_id'])

            # 3. サマリ解析の実行
            summary_results = self._analyze_summary(
                individual_results=individual_results,
                config=analysis_config
            )

            # 4. サマリ結果の保存
            summary_id = self.store_summary_results(
                task_id=parent_task_id,
                source_ids=source_ids,
                summary_results=summary_results
            )

            # 5. サマリダッシュボードの生成
            dashboard_data = self.generate_summary_dashboard(
                task_id=parent_task_id,
                summary_results=summary_results
            )

            # 6. サマリPDFの生成
            pdf_data = self.generate_pdf_report(
                task_id=parent_task_id,
                analysis_results=summary_results,
                template_type='summary'
            )

            return {
                'task_id': parent_task_id,
                'source_ids': source_ids,
                'summary_id': summary_id,
                'summary_results': summary_results,
                'dashboard_url': dashboard_data['url'],
                'pdf_url': pdf_data['url']
            }

        except Exception as e:
            logger.error(f"サマリ解析でエラー: {str(e)}")
            raise

    def generate_dashboard_data(self, source_id: str, 
                              analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """ダッシュボードデータの生成"""
        try:
            # 1. ダッシュボードコンポーネントの取得
            components = self.get_dashboard_components('source_analysis')

            # 2. メトリクスウィジェットの生成
            metrics_widgets = self._generate_metrics_widgets(
                metrics=analysis_results['metrics']
            )

            # 3. 品質評価ウィジェットの生成
            quality_widgets = self._generate_quality_widgets(
                quality=analysis_results['quality']
            )

            # 4. トレンドグラフの生成
            trend_widgets = self._generate_trend_widgets(source_id)

            # 5. レイアウトの構築
            layout = self._build_dashboard_layout(
                metrics_widgets=metrics_widgets,
                quality_widgets=quality_widgets,
                trend_widgets=trend_widgets
            )

            # 6. ダッシュボードの保存
            dashboard_id = self._save_dashboard(
                source_id=source_id,
                layout=layout,
                widgets={
                    'metrics': metrics_widgets,
                    'quality': quality_widgets,
                    'trends': trend_widgets
                }
            )

            return {
                'dashboard_id': dashboard_id,
                'url': f"/dashboard/source/{source_id}",
                'layout': layout
            }

        except Exception as e:
            logger.error(f"ダッシュボード生成でエラー: {str(e)}")
            raise

    def generate_pdf_report(self, task_id: str, analysis_results: Dict[str, Any],
                          template_type: str) -> Dict[str, Any]:
        """PDF報告書の生成"""
        try:
            # 1. レポートテンプレートの取得
            template = self.get_document_template(template_type)

            # 2. レポートセクションの生成
            sections = []
            
            # 2.1 概要セクション
            sections.append(self._generate_summary_section(analysis_results))
            
            # 2.2 メトリクスセクション
            sections.append(self._generate_metrics_section(analysis_results))
            
            # 2.3 品質評価セクション
            sections.append(self._generate_quality_section(analysis_results))
            
            # 2.4 推奨事項セクション
            sections.append(self._generate_recommendations_section(analysis_results))

            # 3. チャートとグラフの生成
            charts = self._generate_report_charts(analysis_results)

            # 4. PDFドキュメントの生成と保存
            document_id = self.create_document_with_references(
                task_id=task_id,
                document_type=template_type,
                content={
                    'sections': sections,
                    'charts': charts
                },
                formatting=template.format_rules
            )

            return {
                'document_id': document_id,
                'url': f"/reports/{document_id}/download",
                'sections': len(sections),
                'charts': len(charts)
            }

        except Exception as e:
            logger.error(f"PDF生成でエラー: {str(e)}")
            raise 

    def analyze_security(self, source_id: str, security_config: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティ分析の実行"""
        try:
            # 1. セキュリティルールの取得
            security_rules = self.get_security_rules(security_config['rule_set'])
            
            # 2. 脆弱性スキャン
            vulnerabilities = self._scan_vulnerabilities(source_id, security_rules)
            
            # 3. コンプライアンスチェック
            compliance_results = self._check_compliance(source_id, security_rules)
            
            # 4. セキュリティメトリクス計算
            security_metrics = self._calculate_security_metrics(
                vulnerabilities, compliance_results
            )
            
            # 5. 結果の永続化
            result_id = self.store_security_results(
                source_id=source_id,
                vulnerabilities=vulnerabilities,
                compliance_results=compliance_results,
                security_metrics=security_metrics
            )
            
            return {
                'result_id': result_id,
                'vulnerabilities': vulnerabilities,
                'compliance': compliance_results,
                'metrics': security_metrics
            }
            
        except Exception as e:
            logger.error(f"セキュリティ分析でエラー: {str(e)}")
            raise 

    def run_benchmark(self, source_id: str, benchmark_config: Dict[str, Any]) -> Dict[str, Any]:
        """ベンチマーク実行"""
        try:
            # 1. ベンチマーク定義の取得
            benchmark_def = self.get_benchmark_definition(benchmark_config['type'])
            
            # 2. メトリクス収集
            metrics = self._collect_benchmark_metrics(source_id, benchmark_def)
            
            # 3. 評価実行
            evaluation = self._evaluate_benchmark(metrics, benchmark_def)
            
            # 4. スコアリング
            scores = self._calculate_benchmark_scores(evaluation, benchmark_def)
            
            # 5. 結果の永続化
            result_id = self.store_benchmark_results(
                source_id=source_id,
                metrics=metrics,
                evaluation=evaluation,
                scores=scores
            )
            
            return {
                'result_id': result_id,
                'metrics': metrics,
                'evaluation': evaluation,
                'scores': scores
            }
            
        except Exception as e:
            logger.error(f"ベンチマーク実行でエラー: {str(e)}")
            raise 

    def process_rag_analysis(self, source_id: str, rag_config: Dict[str, Any]) -> Dict[str, Any]:
        """RAG分析処理"""
        try:
            # 1. ソースコードの取得
            source_data = self.get_source_data(source_id)
            
            # 2. RAGエンジンの初期化
            rag_engine = self._init_rag_engine(rag_config)
            
            # 3. コンテキスト生成
            context = self._generate_rag_context(source_data)
            
            # 4. 質問生成
            questions = self._generate_analysis_questions(context)
            
            # 5. 回答生成
            answers = rag_engine.process_questions(questions, context)
            
            # 6. 結果の統合
            analysis_results = self._integrate_rag_results(answers)
            
            # 7. 結果の永続化
            result_id = self.store_rag_results(
                source_id=source_id,
                context=context,
                questions=questions,
                answers=answers,
                analysis_results=analysis_results
            )
            
            return {
                'result_id': result_id,
                'analysis_results': analysis_results
            }
            
        except Exception as e:
            logger.error(f"RAG分析でエラー: {str(e)}")
            raise 

    def handle_analysis_error(self, task_id: str, error: Exception) -> Dict[str, Any]:
        """エラー処理とリカバリ"""
        try:
            # 1. エラー情報の記録
            error_id = self._log_error(task_id, error)
            
            # 2. 影響範囲の特定
            affected_items = self._identify_affected_items(task_id)
            
            # 3. リカバリ処理
            recovery_plan = self._create_recovery_plan(affected_items)
            recovery_results = self._execute_recovery(recovery_plan)
            
            # 4. 通知
            self._notify_error(task_id, error, recovery_results)
            
            return {
                'error_id': error_id,
                'recovery_status': recovery_results['status'],
                'affected_items': affected_items
            }
            
        except Exception as e:
            logger.error(f"エラー処理でエラー: {str(e)}")
            raise 

    def get_security_rules(self, rule_set: str) -> List[Dict[str, Any]]:
        """セキュリティルールの取得"""
        try:
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM security_rules_master
                    WHERE rule_set = %s AND is_active = true
                    ORDER BY priority DESC
                """, (rule_set,))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"セキュリティルール取得でエラー: {str(e)}")
            raise

    def _scan_vulnerabilities(self, source_id: str, security_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """脆弱性スキャン実行"""
        vulnerabilities = []
        try:
            # ソースコードの取得
            source_data = self.get_source_data(source_id)
            
            # 各ルールに対するスキャン
            for rule in security_rules:
                rule_results = self._apply_security_rule(source_data, rule)
                if rule_results:
                    vulnerabilities.extend(rule_results)
                    
            return vulnerabilities
        except Exception as e:
            logger.error(f"脆弱性スキャンでエラー: {str(e)}")
            raise

    def _check_compliance(self, source_id: str, security_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """コンプライアンスチェック実行"""
        try:
            compliance_results = {
                'overall_status': 'compliant',
                'checks': [],
                'violations': [],
                'recommendations': []
            }
            
            # ソースコードの取得
            source_data = self.get_source_data(source_id)
            
            # 各ルールのコンプライアンスチェック
            for rule in security_rules:
                check_result = self._apply_compliance_check(source_data, rule)
                compliance_results['checks'].append(check_result)
                
                if not check_result['compliant']:
                    compliance_results['overall_status'] = 'non_compliant'
                    compliance_results['violations'].append(check_result)
                    compliance_results['recommendations'].append(
                        self._generate_compliance_recommendation(check_result)
                    )
                    
            return compliance_results
        except Exception as e:
            logger.error(f"コンプライアンスチェックでエラー: {str(e)}")
            raise

    def store_security_results(self, source_id: str, vulnerabilities: List[Dict[str, Any]],
                                 compliance_results: Dict[str, Any], security_metrics: Dict[str, Any]) -> str:
        """セキュリティ分析結果の保存"""
        try:
            result_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            # MongoDBに詳細結果を保存
            security_doc = {
                'result_id': result_id,
                'source_id': source_id,
                'created_at': now,
                'vulnerabilities': vulnerabilities,
                'compliance_results': compliance_results,
                'security_metrics': security_metrics
            }
            mongo_result = self._mongo_db.security_results.insert_one(security_doc)
            
            # PostgreSQLにメタデータを保存
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO security_results (
                        result_id, source_id, severity_level,
                        vulnerability_count, compliance_status,
                        mongodb_document_id, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    result_id,
                    source_id,
                    self._calculate_severity_level(vulnerabilities),
                    len(vulnerabilities),
                    compliance_results['overall_status'],
                    str(mongo_result.inserted_id),
                    now
                ))
                self._pg_conn.commit()
                
            return result_id
        except Exception as e:
            if self._pg_conn:
                self._pg_conn.rollback()
            logger.error(f"セキュリティ結果保存でエラー: {str(e)}")
            raise 

    def get_benchmark_definition(self, benchmark_type: str) -> Dict[str, Any]:
        """ベンチマーク定義の取得"""
        try:
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM benchmark_master
                    WHERE benchmark_type = %s AND is_active = true
                """, (benchmark_type,))
                return dict(cur.fetchone()) if cur.rowcount > 0 else None
        except Exception as e:
            logger.error(f"ベンチマーク定義取得でエラー: {str(e)}")
            raise

    def _collect_benchmark_metrics(self, source_id: str, benchmark_def: Dict[str, Any]) -> Dict[str, Any]:
        """ベンチマークメトリクスの収集"""
        try:
            metrics = {}
            
            # 1. コード品質メトリクス
            quality_metrics = self._collect_quality_metrics(source_id)
            metrics['quality'] = quality_metrics
            
            # 2. パフォーマンスメトリクス
            performance_metrics = self._collect_performance_metrics(source_id)
            metrics['performance'] = performance_metrics
            
            # 3. セキュリティメトリクス
            security_metrics = self._collect_security_metrics(source_id)
            metrics['security'] = security_metrics
            
            # 4. 保守性メトリクス
            maintainability_metrics = self._collect_maintainability_metrics(source_id)
            metrics['maintainability'] = maintainability_metrics
            
            return metrics
        except Exception as e:
            logger.error(f"メトリクス収集でエラー: {str(e)}")
            raise

    def store_benchmark_results(self, source_id: str, metrics: Dict[str, Any],
                              evaluation: Dict[str, Any], scores: Dict[str, Any]) -> str:
        """ベンチマーク結果の保存"""
        try:
            result_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            # MongoDBに詳細結果を保存
            benchmark_doc = {
                'result_id': result_id,
                'source_id': source_id,
                'created_at': now,
                'metrics': metrics,
                'evaluation': evaluation,
                'scores': scores
            }
            mongo_result = self._mongo_db.benchmark_results.insert_one(benchmark_doc)
            
            # PostgreSQLにメタデータを保存
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO benchmark_results (
                        result_id, source_id, overall_score,
                        quality_score, performance_score,
                        security_score, maintainability_score,
                        mongodb_document_id, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    result_id,
                    source_id,
                    scores['overall'],
                    scores['quality'],
                    scores['performance'],
                    scores['security'],
                    scores['maintainability'],
                    str(mongo_result.inserted_id),
                    now
                ))
                self._pg_conn.commit()
                
            return result_id
        except Exception as e:
            if self._pg_conn:
                self._pg_conn.rollback()
            logger.error(f"ベンチマーク結果保存でエラー: {str(e)}")
            raise 

    def _init_rag_engine(self, rag_config: Dict[str, Any]) -> Any:
        """RAGエンジンの初期化"""
        try:
            # RAGエンジンの設定
            engine_config = {
                'model': rag_config.get('model', 'gpt-4'),
                'embedding_model': rag_config.get('embedding_model', 'text-embedding-3-small'),
                'chunk_size': rag_config.get('chunk_size', 1000),
                'chunk_overlap': rag_config.get('chunk_overlap', 200),
                'max_tokens': rag_config.get('max_tokens', 4000)
            }
            
            # RAGエンジンのインスタンス化
            from .rag_engine import RAGEngine
            return RAGEngine(engine_config)
        except Exception as e:
            logger.error(f"RAGエンジン初期化でエラー: {str(e)}")
            raise

    def _generate_rag_context(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """RAG用コンテキストの生成"""
        try:
            context = {
                'source_code': source_data['content'],
                'metadata': source_data['metadata'],
                'ast': source_data.get('ast', {}),
                'analysis_history': self._get_analysis_history(source_data['source_id'])
            }
            return context
        except Exception as e:
            logger.error(f"コンテキスト生成でエラー: {str(e)}")
            raise

    def store_rag_results(self, source_id: str, context: Dict[str, Any],
                         questions: List[str], answers: List[Dict[str, Any]],
                         analysis_results: Dict[str, Any]) -> str:
        """RAG分析結果の保存"""
        try:
            result_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            # MongoDBに詳細結果を保存
            rag_doc = {
                'result_id': result_id,
                'source_id': source_id,
                'created_at': now,
                'context': context,
                'questions': questions,
                'answers': answers,
                'analysis_results': analysis_results
            }
            mongo_result = self._mongo_db.rag_results.insert_one(rag_doc)
            
            # PostgreSQLにメタデータを保存
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO rag_results (
                        result_id, source_id, question_count,
                        answer_count, confidence_score,
                        mongodb_document_id, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    result_id,
                    source_id,
                    len(questions),
                    len(answers),
                    self._calculate_confidence_score(answers),
                    str(mongo_result.inserted_id),
                    now
                ))
                self._pg_conn.commit()
                
            return result_id
        except Exception as e:
            if self._pg_conn:
                self._pg_conn.rollback()
            logger.error(f"RAG結果保存でエラー: {str(e)}")
            raise 

    def _log_error(self, task_id: str, error: Exception) -> str:
        """エラー情報の記録"""
        try:
            error_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO error_logs (
                        error_id, task_id, error_type,
                        error_message, stack_trace,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    error_id,
                    task_id,
                    type(error).__name__,
                    str(error),
                    traceback.format_exc(),
                    now
                ))
                self._pg_conn.commit()
                
            return error_id
        except Exception as e:
            if self._pg_conn:
                self._pg_conn.rollback()
            logger.error(f"エラーログ記録でエラー: {str(e)}")
            raise

    def _identify_affected_items(self, task_id: str) -> List[Dict[str, Any]]:
        """影響を受けるアイテムの特定"""
        try:
            affected_items = []
            
            # 1. 依存タスクの特定
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM task_dependencies
                    WHERE task_id = %s OR dependent_task_id = %s
                """, (task_id, task_id))
                affected_items.extend([
                    {'type': 'task', 'id': row['task_id']}
                    for row in cur.fetchall()
                ])
            
            # 2. 関連する解析結果の特定
            affected_items.extend(
                self._identify_affected_results(task_id)
            )
            
            # 3. 影響を受けるドキュメントの特定
            affected_items.extend(
                self._identify_affected_documents(task_id)
            )
            
            return affected_items
        except Exception as e:
            logger.error(f"影響範囲特定でエラー: {str(e)}")
            raise

    def _create_recovery_plan(self, affected_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """リカバリ計画の作成"""
        try:
            plan = {
                'steps': [],
                'rollback_steps': [],
                'verification_steps': []
            }
            
            for item in affected_items:
                if item['type'] == 'task':
                    plan['steps'].append(
                        self._create_task_recovery_step(item)
                    )
                elif item['type'] == 'result':
                    plan['steps'].append(
                        self._create_result_recovery_step(item)
                    )
                elif item['type'] == 'document':
                    plan['steps'].append(
                        self._create_document_recovery_step(item)
                    )
            
            return plan
        except Exception as e:
            logger.error(f"リカバリ計画作成でエラー: {str(e)}")
            raise

    def _execute_recovery(self, recovery_plan: Dict[str, Any]) -> Dict[str, Any]:
        """リカバリの実行"""
        results = {
            'status': 'success',
            'completed_steps': [],
            'failed_steps': [],
            'rollback_status': None
        }
        
        try:
            # 1. リカバリステップの実行
            for step in recovery_plan['steps']:
                try:
                    self._execute_recovery_step(step)
                    results['completed_steps'].append(step)
                except Exception as e:
                    results['status'] = 'failed'
                    results['failed_steps'].append({
                        'step': step,
                        'error': str(e)
                    })
                    # ロールバックの実行
                    results['rollback_status'] = self._execute_rollback(
                        recovery_plan['rollback_steps'],
                        results['completed_steps']
                    )
                    break
            
            # 2. 検証ステップの実行
            if results['status'] == 'success':
                self._execute_verification_steps(
                    recovery_plan['verification_steps']
                )
            
            return results
        except Exception as e:
            logger.error(f"リカバリ実行でエラー: {str(e)}")
            raise

    def _notify_error(self, task_id: str, error: Exception, 
                     recovery_results: Dict[str, Any]) -> None:
        """エラー通知の送信"""
        try:
            # 通知設定の取得
            notification_settings = self.get_environment_settings('notifications')
            
            # 通知内容の作成
            notification = {
                'type': 'error',
                'task_id': task_id,
                'error_message': str(error),
                'recovery_status': recovery_results['status'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # 通知の送信
            for setting in notification_settings:
                if setting['is_active']:
                    self._send_notification(notification, setting)
        except Exception as e:
            logger.error(f"エラー通知送信でエラー: {str(e)}")
            # 通知失敗は主処理に影響を与えないよう、例外は伝播させない

    def process_analysis_feedback(self, source_id: str, feedback_data: Dict[str, Any]) -> str:
        """Analysis Feedback Flowの実装"""
        try:
            feedback_id = str(uuid.uuid4())
            
            # 1. フィードバックの検証
            validated_feedback = self._validate_feedback(feedback_data)
            
            # 2. 解析結果の更新
            self._update_analysis_with_feedback(source_id, validated_feedback)
            
            # 3. 学習データの更新
            self._update_learning_data(validated_feedback)
            
            # 4. フィードバック履歴の保存
            self._store_feedback_history(feedback_id, source_id, validated_feedback)
            
            return feedback_id
            
        except Exception as e:
            logger.error(f"フィードバック処理でエラー: {str(e)}")
            raise

    def process_system_startup(self) -> Dict[str, Any]:
        """System Startup and Operation Flowの実装"""
        try:
            # 1. システム初期化
            init_status = self._initialize_system_components()
            
            # 2. 設定の読み込み
            config_status = self._load_system_configurations()
            
            # 3. サービスの起動
            service_status = self._start_system_services()
            
            # 4. ヘルスチェック
            health_status = self._perform_health_check()
            
            return {
                'initialization': init_status,
                'configuration': config_status,
                'services': service_status,
                'health': health_status
            }
            
        except Exception as e:
            logger.error(f"システム起動でエラー: {str(e)}")
            raise

    def validate_analysis_process(self, source_id: str, validation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validation Process Flowの実装"""
        try:
            # 1. 入力データの検証
            input_validation = self._validate_input_data(source_id)
            
            # 2. 解析プロセスの検証
            process_validation = self._validate_analysis_process(source_id)
            
            # 3. 出力データの検証
            output_validation = self._validate_output_data(source_id)
            
            # 4. 検証結果の統合
            validation_results = self._integrate_validation_results(
                input_validation,
                process_validation,
                output_validation
            )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"検証プロセスでエラー: {str(e)}")
            raise

    def _validate_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """フィードバックデータの検証"""
        try:
            # 必須フィールドの検証
            required_fields = ['feedback_type', 'content', 'user_id']
            for field in required_fields:
                if field not in feedback_data:
                    raise ValueError(f"必須フィールド {field} が未指定です")

            # フィードバックタイプの検証
            valid_types = ['correction', 'improvement', 'bug_report']
            if feedback_data['feedback_type'] not in valid_types:
                raise ValueError(f"無効なフィードバックタイプ: {feedback_data['feedback_type']}")

            # コンテンツの検証
            if not isinstance(feedback_data['content'], dict):
                raise ValueError("コンテンツは辞書形式である必要があります")

            # 検証済みデータの返却
            return {
                'feedback_type': feedback_data['feedback_type'],
                'content': feedback_data['content'],
                'user_id': feedback_data['user_id'],
                'validated_at': datetime.now(timezone.utc),
                'validation_status': 'valid'
            }

        except Exception as e:
            logger.error(f"フィードバック検証でエラー: {str(e)}")
            raise

    def _update_analysis_with_feedback(self, source_id: str, feedback: Dict[str, Any]) -> None:
        """フィードバックに基づく解析結果の更新"""
        try:
            # 1. 最新の解析結果を取得
            with self._pg_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM analysis_results_partitioned
                    WHERE source_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (source_id,))
                result = cur.fetchone()

            if not result:
                raise ValueError(f"解析結果が見つかりません: {source_id}")

            # 2. フィードバックの適用
            mongo_doc = self._mongo_db.analysis_results_collection.find_one({
                '_id': result['mongodb_document_id']
            })

            if not mongo_doc:
                raise ValueError(f"MongoDB文書が見つかりません: {result['mongodb_document_id']}")

            # 3. 結果の更新
            updated_results = self._apply_feedback_to_results(mongo_doc, feedback)
            
            # 4. 更新の保存
            self._mongo_db.analysis_results_collection.update_one(
                {'_id': result['mongodb_document_id']},
                {'$set': {
                    'results': updated_results,
                    'feedback_applied': True,
                    'last_feedback_at': datetime.now(timezone.utc)
                }}
            )

        except Exception as e:
            logger.error(f"解析結果更新でエラー: {str(e)}")
            raise

    def _update_learning_data(self, feedback: Dict[str, Any]) -> None:
        """学習データの更新"""
        try:
            # 1. 学習データの取得
            learning_data = self._mongo_db.learning_data_collection.find_one({
                'feedback_type': feedback['feedback_type']
            })

            # 2. 新規学習データの作成
            new_learning_data = {
                'feedback_type': feedback['feedback_type'],
                'content': feedback['content'],
                'created_at': datetime.now(timezone.utc)
            }

            # 3. 学習データの更新または挿入
            self._mongo_db.learning_data_collection.update_one(
                {'feedback_type': feedback['feedback_type']},
                {'$push': {'examples': new_learning_data}},
                upsert=True
            )

            # 4. 学習モデルの更新トリガー
            self._trigger_model_update(feedback['feedback_type'])

        except Exception as e:
            logger.error(f"学習データ更新でエラー: {str(e)}")
            raise

    def _initialize_system_components(self) -> Dict[str, str]:
        """システムコンポーネントの初期化"""
        try:
            components_status = {}

            # 1. データベース接続の初期化
            try:
                self._init_db_connections()
                components_status['database'] = 'initialized'
            except Exception as e:
                components_status['database'] = f'failed: {str(e)}'

            # 2. キャッシュの初期化
            try:
                self._init_cache()
                components_status['cache'] = 'initialized'
            except Exception as e:
                components_status['cache'] = f'failed: {str(e)}'

            # 3. ログシステムの初期化
            try:
                self._init_logging()
                components_status['logging'] = 'initialized'
            except Exception as e:
                components_status['logging'] = f'failed: {str(e)}'

            # 4. 一時ディレクトリの初期化
            try:
                self._init_temp_directories()
                components_status['temp_dirs'] = 'initialized'
            except Exception as e:
                components_status['temp_dirs'] = f'failed: {str(e)}'

            return components_status

        except Exception as e:
            logger.error(f"システムコンポーネント初期化でエラー: {str(e)}")
            raise

    def _start_system_services(self) -> Dict[str, str]:
        """システムサービスの起動"""
        try:
            services_status = {}

            # 1. 解析サービスの起動
            try:
                self._start_analysis_service()
                services_status['analysis'] = 'running'
            except Exception as e:
                services_status['analysis'] = f'failed: {str(e)}'

            # 2. モニタリングサービスの起動
            try:
                self._start_monitoring_service()
                services_status['monitoring'] = 'running'
            except Exception as e:
                services_status['monitoring'] = f'failed: {str(e)}'

            # 3. バックグラウンドタスクの起動
            try:
                self._start_background_tasks()
                services_status['background_tasks'] = 'running'
            except Exception as e:
                services_status['background_tasks'] = f'failed: {str(e)}'

            return services_status

        except Exception as e:
            logger.error(f"システムサービス起動でエラー: {str(e)}")
            raise

    def _perform_health_check(self) -> Dict[str, str]:
        """ヘルスチェックの実行"""
        try:
            health_status = {}

            # 1. データベース接続の確認
            try:
                # PostgreSQL確認
                with self._pg_conn.cursor() as cur:
                    cur.execute("SELECT 1")
                # MongoDB確認
                self._mongo_db.command('ping')
                health_status['database'] = 'healthy'
            except Exception as e:
                health_status['database'] = f'unhealthy: {str(e)}'

            # 2. ディスク容量の確認
            try:
                disk_usage = self._check_disk_usage()
                health_status['disk'] = 'healthy' if disk_usage < 90 else 'warning'
            except Exception as e:
                health_status['disk'] = f'error: {str(e)}'

            # 3. メモリ使用量の確認
            try:
                memory_usage = self._check_memory_usage()
                health_status['memory'] = 'healthy' if memory_usage < 85 else 'warning'
            except Exception as e:
                health_status['memory'] = f'error: {str(e)}'

            # 4. サービス状態の確認
            try:
                service_status = self._check_service_status()
                health_status['services'] = service_status
            except Exception as e:
                health_status['services'] = f'error: {str(e)}'

            return health_status

        except Exception as e:
            logger.error(f"ヘルスチェックでエラー: {str(e)}")
            raise

    def _init_cache(self) -> None:
        """キャッシュシステムの初期化"""
        try:
            # キャッシュディレクトリの作成
            cache_dir = Path("cache")
            cache_dir.mkdir(exist_ok=True)
            
            # キャッシュ設定の読み込み
            cache_config = self.get_environment_settings('cache')
            if cache_config:
                self._cache_settings = cache_config[0]
        except Exception as e:
            logger.error(f"キャッシュ初期化でエラー: {str(e)}")
            raise

    def _init_logging(self) -> None:
        """ログシステムの初期化"""
        try:
            log_config = self.get_environment_settings('logging')
            if log_config:
                logging.config.dictConfig(log_config[0]['config'])
        except Exception as e:
            logger.error(f"ログ初期化でエラー: {str(e)}")
            raise

    def _init_temp_directories(self) -> None:
        """一時ディレクトリの初期化"""
        try:
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # 古い一時ファイルの削除
            for item in temp_dir.glob("*"):
                if item.is_file():
                    item.unlink()
        except Exception as e:
            logger.error(f"一時ディレクトリ初期化でエラー: {str(e)}")
            raise

    def _check_disk_usage(self) -> float:
        """ディスク使用率の確認"""
        try:
            usage = psutil.disk_usage('/')
            return usage.percent
        except Exception as e:
            logger.error(f"ディスク使用率確認でエラー: {str(e)}")
            raise

    def _check_memory_usage(self) -> float:
        """メモリ使用率の確認"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent
        except Exception as e:
            logger.error(f"メモリ使用率確認でエラー: {str(e)}")
            raise

    def _check_service_status(self) -> Dict[str, str]:
        """サービス状態の確認"""
        try:
            return {
                'analysis_service': self._check_analysis_service(),
                'monitoring_service': self._check_monitoring_service(),
                'background_tasks': self._check_background_tasks()
            }
        except Exception as e:
            logger.error(f"サービス状態確認でエラー: {str(e)}")
            raise

    def _apply_feedback_to_results(self, mongo_doc: Dict[str, Any], 
                                 feedback: Dict[str, Any]) -> Dict[str, Any]:
        """フィードバックの結果への適用"""
        try:
            results = mongo_doc.get('results', {})
            
            # フィードバックタイプに応じた更新
            if feedback['feedback_type'] == 'correction':
                results = self._apply_correction_feedback(results, feedback)
            elif feedback['feedback_type'] == 'improvement':
                results = self._apply_improvement_feedback(results, feedback)
            elif feedback['feedback_type'] == 'bug_report':
                results = self._apply_bug_report_feedback(results, feedback)
                
            return results
        except Exception as e:
            logger.error(f"フィードバック適用でエラー: {str(e)}")
            raise

    def _trigger_model_update(self, feedback_type: str) -> None:
        """学習モデル更新のトリガー"""
        try:
            # モデル更新タスクの登録
            update_task = {
                'task_type': 'model_update',
                'feedback_type': feedback_type,
                'created_at': datetime.now(timezone.utc)
            }
            self._mongo_db.model_update_tasks.insert_one(update_task)
        except Exception as e:
            logger.error(f"モデル更新トリガーでエラー: {str(e)}")
            raise

    def _check_analysis_service(self) -> str:
        """解析サービスの状態確認"""
        try:
            # サービスプロセスの確認
            service_pid = self._get_service_pid('analysis_service')
            if not service_pid:
                return 'stopped'
                
            # 応答確認
            response = self._check_service_response('analysis')
            return 'running' if response else 'degraded'
            
        except Exception as e:
            logger.error(f"解析サービス確認でエラー: {str(e)}")
            return 'error'

    def _check_monitoring_service(self) -> str:
        """モニタリングサービスの状態確認"""
        try:
            # サービスプロセスの確認
            service_pid = self._get_service_pid('monitoring_service')
            if not service_pid:
                return 'stopped'
                
            # メトリクス収集確認
            metrics_status = self._check_metrics_collection()
            return 'running' if metrics_status else 'degraded'
            
        except Exception as e:
            logger.error(f"モニタリングサービス確認でエラー: {str(e)}")
            return 'error'

    def _check_background_tasks(self) -> str:
        """バックグラウンドタスクの状態確認"""
        try:
            # タスクキューの確認
            queue_status = self._check_task_queue()
            if not queue_status['connected']:
                return 'stopped'
                
            # タスク処理状態の確認
            processing_status = self._check_task_processing()
            return 'running' if processing_status['healthy'] else 'degraded'
            
        except Exception as e:
            logger.error(f"バックグラウンドタスク確認でエラー: {str(e)}")
            return 'error'

    def _start_analysis_service(self) -> None:
        """解析サービスの起動"""
        try:
            # サービス設定の取得
            service_config = self.get_environment_settings('services', 'analysis')
            if not service_config:
                raise ValueError("解析サービスの設定が見つかりません")
                
            # プロセス起動
            self._start_service_process('analysis_service', service_config[0])
            
            # 起動確認
            if not self._wait_for_service('analysis', timeout=30):
                raise RuntimeError("解析サービスの起動に失敗しました")
                
        except Exception as e:
            logger.error(f"解析サービス起動でエラー: {str(e)}")
            raise

    def _start_monitoring_service(self) -> None:
        """モニタリングサービスの起動"""
        try:
            # サービス設定の取得
            service_config = self.get_environment_settings('services', 'monitoring')
            if not service_config:
                raise ValueError("モニタリングサービスの設定が見つかりません")
                
            # プロセス起動
            self._start_service_process('monitoring_service', service_config[0])
            
            # 起動確認
            if not self._wait_for_service('monitoring', timeout=30):
                raise RuntimeError("モニタリングサービスの起動に失敗しました")
                
        except Exception as e:
            logger.error(f"モニタリングサービス起動でエラー: {str(e)}")
            raise

    def _start_background_tasks(self) -> None:
        """バックグラウンドタスクの起動"""
        try:
            # タスク設定の取得
            task_config = self.get_environment_settings('services', 'background_tasks')
            if not task_config:
                raise ValueError("バックグラウンドタスクの設定が見つかりません")
                
            # タスクワーカーの起動
            self._start_task_workers(task_config[0])
            
            # 起動確認
            if not self._check_workers_status(timeout=30):
                raise RuntimeError("バックグラウンドタスクの起動に失敗しました")
                
        except Exception as e:
            logger.error(f"バックグラウンドタスク起動でエラー: {str(e)}")
            raise

    def _apply_correction_feedback(self, results: Dict[str, Any], 
                                 feedback: Dict[str, Any]) -> Dict[str, Any]:
        """修正フィードバックの適用"""
        try:
            # 修正内容の検証
            if not self._validate_correction(feedback['content']):
                raise ValueError("無効な修正内容です")
                
            # 結果の更新
            updated_results = results.copy()
            for correction in feedback['content']['corrections']:
                path = correction['path']
                value = correction['value']
                self._update_result_value(updated_results, path, value)
                
            return updated_results
            
        except Exception as e:
            logger.error(f"修正フィードバック適用でエラー: {str(e)}")
            raise

    def _apply_improvement_feedback(self, results: Dict[str, Any], 
                                  feedback: Dict[str, Any]) -> Dict[str, Any]:
        """改善フィードバックの適用"""
        try:
            # 改善提案の検証
            if not self._validate_improvement(feedback['content']):
                raise ValueError("無効な改善提案です")
                
            # 結果の更新
            updated_results = results.copy()
            updated_results['improvements'] = updated_results.get('improvements', [])
            updated_results['improvements'].append({
                'suggestion': feedback['content']['suggestion'],
                'impact': feedback['content']['impact'],
                'priority': feedback['content']['priority'],
                'created_at': datetime.now(timezone.utc)
            })
                
            return updated_results
            
        except Exception as e:
            logger.error(f"改善フィードバック適用でエラー: {str(e)}")
            raise

    def _apply_bug_report_feedback(self, results: Dict[str, Any], 
                                 feedback: Dict[str, Any]) -> Dict[str, Any]:
        """バグレポートフィードバックの適用"""
        try:
            # バグレポートの検証
            if not self._validate_bug_report(feedback['content']):
                raise ValueError("無効なバグレポートです")
                
            # 結果の更新
            updated_results = results.copy()
            updated_results['bug_reports'] = updated_results.get('bug_reports', [])
            updated_results['bug_reports'].append({
                'description': feedback['content']['description'],
                'severity': feedback['content']['severity'],
                'steps_to_reproduce': feedback['content']['steps'],
                'reported_at': datetime.now(timezone.utc)
            })
                
            return updated_results
            
        except Exception as e:
            logger.error(f"バグレポートフィードバック適用でエラー: {str(e)}")
            raise

    def _store_feedback_history(self, feedback_id: str, source_id: str,
                              feedback: Dict[str, Any]) -> None:
        """フィードバック履歴の保存"""
        try:
            # MongoDBに詳細を保存
            feedback_doc = {
                'feedback_id': feedback_id,
                'source_id': source_id,
                'feedback_type': feedback['feedback_type'],
                'content': feedback['content'],
                'user_id': feedback['user_id'],
                'created_at': datetime.now(timezone.utc)
            }
            self._mongo_db.feedback_history.insert_one(feedback_doc)
            
            # PostgreSQLにメタデータを保存
            with self._pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO feedback_history (
                        feedback_id, source_id, feedback_type,
                        user_id, created_at
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    feedback_id,
                    source_id,
                    feedback['feedback_type'],
                    feedback['user_id'],
                    datetime.now(timezone.utc)
                ))
                self._pg_conn.commit()
                
        except Exception as e:
            if self._pg_conn:
                self._pg_conn.rollback()
            logger.error(f"フィードバック履歴保存でエラー: {str(e)}")
            raise

    def _get_service_pid(self, service_name: str) -> Optional[int]:
        """サービスのPID取得"""
        try:
            pid_file = Path(f"/var/run/cobana/{service_name}.pid")
            if not pid_file.exists():
                return None
                
            pid = int(pid_file.read_text().strip())
            if not psutil.pid_exists(pid):
                return None
                
            return pid
        except Exception as e:
            logger.error(f"サービスPID取得でエラー: {str(e)}")
            return None

    def _check_task_queue(self) -> Dict[str, Any]:
        """タスクキューの状態確認"""
        try:
            # キュー接続の確認
            queue_status = {
                'connected': False,
                'queue_size': 0,
                'processing': 0
            }
            
            # RabbitMQの状態確認
            queue_info = self._mongo_db.task_queue_status.find_one(
                sort=[('created_at', -1)]
            )
            if queue_info and (datetime.now(timezone.utc) - queue_info['created_at']).seconds < 60:
                queue_status.update({
                    'connected': True,
                    'queue_size': queue_info['queue_size'],
                    'processing': queue_info['processing_tasks']
                })
                
            return queue_status
        except Exception as e:
            logger.error(f"タスクキュー確認でエラー: {str(e)}")
            return {'connected': False, 'error': str(e)}

    def _check_task_processing(self) -> Dict[str, Any]:
        """タスク処理状態の確認"""
        try:
            processing_status = {
                'healthy': False,
                'active_workers': 0,
                'completed_tasks': 0,
                'failed_tasks': 0
            }
            
            # ワーカーの状態確認
            workers = self._mongo_db.worker_status.find({
                'last_heartbeat': {'$gte': datetime.now(timezone.utc) - timedelta(minutes=5)}
            })
            
            active_workers = list(workers)
            if not active_workers:
                return processing_status
                
            # タスク処理状況の集計
            task_stats = self._mongo_db.task_statistics.find_one(
                sort=[('created_at', -1)]
            )
            
            if task_stats:
                processing_status.update({
                    'healthy': True,
                    'active_workers': len(active_workers),
                    'completed_tasks': task_stats['completed_count'],
                    'failed_tasks': task_stats['failed_count']
                })
                
            return processing_status
        except Exception as e:
            logger.error(f"タスク処理状態確認でエラー: {str(e)}")
            return {'healthy': False, 'error': str(e)}

    def _start_service_process(self, service_name: str, config: Dict[str, Any]) -> None:
        """サービスプロセスの起動"""
        try:
            # プロセス起動コマンドの構築
            cmd = [
                'python',
                f'services/{service_name}.py',
                '--config', json.dumps(config)
            ]
            
            # プロセス起動
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # PIDファイルの作成
            pid_dir = Path("/var/run/cobana")
            pid_dir.mkdir(parents=True, exist_ok=True)
            
            with open(pid_dir / f"{service_name}.pid", 'w') as f:
                f.write(str(process.pid))
                
        except Exception as e:
            logger.error(f"サービスプロセス起動でエラー: {str(e)}")
            raise

    def _wait_for_service(self, service_type: str, timeout: int = 30) -> bool:
        """サービス起動の待機"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self._check_service_response(service_type):
                    return True
                time.sleep(1)
            return False
        except Exception as e:
            logger.error(f"サービス待機でエラー: {str(e)}")
            return False

    def _start_task_workers(self, config: Dict[str, Any]) -> None:
        """タスクワーカーの起動"""
        try:
            worker_count = config.get('worker_count', 3)
            
            for i in range(worker_count):
                worker_name = f"worker_{i+1}"
                worker_config = {
                    **config,
                    'worker_id': worker_name
                }
                
                # ワーカープロセスの起動
                self._start_service_process(
                    f"task_worker_{i+1}",
                    worker_config
                )
                
        except Exception as e:
            logger.error(f"タスクワーカー起動でエラー: {str(e)}")
            raise

    def _check_workers_status(self, timeout: int = 30) -> bool:
        """ワーカーの状態確認"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                status = self._check_task_processing()
                if status['healthy'] and status['active_workers'] > 0:
                    return True
                time.sleep(1)
            return False
        except Exception as e:
            logger.error(f"ワーカー状態確認でエラー: {str(e)}")
            return False

    def _validate_improvement(self, content: Dict[str, Any]) -> bool:
        """改善提案の検証"""
        try:
            required_fields = ['suggestion', 'impact', 'priority']
            if not all(field in content for field in required_fields):
                return False
                
            if not isinstance(content['suggestion'], str):
                return False
                
            if content['impact'] not in ['high', 'medium', 'low']:
                return False
                
            if not isinstance(content['priority'], int) or not (1 <= content['priority'] <= 5):
                return False
                
            return True
        except Exception as e:
            logger.error(f"改善提案検証でエラー: {str(e)}")
            return False

    def _validate_bug_report(self, content: Dict[str, Any]) -> bool:
        """バグレポートの検証"""
        try:
            required_fields = ['description', 'severity', 'steps']
            if not all(field in content for field in required_fields):
                return False
                
            if not isinstance(content['description'], str):
                return False
                
            if content['severity'] not in ['critical', 'high', 'medium', 'low']:
                return False
                
            if not isinstance(content['steps'], list):
                return False
                
            return True
        except Exception as e:
            logger.error(f"バグレポート検証でエラー: {str(e)}")
            return False