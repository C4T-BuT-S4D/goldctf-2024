#!/usr/bin/env python3

import sys
import time
from typing import List

import api
import des
import slide


def attack(client: api.API, username: bytes) -> bytes:
    plaintext = b'AAAAAAAA'
    ciphertext = client.encrypt(plaintext, username)

    # break the cipher
    client.encrypt(b'AABB', username)
    time.sleep(0.5)

    response = client.encrypt(plaintext, username)

    if response.startswith(b'error'):
        return response

    assert response != ciphertext, 'cipher is not vulnerable'

    oracle_calls = 0
    oracle_data = 0

    oracle_part_size = 8 * 1024

    def vuln_oracle(blocks: List[des.Bytes]) -> List[des.Bytes]:
        nonlocal oracle_calls, oracle_data, oracle_part_size

        result = []

        for i in range(0, len(blocks), oracle_part_size):
            part = blocks[i : i + oracle_part_size]

            plaintext = b''.join(part)
            ciphertext = client.encrypt(plaintext, username)
            new_blocks = [ciphertext[i : i + 8] for i in range(0, len(ciphertext), 8)]

            result += new_blocks

            print(f'encrypted {i + oracle_part_size} / {len(blocks)}')

            oracle_calls += 1
            oracle_data += len(plaintext) + len(ciphertext)

        return result

    keys = slide.recover_possible_keys(vuln_oracle, plaintext, ciphertext)
    # print(keys)

    print(f'oracle calls: {oracle_calls} by {oracle_part_size / 1024} KB')
    print(f'oracle data: {oracle_data / 1024} KB, {oracle_data / 1024 / 1024} MB')

    for key in keys:
        secret = client.login(username, key)

        if not secret.startswith(b'error'):
            print(f'found key: {key}')

            return secret


def main():
    hostname = sys.argv[1]
    username = sys.argv[2]

    with api.connect(hostname) as client:
        flag = attack(client, username)
        print(flag)

        client.exit()


if __name__ == '__main__':
    main()
