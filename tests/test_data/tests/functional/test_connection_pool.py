import pytest
import threading
import time
from src.db.connection_pool import DatabaseConnectionPool
from src.db.ast_repository import ASTRepository

class TestConnectionPool:
    def setup_method(self):
        self.connection_string = "postgresql://cobana_admin:Kanami1001!@172.16.0.13/cobol_analysis_db"
        self.ast_repo = ASTRepository(connection_string=self.connection_string)

    def test_connection_pool_singleton(self):
        # シングルトンパターンのテスト
        pool1 = DatabaseConnectionPool(dsn=self.connection_string)
        pool2 = DatabaseConnectionPool(dsn=self.connection_string)
        assert pool1 is pool2

    def test_connection_reuse(self):
        # コネクション再利用のテスト
        with self.ast_repo.get_connection() as conn1:
            status1 = self.ast_repo.pool.get_status()
            with self.ast_repo.get_connection() as conn2:
                status2 = self.ast_repo.pool.get_status()
                assert status2['active_connections'] == status1['active_connections'] + 1

    def test_concurrent_connections(self):
        # 同時接続のテスト
        def worker():
            with self.ast_repo.get_connection() as conn:
                time.sleep(0.1)  # 接続を少し保持
                cur = conn.cursor()
                cur.execute("SELECT 1")

        threads = []
        for _ in range(5):  # 5つの同時接続
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # すべての接続が正しく解放されていることを確認
        status = self.ast_repo.pool.get_status()
        assert status['active_connections'] == 0

    def test_connection_limit(self):
        # 最大接続数の制限テスト
        connections = []
        max_conn = self.ast_repo.pool.pool.maxconn

        # 最大接続数まで接続を作成
        for _ in range(max_conn):
            conn = self.ast_repo.pool.pool.getconn()
            connections.append(conn)

        # これ以上の接続は失敗するはず
        with pytest.raises(Exception):
            self.ast_repo.pool.pool.getconn()

        # クリーンアップ
        for conn in connections:
            self.ast_repo.pool.pool.putconn(conn) 