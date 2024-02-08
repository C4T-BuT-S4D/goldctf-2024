#!/usr/bin/env python3

from typing import Iterator
import contextlib

import minipwn as pwn


class API:
    def __init__(self, io: pwn.remote):
        self.io = io

    def register(self, username: bytes, password: bytes, secret: bytes) -> bytes:
        self.io.sendlineafter(b'> ', b'REGISTER')

        self.io.sendlineafter(b': ', username)
        self.io.sendlineafter(b': ', password)
        self.io.sendlineafter(b': ', secret)

        return self.io.recvline().strip()

    def login(self, username: bytes, password: bytes) -> bytes:
        self.io.sendlineafter(b'> ', b'LOGIN')

        self.io.sendlineafter(b': ', username)
        self.io.sendlineafter(b': ', password)

        return self.io.recvline().strip()

    def logout(self) -> bytes:
        self.io.sendlineafter(b'> ', b'LOGOUT')

        return self.io.recvline().strip()

    def encrypt(self, plaintext: bytes, username: bytes = None) -> bytes:
        self.io.sendlineafter(b'> ', b'ENCRYPT')

        if username is not None:
            self.io.sendlineafter(b': ', username)

        self.io.sendlineafter(b': ', plaintext.hex().encode())

        line = self.io.recvline().strip()

        if line.startswith(b'error'):
            return line

        ciphertext = self.io.recvline().strip().decode()

        return bytes.fromhex(ciphertext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        self.io.sendlineafter(b'> ', b'DECRYPT')

        self.io.sendlineafter(b': ', ciphertext.hex().encode())

        line = self.io.recvline().strip()

        if line.startswith(b'error'):
            return line

        plaintext = self.io.recvline().strip().decode()

        return bytes.fromhex(plaintext)

    def exit(self) -> bytes:
        self.io.sendlineafter(b'> ', b'EXIT')

        return self.io.recvline().strip()


@contextlib.contextmanager
def connect(hostname: str, port: int = 17171) -> Iterator[API]:
    io = pwn.remote(hostname, port)
    api = API(io)

    try:
        yield api
    finally:
        io.s.close()
