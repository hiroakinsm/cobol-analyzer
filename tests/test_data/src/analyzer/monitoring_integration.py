from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import psutil
import aiohttp
import json
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """監視設定"""
    app_name: str = "cobol-analyzer"
    prometheus_gateway: str = "http://localhost:9091"
    alert_threshold: Dict[str, float] = None
    check_interval: float = 60.0  # 秒
    metrics_retention: int = 1440  # 24時間分
    alert_channels: List[str] = None
    
    def __post_init__(self):
        if self.alert_threshold is None:
            self.alert_threshold = {
                'cpu_usage': 80.0,
                'memory_usage': 85.0,
                'error_rate': 0.05,
                'response_time': 2.0
            }
        if self.alert_channels is None:
            self.alert_channels = ['slack', 'email']

class MonitoringIntegration:
    """監視機能を統合管理するクラス"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self._registry = CollectorRegistry()
        self._setup_metrics()
        self._metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._is_monitoring = False

    def _setup_metrics(self):
        """メトリクスの初期設定"""
        try:
            self._metrics = {
                'cpu_usage': Gauge('cpu_usage_percent', 
                                 'CPU使用率', 
                                 registry=self._registry),
                'memory_usage': Gauge('memory_usage_percent', 
                                    'メモリ使用率', 
                                    registry=self._registry),
                'error_rate': Gauge('error_rate', 
                                  'エラー率', 
                                  registry=self._registry),
                'response_time': Gauge('response_time_seconds', 
                                     'レスポンス時間', 
                                     registry=self._registry)
            }
        except Exception as e:
            logger.error(f"メトリクス設定でエラー: {str(e)}")

    async def start_monitoring(self):
        """監視の開始"""
        try:
            self._is_monitoring = True
            while self._is_monitoring:
                await self._collect_metrics()
                await self._check_alerts()
                await self._push_metrics()
                await asyncio.sleep(self.config.check_interval)
        except Exception as e:
            logger.error(f"監視開始でエラー: {str(e)}")
            self._is_monitoring = False

    async def stop_monitoring(self):
        """監視の停止"""
        self._is_monitoring = False

    async def _collect_metrics(self):
        """メトリクスの収集"""
        try:
            # システムメトリクス
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            
            # アプリケーションメトリクス
            app_metrics = await self._collect_app_metrics()
            
            # メトリクスの更新
            self._metrics['cpu_usage'].set(cpu_usage)
            self._metrics['memory_usage'].set(memory_usage)
            self._metrics['error_rate'].set(app_metrics.get('error_rate', 0))
            self._metrics['response_time'].set(app_metrics.get('response_time', 0))
            
            # 履歴の保存
            self._store_metrics_history({
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                **app_metrics
            })
            
        except Exception as e:
            logger.error(f"メトリクス収集でエラー: {str(e)}")

    async def _collect_app_metrics(self) -> Dict[str, float]:
        """アプリケーションメトリクスの収集"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8080/metrics") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'error_rate': data.get('error_rate', 0),
                            'response_time': data.get('response_time', 0)
                        }
            return {}
        except Exception as e:
            logger.error(f"アプリケーションメトリクス収集でエラー: {str(e)}")
            return {}

    def _store_metrics_history(self, metrics: Dict[str, Any]):
        """メトリクス履歴の保存"""
        try:
            timestamp = datetime.now()
            for metric_name, value in metrics.items():
                if metric_name not in self._metrics_history:
                    self._metrics_history[metric_name] = []
                
                self._metrics_history[metric_name].append({
                    'timestamp': timestamp.isoformat(),
                    'value': value
                })
                
                # 古いデータの削除
                cutoff_time = timestamp - timedelta(minutes=self.config.metrics_retention)
                self._metrics_history[metric_name] = [
                    m for m in self._metrics_history[metric_name]
                    if datetime.fromisoformat(m['timestamp']) > cutoff_time
                ]
        except Exception as e:
            logger.error(f"メトリクス履歴保存でエラー: {str(e)}")

    async def _check_alerts(self):
        """アラートのチェック"""
        try:
            current_metrics = {
                name: metric._value.get() 
                for name, metric in self._metrics.items()
            }
            
            for metric_name, threshold in self.config.alert_threshold.items():
                current_value = current_metrics.get(metric_name)
                if current_value is not None and current_value > threshold:
                    await self._create_alert(
                        metric_name, 
                        current_value, 
                        threshold
                    )
        except Exception as e:
            logger.error(f"アラートチェックでエラー: {str(e)}")

    async def _create_alert(self, 
                          metric_name: str, 
                          current_value: float, 
                          threshold: float):
        """アラートの作成"""
        try:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'metric': metric_name,
                'value': current_value,
                'threshold': threshold,
                'message': f"{metric_name}が閾値を超過: {current_value} > {threshold}"
            }
            
            self._alerts.append(alert)
            
            # アラートの通知
            for channel in self.config.alert_channels:
                await self._send_alert(channel, alert)
                
        except Exception as e:
            logger.error(f"アラート作成でエラー: {str(e)}")

    async def _send_alert(self, channel: str, alert: Dict[str, Any]):
        """アラートの送信"""
        try:
            if channel == 'slack':
                await self._send_slack_alert(alert)
            elif channel == 'email':
                await self._send_email_alert(alert)
        except Exception as e:
            logger.error(f"アラート送信でエラー: {str(e)}")

    async def _push_metrics(self):
        """メトリクスのプッシュ"""
        try:
            push_to_gateway(
                self.config.prometheus_gateway,
                job=self.config.app_name,
                registry=self._registry
            )
        except Exception as e:
            logger.error(f"メトリクスプッシュでエラー: {str(e)}")

    def get_metrics_history(self, 
                          metric_name: str = None, 
                          start_time: datetime = None) -> Dict[str, Any]:
        """メトリクス履歴の取得"""
        try:
            if metric_name:
                history = self._metrics_history.get(metric_name, [])
            else:
                history = self._metrics_history
                
            if start_time:
                if metric_name:
                    return [
                        m for m in history
                        if datetime.fromisoformat(m['timestamp']) >= start_time
                    ]
                else:
                    return {
                        name: [
                            m for m in metrics
                            if datetime.fromisoformat(m['timestamp']) >= start_time
                        ]
                        for name, metrics in history.items()
                    }
            
            return history
        except Exception as e:
            logger.error(f"メトリクス履歴取得でエラー: {str(e)}")
            return {}

    def get_alerts(self, 
                  start_time: datetime = None, 
                  metric_name: str = None) -> List[Dict[str, Any]]:
        """アラート履歴の取得"""
        try:
            alerts = self._alerts
            
            if start_time:
                alerts = [
                    a for a in alerts
                    if datetime.fromisoformat(a['timestamp']) >= start_time
                ]
            
            if metric_name:
                alerts = [
                    a for a in alerts
                    if a['metric'] == metric_name
                ]
            
            return alerts
        except Exception as e:
            logger.error(f"アラート履歴取得でエラー: {str(e)}")
            return [] 