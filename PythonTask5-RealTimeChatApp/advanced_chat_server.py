import argparse
import os
import sqlite3
import socket
import threading
from datetime import datetime
from typing import Dict, List, Set, Tuple

HOST = os.getenv('CHAT_HOST', '0.0.0.0')
PORT = int(os.getenv('CHAT_PORT', '5001'))
DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')
clients: Set[socket.socket] = set()
rooms: Dict[str, Set[socket.socket]] = {}
usernames: Dict[socket.socket, str] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Advanced chat server')
    parser.add_argument('--host', default=HOST, help='Host interface to bind to')
    parser.add_argument('--port', type=int, default=PORT, help='Port to listen on')
    return parser.parse_args()


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def save_message(room: str, username: str, message: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO messages (room, username, message, timestamp) VALUES (?, ?, ?, ?)',
        (room, username, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    )
    conn.commit()
    conn.close()


def load_history(room: str) -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT username, message, timestamp FROM messages WHERE room = ? ORDER BY id ASC LIMIT 50', (room,))
    rows = cur.fetchall()
    conn.close()
    return [f"[{ts}] {user}: {msg}" for user, msg, ts in rows]


def replace_emojis(text: str) -> str:
    mapping = {
        ':smile:': '😊',
        ':sad:': '😢',
        ':heart:': '❤️',
        ':party:': '🎉',
        ':fire:': '🔥',
    }
    for shortcode, emoji in mapping.items():
        text = text.replace(shortcode, emoji)
    return text


def send_to_client(client: socket.socket, message: str) -> None:
    try:
        client.sendall(message.encode('utf-8'))
    except Exception:
        pass


def broadcast(room: str, message: str, sender: socket.socket | None = None) -> None:
    for client in list(rooms.get(room, set())):
        if client is sender:
            continue
        send_to_client(client, message)


def handle_client(client: socket.socket, address: Tuple[str, int]) -> None:
    client.sendall(b'Welcome to the chat server. Type REGISTER username password or LOGIN username password.\n')
    auth_state = 'pending'
    username = None
    room = None

    try:
        while True:
            data = client.recv(4096)
            if not data:
                break
            text = data.decode('utf-8').strip()
            if not text:
                continue

            if auth_state == 'pending':
                parts = text.split()
                if len(parts) != 3 or parts[0].upper() not in {'REGISTER', 'LOGIN'}:
                    send_to_client(client, 'Use REGISTER username password or LOGIN username password.\n')
                    continue

                action, uname, password = parts
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                if action.upper() == 'REGISTER':
                    try:
                        cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (uname, password))
                        conn.commit()
                        send_to_client(client, f'Account created for {uname}. Please login.\n')
                    except sqlite3.IntegrityError:
                        send_to_client(client, 'Username already exists.\n')
                    finally:
                        conn.close()
                    continue

                cur.execute('SELECT password FROM users WHERE username = ?', (uname,))
                row = cur.fetchone()
                conn.close()
                if row and row[0] == password:
                    username = uname
                    usernames[client] = uname
                    clients.add(client)
                    auth_state = 'authenticated'
                    send_to_client(client, f'Authenticated as {username}. Join a room with JOIN roomname.\n')
                else:
                    send_to_client(client, 'Invalid username or password.\n')
                continue

            if auth_state == 'authenticated':
                if text.upper().startswith('JOIN '):
                    new_room = text.split(maxsplit=1)[1].strip()
                    if room:
                        rooms[room].discard(client)
                    room = new_room
                    rooms.setdefault(room, set()).add(client)
                    history = load_history(room)
                    if history:
                        send_to_client(client, '--- Room history ---\n')
                        for line in history:
                            send_to_client(client, line + '\n')
                    send_to_client(client, f'Joined room {room}.\n')
                    continue

                if room is None:
                    send_to_client(client, 'Join a room first with JOIN roomname.\n')
                    continue

                cleaned = replace_emojis(text)
                timestamp = datetime.now().strftime('%H:%M')
                formatted = f"[{timestamp}] {username}: {cleaned}\n"
                save_message(room, username, cleaned)
                broadcast(room, formatted, sender=client)
    except Exception:
        pass
    finally:
        if client in clients:
            clients.remove(client)
        if client in usernames:
            del usernames[client]
        if room:
            rooms.get(room, set()).discard(client)
        try:
            client.close()
        except Exception:
            pass


def main() -> None:
    args = parse_args()
    init_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.host, args.port))
    server.listen(10)
    print(f"Advanced chat server running on {args.host}:{args.port}")

    while True:
        client, address = server.accept()
        print(f"Connection from {address}")
        threading.Thread(target=handle_client, args=(client, address), daemon=True).start()


if __name__ == '__main__':
    main()
