from typing import List
from model import GiftFilterDontBuy, SendFromTo
import toml

# Загружаем конфиг из файла
config = toml.load("config.toml")

# Распаковываем переменные напрямую
sessions_for_checking = config["sessions_for_checking"]
send_config = [SendFromTo(**item) for item in config["send_config"]]
sleep_send_seconds = config["sleep_send_seconds"]
sleep_checking_seconds = config["sleep_checking_seconds"]
is_test_mode = config["is_test_mode"]
test_mode_max_balance = config["test_mode_max_balance"]
is_infinite_buying = config["is_infinite_buying"]

# Обрабатываем gift_filters с преобразованием 'inf' в float('inf')
gift_filters = [
    GiftFilterDontBuy(
        supply_range=(
            int(item["supply_range"][0]),
            float('inf') if item["supply_range"][1] == "inf" else int(item["supply_range"][1])
        ),
        price_range=(
            int(item["price_range"][0]),
            float('inf') if item["price_range"][1] == "inf" else int(item["price_range"][1])
        )
    )
    for item in config["gift_filters"]
]