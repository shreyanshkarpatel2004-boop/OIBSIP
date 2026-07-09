# Real-Time Chat Application

This project includes:
- A beginner-friendly command-line chat app using Python sockets.
- An advanced tkinter GUI chat app with rooms, authentication, history, and emoji support.

## Beginner CLI Chat

Run the server:
```bash
python chat_server.py
```

Run the client in another terminal:
```bash
python chat_client.py
```

## Advanced GUI Chat

Run the server:
```bash
python advanced_chat_server.py
```

Run the GUI client:
```bash
python advanced_chat_client.py
```

## Features
- Real-time bidirectional messaging
- Timestamped messages
- Graceful disconnect notifications
- User registration and login with SQLite
- Multiple chat rooms
- Room message history
- Emoji shortcode support such as :smile:

## Storage and Security
- User accounts and chat history are stored in a local SQLite database.
- Messages are not encrypted in transit or at rest.
- This is a learning project and should not be used for truly sensitive communication.
