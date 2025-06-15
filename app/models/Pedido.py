from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List

@dataclass
class PedidoItem:
    id: str
    produto_id: str
    quantidade: int
    valor_unitario: Decimal

    @property
    def total(self) -> Decimal:
        return self.quantidade * self.valor_unitario

@dataclass
class Pedido:
    id: str
    cliente_id: str
    itens: List[PedidoItem] = field(default_factory=list)
    data: datetime

    @property
    def total_amount(self) -> Decimal:
        return sum(item.total for item in self.order_items)