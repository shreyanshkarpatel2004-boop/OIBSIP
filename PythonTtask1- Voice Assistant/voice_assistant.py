import json
import os
import re
import smtplib
import threading
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, date
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Optional

try:
    import pyttsx3
except ImportError:  # pragma: no cover - handled at runtime
    pyttsx3 = None

try:
 import speech_recognition as sr
except ImportError:  # pragma: no cover - handled at runtime
    sr = None


CONFIG_PATH = Path(__file__).with_name("config.json")
KNOWLEDGE_BASE = {
    "python": "Python is a popular high-level programming language used for automation, web development, and AI.",
    "ai": "Artificial intelligence is the field of creating systems that can perform tasks that normally require human intelligence.",
    "earth": "Earth is the third planet from the Sun in our solar system.",
    "github": "GitHub is a platform for hosting and sharing code repositories.",
}


class VoiceAssistant:
    def __init__(self) -> None:
        self.config = self.load_config()
        self.engine = self.init_tts()
        self.recognizer = None
        self.microphone = None

    def load_config(self) -> Dict:
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open("r", encoding="utf-8") as handle:
                return json.load(handle)

        default_config = {
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your_email@example.com",
                "sender_password": "your_app_password",
                "recipient_email": "recipient@example.com",
            },
            "weather": {
                "api_key": "your_openweather_api_key"
            },
            "custom_commands": {},
        }
        with CONFIG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(default_config, handle, indent=2)
        return default_config

    def init_tts(self):
        if pyttsx3 is None:
            return None
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        return engine

    def speak(self, text: str) -> None:
        print(f"Assistant: {text}")
        if self.engine is not None:
            self.engine.say(text)
            self.engine.runAndWait()

    def setup_audio(self):
        if sr is None:
            raise RuntimeError("speech_recognition is not installed")
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    def listen_once(self) -> Optional[str]:
        if self.recognizer is None or self.microphone is None:
            raise RuntimeError("Audio setup has not been completed")

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.speak("Listening...")
            audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)

        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            self.speak("Sorry, I did not understand that. Please repeat.")
            return None
        except sr.RequestError:
            self.speak("The speech service is unavailable right now.")
            return None

    def extract_intent(self, text: str) -> str:
        lower = text.lower()
        custom_commands = self.config.get("custom_commands", {})
        for phrase in custom_commands:
            if phrase.lower() in lower:
                return "custom"

        if any(token in lower for token in ["hello", "hi", "hey"]):
            return "greeting"
        if any(token in lower for token in ["what time", "current time", "time is", "tell me the time", "what is the time"]):
            return "time"
        if any(token in lower for token in ["what date", "today's date", "today date", "date is"]):
            return "date"
        if any(token in lower for token in ["search for", "search", "google", "look up", "find"]):
            return "search"
        if any(token in lower for token in ["weather", "forecast"]):
            return "weather"
        if any(token in lower for token in ["email", "send mail", "send an email"]):
            return "email"
        if any(token in lower for token in ["remind", "reminder"]):
            return "reminder"
        if any(token in lower for token in ["add custom command", "custom command"]):
            return "add_custom"
        # Only treat generic 'what is' style queries as knowledge when they mention known topics
        if any(token in lower for token in ["what is", "who is", "can you tell me", "tell me about"]):
            if any(topic in lower for topic in KNOWLEDGE_BASE):
                return "knowledge"
        if any(token in lower for token in ["exit", "bye", "stop", "shutdown"]):
            return "exit"
        return "unknown"

    def handle_command(self, text: str) -> bool:
        intent = self.extract_intent(text)
        custom_commands = self.config.get("custom_commands", {})

        if intent == "custom":
            for phrase, response in custom_commands.items():
                if phrase.lower() in text.lower():
                    self.speak(response)
                    return False

        if intent == "greeting":
            self.speak("Hello! I am your voice assistant. How can I help you today?")
            return False

        if intent == "time":
            current_time = datetime.now().strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}.")
            return False

        if intent == "date":
            current_date = date.today().strftime("%B %d, %Y")
            self.speak(f"Today is {current_date}.")
            return False

        if intent == "search":
            query = self._extract_query(text, ["search for", "search", "google", "look up", "find"])
            if query:
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
                self.speak(f"Searching the web for {query}.")
            else:
                self.speak("Please tell me what to search for.")
            return False

        if intent == "weather":
            city = self._extract_city(text)
            self.speak(self.get_weather(city))
            return False

        if intent == "email":
            self.handle_email_request(text)
            return False

        if intent == "reminder":
            self.handle_reminder_request(text)
            return False

        if intent == "add_custom":
            self.add_custom_command(text)
            return False

        if intent == "knowledge":
            self.speak(self.answer_knowledge_question(text))
            return False

        if intent == "exit":
            self.speak("Goodbye!")
            return True

        self.speak("Sorry, I did not understand that command. Please try again.")
        return False

    def _extract_query(self, text: str, patterns: list) -> str:
        lowered = text.lower()
        for pattern in patterns:
            if pattern in lowered:
                query = text.lower().replace(pattern, "", 1).strip()
                return query
        return ""

    def _extract_city(self, text: str) -> str:
        match = re.search(r"in\s+([a-zA-Z\s]+)$", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "London"

    def get_weather(self, city: str) -> str:
        api_key = self.config.get("weather", {}).get("api_key", "")
        if not api_key or api_key.startswith("your_"):
            return "Weather lookup is not configured. Add an OpenWeatherMap API key in the config file."

        encoded_city = urllib.parse.quote(city)
        url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded_city}&appid={api_key}&units=metric"
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.load(response)
        except Exception:
            return f"I could not fetch the weather for {city} right now."

        if data.get("cod") != 200:
            return f"I could not find weather information for {city}."

        weather_desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"The weather in {city} is {weather_desc} with a temperature of {temp} degrees Celsius."

    def handle_email_request(self, text: str) -> None:
        email_config = self.config.get("email", {})
        sender = email_config.get("sender_email", "")
        password = email_config.get("sender_password", "")
        recipient = email_config.get("recipient_email", "")
        if not sender or not password or not recipient or sender.startswith("your_"):
            self.speak("Email sending is not configured. Please update the config file with sender and recipient details.")
            return

        message_text = self._extract_message(text)
        if not message_text:
            self.speak("Please tell me the message to send.")
            return

        try:
            msg = EmailMessage()
            msg["Subject"] = "Voice Assistant Email"
            msg["From"] = sender
            msg["To"] = recipient
            msg.set_content(message_text)
            with smtplib.SMTP(email_config.get("smtp_server", "smtp.gmail.com"), email_config.get("smtp_port", 587)) as smtp:
                smtp.starttls()
                smtp.login(sender, password)
                smtp.send_message(msg)
            self.speak("Your email has been sent.")
        except Exception as exc:
            self.speak(f"I could not send the email. Error: {exc}")

    def _extract_message(self, text: str) -> str:
        cleaned = re.sub(r"^(email|send email|send an email|send mail)\s*", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"^message\s*", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def handle_reminder_request(self, text: str) -> None:
        match = re.search(r"(\d+)\s*(second|seconds|minute|minutes|hour|hours)", text, re.IGNORECASE)
        if not match:
            self.speak("Please tell me how long to wait before the reminder.")
            return

        amount = int(match.group(1))
        unit = match.group(2).lower()
        if unit.startswith("second"):
            seconds = amount
        elif unit.startswith("minute"):
            seconds = amount * 60
        else:
            seconds = amount * 3600

        message = re.sub(r"(remind me|reminder|in\s+\d+\s*(second|seconds|minute|minutes|hour|hours))", "", text, flags=re.IGNORECASE).strip()
        message = message or "Reminder"

        timer = threading.Timer(seconds, lambda: self.speak(f"Reminder: {message}"))
        timer.daemon = True
        timer.start()
        self.speak(f"Reminder set for {amount} {unit}.")

    def add_custom_command(self, text: str) -> None:
        match = re.search(r"add custom command\s+(.+?)\s+to\s+(.+)", text, re.IGNORECASE)
        if not match:
            self.speak("Please provide a command phrase and response in the format: add custom command <phrase> to <response>.")
            return

        phrase = match.group(1).strip()
        response = match.group(2).strip()
        self.config.setdefault("custom_commands", {})[phrase] = response
        with CONFIG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(self.config, handle, indent=2)
        self.speak(f"Added custom command for {phrase}.")

    def answer_knowledge_question(self, text: str) -> str:
        lower = text.lower()
        for topic, answer in KNOWLEDGE_BASE.items():
            if topic in lower:
                return answer
        return "I can answer common questions about Python, AI, Earth, and GitHub."

    def run(self) -> None:
        if sr is None:
            self.speak("The speech_recognition package is not installed. Please install the requirements first.")
            return

        self.setup_audio()
        self.speak("Voice assistant is ready. Say a command such as hello, time, date, search, weather, email, reminder, or stop.")

        while True:
            try:
                command = self.listen_once()
                if command is None:
                    continue
                print(f"You said: {command}")
                should_exit = self.handle_command(command)
                if should_exit:
                    break
            except KeyboardInterrupt:
                self.speak("Goodbye!")
                break
            except Exception as exc:  # pragma: no cover - runtime safety
                self.speak(f"An unexpected error occurred: {exc}")


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
