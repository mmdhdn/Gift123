from dataclasses import dataclass
from typing import Tuple

@dataclass
class GiftFilterDontBuy:
    supply_range: Tuple[float, float]
    price_range: Tuple[float, float]

@dataclass
class SendFromTo:
    session_name_send_from: str
    username_send_to: str