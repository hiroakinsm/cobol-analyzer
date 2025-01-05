import pytest
import psycopg2
import threading
import time
from src.db.ast_repository import ASTRepository
from src.db.metadata_repository import MetadataRepository

class TestComplexDatabaseErrors:
    def setup_method(self):
        self.connection_string = "postgresql://cobana_admin:Kanami1001!@172.16.0.13/cobol_analysis_db"
        self.ast_repo = ASTRepository(connection_string=self.connection_string)
        self.metadata_repo = MetadataRepository(connection_string=self.connection_string)

    def test_transaction_rollback(self):
        # トランザクション失敗とロールバックのテスト
        program_id = "PROG001"
        
        with self.ast_repo._get_connection() as conn:
            with conn.cursor() as cur:
                # トランザクション開始
                cur.execute("BEGIN")
                
                # 正常なクエリ
                cur.execute("SELECT * FROM ast_nodes WHERE program_id = %s", (program_id,))
                
                # 不正なクエリ（エラーを発生させる）
                with pytest.raises(psycopg2.Error):
                    cur.execute("INSERT INTO nonexistent_table VALUES (1)")
                
                # ロールバックされることを確認
                assert conn.get_transaction_status() == psycopg2.extensions.TRANSACTION_STATUS_INERROR

    def test_deadlock_detection(self):
        # デッドロックの検出テスト
        def transaction1(repo):
            with repo._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("BEGIN")
                    cur.execute("LOCK TABLE ast_nodes IN ACCESS EXCLUSIVE MODE")
                    time.sleep(2)  # デッドロックを発生させるための待機
                    cur.execute("SELECT * FROM program_metadata")

        def transaction2(repo):
            with repo._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("BEGIN")
                    cur.execute("LOCK TABLE program_metadata IN ACCESS EXCLUSIVE MODE")
                    time.sleep(2)  # デッドロックを発生させるための待機
                    cur.execute("SELECT * FROM ast_nodes")

        # 2つのトランザクションを同時実行
        thread1 = threading.Thread(target=transaction1, args=(self.ast_repo,))
        thread2 = threading.Thread(target=transaction2, args=(self.ast_repo,))

        with pytest.raises(psycopg2.OperationalError) as exc_info:
            thread1.start()
            thread2.start()
            thread1.join()
            thread2.join()

        assert "deadlock detected" in str(exc_info.value).lower()

    def test_query_timeout(self):
        # クエリタイムアウトのテスト
        with self.ast_repo._get_connection() as conn:
            with conn.cursor() as cur:
                # タイムアウトを1ミリ秒に設定
                cur.execute("SET statement_timeout = 1")
                
                # 重い処理を実行
                with pytest.raises(psycopg2.OperationalError) as exc_info:
                    cur.execute("""
                        WITH RECURSIVE deep_tree AS (
                            SELECT id, parent_id, 1 as depth
                            FROM ast_nodes
                            UNION ALL
                            SELECT a.id, a.parent_id, dt.depth + 1
                            FROM ast_nodes a
                            JOIN deep_tree dt ON a.parent_id = dt.id
                            WHERE dt.depth < 1000000
                        )
                        SELECT * FROM deep_tree
                    """)

                assert "statement timeout" in str(exc_info.value).lower()

    def test_connection_pool_exhaustion(self):
        # 接続プール枯渇のテスト
        connections = []
        max_connections = 5  # テスト用の最大接続数
        
        try:
            # 最大接続数を超えて接続を作成
            for _ in range(max_connections + 1):
                conn = psycopg2.connect(self.connection_string)
                connections.append(conn)
        except psycopg2.OperationalError as e:
            assert "too many connections" in str(e).lower()
        finally:
            # 接続をクリーンアップ
            for conn in connections:
                conn.close() 