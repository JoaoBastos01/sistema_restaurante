from app.db import get_connection

class UsuarioDAO:
    @staticmethod
    def autenticar(email, senha):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, is_admin FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
        usuario = cur.fetchone()
        cur.close()
        conn.close()
        return usuario

    @staticmethod
    def registrar(nome, email, senha):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (nome, email, senha, is_admin) VALUES (%s, %s, %s, false)", (nome, email, senha))
        conn.commit()
        cur.close()
        conn.close()
