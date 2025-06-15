from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List

@dataclass
class CardapioItem:
    id: str
    descricao: str
    valor: Decimal