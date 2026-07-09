import socket
import threading
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5000

clients = []


def broadcast(message: str, sender_socket: socket.socket | None = None) -> None:
    for client in clients:
        if client is sender_socket:
            continue
        try:
            client.sendall(message.encode('utf-8'))
        except Exception:
            pass


def handle_client(client: socket.socket, address: tuple[str, int]) -> None:
    try:
        username = client.recv(1024).decode('utf-8').strip() or f'User{address[1]}'
        clients.append(client)
        welcome = f"[{datetime.now().strftime('%H:%M')}] Server: {username} joined the chat.\n"
        broadcast(welcome, sender_socket=None)
        client.sendall(f"[{datetime.now().strftime('%H:%M')}] Server: Connected to chat server.\n".encode('utf-8'))

        while True:
            data = client.recv(1024)
            if not data:
                break
            message = data.decode('utf-8').rstrip('\n')
            timestamp = datetime.now().strftime('%H:%M')
            formatted = f"[{timestamp}] {username}: {message}\n"
            broadcast(formatted, sender_socket=client)
    except Exception:
        pass
    finally:
        if client in clients:
            clients.remove(client)
        try:
            client.close()
        except Exception:
            pass
        disconnect_message = f"[{datetime.now().strftime('%H:%M')}] Server: {username if 'username' in locals() else 'A user'} left the chat.\n"
        broadcast(disconnect_message, sender_socket=None)


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        client, address = server.accept()
        print(f"Connection from {address}")
        threading.Thread(target=handle_client, args=(client, address), daemon=True).start()


if __name__ == '__main__':
    main()
