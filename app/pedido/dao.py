from app.db import get_connection

class PedidoDAO:
    def __init__(self,conn):
        self.conn = conn
        
    def registrar(cliente_id, itens_json):
        cur = self.conn.cursor()
        cur.execute("CALL registrar_pedido(%s, %s::jsonb)", (cliente_id, itens_json))
        self.conn.commit()
        cur.close()

    def listar_pedidos(status):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM listar_pedidos(%s)", (status,))
        pedidos = cur.fetchall()
        cur.close()
        return pedidos

    def detalhar_pedido(pedido_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM detalhar_pedido(%s)", (pedido_id,))
        detalhes = cur.fetchone()
        cur.close()
        return detalhes

    def atualizar_status(pedido_id, novo_status):
        cur = self.conn.cursor()
        cur.execute("CALL atualizar_status_pedido(%s, %s)", (pedido_id, novo_status))
        self.conn.commit()
        cur.close()