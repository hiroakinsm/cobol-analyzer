from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VisualizerConfig:
    """可視化の設定"""
    plot_width: int = 1200
    plot_height: int = 800
    theme: str = "plotly_dark"
    max_points: int = 1000
    update_interval: int = 60  # 更新間隔（秒）
    export_format: str = "html"

class MetricsVisualizer:
    """メトリクスの可視化を管理するクラス"""
    
    def __init__(self, config: VisualizerConfig):
        self.config = config
        self._current_figures: Dict[str, go.Figure] = {}
        self._data_cache: Dict[str, List[Dict[str, Any]]] = {}

    def create_dashboard(self, metrics_data: Dict[str, Any]) -> str:
        """ダッシュボードの作成"""
        try:
            # サブプロットの作成
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'System Resources', 'Performance Metrics',
                    'Error Rates', 'Response Times',
                    'Batch Processing', 'Network Activity'
                ),
                specs=[[{'type': 'indicator'}, {'type': 'scatter'}],
                      [{'type': 'scatter'}, {'type': 'scatter'}],
                      [{'type': 'bar'}, {'type': 'scatter'}]]
            )

            # システムリソースのゲージ
            self._add_system_gauges(fig, metrics_data.get('system', {}))
            
            # パフォーマンスメトリクスの時系列
            self._add_performance_trends(fig, metrics_data.get('performance', {}))
            
            # エラー率の棒グラフ
            self._add_error_bars(fig, metrics_data.get('errors', {}))
            
            # レスポンスタイムの分布
            self._add_response_distribution(fig, metrics_data.get('response_times', []))
            
            # バッチ処理の状況
            self._add_batch_metrics(fig, metrics_data.get('batch', {}))
            
            # ネットワークアクティビティ
            self._add_network_activity(fig, metrics_data.get('network', {}))

            # レイアウトの設定
            self._configure_layout(fig)
            
            # HTMLファイルとして保存
            output_path = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            fig.write_html(output_path)
            
            return output_path

        except Exception as e:
            logger.error(f"ダッシュボード作成でエラー: {str(e)}")
            return ""

    def _add_system_gauges(self, fig: go.Figure, system_data: Dict[str, Any]):
        """システムリソースゲージの追加"""
        try:
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=system_data.get('cpu_usage', 0),
                    title={'text': "CPU Usage (%)"},
                    gauge={'axis': {'range': [0, 100]},
                          'threshold': {'line': {'color': "red", 'width': 4},
                                      'value': 80}},
                    domain={'row': 0, 'column': 0}
                )
            )
        except Exception as e:
            logger.error(f"システムゲージ追加でエラー: {str(e)}")

    def _add_performance_trends(self, fig: go.Figure, perf_data: Dict[str, Any]):
        """パフォーマンストレンドの追加"""
        try:
            timestamps = perf_data.get('timestamps', [])
            values = perf_data.get('values', [])
            
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=values,
                    mode='lines',
                    name='Performance'
                ),
                row=1, col=2
            )
        except Exception as e:
            logger.error(f"パフォーマンストレンド追加でエラー: {str(e)}")

    def _add_error_bars(self, fig: go.Figure, error_data: Dict[str, Any]):
        """エラー率の棒グラフ追加"""
        try:
            categories = list(error_data.keys())
            values = list(error_data.values())
            
            fig.add_trace(
                go.Bar(
                    x=categories,
                    y=values,
                    name='Errors'
                ),
                row=2, col=1
            )
        except Exception as e:
            logger.error(f"エラー棒グラフ追加でエラー: {str(e)}")

    def _add_response_distribution(self, fig: go.Figure, response_times: List[float]):
        """レスポンスタイム分布の追加"""
        try:
            fig.add_trace(
                go.Histogram(
                    x=response_times,
                    nbinsx=30,
                    name='Response Times'
                ),
                row=2, col=2
            )
        except Exception as e:
            logger.error(f"レスポンス分布追加でエラー: {str(e)}")

    def _add_batch_metrics(self, fig: go.Figure, batch_data: Dict[str, Any]):
        """バッチ処理メトリクスの追加"""
        try:
            timestamps = batch_data.get('timestamps', [])
            sizes = batch_data.get('sizes', [])
            
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=sizes,
                    mode='lines+markers',
                    name='Batch Sizes'
                ),
                row=3, col=1
            )
        except Exception as e:
            logger.error(f"バッチメトリクス追加でエラー: {str(e)}")

    def _add_network_activity(self, fig: go.Figure, network_data: Dict[str, Any]):
        """ネットワークアクティビティの追加"""
        try:
            timestamps = network_data.get('timestamps', [])
            incoming = network_data.get('incoming', [])
            outgoing = network_data.get('outgoing', [])
            
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=incoming,
                    mode='lines',
                    name='Incoming'
                ),
                row=3, col=2
            )
            
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=outgoing,
                    mode='lines',
                    name='Outgoing'
                ),
                row=3, col=2
            )
        except Exception as e:
            logger.error(f"ネットワークアクティビティ追加でエラー: {str(e)}")

    def _configure_layout(self, fig: go.Figure):
        """レイアウトの設定"""
        try:
            fig.update_layout(
                template=self.config.theme,
                width=self.config.plot_width,
                height=self.config.plot_height,
                showlegend=True,
                title_text="System Metrics Dashboard",
                title_x=0.5
            )
        except Exception as e:
            logger.error(f"レイアウト設定でエラー: {str(e)}")

    def export_metrics(self, 
                      metrics_data: Dict[str, Any], 
                      format: str = None) -> str:
        """メトリクスのエクスポート"""
        try:
            export_format = format or self.config.export_format
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if export_format == 'csv':
                return self._export_to_csv(metrics_data, timestamp)
            elif export_format == 'html':
                return self._export_to_html(metrics_data, timestamp)
            else:
                logger.error(f"未対応のエクスポート形式: {export_format}")
                return ""
                
        except Exception as e:
            logger.error(f"メトリクスエクスポートでエラー: {str(e)}")
            return ""

    def _export_to_csv(self, metrics_data: Dict[str, Any], timestamp: str) -> str:
        """CSVへのエクスポート"""
        try:
            df = pd.DataFrame(metrics_data)
            output_path = f"metrics_{timestamp}.csv"
            df.to_csv(output_path, index=False)
            return output_path
        except Exception as e:
            logger.error(f"CSV出力でエラー: {str(e)}")
            return ""

    def _export_to_html(self, metrics_data: Dict[str, Any], timestamp: str) -> str:
        """HTMLへのエクスポート"""
        try:
            dashboard_path = self.create_dashboard(metrics_data)
            return dashboard_path
        except Exception as e:
            logger.error(f"HTML出力でエラー: {str(e)}")
            return "" 