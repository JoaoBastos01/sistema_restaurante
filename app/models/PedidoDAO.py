from DbConnection import DbConnection
from Pedido import Pedido, PedidoItem
from typing import Optional

class PedidoDAO:
    def __init__(self, connection: DbConnection):
        self.connection = connection

    def get_by_id(self, pedido_id: str) -> Optional[Pedido]:
        query_pedido = "SELECT id, cliente_id, data FROM pedidos WHERE id = %s"
        data_pedido = self.connection.fetch_one(query_pedido, (pedido_id,))
        
        if not data_pedido:
            return None
        
        query_itens = """
            SELECT id, produto_id, quantidade, valor_unitario 
            FROM pedidos_itens 
            WHERE pedido_id = %s
        """
        data_itens = self.connection.fetch_all(query_itens, (pedido_id,))
        
        itens = [
            PedidoItem(
                id=item["id"],
                produto_id=item["produto_id"],
                quantidade=item["quantidade"],
                valor_unitario=item["valor_unitario"]
            )
            for item in data_itens
        ]
            
        pedido = Pedido(
            id=data_pedido["id"], 
            cliente_id=data_pedido["cliente_id"], 
            itens=itens, 
            data=data_pedido["data"]
        )

        return pedido