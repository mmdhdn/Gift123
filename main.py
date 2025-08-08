import asyncio
import random
import time

import pyrogram
from pyrogram import Client
from pyrogram.errors import StargiftUsageLimited, FormSubmitDuplicate, FloodWait

from config import sleep_send_seconds, sleep_checking_seconds, sessions_for_checking, send_config, is_test_mode, gift_filters, is_infinite_buying
from helper import get_logger
from model import SendFromTo, Sessions, Session, SessionType, GiftsCache
from task_manager import TaskManager


class GiftFlashBuyer:
    def __init__(self):
        self.main_logger = get_logger("Main")
        self.account_starter_logger = get_logger("AccStarter")
        self.new_gifts = None
        self.task_manager_checker = TaskManager()
        self.gift_cache = GiftsCache()

        self.sessions: Sessions = Sessions()

    async def account_starter(self):
        self.account_starter_logger.info(f"Starting checker sessions")
        for session in sessions_for_checking:
            is_sucessesfully_started = await self.sessions.add_session(
                session_name_file=session,
                is_checker=True,
                logger=self.account_starter_logger
            )

        self.account_starter_logger.info(f"Starting buyer sessions")
        for config in send_config:
            is_sucessesfully_started = await self.sessions.add_session(
                session_name_file=config.session_name_send_from,
                is_buying=True,
                logger=self.account_starter_logger
            )

    async def check_gifts_from_session(self, session: Session):
        checker_logger = get_logger(f"Checker-{session.name}")
        checker_logger.info(f"Started checking")

        while True:
            available_gifts = await session.cli.get_available_gifts()    # чекаем новые подарки
            self.gift_cache.init_cache(available_gifts)

            new_gifts_available = self.gift_cache.get_new_gifts_available(available_gifts)
            if new_gifts_available:
                log_message = "Available new gifts:\n"
                for gift in new_gifts_available:
                    log_message += GiftsCache.log_gift_string(gift)
                checker_logger.info(log_message.strip())
                checker_logger.info("Stopping checker")
                raise StopAsyncIteration

            checker_logger.info(f"Checked")
            await asyncio.sleep(sleep_checking_seconds)

    async def buy_gift(self, session: Session, gift: pyrogram.types.Gift):
        buyer_logger = get_logger(f"Buyer-{session.name}")

        buyer_logger.info(f"Trying to buy gift {GiftsCache.log_gift_string(gift)}")

        send_to = None
        for config in send_config:
            if session.name == config.session_name_send_from:
                send_to = config.username_send_to

        attempts = 0
        max_attempts = 30
        while attempts < max_attempts:
            try:
                await session.cli.send_gift(send_to, gift.id, is_private=True, text="gift from @kod4dusha")
                buyer_logger.info(f"Gift {GiftsCache.log_gift_string(gift)} was buyed sucessfully")
                break
            except StargiftUsageLimited:
                buyer_logger.exception(f"Oops, [{session.name} --> {send_to}] {GiftsCache.log_gift_string(gift)}: StargiftUsageLimited'", exc_info=True)
                break
            except FloodWait as e:
                buyer_logger.exception(f"FloodWait Error, waiting for {e.value}sec", exc_info=True)
                await asyncio.sleep(e.value)
            except FormSubmitDuplicate:
                wait_time = 0.3
                buyer_logger.exception(f"FormSubmitDuplicate Error, waiting for {wait_time}sec", exc_info=True)
                await asyncio.sleep(wait_time)
            except Exception as e:
                buyer_logger.exception("Unexcepted exception", exc_info=True)
                await asyncio.sleep(0.3)

        buyer_logger.info(f"[{session.name} --> {send_to}] done")

    async def main(self):
        await self.account_starter()

        self.main_logger.info("Started program")

        self.main_logger.info("Checking gifts")
        await self.task_manager_checker.run([self.check_gifts_from_session(session) for session in self.sessions.checker_sessions])
        self.main_logger.info("Stoped checking gifts")

        if not self.gift_cache.new_gifts_available:
            self.main_logger.info("No new gifts availbale, stopping main")
            return

        self.main_logger.info("Сreating buying tasks")
        tasks_buy = []
        for session in self.sessions.buyer_sessions:
            while session.balance_available:
                start_balance = session.balance_available

                for gift in self.gift_cache.new_gifts_available:
                    if session.balance_available >= gift.price:
                        tasks_buy.append(self.buy_gift(session, gift))
                        self.main_logger.info(f"Account: {session.name}, buy {GiftsCache.log_gift_string(gift)}")
                        session.balance_available -= gift.price
                    else:
                        self.main_logger.warning(f"Not enough stars balance {session.balance_available} to buy {GiftsCache.log_gift_string(gift)}")
                        continue

                if session.balance_available == start_balance:
                    break

        self.main_logger.info("Starting tasks")
        await self.task_manager_checker.run(tasks_buy)
        self.main_logger.info("Done tasks")

        await self.sessions.stop_all()

if __name__ == "__main__":
    head_logger = get_logger("Head")

    while True:
        head_logger.info("Started")
        try:
            gift_flash_buyer = GiftFlashBuyer()
            asyncio.run(gift_flash_buyer.main())
        except Exception as e:
            head_logger.exception(e)
            break

        if not is_infinite_buying:
            break

        if is_test_mode:
            break

    head_logger.info("Program end")
    time.sleep(100000)
