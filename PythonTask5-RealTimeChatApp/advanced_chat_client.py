import argparse
import os
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

HOST = os.getenv('CHAT_HOST', '127.0.0.1')
PORT = int(os.getenv('CHAT_PORT', '5001'))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Advanced chat client')
    parser.add_argument('--host', default=HOST, help='Server host to connect to')
    parser.add_argument('--port', type=int, default=PORT, help='Server port to connect to')
    return parser.parse_args()


class ChatClient:
    def __init__(self, root: tk.Tk, host: str, port: int) -> None:
        self.root = root
        self.host = host
        self.port = port
        self.root.title('Advanced Chat')
        self.root.geometry('700x500')

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.focused = True
        self.running = False

        try:
            self.client.connect((self.host, self.port))
        except OSError as exc:
            messagebox.showerror(
                'Connection Error',
                f'Could not connect to the chat server at {self.host}:{self.port}.\nStart advanced_chat_server.py first.\n\n{exc}'
            )
            self.root.destroy()
            return

        self.text_area = scrolledtext.ScrolledText(root, state='disabled')
        self.text_area.pack(fill='both', expand=True, padx=8, pady=8)

        entry_frame = tk.Frame(root)
        entry_frame.pack(fill='x', padx=8, pady=(0, 8))
        self.entry = tk.Entry(entry_frame)
        self.entry.pack(side='left', fill='x', expand=True)
        self.entry.bind('<Return>', self.send_message)
        tk.Button(entry_frame, text='Send', command=self.send_message).pack(side='left', padx=(6, 0))

        self.running = True
        self.root.bind('<FocusIn>', self.on_focus)
        self.root.bind('<FocusOut>', self.on_blur)
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.authenticate()

        self.root.protocol('WM_DELETE_WINDOW', self.close_app)

    def on_focus(self, event=None) -> None:
        self.focused = True
        self.root.title('Advanced Chat')

    def on_blur(self, event=None) -> None:
        self.focused = False

    def show_notification(self, message: str) -> None:
        if self.focused:
            return
        self.root.title('New message - Advanced Chat')
        messagebox.showinfo('New message', message.strip())

    def display_message(self, message: str) -> None:
        self.text_area.configure(state='normal')
        self.text_area.insert('end', message)
        self.text_area.configure(state='disabled')
        self.text_area.see('end')
        if not self.focused and message.strip():
            self.root.after(0, self.show_notification, message)

    def authenticate(self) -> None:
        while True:
            action = simpledialog.askstring('Authentication', 'Enter REGISTER or LOGIN', parent=self.root)
            if action is None:
                self.close_app()
                return
            action = action.strip().upper()
            if action not in {'REGISTER', 'LOGIN'}:
                messagebox.showwarning('Invalid input', 'Please enter REGISTER or LOGIN.')
                continue

            username = simpledialog.askstring('Username', 'Enter username', parent=self.root)
            password = simpledialog.askstring('Password', 'Enter password', parent=self.root)
            if not username or not password:
                messagebox.showwarning('Invalid input', 'Username and password are required.')
                continue
            self.client.sendall(f'{action} {username} {password}'.encode('utf-8'))
            return

    def receive_messages(self) -> None:
        while self.running:
            try:
                data = self.client.recv(4096)
                if not data:
                    break
                message = data.decode('utf-8')
                self.root.after(0, self.display_message, message)
            except Exception:
                break

    def send_message(self, event=None) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        if text.upper().startswith('REGISTER ') or text.upper().startswith('LOGIN '):
            self.client.sendall(text.encode('utf-8'))
        else:
            self.client.sendall(text.encode('utf-8'))
        self.entry.delete(0, 'end')

    def close_app(self) -> None:
        self.running = False
        try:
            self.client.close()
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    args = parse_args()
    root = tk.Tk()
    ChatClient(root, args.host, args.port)
    root.mainloop()


if __name__ == '__main__':
    main()
