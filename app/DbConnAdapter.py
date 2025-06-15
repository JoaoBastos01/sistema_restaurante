from psycopg2.extras import RealDictCursor
from db import get_db
from DbConnection import DbConnection

class DbConnAdapter(DbConnection):
    def _execute(self, sql: str, params: tuple = None, fetch: str = None):
        conn = None
        try:
            conn = get_db()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                if fetch == "one":
                    result = cur.fetchone()
                elif fetch == "all":
                    result = cur.fetchall()
                else:
                    result = None
                    conn.commit()
                return result
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def fetch_one(self, sql: str, params: tuple = None):
        return self._execute(sql, params, fetch="one")

    def fetch_all(self, sql: str, params: tuple = None):
        return self._execute(sql, params, fetch="all")

    def execute_and_commit(self, sql: str, params: tuple = None):
        self._execute(sql, params)