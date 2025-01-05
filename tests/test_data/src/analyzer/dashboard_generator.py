from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class DashboardMetrics:
    """ダッシュボード用メトリクス"""
    total_programs: int = 0
    total_lines: int = 0
    average_complexity: float = 0.0
    quality_score: float = 0.0
    risk_level: str = "LOW"
    trend_data: Dict[str, List[float]] = None
    
    def __post_init__(self):
        if self.trend_data is None:
            self.trend_data = defaultdict(list)

class DashboardGenerator:
    """ダッシュボードデータの生成を管理するクラス"""
    
    def __init__(self, persistence_manager):
        self.persistence = persistence_manager

    async def generate_dashboard_data(self, time_range: str = "1w") -> Dict[str, Any]:
        """ダッシュボードデータの生成"""
        try:
            # 基本メトリクスの収集
            metrics = await self._collect_dashboard_metrics(time_range)
            
            # トレンドデータの生成
            trends = await self._generate_trend_data(time_range)
            
            # 品質指標の計算
            quality = await self._calculate_quality_indicators()
            
            # リスク分析
            risks = await self._analyze_risks()
            
            return {
                'metrics': metrics,
                'trends': trends,
                'quality': quality,
                'risks': risks,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"ダッシュボードデータ生成でエラー: {str(e)}")
            return {}

    async def _collect_dashboard_metrics(self, time_range: str) -> DashboardMetrics:
        """基本メトリクスの収集"""
        try:
            # 時間範囲の計算
            end_date = datetime.now()
            start_date = self._calculate_start_date(end_date, time_range)
            
            # PostgreSQLからメトリクスを取得
            async with self.persistence.pg_pool.acquire() as conn:
                metrics = await conn.fetch('''
                    SELECT 
                        COUNT(DISTINCT source_id) as total_programs,
                        SUM(total_lines) as total_lines,
                        AVG(cyclomatic_complexity) as avg_complexity,
                        AVG(maintainability_index) as avg_maintainability
                    FROM analysis_metrics
                    WHERE timestamp BETWEEN $1 AND $2
                ''', start_date, end_date)
                
                if metrics and metrics[0]:
                    return DashboardMetrics(
                        total_programs=metrics[0]['total_programs'],
                        total_lines=metrics[0]['total_lines'] or 0,
                        average_complexity=metrics[0]['avg_complexity'] or 0.0,
                        quality_score=metrics[0]['avg_maintainability'] or 0.0,
                        risk_level=self._calculate_risk_level(
                            metrics[0]['avg_complexity'] or 0.0,
                            metrics[0]['avg_maintainability'] or 0.0
                        )
                    )
                return DashboardMetrics()
        except Exception as e:
            logger.error(f"メトリクス収集でエラー: {str(e)}")
            return DashboardMetrics()

    async def _generate_trend_data(self, time_range: str) -> Dict[str, List[Dict[str, Any]]]:
        """トレンドデータの生成"""
        try:
            end_date = datetime.now()
            start_date = self._calculate_start_date(end_date, time_range)
            
            # 日次のメトリクスを取得
            async with self.persistence.pg_pool.acquire() as conn:
                daily_metrics = await conn.fetch('''
                    SELECT 
                        DATE_TRUNC('day', timestamp) as date,
                        AVG(cyclomatic_complexity) as complexity,
                        AVG(maintainability_index) as maintainability,
                        COUNT(DISTINCT source_id) as programs_analyzed
                    FROM analysis_metrics
                    WHERE timestamp BETWEEN $1 AND $2
                    GROUP BY DATE_TRUNC('day', timestamp)
                    ORDER BY date
                ''', start_date, end_date)
            
            trends = {
                'complexity': [],
                'maintainability': [],
                'analysis_volume': []
            }
            
            for metric in daily_metrics:
                date_str = metric['date'].isoformat()
                trends['complexity'].append({
                    'date': date_str,
                    'value': float(metric['complexity'] or 0)
                })
                trends['maintainability'].append({
                    'date': date_str,
                    'value': float(metric['maintainability'] or 0)
                })
                trends['analysis_volume'].append({
                    'date': date_str,
                    'value': int(metric['programs_analyzed'])
                })
            
            return trends
        except Exception as e:
            logger.error(f"トレンドデータ生成でエラー: {str(e)}")
            return {}

    async def _calculate_quality_indicators(self) -> Dict[str, Any]:
        """品質指標の計算"""
        try:
            # MongoDBから品質メトリクスを取得
            db = self.persistence.mongo_client.cobol_analysis
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'maintainability': {'$avg': '$metrics.maintainability_index'},
                        'reliability': {'$avg': '$metrics.reliability_score'},
                        'documentation': {'$avg': '$metrics.documentation.comment_ratio'},
                        'issues_count': {'$sum': {'$size': '$details.potential_issues'}}
                    }
                }
            ]
            
            result = await db.analysis_details.aggregate(pipeline).to_list(length=1)
            
            if result and result[0]:
                metrics = result[0]
                return {
                    'overall_score': self._calculate_overall_quality(metrics),
                    'maintainability': metrics['maintainability'] or 0,
                    'reliability': metrics['reliability'] or 0,
                    'documentation': metrics['documentation'] or 0,
                    'issues_density': metrics['issues_count'] / 1000  # 1000行あたりの問題数
                }
            return {}
        except Exception as e:
            logger.error(f"品質指標計算でエラー: {str(e)}")
            return {}

    async def _analyze_risks(self) -> Dict[str, Any]:
        """リスク分析の実行"""
        try:
            db = self.persistence.mongo_client.cobol_analysis
            
            # 高リスクの条件を定義
            high_risk_conditions = {
                'cyclomatic_complexity': {'$gt': 20},
                'maintainability_index': {'$lt': 65},
                '$or': [
                    {'details.potential_issues.severity': 'HIGH'},
                    {'details.quality_metrics.reliability.error_handling.coverage': {'$lt': 50}}
                ]
            }
            
            # リスク分析の実行
            risk_analysis = await db.analysis_details.aggregate([
                {'$match': high_risk_conditions},
                {'$group': {
                    '_id': None,
                    'high_risk_count': {'$sum': 1},
                    'risk_sources': {'$push': '$source_id'},
                    'common_issues': {'$push': '$details.potential_issues'}
                }}
            ]).to_list(length=1)
            
            if risk_analysis and risk_analysis[0]:
                return {
                    'high_risk_programs': risk_analysis[0]['high_risk_count'],
                    'risk_sources': risk_analysis[0]['risk_sources'][:10],  # 上位10件
                    'common_issues': self._summarize_common_issues(
                        risk_analysis[0]['common_issues']
                    )
                }
            return {}
        except Exception as e:
            logger.error(f"リスク分析でエラー: {str(e)}")
            return {}

    def _calculate_start_date(self, end_date: datetime, time_range: str) -> datetime:
        """時間範囲の開始日を計算"""
        range_map = {
            '1d': timedelta(days=1),
            '1w': timedelta(weeks=1),
            '1m': timedelta(days=30),
            '3m': timedelta(days=90),
            '6m': timedelta(days=180),
            '1y': timedelta(days=365)
        }
        return end_date - range_map.get(time_range, range_map['1w'])

    def _calculate_risk_level(self, complexity: float, maintainability: float) -> str:
        """リスクレベルの計算"""
        if complexity > 20 or maintainability < 65:
            return "HIGH"
        elif complexity > 10 or maintainability < 75:
            return "MEDIUM"
        return "LOW"

    def _calculate_overall_quality(self, metrics: Dict[str, float]) -> float:
        """総合品質スコアの計算"""
        weights = {
            'maintainability': 0.4,
            'reliability': 0.3,
            'documentation': 0.3
        }
        
        score = sum(
            metrics.get(key, 0) * weight
            for key, weight in weights.items()
        )
        
        return min(max(score, 0), 100)  # 0-100の範囲に正規化

    def _summarize_common_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """共通の問題点をサマリ化"""
        issue_counts = defaultdict(int)
        for issue_list in issues:
            for issue in issue_list:
                issue_type = issue.get('type', 'UNKNOWN')
                issue_counts[issue_type] += 1
        
        return dict(sorted(
            issue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])  # 上位10件の問題を返す 