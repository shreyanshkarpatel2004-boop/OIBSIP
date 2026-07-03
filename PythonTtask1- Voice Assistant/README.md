# Voice Assistant

This project is a Python-based voice assistant that listens to spoken commands and responds with useful actions. It includes beginner-friendly features such as greetings, time/date reporting, web search, and text-to-speech responses, along with advanced capabilities like weather lookup, email sending, reminders, a small knowledge base, and custom commands.

## Features

- Listen to voice input with SpeechRecognition
- Respond with text-to-speech using pyttsx3
- Greet users with a predefined response
- Tell the current time and date
- Open a web browser for a search query
- Handle unrecognized speech gracefully
- Fetch live weather updates from OpenWeatherMap
- Send an email using SMTP
- Set timed reminders
- Answer simple general knowledge questions
- Add custom commands through the configuration file

## Setup

1. Create and activate a virtual environment if desired.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Update the placeholders in config.json with your email credentials and OpenWeatherMap API key.
4. Run the assistant:
   ```bash
   python voice_assistant.py
   ```

## Privacy note

The assistant processes voice input locally on your machine when possible, but it may send data to external services for speech recognition and weather updates. The program uses your microphone audio, the spoken text, and the configured email/weather settings. No voice data is stored by default; however, speech recognition services may process your audio through their API. Keep your email password secure and avoid using real credentials in shared environments.
