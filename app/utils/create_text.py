__all__ = ["create_text"]


from unicex import Exchange, MarketType
from unicex.extra import generate_ex_link, make_humanreadable


def create_text(
    symbol: str,
    price_change: float,
    start_price: float,
    last_price: float,
    exchange: Exchange,
    market_type: MarketType,
    daily_price: float,
    daily_volume: float,
) -> str:
    """Формирует красивый текст сигнала о резком изменении цены. Готовый текст для отправки пользователю."""
    # Ссылка на биржу для быстрого перехода к инструменту
    ex_link = generate_ex_link(exchange, market_type, symbol)

    direction_emoji = "🚀" if price_change >= 0 else "🔻"
    change_sign = "+" if price_change >= 0 else ""

    # Основной заголовок сигнала
    header = f"{direction_emoji} Резкое изменение цены: {symbol}"

    # Читаемая часть с цифрами
    body = (
        f"Изменение: {change_sign}{price_change:.2f}%\n"
        f"Начальная цена: {start_price} $\n"
        f"Текущая цена: {last_price} $\n"
        f"Цена за день: {daily_price} %\n"
        f"Объем за день: {make_humanreadable(daily_volume, locale='ru')} $."
    )

    # Призыв к действию и ссылка
    footer = f"{ex_link}"

    return f"{header}\n\n{body}\n\n{footer}"
