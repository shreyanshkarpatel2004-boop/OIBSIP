import os
import sys
import requests

API_URL = "https://api.openweathermap.org/data/2.5/weather"


def c_to_f(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def get_api_key() -> str:
    key = os.environ.get("OPENWEATHER_API_KEY")
    if key:
        return key

    print("Set the OPENWEATHER_API_KEY environment variable or paste your API key.")
    key = input("API key: ").strip()
    if not key:
        print("No API key provided. Exiting.")
        sys.exit(1)
    return key


def fetch_weather(query: str, api_key: str):
    params = {"appid": api_key, "units": "metric"}
    if query.isdigit():
        params["zip"] = query
    else:
        params["q"] = query

    try:
        response = requests.get(API_URL, params=params, timeout=10)
    except requests.RequestException as exc:
        return {"error": f"Network error: {exc}"}

    if response.status_code != 200:
        try:
            payload = response.json()
            message = payload.get("message", response.text)
        except Exception:
            message = response.text
        return {"error": f"API error ({response.status_code}): {message}"}

    return {"data": response.json()}


def display_weather(data: dict) -> None:
    main = data.get("main", {})
    weather = data.get("weather", [{}])[0]
    wind = data.get("wind", {})

    temp_c = main.get("temp")
    if temp_c is None:
        print("Temperature data is not available.")
        return

    temp_f = c_to_f(temp_c)
    humidity = main.get("humidity", "?")
    description = weather.get("description", "?").title()
    wind_speed = wind.get("speed", "?")

    print(f"Location: {data.get('name', 'Unknown')}")
    print(f"Temperature: {temp_c:.1f} °C / {temp_f:.1f} °F")
    print(f"Humidity: {humidity}%")
    print(f"Condition: {description}")
    print(f"Wind speed: {wind_speed} m/s")


def main() -> None:
    api_key = get_api_key()

    query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    while not query:
        query = input("Enter a city name or ZIP code: ").strip()
        if not query:
            print("Please enter a non-empty city name or ZIP code.")

    result = fetch_weather(query, api_key)
    if "error" in result:
        print(result["error"])
        sys.exit(1)

    display_weather(result["data"])


if __name__ == "__main__":
    main()
