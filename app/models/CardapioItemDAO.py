from DbConnection import DbConnection
from typing import Optional
from CardapioItem import CardapioItem

class CardapioItemDAO():

    def __init__(self, connection: DbConnection):
        self.connection = connection

    def get_by_id(self, id: str) -> Optional[CardapioItem]:
        query = """
            SELECT descricao, valor, categoria 
            FROM cardapio_itens 
            WHERE id = %s
        """
        data = self.connection.fetch_one(query, (id))
        
        if not data:
            return None
        
        item = CardapioItem(id, data["descricao"], data["valor"], data["categoria"])
        return item
    
    def get_all(self):
        query = """
            SELECT descricao, valor, categoria 
            FROM cardapio_itens 
        """
        data = self.connection.fetch_all(query)
        
        itens = [
            CardapioItem(id, item["descricao"], item["valor"], item["categoria"])
            for item in data
        ]
        
        return itens