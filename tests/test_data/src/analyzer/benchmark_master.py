from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkMetric:
    """ベンチマーク評価指標"""
    category: str
    sub_category: str
    metric_name: str
    description: str
    unit: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    target_value: Optional[float]
    warning_threshold: Optional[float]
    error_threshold: Optional[float]
    evaluation_rule: Optional[str]
    weight: float = 1.0

@dataclass
class BenchmarkStandard:
    """ベンチマーク基準値"""
    standard_type: str  # 'industry', 'organization', 'project'
    standard_name: str
    target_value: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    description: Optional[str]
    source_reference: Optional[str]

class BenchmarkMasterManager:
    """ベンチマーク評価基準のマスタ管理"""
    
    def __init__(self, master_dir: str = "masters/benchmarks"):
        self._master_dir = master_dir
        self._metrics: Dict[str, BenchmarkMetric] = {}
        self._standards: Dict[str, Dict[str, BenchmarkStandard]] = {}
        self._load_masters()

    def _load_masters(self):
        """マスタ情報の読み込み"""
        try:
            # メトリクス定義の読み込み
            metrics_file = os.path.join(self._master_dir, "benchmark_metrics.json")
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics_data = json.load(f)
                    for metric_data in metrics_data:
                        metric = BenchmarkMetric(**metric_data)
                        key = f"{metric.category}.{metric.sub_category}.{metric.metric_name}"
                        self._metrics[key] = metric

            # 基準値定義の読み込み
            standards_file = os.path.join(self._master_dir, "benchmark_standards.json")
            if os.path.exists(standards_file):
                with open(standards_file, 'r', encoding='utf-8') as f:
                    standards_data = json.load(f)
                    for standard_data in standards_data:
                        metric_key = f"{standard_data['category']}.{standard_data['sub_category']}.{standard_data['metric_name']}"
                        if metric_key not in self._standards:
                            self._standards[metric_key] = {}
                        
                        standard = BenchmarkStandard(
                            standard_type=standard_data['standard_type'],
                            standard_name=standard_data['standard_name'],
                            target_value=standard_data.get('target_value'),
                            min_value=standard_data.get('min_value'),
                            max_value=standard_data.get('max_value'),
                            description=standard_data.get('description'),
                            source_reference=standard_data.get('source_reference')
                        )
                        standard_key = f"{standard.standard_type}.{standard.standard_name}"
                        self._standards[metric_key][standard_key] = standard

        except Exception as e:
            logger.error(f"ベンチマークマスタ読み込みでエラー: {str(e)}")
            raise

    def get_metric(self, category: str, sub_category: str, metric_name: str) -> Optional[BenchmarkMetric]:
        """メトリクス定義の取得"""
        key = f"{category}.{sub_category}.{metric_name}"
        return self._metrics.get(key)

    def get_standards(self, category: str, sub_category: str, metric_name: str) -> Dict[str, BenchmarkStandard]:
        """基準値定義の取得"""
        key = f"{category}.{sub_category}.{metric_name}"
        return self._standards.get(key, {})

    def evaluate_metric(self, category: str, sub_category: str, metric_name: str, value: float) -> Dict[str, Any]:
        """メトリクス値の評価"""
        try:
            metric = self.get_metric(category, sub_category, metric_name)
            if not metric:
                return {'status': 'unknown', 'message': 'メトリクス定義が見つかりません'}

            result = {
                'value': value,
                'target': metric.target_value,
                'status': 'normal',
                'violations': []
            }

            # 閾値チェック
            if metric.error_threshold is not None and value >= metric.error_threshold:
                result['status'] = 'error'
                result['violations'].append(f'エラー閾値 {metric.error_threshold} を超過')
            elif metric.warning_threshold is not None and value >= metric.warning_threshold:
                result['status'] = 'warning'
                result['violations'].append(f'警告閾値 {metric.warning_threshold} を超過')

            # 範囲チェック
            if metric.min_value is not None and value < metric.min_value:
                result['violations'].append(f'最小値 {metric.min_value} を下回り')
            if metric.max_value is not None and value > metric.max_value:
                result['violations'].append(f'最大値 {metric.max_value} を超過')

            # カスタム評価ルール
            if metric.evaluation_rule:
                try:
                    rule_result = eval(metric.evaluation_rule, {'value': value})
                    if not rule_result:
                        result['violations'].append('カスタム評価ルールに違反')
                except Exception as e:
                    logger.error(f"評価ルール実行でエラー: {str(e)}")

            return result

        except Exception as e:
            logger.error(f"メトリクス評価でエラー: {str(e)}")
            return {'status': 'error', 'message': str(e)} 