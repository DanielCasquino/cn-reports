#!/usr/bin/env python3
import socket, pathlib, os

HOST = "0.0.0.0"
PORT = 29707


def handle_client(conn):
    f = conn.makefile("rb")
    first = f.readline().decode("utf-8", "replace").strip()

    if first == "HELLO":
        conn.sendall(b"WELCOME\n")
        return

    if first.startswith("FILE "):
        _, name, size_s = first.split(" ", 2)
        size = int(size_s)
        out_path = pathlib.Path("received_" + pathlib.Path(name).name)

        remaining = size
        with open(out_path, "wb") as out:
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    raise ConnectionError("Conexion cerrada antes de tiempo")
                out.write(chunk)
                remaining -= len(chunk)
        conn.sendall(b"OK\n")
        return

    conn.sendall(b"ERR unknown command\n")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Servidor escuchando en {HOST}:{PORT} ...")
        while True:
            conn, addr = s.accept()
            with conn:
                handle_client(conn)


if __name__ == "__main__":
    main()
