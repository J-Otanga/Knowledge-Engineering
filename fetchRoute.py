import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

TOWN_COORDINATES = {
    "Nairobi": (-1.2864, 36.8172),
    "Nakuru": (-0.3031, 36.0800),
    "Kericho": (-0.3677, 35.2831),
    "Eldoret": (0.5143, 35.2698),
    "Kakamega": (0.2827, 34.7519),
    "Kisii": (-0.6817, 34.7667),
    "Kisumu": (-0.0917, 34.7680),
}


def decode_wmo_weather(code: int) -> str:
    """Maps WMO weather interpretation codes to Trailer KB weather states."""
    if code in (0, 1, 2, 3):
        return "Clear"
    elif code in (45, 48):
        return "Fog"
    elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99):
        return "Rain"
    return "Clear"


def fetch_kenya_corridor_weather(output_file: str = "kenya_highway_weather_kb.json") -> dict:
    """Queries Open-Meteo API for each town node in the PE3 directed graph."""
    weather_kb = {
        "source": "Open-Meteo Public Forecast API (https://api.open-meteo.com/v1/forecast)",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "towns": {},
    }

    for town, (lat, lon) in TOWN_COORDINATES.items():
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true"
        )
        try:
            with urllib.request.urlopen(url, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
                current = payload.get("current_weather", {})
                wmo_code = int(current.get("weathercode", 0))
                condition = decode_wmo_weather(wmo_code)
                weather_kb["towns"][town] = {
                    "latitude": lat,
                    "longitude": lon,
                    "temperature_c": current.get("temperature"),
                    "windspeed_kmh": current.get("windspeed"),
                    "weather_code": wmo_code,
                    "condition": condition,
                }
                print(f"[API OK] {town:10} -> {condition} ({current.get('temperature')}°C)")
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print(f"[FALLBACK] {town:10} -> Clear (API unreachable: {exc})")
            weather_kb["towns"][town] = {
                "latitude": lat,
                "longitude": lon,
                "temperature_c": 22.0,
                "windspeed_kmh": 10.0,
                "weather_code": 0,
                "condition": "Clear",
            }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(weather_kb, f, indent=2)

    print(f"\nSaved API knowledge base facts to '{output_file}'.")
    return weather_kb


if __name__ == "__main__":
    fetch_kenya_corridor_weather()