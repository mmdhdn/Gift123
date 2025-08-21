import asyncio

from tg_gift_buyer.models import StarGiftModel
from tg_gift_buyer.buyer import GiftBuyer
from tg_gift_buyer import mtproto


class DummyClient:
    session_name = "sess"


def make_gift():
    return StarGiftModel(
        id=1,
        title="G",
        stars=10,
        limited=False,
        sold_out=False,
        type="unlimited",
    )


def test_buyer_simulation():
    gift = make_gift()
    buyer = GiftBuyer(DummyClient(), ["@user"], simulation=True)
    res = asyncio.run(buyer.buy(gift, 1))
    assert res.success


def test_buyer_precheck_skip(monkeypatch):
    gift = make_gift()
    buyer = GiftBuyer(DummyClient(), ["@user"], skip_on_low_balance=True)
    buyer._balance_cache = 5  # price 10 > balance 5

    called = {"resolve": False, "buy": False}

    async def fake_resolve(client, recipient):
        called["resolve"] = True
        return object()

    async def fake_buy(client, user, gift_id):
        called["buy"] = True
        return None

    monkeypatch.setattr(mtproto, "resolve_user", fake_resolve)
    monkeypatch.setattr(mtproto, "buy_star_gift", fake_buy)

    res = asyncio.run(buyer.buy(gift, 1))
    assert not res.success
    assert res.message == "skipped_low_balance"
    assert not called["resolve"] and not called["buy"]


def test_buyer_low_balance_rpc_error(monkeypatch):
    gift = make_gift()

    async def fake_resolve(client, recipient):
        return object()

    async def fake_buy(client, user, gift_id):
        raise mtproto.errors.RPCError(None, "BALANCE_TOO_LOW")

    monkeypatch.setattr(mtproto, "resolve_user", fake_resolve)
    monkeypatch.setattr(mtproto, "buy_star_gift", fake_buy)

    buyer = GiftBuyer(DummyClient(), ["@user"], skip_on_low_balance=True)
    res = asyncio.run(buyer.buy(gift, 1))
    assert not res.success
    assert res.message == "skipped_low_balance"

    buyer2 = GiftBuyer(DummyClient(), ["@user"], skip_on_low_balance=False)
    res2 = asyncio.run(buyer2.buy(gift, 1))
    assert not res2.success
    assert "BALANCE_TOO_LOW" in res2.message
