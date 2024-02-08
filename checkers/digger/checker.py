#!/usr/bin/env python3

import sys
import socket
import string
import secrets
from typing import Any, Tuple, List

import checklib

import api
import des


def random_username(length: int = None) -> str:
    if length is None:
        length = 10 + secrets.randbelow(20)

    alpha = string.ascii_letters + string.digits

    return ''.join(secrets.choice(alpha) for _ in range(length))


def random_password() -> str:
    length = 8
    alpha = string.ascii_letters + string.digits + string.punctuation

    return ''.join(secrets.choice(alpha) for _ in range(length))


def random_secret(length: int = None) -> str:
    if length is None:
        length = 32 + secrets.randbelow(64)

    return secrets.token_urlsafe(length)[:length]


def random_plaintext(blocks_count: int = None) -> List[bytes]:
    if blocks_count is None:
        blocks_count = 4 + secrets.randbelow(16)

    plaintext = []

    while len(plaintext) < blocks_count:
        block = secrets.token_bytes(8)

        if b'error' not in block:
            plaintext.append(block)

    return plaintext


def des_encrypt(key: bytes, plaintext: List[bytes]) -> bytes:
    cipher = des.DES(key)
    ciphertext = []

    for block in plaintext:
        ciphertext.append(cipher.encrypt(block))

    return b''.join(ciphertext)


class Checker(checklib.BaseChecker):
    vulns: int = 1
    timeout: int = 20
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except self.get_check_finished_exception():
            raise
        except socket.timeout as ex:
            self.cquit(
                checklib.Status.DOWN,
                'timeout error',
                f'timeout error: {ex}',
            )
        except ConnectionError as ex:
            self.cquit(
                checklib.Status.DOWN,
                'connection error',
                f'connection error: {ex}',
            )
        except socket.error as ex:
            self.cquit(
                checklib.Status.MUMBLE,
                'socket error',
                f'socket error: {ex}',
            )

    def check(self):
        username = random_username()
        password = random_password()
        secret = random_secret()

        plaintext1 = random_plaintext()
        ciphertext1 = des_encrypt(password.encode(), plaintext1)

        plaintext2 = random_plaintext()
        ciphertext2 = des_encrypt(password.encode(), plaintext2)

        with api.connect(self.host) as client:
            response = client.register(
                username.encode(),
                password.encode(),
                secret.encode(),
            )
            if response.startswith(b'error'):
                if b'user already exists' in response:
                    self.throw_mumble('user already exists', response)

                self.throw_mumble('failed to register', response)

            client.exit()

        with api.connect(self.host) as client:
            response = client.login(
                username.encode(),
                password.encode(),
            )
            if response.startswith(b'error'):
                if b'user does not exist' in response:
                    self.throw_mumble('user does not exist', response)

                self.throw_mumble('failed to login', response)

            if not response.endswith(secret.encode()):
                self.throw_mumble('invalid secret', response)

            def encrypt_scenario():
                response = client.encrypt(
                    b''.join(plaintext1),
                )
                if response.startswith(b'error'):
                    self.throw_mumble('failed to encrypt', response)

                if response != ciphertext1:
                    self.throw_mumble('invalid encryption', response)

            def decrypt_scenario():
                response = client.decrypt(
                    ciphertext1,
                )
                if response.startswith(b'error'):
                    self.throw_mumble('failed to decrypt', response)

                if response != b''.join(plaintext1):
                    self.throw_mumble('invalid decryption', response)

            if secrets.randbits(1) == 0:
                encrypt_scenario()
                decrypt_scenario()
            else:
                decrypt_scenario()
                encrypt_scenario()

            client.logout()
            client.exit()

        with api.connect(self.host) as client:
            response = client.encrypt(
                b''.join(plaintext2),
                username,
            )
            if response.startswith(b'error'):
                self.throw_mumble('failed to encrypt', response)

            if response != ciphertext2:
                self.throw_mumble('invalid encryption', response)

            client.exit()

        self.cquit(checklib.Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        username = random_username()
        password = random_password()

        with api.connect(self.host) as client:
            response = client.register(
                username.encode(),
                password.encode(),
                flag.encode(),
            )
            if response.startswith(b'error'):
                if b'user already exists' in response:
                    self.throw_mumble('user already exists', response)

                self.throw_mumble('failed to register', response)

            client.exit()

        self.cquit(
            checklib.Status.OK,
            username,
            self.store_flag_id(username, password),
        )

    def get(self, flag_id: str, flag: str, vuln: str):
        username, password = self.load_flag_id(flag_id)

        with api.connect(self.host) as client:
            response = client.login(
                username.encode(),
                password.encode(),
            )
            if response.startswith(b'error'):
                if b'user does not exist' in response:
                    self.throw_corrupt('user does not exist', response)

                self.throw_mumble('failed to login', response)

            if not response.endswith(flag.encode()):
                self.throw_corrupt('invalid secret', response)

            client.logout()
            client.exit()

        self.cquit(checklib.Status.OK)

    def throw_mumble(self, message: str, reason: Any):
        self.cquit(
            checklib.Status.MUMBLE,
            message,
            f'{message}: {repr(reason)[:128]}',
        )

    def throw_corrupt(self, message: str, reason: Any):
        self.cquit(
            checklib.Status.CORRUPT,
            message,
            f'{message}: {repr(reason)[:128]}',
        )

    def store_flag_id(self, username: str, password: str) -> str:
        return f'{username} {password}'
    
    def load_flag_id(self, flag_id: str) -> Tuple[str, str]:
        return flag_id.split(' ')


if __name__ == "__main__":
    host = sys.argv[2]
    checker = Checker(host)

    try:
        action = sys.argv[1]
        arguments = sys.argv[3:]

        checker.action(action, *arguments)
    except checker.get_check_finished_exception():
        checklib.cquit(
            checklib.Status(checker.status),
            checker.public,
            checker.private,
        )
