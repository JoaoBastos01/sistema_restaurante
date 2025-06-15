from db import get_db
from flask_login import UserMixin
from psycopg2.extras import DictCursor
from typing import TypedDict, cast

class UserData(TypedDict):
    id: int
    username: str
    password_hash: str
    role: str

class User(UserMixin):
    id: int
    username: str
    password_hash: str
    role: str

    def __init__(self, id: int, username: str, password_hash: str, role: str):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def get(user_id):
        conn = get_db()
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
            user_data = cur.fetchone()
            if not user_data:
                return None

            typed_user_data = cast(UserData, user_data)
            return User(**typed_user_data)