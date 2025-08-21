from __future__ import annotations

"""Real MTProto calls for Telegram star gifts using Telethon."""

from typing import Tuple, List, Optional

try:  # pragma: no cover - telethon may be missing in tests
    from telethon import functions, types, errors
except Exception:  # pragma: no cover - provide minimal stubs
    class errors:  # type: ignore
        class RPCError(Exception):
            def __init__(self, message: str = "") -> None:
                super().__init__(message)
                self.message = message

        class FloodWaitError(RPCError):
            def __init__(self, seconds: int) -> None:
                super().__init__(f"FLOOD_WAIT_{seconds}")
                self.seconds = seconds

    class types:  # type: ignore
        class StarGift:
            def __init__(
                self,
                id: int,
                title: str | None = None,
                stars: int = 0,
                availability_total: int | None = None,
                availability_remains: int | None = None,
                rarity: str | None = None,
                premium: bool | None = None,
            ) -> None:
                self.id = id
                self.title = title
                self.stars = stars
                self.availability_total = availability_total
                self.availability_remains = availability_remains
                self.rarity = rarity
                self.premium = premium

        class InputUser:
            def __init__(self, user_id: int = 0, access_hash: int = 0) -> None:
                self.user_id = user_id
                self.access_hash = access_hash

        class InputPeerUser(InputUser):
            pass

        class TextWithEntities:
            def __init__(self, text: str = "", entities: Optional[List] = None) -> None:
                self.text = text
                self.entities = entities or []

        class InputInvoiceStarGift:
            def __init__(
                self,
                user_id: "types.InputUser",
                gift_id: int,
                hide_name: bool = False,
                message: Optional["types.TextWithEntities"] = None,
            ) -> None:
                self.user_id = user_id
                self.gift_id = gift_id
                self.hide_name = hide_name
                self.message = message

    class _Payments:
        class GetStarGiftsRequest:
            def __init__(self, hash: int) -> None:
                self.hash = hash

        class GetPaymentFormRequest:
            def __init__(self, invoice: "types.InputInvoiceStarGift") -> None:
                self.invoice = invoice

        class SendStarsFormRequest:
            def __init__(self, form_id: int, invoice: "types.InputInvoiceStarGift") -> None:
                self.form_id = form_id
                self.invoice = invoice

    class functions:  # type: ignore
        payments = _Payments()


class GiftApiError(RuntimeError):
    """Raised when Telegram API returns an error."""


async def list_gifts(client, last_hash: int = 0) -> Tuple[int, List[types.StarGift]]:
    """Call payments.getStarGifts and return (new_hash, gifts)."""
    try:
        res = await client(functions.payments.GetStarGiftsRequest(hash=last_hash))
        new_hash = getattr(res, "hash", 0)
        gifts = list(getattr(res, "gifts", []))
        return new_hash, gifts
    except errors.RPCError as e:  # pragma: no cover - network error
        raise GiftApiError(f"getStarGifts failed: {e}")


async def resolve_user(client, username_or_id: str) -> types.InputUser:
    """Resolve @username or numeric ID to InputUser."""
    ent = await client.get_input_entity(username_or_id)
    if isinstance(ent, types.InputPeerUser):
        return types.InputUser(user_id=ent.user_id, access_hash=ent.access_hash)
    if not isinstance(ent, types.InputUser):
        raise GiftApiError("Recipient must be a user (not channel).")
    return ent


async def buy_star_gift(
    client,
    recipient: types.InputUser,
    gift_id: int,
    hide_name: bool = False,
    message_entities: Optional[types.TextWithEntities] = None,
):
    """Buy a star gift for the recipient via:
       InputInvoiceStarGift -> payments.getPaymentForm -> payments.sendStarsForm.
    """
    invoice = types.InputInvoiceStarGift(
        peer=recipient,
        gift_id=int(gift_id),
        hide_name=hide_name,
        message=message_entities,
    )
    try:
        form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
        try:
            result = await client(
                functions.payments.SendStarsFormRequest(
                    form_id=getattr(form, "form_id", 0), invoice=invoice
                )
            )
            return result
        except errors.RPCError as e:
            # If payment form expired, fetch a fresh one and retry once.
            if "FORM_EXPIRED" in str(e):
                form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
                result = await client(
                    functions.payments.SendStarsFormRequest(
                        form_id=getattr(form, "form_id", 0), invoice=invoice
                    )
                )
                return result
            name = e.__class__.__name__.upper()
            msg = str(e).upper()
            if "BALANCE" in name and "LOW" in name or "BALANCE_TOO_LOW" in msg:
                # Propagate balance related errors so callers can skip gracefully.
                raise e
            raise GiftApiError(f"sendStarsForm failed: {e}")
    except errors.FloodWaitError:  # pragma: no cover - caller should handle
        raise
    except errors.RPCError as e:  # pragma: no cover - network error
        raise GiftApiError(f"sendStarsForm failed: {e}")


__all__ = ["GiftApiError", "list_gifts", "resolve_user", "buy_star_gift", "types", "errors", "functions"]
