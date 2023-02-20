from collections import namedtuple
import time
from typing import Generator

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

Update = namedtuple("Update", ["price", "price_change", "price_change_percent", "ts"])


class ETHUSDTMonitor:

    def __init__(self, session: requests.Session,  percent_threshold: float = 1.0, time_interval: int = 60*60):
        self.percent_threshold = percent_threshold
        self.time_interval = time_interval
        self.initial = None
        self.session = session
        self.api_endpoint = 'https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=ETHUSDT'

    def monitor(self) -> None:
        for update in self.get_prices():
            if self.initial is None:
                self.initial = update
            elif update.ts - self.initial.ts >= self.time_interval:
                self.compare(self.initial, update)
                self.initial = update
            self.print_price(update)
            time.sleep(0.5)

    def get_prices(self) -> Generator[Update, None, None]:
        with self.session as session:
            while True:
                try:
                    resp = session.get(self.api_endpoint).json()
                except requests.exceptions.RetryError:
                    raise Exception("Ошибка сети попробуйте еще раз")
                last_price = float(resp["lastPrice"])
                price_change = float(resp["priceChange"])
                price_change_percent = float(resp["priceChangePercent"])
                yield Update(last_price, price_change, price_change_percent, time.monotonic())

    def compare(self, initial: Update, current: Update) -> None:
        percentage = 100 * (current.price - initial.price) / initial.price
        if percentage > self.percent_threshold:
            print("\n")
            print(f"Цена поднялась на  {percentage}% процентов за данный период")
            print("Текущая цена: ", current.price)
            print("\n")
        elif percentage < -self.percent_threshold:
            print("\n")
            print(f"Цена снизилась на  {-percentage}% процентов за данный период")
            print("Текущая цена: ", current.price)
            print("\n")
        else:
            print("\n")
            print(f"Текущий процент изменения: {percentage} %")
            print("Текущая цена: ", current.price)
            print("\n")

    def print_price(self, update: Update) -> None:
        print("Текущая цена: ", update.price)
        print("Процент изменения: ", update.price_change_percent, "%")
        print("Изменение стоимости: ", update.price_change)
        print("*" * 20)



def retry_session(retries, session=None, backoff_factor=0.3) -> requests.Session:
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def main():
    """Я тут задал собственные значения для отслеживания цены изменения,
    можно убрать и период отслеживания будет равен к 60 мин.
    """
    session = retry_session(5, session=requests.Session())
    monitor = ETHUSDTMonitor(session=session, percent_threshold=0.01, time_interval=5)
    monitor.monitor()


if __name__ == "__main__":
    main()
