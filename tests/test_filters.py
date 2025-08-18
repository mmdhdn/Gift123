from tg_gift_buyer.models import Gift, FilterBlock
from tg_gift_buyer.filters import gift_matches


def test_gift_matches():
    gift = Gift(id=1, title="G", price=100, supply=10, gift_type="limited")
    filt = FilterBlock(min_price=50, max_price=150)
    assert gift_matches(gift, [filt])
    filt2 = FilterBlock(min_price=200)
    assert not gift_matches(gift, [filt2])
