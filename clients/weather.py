import httpx
from typing import Dict, Any

WEATHER_API_URL = "https://api.example.com/weather"


async def get_weather(city: str) -> Dict[str, Any]:
    """
    Получает погоду для города через внешний API.

    Args:
        city: Название города

    Returns:
        Dict с ключами 'city' и 'temp_c'

    Raises:
        httpx.HTTPStatusError: при статусе 4xx/5xx
        httpx.ReadTimeout: при таймауте
        httpx.ConnectError: при ошибке подключения
        KeyError: если в ответе отсутствует temp_c
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            WEATHER_API_URL,
            params={"q": city}
        )
        response.raise_for_status()
        data = response.json()
        return {
            "city": city,
            "temp_c": data["temp_c"]
        }