import psycopg2
from psycopg2.extras import DictCursor
from src.db.error_handler import DatabaseErrorHandler, with_retry
from src.db.base_repository import BaseRepository, with_auto_reconnect

class ASTRepository(BaseRepository):
    def __init__(self, connection_string):
        connection_params = {
            'dsn': connection_string,
            'min_conn': 2,
            'max_conn': 10
        }
        super().__init__(connection_params)
        self.error_handler = DatabaseErrorHandler()

    @with_auto_reconnect()
    def get_ast(self, program_id):
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    query = "SELECT * FROM ast_nodes WHERE program_id = %s"
                    cur.execute(query, (program_id,))
                    return cur.fetchall()
        except psycopg2.Error as e:
            self.error_handler.handle_query_error(e, query=query, params={"program_id": program_id})

    @with_auto_reconnect()
    def get_call_statements(self, program_id):
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    query = "SELECT * FROM ast_nodes WHERE program_id = %s AND node_type = 'CALL'"
                    cur.execute(query, (program_id,))
                    return cur.fetchall()
        except psycopg2.Error as e:
            self.error_handler.handle_query_error(e, query=query, params={"program_id": program_id})

    @with_auto_reconnect()
    def get_copy_statements(self, program_id):
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    query = "SELECT * FROM ast_nodes WHERE program_id = %s AND node_type = 'COPY'"
                    cur.execute(query, (program_id,))
                    return cur.fetchall()
        except psycopg2.Error as e:
            self.error_handler.handle_query_error(e, query=query, params={"program_id": program_id})

    def validate_program_id(self, program_id):
        try:
            if not program_id:
                raise ValueError("Program ID cannot be empty")
            if not program_id.isalnum():
                raise ValueError("Program ID must be alphanumeric")
            if len(program_id) > 8:
                raise ValueError("Program ID cannot exceed 8 characters")
            return True
        except ValueError as e:
            self.error_handler.handle_validation_error(e, "program_id", program_id)

    @with_auto_reconnect()
    def get_ast_nodes_by_type(self, program_id, node_type):
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    query = "SELECT * FROM ast_nodes WHERE program_id = %s AND node_type = %s"
                    cur.execute(query, (program_id, node_type))
                    return cur.fetchall()
        except psycopg2.Error as e:
            self.error_handler.handle_query_error(e, query=query, params={
                "program_id": program_id,
                "node_type": node_type
            })

    def validate_node_data(self, node):
        try:
            required_fields = ['id', 'program_id', 'node_type', 'node_value']
            for field in required_fields:
                if field not in node:
                    raise KeyError(f"Required field '{field}' is missing")
            return True
        except KeyError as e:
            self.error_handler.handle_validation_error(e, "node_data", node) 