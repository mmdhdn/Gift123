import asyncio
import logging
from types import SimpleNamespace

from tg_gift_buyer import runner, mtproto
from tg_gift_buyer.models import GiftFilter


def test_simulation_does_not_buy(monkeypatch, caplog):
    async def fake_list_gifts(client, last_hash):
        gift = mtproto.types.StarGift(id=1, stars=5, availability_total=10, availability_remains=5)
        return 1, [gift]

    async def fake_buy(*args, **kwargs):
        raise AssertionError("buy_star_gift should not be called in simulation")

    monkeypatch.setattr(mtproto, "list_gifts", fake_list_gifts)
    monkeypatch.setattr(mtproto, "buy_star_gift", fake_buy)

    caplog.set_level(logging.INFO)
    flt = GiftFilter()
    asyncio.run(runner.run_monitor(object(), ["@user"], [flt], poll_interval=0, simulation=True, iterations=1))
    assert any("Would buy gift" in r.message for r in caplog.records)
