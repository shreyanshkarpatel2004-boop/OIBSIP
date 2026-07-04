import os
import threading
from datetime import datetime
from io import BytesIO

import requests
import tkinter as tk
from tkinter import simpledialog, ttk
from PIL import Image, ImageTk

API_WEATHER = "https://api.openweathermap.org/data/2.5/weather"
API_ONECALL = "https://api.openweathermap.org/data/2.5/onecall"
ICON_URL = "https://openweathermap.org/img/wn/{icon}@2x.png"


class WeatherApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.api_key = os.environ.get("OPENWEATHER_API_KEY", "")
        self.unit = "metric"
        self.last_location = None
        self.icon_refs = []

        root.title("Weather App")
        root.geometry("900x640")

        top = ttk.Frame(root, padding=8)
        top.pack(fill=tk.X)

        self.city_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.city_var, width=40).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(top, text="Get Weather", command=self.start_fetch).pack(side=tk.LEFT)
        ttk.Button(top, text="Detect Location", command=self.detect_location).pack(side=tk.LEFT, padx=(6, 0))
        self.unit_btn = ttk.Button(top, text="°C", command=self.toggle_unit)
        self.unit_btn.pack(side=tk.RIGHT)

        self.error_lbl = ttk.Label(root, foreground="red", wraplength=850)
        self.error_lbl.pack(fill=tk.X, padx=8, pady=(0, 6))

        self.current_frame = ttk.LabelFrame(root, text="Current Weather", padding=10)
        self.current_frame.pack(fill=tk.X, padx=8, pady=6)

        self.hourly_frame = ttk.LabelFrame(root, text="Next 6 Hours", padding=10)
        self.hourly_frame.pack(fill=tk.X, padx=8, pady=6)

        self.daily_frame = ttk.LabelFrame(root, text="Next 5 Days", padding=10)
        self.daily_frame.pack(fill=tk.X, padx=8, pady=6)

    def toggle_unit(self) -> None:
        self.unit = "imperial" if self.unit == "metric" else "metric"
        self.unit_btn.config(text="°F" if self.unit == "imperial" else "°C")
        if self.last_location:
            self.start_fetch(self.last_location)

    def show_error(self, message: str) -> None:
        self.error_lbl.config(text=message)

    def ensure_api_key(self) -> bool:
        if self.api_key:
            return True

        key = simpledialog.askstring(
            "OpenWeather API Key",
            "Enter your OpenWeather API key (or set OPENWEATHER_API_KEY in your terminal):",
            parent=self.root,
        )
        if key:
            self.api_key = key.strip()
            os.environ["OPENWEATHER_API_KEY"] = self.api_key
            return True

        self.show_error("Missing OPENWEATHER_API_KEY. Please enter a valid API key.")
        return False

    def clear_results(self) -> None:
        for frame in (self.current_frame, self.hourly_frame, self.daily_frame):
            for child in frame.winfo_children():
                child.destroy()
        self.icon_refs.clear()

    def start_fetch(self, override: str | None = None) -> None:
        location = (override or self.city_var.get()).strip()
        if not location:
            self.show_error("Please enter a city name or use Detect Location.")
            return

        self.show_error("")
        threading.Thread(target=self.fetch_and_display, args=(location,), daemon=True).start()

    def detect_location(self) -> None:
        def _detect() -> None:
            try:
                response = requests.get("https://ipinfo.io/json", timeout=8)
                payload = response.json()
                city = payload.get("city")
                if city:
                    self.city_var.set(city)
                    self.start_fetch(city)
                else:
                    self.show_error("Location detection failed.")
            except Exception:
                self.show_error("Location detection failed.")

        threading.Thread(target=_detect, daemon=True).start()

    def fetch_and_display(self, location: str) -> None:
        if not self.ensure_api_key():
            return

        try:
            weather_params = {"q": location, "appid": self.api_key, "units": "metric"}
            weather_resp = requests.get(API_WEATHER, params=weather_params, timeout=10)
            if weather_resp.status_code != 200:
                payload = weather_resp.json() if weather_resp.headers.get("content-type", "").startswith("application/json") else {}
                self.show_error(f"Error: {payload.get('message', weather_resp.text)}")
                return

            weather_data = weather_resp.json()
            coord = weather_data.get("coord", {})
            lat = coord.get("lat")
            lon = coord.get("lon")
            if lat is None or lon is None:
                self.show_error("Location coordinates were not found.")
                return

            onecall_params = {"lat": lat, "lon": lon, "exclude": "minutely,alerts", "appid": self.api_key, "units": "metric"}
            if self.unit == "imperial":
                onecall_params["units"] = "imperial"
            onecall_resp = requests.get(API_ONECALL, params=onecall_params, timeout=10)
            if onecall_resp.status_code != 200:
                payload = onecall_resp.json() if onecall_resp.headers.get("content-type", "").startswith("application/json") else {}
                self.show_error(f"Forecast error: {payload.get('message', onecall_resp.text)}")
                return

            self.last_location = location
            self.root.after(0, lambda: self.update_ui(weather_data, onecall_resp.json()))
        except requests.RequestException as exc:
            self.show_error(f"Network error: {exc}")
        except Exception as exc:
            self.show_error(str(exc))

    def load_icon(self, icon_code: str, size: tuple[int, int] = (80, 80)):
        try:
            response = requests.get(ICON_URL.format(icon=icon_code), timeout=8)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert("RGBA")
            image = image.resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.icon_refs.append(photo)
            return photo
        except Exception:
            return None

    def update_ui(self, weather_data: dict, onecall_data: dict) -> None:
        self.clear_results()

        current = onecall_data.get("current", {})
        weather = current.get("weather", [{}])[0]
        temp = current.get("temp")
        humidity = current.get("humidity")
        wind = current.get("wind_speed")
        description = weather.get("description", "").title()
        icon_code = weather.get("icon")
        unit_symbol = "°F" if self.unit == "imperial" else "°C"

        left = ttk.Frame(self.current_frame)
        left.pack(side=tk.LEFT, padx=8, pady=8)
        if icon_code:
            icon_photo = self.load_icon(icon_code)
            if icon_photo:
                ttk.Label(left, image=icon_photo).pack()

        right = ttk.Frame(self.current_frame)
        right.pack(side=tk.LEFT, padx=8, pady=8)
        ttk.Label(right, text=weather_data.get("name", "Unknown"), font=(None, 14, "bold")).pack(anchor=tk.W)
        ttk.Label(right, text=f"{temp} {unit_symbol}").pack(anchor=tk.W)
        ttk.Label(right, text=description).pack(anchor=tk.W)
        ttk.Label(right, text=f"Humidity: {humidity}%").pack(anchor=tk.W)
        ttk.Label(right, text=f"Wind: {wind} {'mph' if self.unit == 'imperial' else 'm/s'}").pack(anchor=tk.W)

        hourly_items = onecall_data.get("hourly", [])[:6]
        for item in hourly_items:
            hour_frame = ttk.Frame(self.hourly_frame)
            hour_frame.pack(side=tk.LEFT, padx=6, pady=4)
            dt = datetime.fromtimestamp(item.get("dt", 0)).strftime("%H:%M")
            weather_item = item.get("weather", [{}])[0]
            icon_code = weather_item.get("icon")
            temp_value = item.get("temp")
            if icon_code:
                icon_photo = self.load_icon(icon_code, size=(48, 48))
                if icon_photo:
                    ttk.Label(hour_frame, image=icon_photo).pack()
            ttk.Label(hour_frame, text=dt).pack()
            ttk.Label(hour_frame, text=f"{temp_value} {unit_symbol}").pack()

        daily_items = onecall_data.get("daily", [])[1:6]
        for item in daily_items:
            day_frame = ttk.Frame(self.daily_frame)
            day_frame.pack(side=tk.LEFT, padx=6, pady=4)
            dt = datetime.fromtimestamp(item.get("dt", 0)).strftime("%a %d")
            weather_item = item.get("weather", [{}])[0]
            icon_code = weather_item.get("icon")
            temp_data = item.get("temp", {})
            low = temp_data.get("min")
            high = temp_data.get("max")
            if icon_code:
                icon_photo = self.load_icon(icon_code, size=(48, 48))
                if icon_photo:
                    ttk.Label(day_frame, image=icon_photo).pack()
            ttk.Label(day_frame, text=dt).pack()
            ttk.Label(day_frame, text=f"{low}/{high} {unit_symbol}").pack()


if __name__ == "__main__":
    root = tk.Tk()
    WeatherApp(root)
    root.mainloop()
