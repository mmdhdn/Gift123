import asyncio
import random
import time

import pyrogram
from pyrogram import Client
from pyrogram.errors import StargiftUsageLimited, FormSubmitDuplicate, FloodWait

from config import sleep_checking_seconds, sessions_for_checking, send_config, is_test_mode, gift_filters, is_infinite_buying
from helper import get_logger
from model import SendFromTo, Sessions, Session, SessionType, GiftsCache
from task_manager import TaskManager

sessions: Sessions = Sessions()

async def account_starter():
    """
    Стартует сессии для проверки подарков и покупки подарков.
    После старта каждой сессии для покупки отправляет сообщение в указанный канал
    с информацией о балансе и логикой покупки.
    """
    account_starter_logger = get_logger("AccStarter")
    account_starter_logger.info(f"Starting checker sessions")
    # запускаем сессии для проверки наличия новых подарков
    for session_name in sessions_for_checking:
        is_successfully_started = await sessions.add_session(
            session_name_file=session_name,
            is_checker=True,
            logger=account_starter_logger
        )

    account_starter_logger.info(f"Starting buyer sessions")
    # запускаем сессии для покупки подарков
    for cfg in send_config:
        is_successfully_started = await sessions.add_session(
            session_name_file=cfg.session_name_send_from,
            is_buying=True,
            logger=account_starter_logger
        )
        # если сессия была успешно создана, отправляем приветственное сообщение в канал
        try:
            # получаем объект сессии
            session_obj = next((s for s in sessions.available if s.name == cfg.session_name_send_from), None)
            if session_obj and session_obj.cli:
                # Формируем строку с диапазонами для покупки
                filter_strings = []
                for f in gift_filters:
                    supply_start, supply_end = f.supply_range
                    price_start, price_end = f.price_range
                    # форматируем бесконечность
                    supply_end_str = "∞" if supply_end == float('inf') else str(int(supply_end))
                    price_end_str = "∞" if price_end == float('inf') else str(int(price_end))
                    filter_strings.append(f"{int(price_start)}-{price_end_str} ({int(supply_start)}-{supply_end_str})")
                # Собираем приветственное сообщение
                stars_balance = session_obj.balance_available
                message_lines = [
                    "✅ Gifts Buyer Successfully Started",
                    "",
                    f"Your current balance: {stars_balance} ⭐",
                    "",
                    "📝 Gift purchase logic:",
                    "According to your configured ranges:",
                    "نوع و مقدار سفارش",
                    "",
                ]
                for fs in filter_strings:
                    message_lines.append(f"• {fs}")
                message_lines.append("💡 Gifts outside the specified criteria will be automatically skipped")
                # Соединяем строки
                message_text = "\n".join(message_lines)
                # отправляем сообщение в канал/пользователю
                await session_obj.cli.send_message(cfg.username_send_to, message_text)
        except Exception as e:
            # если отправка не удалась, логируем, но продолжаем работу
            account_starter_logger.exception(f"Failed to send start message for {cfg.session_name_send_from}: {e}", exc_info=True)


class GiftFlashBuyer:
    def __init__(self):
        self.main_logger = get_logger("Main")
        self.new_gifts = None
        self.task_manager_checker = TaskManager()
        self.gift_cache = GiftsCache()

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

        # определяем получателя подарка/канал
        send_to = None
        for cfg in send_config:
            if session.name == cfg.session_name_send_from:
                send_to = cfg.username_send_to

        attempts = 0
        max_attempts = 30
        while attempts < max_attempts:
            try:
                await session.cli.send_gift(send_to, gift.id, is_private=True, text="gift from @kod4dusha")
                buyer_logger.info(f"Gift {GiftsCache.log_gift_string(gift)} was buyed sucessfully")
                # отправляем отчёт о покупке
                try:
                    await session.cli.send_message(send_to, f"✅ Gift purchased successfully:\n{GiftsCache.log_gift_string(gift)}")
                except Exception as e_send:
                    buyer_logger.exception(f"Failed to send purchase report: {e_send}", exc_info=True)
                break
            except StargiftUsageLimited:
                buyer_logger.exception(f"Oops, [{session.name} --> {send_to}] {GiftsCache.log_gift_string(gift)}: StargiftUsageLimited'", exc_info=True)
                # отправляем отчёт об ошибке
                try:
                    await session.cli.send_message(send_to, f"⚠️ Cannot buy gift due to usage limit:\n{GiftsCache.log_gift_string(gift)}")
                except Exception as e_send:
                    buyer_logger.exception(f"Failed to send error report: {e_send}", exc_info=True)
                break
            except FloodWait as e:
                buyer_logger.exception(f"FloodWait Error, waiting for {e.value}sec", exc_info=True)
                # отправляем отчёт о FloodWait
                try:
                    await session.cli.send_message(send_to, f"⏳ Flood wait {e.value} sec while buying gift:\n{GiftsCache.log_gift_string(gift)}")
                except Exception as e_send:
                    buyer_logger.exception(f"Failed to send flood wait report: {e_send}", exc_info=True)
                await asyncio.sleep(e.value)
            except FormSubmitDuplicate:
                wait_time = 0.3
                buyer_logger.exception(f"FormSubmitDuplicate Error, waiting for {wait_time}sec", exc_info=True)
                # отправляем отчёт о дублировании
                try:
                    await session.cli.send_message(send_to, f"⚠️ Duplicate form submission; retrying:\n{GiftsCache.log_gift_string(gift)}")
                except Exception as e_send:
                    buyer_logger.exception(f"Failed to send duplicate form report: {e_send}", exc_info=True)
                await asyncio.sleep(wait_time)
            except Exception as e:
                buyer_logger.exception("Unexcepted exception", exc_info=True)
                # отправляем отчёт о неожиданных ошибках
                try:
                    await session.cli.send_message(send_to, f"❌ Unexpected error: {e} while buying gift:\n{GiftsCache.log_gift_string(gift)}")
                except Exception as e_send:
                    buyer_logger.exception(f"Failed to send unexpected error report: {e_send}", exc_info=True)
                await asyncio.sleep(0.3)

        buyer_logger.info(f"[{session.name} --> {send_to}] done")

    async def main(self):
        self.main_logger.info("Started program")

        self.main_logger.info("Checking gifts")
        await self.task_manager_checker.run([self.check_gifts_from_session(session) for session in sessions.checker_sessions])
        self.main_logger.info("Stoped checking gifts")

        if not self.gift_cache.new_gifts_available:
            self.main_logger.info("No new gifts availbale, stopping main")
            return

        self.main_logger.info("Сreating buying tasks")
        tasks_buy = []
        for session in sessions.buyer_sessions:
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

async def loop_infinite():
    head_logger = get_logger("Head")

    # стартуем аккаунты
    await account_starter()

    while True:
        head_logger.info("Started")
        try:
            gift_flash_buyer = GiftFlashBuyer()
            await gift_flash_buyer.main()
        except Exception as e:
            head_logger.exception(e)
            break

        if not is_infinite_buying:
            break

        if is_test_mode:
            break

    head_logger.info("Program end")
    time.sleep(100000)

if __name__ == "__main__":
    asyncio.run(loop_infinite())