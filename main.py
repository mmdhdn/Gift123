import asyncio
import time

from pyrogram import Client
from pyrogram.errors import StargiftUsageLimited

from config import sleep_send_seconds, sleep_checking_seconds, sessions_for_checking, send_config, is_test_mode, gift_filters, is_infinite_buying
from helper import get_logger
from model import SendFromTo

class GiftFlashBuyer:
    def __init__(self):
        self.checker_logger = get_logger("Checker")
        self.new_gifts = None

    async def check_new_gifts(self, session_list, len_old):
        while True:
            for session in session_list:
                data_gifts = await session.get_available_gifts()    # чекаем новые подарки
                self.checker_logger.info(f"Checked")
                if not is_test_mode:
                    gifts_limit = [i.id for i in data_gifts if i.is_limited]   # создание списка лимитированных подарков для сравнения
                else:
                    gifts_limit = [i.id for i in data_gifts]
                if len(gifts_limit) > len_old:   # если появились новые подарки
                    return data_gifts
            await asyncio.sleep(sleep_checking_seconds)

    async def buy_gifts(self, config: SendFromTo):
        acc_logger = get_logger(config.session_name_send_from)

        async with Client(config.session_name_send_from) as app:  # запускаем основной аккаунт
            balance = await app.get_stars_balance()
            for gift in self.new_gifts:  # цикл по всем подаркам начиная с самого маленького саплая
                if not any(
                        f.supply_range[0] <= gift['total'] <= f.supply_range[1] and
                        f.price_range[0] <= gift['price'] <= f.price_range[1]
                        for f in gift_filters
                ):
                    continue

                count_gifts = balance // gift['price']  # считаем сколько подарков можем купить
                if not count_gifts:  # переходим к следующему если не хватает баланса
                    acc_logger.exception(f"Not enough stars balance {balance} to buy gift-{gift['id']} for price {gift['price']} stars")
                    continue

                acc_logger.exception(f"Trying to buy gift-{gift['id']} for price {gift['price']} stars")
                for _ in range(count_gifts):
                    try:
                        await app.send_gift(config.username_send_to, gift['id'], is_private=True)
                        await asyncio.sleep(sleep_send_seconds)
                        acc_logger.exception(f"Gift gift-{gift['id']} was buyed sucessfully")
                    except StargiftUsageLimited:
                        acc_logger.exception(f"Oops, [{config.session_name_send_from} --> {config.username_send_to}] gift with price {gift['price']}: StargiftUsageLimited'", exc_info=True)
                        break  # если кончился саплай переходим к следующему подарку
                    except Exception as e:
                        acc_logger.exception("Unexcepted exception", exc_info=True)

                balance = await app.get_stars_balance()

            acc_logger.info(f"[{config.session_name_send_from} --> {config.username_send_to}] done")

    async def main(self):
        session_list = [Client(session) for session in sessions_for_checking]
        self.checker_logger.info(f"Available sessions: {len(session_list)}")
        try:
            for i, session in enumerate(session_list):
                await session.start()
                self.checker_logger.info(f"Started session: {sessions_for_checking[i]}")
            head_logger.info("Started program")
            old_gifts = await session_list[0].get_available_gifts()   # получения списка подарков для сравнения и обнаружения новых
            if not is_test_mode:
                old_gifts = {i.id for i in old_gifts if i.is_limited}  # создание множество лимитированных подарков для сравнения
            else:
                old_gifts = {i.id for i in old_gifts[2:]}  # test cache, 2 gifts
            self.checker_logger.info(f"Old limited gifts count (Cache): {len(old_gifts)}")
            self.checker_logger.info(f"Checking new gifts")
            data_gifts = await self.check_new_gifts(session_list, len(old_gifts))
        finally:
            for session in session_list:
                await session.stop()

        if not is_test_mode:
            gifts_limit_dict = {gift.id: gift for gift in data_gifts if gift.is_limited}    # создания словаря из подарков для обращения к подарку по id
        else:
            gifts_limit_dict = {gift.id: gift for gift in data_gifts}
        self.new_gifts = [gifts_limit_dict[gift_id] for gift_id in gifts_limit_dict.keys() if gift_id not in old_gifts]     # отбираем новые подарки по id
        self.new_gifts = [{"id": gift.id, "total": gift.total_amount or 0, "price": gift.price} for gift in self.new_gifts]    # получаем саплай и цену для сортировки
        self.new_gifts = sorted(self.new_gifts, key= lambda x:x['total'])   # сортируем по саплаю
        self.checker_logger.info(f"Found new {len(self.new_gifts)} gifts!")

        # запускаем все аккаунты на покупку
        await asyncio.gather(*[self.buy_gifts(config) for config in send_config])

if __name__ == "__main__":
    head_logger = get_logger("Head")

    while True:
        head_logger.info("Do checking")
        try:
            gift_flash_buyer = GiftFlashBuyer()
            asyncio.run(gift_flash_buyer.main())
        except Exception as e:
            head_logger.exception(e)
            break

        if not is_infinite_buying:
            break

    head_logger.info("Program end")
    time.sleep(100000)
