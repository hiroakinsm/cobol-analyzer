from typing import Dict, Any, List, Optional, Set
import logging
import asyncio
import json
from datetime import datetime
from dataclasses import dataclass
import websockets
from websockets.server import WebSocketServerProtocol
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class UpdaterConfig:
    """リアルタイム更新の設定"""
    host: str = "0.0.0.0"
    port: int = 8765
    update_interval: float = 1.0  # 更新間隔（秒）
    max_clients: int = 100
    history_size: int = 1000
    allowed_topics: Set[str] = None

    def __post_init__(self):
        if self.allowed_topics is None:
            self.allowed_topics = {
                'system_metrics',
                'analysis_status',
                'performance_metrics',
                'error_alerts'
            }

class RealtimeUpdater:
    """リアルタイム更新を管理するクラス"""
    
    def __init__(self, config: UpdaterConfig):
        self.config = config
        self._clients: Set[WebSocketServerProtocol] = set()
        self._data_cache: Dict[str, deque] = {
            topic: deque(maxlen=config.history_size)
            for topic in config.allowed_topics
        }
        self._running = False
        self._server = None

    async def start(self):
        """更新サービスの開始"""
        try:
            self._running = True
            self._server = await websockets.serve(
                self._handle_client,
                self.config.host,
                self.config.port
            )
            logger.info(f"リアルタイム更新サービスを開始: {self.config.host}:{self.config.port}")
            
            # 更新タスクの開始
            asyncio.create_task(self._update_loop())
            
            await self._server.wait_closed()
            
        except Exception as e:
            logger.error(f"更新サービス開始でエラー: {str(e)}")
            self._running = False

    async def stop(self):
        """更新サービスの停止"""
        try:
            self._running = False
            if self._server:
                self._server.close()
                await self._server.wait_closed()
            
            # クライアント接続のクローズ
            for client in self._clients:
                await client.close()
            self._clients.clear()
            
            logger.info("リアルタイム更新サービスを停止しました")
        except Exception as e:
            logger.error(f"更新サービス停止でエラー: {str(e)}")

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """クライアント接続の処理"""
        try:
            # クライアント数の制限チェック
            if len(self._clients) >= self.config.max_clients:
                await websocket.close(1013, "最大接続数に達しました")
                return

            # クライアントの登録
            self._clients.add(websocket)
            logger.info(f"新しいクライアント接続: {websocket.remote_address}")

            try:
                # 初期データの送信
                await self._send_initial_data(websocket)
                
                # クライアントメッセージの処理
                async for message in websocket:
                    await self._process_client_message(websocket, message)
                    
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                # クライアントの登録解除
                self._clients.remove(websocket)
                logger.info(f"クライアント切断: {websocket.remote_address}")
                
        except Exception as e:
            logger.error(f"クライアント処理でエラー: {str(e)}")

    async def _update_loop(self):
        """定期的な更新ループ"""
        try:
            while self._running:
                # 最新データの収集
                updates = await self._collect_updates()
                
                # 全クライアントへの送信
                if updates:
                    await self._broadcast_updates(updates)
                
                await asyncio.sleep(self.config.update_interval)
                
        except Exception as e:
            logger.error(f"更新ループでエラー: {str(e)}")
            self._running = False

    async def _collect_updates(self) -> Dict[str, Any]:
        """更新データの収集"""
        try:
            updates = {}
            
            # システムメトリクス
            system_metrics = await self._get_system_metrics()
            if system_metrics:
                updates['system_metrics'] = system_metrics
            
            # 解析状況
            analysis_status = await self._get_analysis_status()
            if analysis_status:
                updates['analysis_status'] = analysis_status
            
            # パフォーマンスメトリクス
            performance_metrics = await self._get_performance_metrics()
            if performance_metrics:
                updates['performance_metrics'] = performance_metrics
            
            return updates
            
        except Exception as e:
            logger.error(f"更新データ収集でエラー: {str(e)}")
            return {}

    async def _broadcast_updates(self, updates: Dict[str, Any]):
        """全クライアントへの更新送信"""
        try:
            message = {
                'type': 'update',
                'timestamp': datetime.now().isoformat(),
                'data': updates
            }
            
            # 切断されたクライアントの検出用
            disconnected = set()
            
            # 全クライアントへの送信
            for client in self._clients:
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
                except Exception as e:
                    logger.error(f"クライアント {client.remote_address} への送信でエラー: {str(e)}")
                    disconnected.add(client)
            
            # 切断されたクライアントの削除
            for client in disconnected:
                self._clients.remove(client)
                
        except Exception as e:
            logger.error(f"更新ブロードキャストでエラー: {str(e)}")

    async def _send_initial_data(self, websocket: WebSocketServerProtocol):
        """初期データの送信"""
        try:
            # キャッシュされた履歴データの送信
            initial_data = {
                topic: list(self._data_cache[topic])
                for topic in self.config.allowed_topics
            }
            
            message = {
                'type': 'initial',
                'timestamp': datetime.now().isoformat(),
                'data': initial_data
            }
            
            await websocket.send(json.dumps(message))
            
        except Exception as e:
            logger.error(f"初期データ送信でエラー: {str(e)}")

    async def _process_client_message(self, 
                                   websocket: WebSocketServerProtocol, 
                                   message: str):
        """クライアントメッセージの処理"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                # トピックの購読
                topics = data.get('topics', [])
                await self._handle_subscription(websocket, topics)
            elif message_type == 'unsubscribe':
                # トピックの購読解除
                topics = data.get('topics', [])
                await self._handle_unsubscription(websocket, topics)
                
        except json.JSONDecodeError:
            logger.error("不正なJSONメッセージを受信")
        except Exception as e:
            logger.error(f"クライアントメッセージ処理でエラー: {str(e)}")

    def update_cache(self, topic: str, data: Any):
        """キャッシュデータの更新"""
        try:
            if topic in self.config.allowed_topics:
                self._data_cache[topic].append({
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                })
        except Exception as e:
            logger.error(f"キャッシュ更新でエラー: {str(e)}") 