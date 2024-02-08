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

    test_ciphertext = client.encrypt(plaintext, username)
    assert test_ciphertext != ciphertext, 'cipher is not vulnerable'

    def vuln_oracle(blocks: List[des.Bytes]) -> List[des.Bytes]:
        result = []

        part_size = 8 * 1024

        for i in range(0, len(blocks), part_size):
            part = blocks[i : i + part_size]

            plaintext = b''.join(part)
            ciphertext = client.encrypt(plaintext, username)
            new_blocks = [ciphertext[i : i + 8] for i in range(0, len(ciphertext), 8)]

            result += new_blocks

        return result

    keys = slide.recover_possible_keys(vuln_oracle, plaintext, ciphertext)
    # print(keys)

    for key in keys:
        secret = client.login(username, key)

        if not secret.startswith(b'error'):
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
