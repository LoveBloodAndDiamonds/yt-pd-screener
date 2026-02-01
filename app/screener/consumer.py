__all__ = ["Consumer"]

import asyncio
import time

from unicex import Exchange, KlineDict, MarketType
from unicex.extra import TimeoutTracker, percent_greater

from app.config import config, logger
from app.models import SettingsDTO
from app.utils import TelegramBot, create_text

from .producer import Producer


class Consumer:
    """Обработчик данных для скринера."""

    _PARSE_INTERVAL: int = 1
    """Интервал проверки данных."""

    def __init__(
        self,
        producer: Producer,
        settings: SettingsDTO,
        exchange: Exchange = config.exchange,
        market_type: MarketType = config.market_type,
    ) -> None:
        self._producer = producer
        self._settings = settings
        self._exchange = exchange
        self._market_type = market_type
        self._telegram_bot = TelegramBot()
        self._timeout_tracker = TimeoutTracker[str]()
        self._running = True

    def update_settings(self, settings: SettingsDTO) -> None:
        """Обновляет настройки скринера."""
        self._settings = settings

    async def start(self) -> None:
        """Запускает обработку данных."""
        logger.info("Starting consumer...")
        while self._running:
            try:
                if not self._settings.is_ready:
                    continue
                await self._process()
            except Exception as e:
                logger.error(f"Error processing data: {e}")
            finally:
                await asyncio.sleep(self._PARSE_INTERVAL)

    async def stop(self) -> None:
        """Останавливает обработку данных."""
        logger.info("Stopping consumer...")
        self._running = False
        await self._telegram.close()

    async def _process(self) -> None:
        """Обрабатывает данные."""
        data = await self._producer.fetch_collected_data()

        tasks = []
        for symbol, klines in data.items():
            if self._timeout_tracker.is_blocked(symbol):
                continue

            task = await self._process_symbol(symbol, klines)
            if task:
                self._timeout_tracker.block(symbol, self._settings.timeout)
                tasks.append(task)

        await asyncio.gather(*tasks)
        logger.success(f"Sended {len(tasks)} signals!")

    async def _process_symbol(self, symbol: str, klines: list[KlineDict]) -> asyncio.Task | None:
        """Обрабатывает данные по тикеру."""
        price_change, start_price, last_price = self._calculate_price_change(klines)

        if price_change > self._settings.min_growth:
            return asyncio.create_task(
                self._telegram_bot.send_message(
                    bot_token=self._settings.bot_token,  # type: ignore
                    chat_id=self._settings.chat_id,  # type: ignore
                    text=create_text(
                        symbol,
                        price_change,
                        start_price,
                        last_price,
                        self._exchange,
                        self._market_type,
                    ),
                )
            )

    def _calculate_price_change(self, klines: list[KlineDict]) -> tuple[float, float, float]:
        """Подсчет изменения цены в процентах на основе направления.

        Returns:
            tuple[float, float, float]: (price_change, start_price, last_price)
        """
        if not klines:
            return 0, 0, 0

        threshold = (time.time() - self._settings.interval) * 1000
        valid_klines = [k for k in klines if k["t"] > threshold]

        if not valid_klines:
            return 0, 0, 0

        last_price = valid_klines[-1]["h"]
        start_price = min(k["l"] for k in valid_klines)
        price_change = percent_greater(lower=start_price, higher=last_price)

        return price_change, start_price, last_price
