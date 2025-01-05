import psycopg2
from psycopg2.extras import DictCursor

class MetadataRepository:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def get_metadata(self, program_id):
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(
                    "SELECT * FROM program_metadata WHERE program_id = %s",
                    (program_id,)
                )
                return cur.fetchone() 