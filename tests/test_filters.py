from tg_gift_buyer.models import StarGiftModel, GiftFilter
from tg_gift_buyer.filters import gift_matches


def test_price_and_type():
    gift = StarGiftModel(
        id=1,
        title="Gift1",
        stars=100,
        limited=False,
        sold_out=False,
        type="unlimited"
    )
    flt = GiftFilter(min_price=50, max_price=200, gift_types=["unlimited"])
    assert gift_matches(gift, [flt])

    flt2 = GiftFilter(min_price=150)
    assert not gift_matches(gift, [flt2])


def test_supply_and_sold_out():
    gift = StarGiftModel(
        id=2,
        title="Gift2",
        stars=100,
        limited=True,
        sold_out=False,
        availability_remains=5,
        type="limited"
    )
    flt = GiftFilter(min_supply=1, max_supply=10, gift_types=["limited"])
    assert gift_matches(gift, [flt])

    flt2 = GiftFilter(min_supply=6, gift_types=["limited"])
    assert not gift_matches(gift, [flt2])

    gift.sold_out = True
    assert not gift_matches(gift, [flt])
