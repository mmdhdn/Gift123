from dataclasses import dataclass, field
from typing import Tuple, List

import loggerex
import pyrogram.client

import config


@dataclass
class GiftFilterDontBuy:
    supply_range: Tuple[float, float]
    price_range: Tuple[float, float]

@dataclass
class SendFromTo:
    session_name_send_from: str
    username_send_to: str

class SessionType:
    checking = 0
    buying = 1

@dataclass
class Session:
    name: str
    is_checker: bool = False
    is_buying: bool = False
    cli: pyrogram.client.Client = None
    balance_available: int = None

    async def start(self):
        self.cli = pyrogram.Client(self.name)
        await self.cli.start()

@dataclass
class Sessions:
    available: List[Session] = field(default_factory=list)

    @property
    def checker_sessions(self):
        return [session for session in self.available if session.is_checker]

    @property
    def buyer_sessions(self):
        return [session for session in self.available if session.is_buying]

    async def add_session(self, session_name_file: str, logger: loggerex.logger, is_checker: bool = False, is_buying: bool = False) -> bool:
        for s in self.available:
            if s.name == session_name_file:
                if is_buying:
                    s.is_buying = is_buying

                if is_checker:
                    s.is_checker = is_checker

                logger.info(f"Session {session_name_file} already started, continuing")
                return False

        session = Session(
            name=session_name_file,
            is_checker=is_checker,
            is_buying=is_buying,
        )
        try:
            await session.start()
            session.balance_available = await session.cli.get_stars_balance()
            # if config.is_test_mode:
            #     session.balance_available = min(config.test_mode_max_balance, session.balance_available)

            me = await session.cli.get_me()
            logger.info(f"Started session: {session.name}, balance: {session.balance_available}, name: {me.first_name} {me.last_name}, username: {me.username}")
            self.available.append(session)
            return True
        except Exception as e:
            logger.exception(f"Unexcepted exception", exc_info=True)

        return False

    async def stop_all(self):
        for session in self.available:
            await session.cli.stop()

@dataclass
class GiftsCache:
    current_gifts: List[pyrogram.types.Gift] = field(default_factory=list)
    new_gifts_available: List[pyrogram.types.Gift] = field(default_factory=list)

    def filter_gifts(self, gifts: List[pyrogram.types.Gift])-> List[pyrogram.types.Gift]:
        if config.is_test_mode:
            return gifts

        filtered_by_limited = [gift for gift in gifts if gift.is_limited]

        filtered_by_supply_price_config = [gift for gift in filtered_by_limited if any(
            f.supply_range[0] <= gift.total_amount <= f.supply_range[1] and
            f.price_range[0] <= gift.price <= f.price_range[1]
            for f in config.gift_filters
        )]

        return filtered_by_supply_price_config

    def init_cache(self, available_gifts):
        filtered_gifts = self.filter_gifts(available_gifts)

        if not self.current_gifts:
            self.current_gifts = list(filtered_gifts)

        if config.is_test_mode:
            self.current_gifts = self.current_gifts[2:]

    def get_new_gifts_available(self, available_gifts_new: List[pyrogram.types.Gift]) -> List[pyrogram.types.Gift]:
        filtered_gifts_new = self.filter_gifts(available_gifts_new)

        current_ids = {gift.id for gift in self.current_gifts}
        new_gifts = [
            gift for gift in filtered_gifts_new
            if gift.id not in current_ids
        ]

        self.new_gifts_available = new_gifts
        # Обновляем кеш новыми данными
        self.current_gifts = list(filtered_gifts_new)

        return new_gifts

    @staticmethod
    def log_gift_string(gift: pyrogram.types.Gift):
        return (
            f"ID: {gift.id} | "
            f"Title: {gift.title} | "
            f"Amount: {gift.total_amount} | "
            f"Price: {gift.price}\n"
        )