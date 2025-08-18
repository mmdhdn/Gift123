import asyncio
from types import SimpleNamespace
import asyncio
from types import SimpleNamespace

from tg_gift_buyer import mtproto


def test_list_gifts():
    class FakeClient:
        async def __call__(self, request):
            assert isinstance(request, mtproto.functions.payments.GetStarGiftsRequest)
            return SimpleNamespace(hash=123, gifts=[mtproto.types.StarGift(id=1, stars=5)])

    client = FakeClient()
    new_hash, gifts = asyncio.run(mtproto.list_gifts(client, 0))
    assert new_hash == 123
    assert gifts[0].id == 1


def test_buy_star_gift_flow():
    calls = []

    class FakeClient:
        async def __call__(self, request):
            calls.append(type(request))
            if isinstance(request, mtproto.functions.payments.GetPaymentFormRequest):
                return SimpleNamespace(form_id=7)
            if isinstance(request, mtproto.functions.payments.SendStarsFormRequest):
                return SimpleNamespace(ok=True)
            raise AssertionError("Unexpected request")

        async def get_input_entity(self, username):
            return mtproto.types.InputPeerUser(user_id=1, access_hash=2)

    client = FakeClient()
    recipient = asyncio.run(mtproto.resolve_user(client, "@user"))
    res = asyncio.run(mtproto.buy_star_gift(client, recipient, 42))
    assert hasattr(res, "ok")
    assert calls.count(mtproto.functions.payments.GetPaymentFormRequest) == 1
    assert calls.count(mtproto.functions.payments.SendStarsFormRequest) == 1


def test_buy_star_gift_retries_form_expired():
    class FakeClient:
        def __init__(self):
            self.form_calls = 0
            self.send_calls = 0

        async def __call__(self, request):
            if isinstance(request, mtproto.functions.payments.GetPaymentFormRequest):
                self.form_calls += 1
                return SimpleNamespace(form_id=1)
            if isinstance(request, mtproto.functions.payments.SendStarsFormRequest):
                self.send_calls += 1
                if self.send_calls == 1:
                    raise mtproto.errors.RPCError("FORM_EXPIRED")
                return SimpleNamespace(ok=True)
            raise AssertionError

    client = FakeClient()
    recipient = mtproto.types.InputUser(user_id=1, access_hash=2)
    res = asyncio.run(mtproto.buy_star_gift(client, recipient, 1))
    assert hasattr(res, "ok")
    assert client.form_calls == 2
    assert client.send_calls == 2
