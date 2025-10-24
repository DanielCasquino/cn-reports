#!/usr/bin/env python3
import socket, os, argparse


def hello(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(b"HELLO\n")
        print(s.recv(1024).decode().strip())


def send_file(host, port, path):
    size = os.path.getsize(path)
    name = os.path.basename(path)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        header = f"FILE {name} {size}\n".encode()
        s.sendall(header)
        with open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                s.sendall(chunk)
        print(s.recv(1024).decode().strip())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--file", help="ruta al .txt a enviar")
    args = ap.parse_args()

    if args.file:
        send_file(args.host, args.port, args.file)
    else:
        hello(args.host, args.port)
