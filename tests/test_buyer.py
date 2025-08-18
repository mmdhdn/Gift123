import asyncio

from tg_gift_buyer.models import Gift
from tg_gift_buyer.buyer import GiftBuyer
from tg_gift_buyer.mtproto import MTProtoClient


class DummyAPI(MTProtoClient):
    def __init__(self):
        pass

    async def buy_gift(self, gift_id: int, amount: int, recipient: str):
        return {"ok": True, "gift_id": gift_id, "amount": amount, "recipient": recipient}


def test_buyer_simulation():
    gift = Gift(id=1, title="G", price=10)
    buyer = GiftBuyer(DummyAPI(), ["@user"], simulation=True)
    res = asyncio.run(buyer.buy(gift, 1))
    assert res.success
