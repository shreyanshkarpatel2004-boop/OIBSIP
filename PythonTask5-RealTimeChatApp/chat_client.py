import socket
import threading
import sys
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5000


def receive_messages(sock: socket.socket) -> None:
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("Disconnected from server.")
                break
            print(data.decode('utf-8'), end='')
        except Exception:
            break


def main() -> None:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    username = input("Enter your name: ").strip() or "Guest"
    client.sendall(username.encode('utf-8'))

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    while True:
        message = input()
        if message.lower() in {'exit', 'quit'}:
            client.close()
            sys.exit(0)
        client.sendall(message.encode('utf-8'))


if __name__ == '__main__':
    main()
