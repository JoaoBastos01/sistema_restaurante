class ItemCardapioDAO:
    def __init__(self, conn):
        self.conn = conn

    def listar_itens_disponiveis(self):
        """
        Retorna todos os itens disponíveis no cardápio.
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, description, price
                FROM itens_cardapio
                WHERE available = TRUE
                ORDER BY name;
            """)
            return cur.fetchall()

    def buscar_item_por_id(self, item_id):
        """
        Retorna um único item do cardápio pelo ID.
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, description, price
                FROM itens_cardapio
                WHERE id = %s;
            """, (item_id,))
            return cur.fetchone()