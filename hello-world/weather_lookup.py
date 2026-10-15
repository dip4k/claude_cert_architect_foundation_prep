"""Simple weather lookup utility.

Uses wttr.in, a free/open-source console-friendly weather service, to fetch
current weather data. No API key required.
"""
import urllib.request

WTTR_URL = "https://wttr.in/{city}?format=j1"


def get_weather_raw(city: str = "London", timeout: int = 10) -> str:
    """Fetch raw JSON weather data for a city from wttr.in.

    Args:
        city: City name to look up weather for. Defaults to "London".
        timeout: Request timeout in seconds.

    Returns:
        Raw JSON response body as a string.
    """
    url = WTTR_URL.format(city=city)
    request = urllib.request.Request(url, headers={"User-Agent": "curl/7.64.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def get_london_weather() -> str:
    """Convenience helper that always returns London's raw weather JSON."""
    return get_weather_raw("London")
