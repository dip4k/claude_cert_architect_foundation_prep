"""Simple JSON parsing utility for wttr.in weather responses.

Kept intentionally minimal: just pulls out the handful of fields we care
about from the raw wttr.in JSON payload (format=j1).
"""
import json
from typing import Any, Dict


def parse_weather_json(raw_json: str) -> Dict[str, Any]:
    """Parse a raw wttr.in JSON response into a simple flat dict.

    Args:
        raw_json: Raw JSON string as returned by wttr.in (format=j1).

    Returns:
        Dict with basic weather fields: city, temperature_C, temperature_F,
        feels_like_C, humidity, description, wind_speed_kmph.
    """
    data = json.loads(raw_json)

    current = (data.get("current_condition") or [{}])[0]
    area = (data.get("nearest_area") or [{}])[0]

    city_name = ""
    area_names = area.get("areaName") or []
    if area_names:
        city_name = area_names[0].get("value", "")

    description = ""
    weather_desc = current.get("weatherDesc") or []
    if weather_desc:
        description = weather_desc[0].get("value", "")

    return {
        "city": city_name,
        "temperature_C": current.get("temp_C"),
        "temperature_F": current.get("temp_F"),
        "feels_like_C": current.get("FeelsLikeC"),
        "humidity": current.get("humidity"),
        "description": description,
        "wind_speed_kmph": current.get("windspeedKmph"),
    }
