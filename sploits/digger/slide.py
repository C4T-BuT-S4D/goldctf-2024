#!/usr/bin/env python3

import random
import itertools
from typing import List, Tuple, Callable

import des
import tables


PAIRS_COUNT = (2 ** 14)
PAIRS_TRIES = 8

Pair = Tuple[des.Bytes, des.Bytes]
Oracle = Callable[[List[des.Bytes]], List[des.Bytes]]

INV_ROUND_PERMUTATION = [
    tables.ROUND_PERMUTATION.index(i + 1) + 1
    for i in range(len(tables.ROUND_PERMUTATION))
]

PC1_tmp = {y: x for x, y in enumerate(tables.PC1)}
INV_PC1 = [
    PC1_tmp.get(i + 1, -1) + 1
    for i in range(64)
]

PC2_tmp = {y: x for x, y in enumerate(tables.PC2)}
INV_PC2 = [
    PC2_tmp.get(i + 1, -1) + 1
    for i in range(56)
]


def urandom(length: int) -> bytes:
    return bytes(
        random.randrange(0, 256) for _ in range(length)
    )


def permutate_bytes(block: des.Bytes, table: des.Table) -> des.Bytes:
    block_bits = des.block_to_bits(block)
    block_bits = des.permutate(block_bits, table)
    block = des.bits_to_block(block_bits, 8)

    return block


def extract_round_key_candidates(plaintext: des.Bytes, ciphertext: des.Bytes) -> List[des.Bits]:
    plaintext = des.block_to_bits(plaintext)
    ciphertext = des.block_to_bits(ciphertext)

    plaintext = des.permutate(plaintext, tables.INITIAL_PERMUTATION)

    left1, right1 = plaintext[:32], plaintext[32:]
    left2, right2 = ciphertext[:32], ciphertext[32:]
    assert right1 == left2

    new_right = des.xor(right2, left1)
    new_right = des.permutate(new_right, INV_ROUND_PERMUTATION)

    old_right = des.expand(right1, tables.EXPANSION)

    round_keys = []

    for i in range(8):
        round_key = sum([x[0] for x in round_keys], [])
        round_keys_part = []

        for value in range(2 ** 6):
            key_part = des.int_to_bits(value, 6)
            round_key_test = round_key + key_part + [0] * (48)

            old_right_test = des.xor(old_right, round_key_test)
            old_right_test = des.substitute(old_right_test, tables.SBOX)

            if old_right_test[:(i + 1) * 4] == new_right[:(i + 1) * 4]:
                round_keys_part.append(key_part)

        round_keys.append(round_keys_part)

    return round_keys


def find_round_key(pairs1: List[Pair], pairs2: List[Pair]) -> des.Bits:
    sub_blocks1 = {
        ciphertext[:4]: i
        for i, (_, ciphertext) in enumerate(pairs1)
    }

    sub_blocks2 = {
        ciphertext[4:]: i
        for i, (_, ciphertext) in enumerate(pairs2)
    }

    static_des = des.DES(b'AAAAAAAA')

    for sub_block in sub_blocks1:
        index1, index2 = None, None

        if sub_block in sub_blocks2:
            index1 = sub_blocks1[sub_block]
            index2 = sub_blocks2[sub_block]

            plaintext1, ciphertext1 = pairs1[index1]
            plaintext2, ciphertext2 = pairs2[index2]

            ciphertext1 = permutate_bytes(ciphertext1, tables.FINAL_PERMUTATION)

            candidates = extract_round_key_candidates(plaintext1, plaintext2)

            for candidate in itertools.product(*candidates):
                candidate = sum(candidate, [])
                static_des.round_keys = [candidate] * len(static_des.round_keys)

                if static_des.encrypt(plaintext1) == ciphertext1:
                    return candidate
                

def bruteforce_master_key(round_key: des.Bits, plaintext: des.Bytes, ciphertext: des.Bytes) -> des.Bits:
    round_key = des.permutate(round_key + [-1], INV_PC2)[:56]

    left, right = round_key[:28], round_key[28:]

    # in the challenge rotation == 0, so skip it:
    # rotation = tables.KEY_ROTATION[0]
    # left = left[-rotation:] + left[:-rotation]
    # right = right[-rotation:] + right[:-rotation]

    round_key = left + right
    master_key = des.permutate(round_key + [-2], INV_PC1)[:64]

    indices1 = [i for i in range(len(master_key)) if master_key[i] == -1]
    indices2 = [i for i in range(len(master_key)) if master_key[i] == -2]

    for key_part in range(2 ** 8):
        bits = des.int_to_bits(key_part, 8)

        candidate = master_key[:]

        for i, index in enumerate(indices1):
            candidate[index] = bits[i]

        candidate_clean = candidate[:]

        for index in indices2:
            candidate_clean[index] = 0

        key = des.bits_to_block(candidate_clean, 8)
        cipher = des.DES(key)

        if cipher.encrypt(plaintext) == ciphertext:
            return candidate


def slide_attack(oracle: Oracle) -> des.Bits:
    plaintexts1 = []
    plaintexts2 = []

    ciphertexts1 = []
    ciphertexts2 = []

    const_part = b'A' * 4

    for k in range(PAIRS_TRIES):
        print(f'trying {PAIRS_COUNT} blocks more')

        plaintexts1_part = []
        plaintexts2_part = []

        for i in range(PAIRS_COUNT):
            plaintext1 = urandom(4) + const_part
            plaintext1 = permutate_bytes(plaintext1, tables.FINAL_PERMUTATION)
            plaintexts1_part.append(plaintext1)

            plaintext2 = const_part + urandom(4)
            plaintext2 = permutate_bytes(plaintext2, tables.FINAL_PERMUTATION)
            plaintexts2_part.append(plaintext2)

        ciphertexts1_part = oracle(plaintexts1_part)
        ciphertexts2_part = oracle(plaintexts2_part)

        ciphertexts1_part = [
            permutate_bytes(ciphertext, tables.INITIAL_PERMUTATION)
            for ciphertext in ciphertexts1_part
        ]

        ciphertexts2_part = [
            permutate_bytes(ciphertext, tables.INITIAL_PERMUTATION)
            for ciphertext in ciphertexts2_part
        ]

        plaintexts2_part = [
            permutate_bytes(plaintext, tables.INITIAL_PERMUTATION)
            for plaintext in plaintexts2_part
        ]

        plaintexts1 += plaintexts1_part
        plaintexts2 += plaintexts2_part

        ciphertexts1 += ciphertexts1_part
        ciphertexts2 += ciphertexts2_part

        pairs1 = list(zip(plaintexts1, ciphertexts1))
        pairs2 = list(zip(plaintexts2, ciphertexts2))

        round_key = find_round_key(pairs1, pairs2)

        if round_key is not None:
            print(f'found round_key: {round_key}')

            return round_key


def recover_possible_keys(vuln_oracle: Oracle, plaintext: des.Bytes, ciphertext: des.Bytes) -> List[bytes]:
    round_key = slide_attack(vuln_oracle)
    assert round_key is not None, 'slide attack failed'

    master_key = bruteforce_master_key(round_key, plaintext, ciphertext)
    print(f'master_key: {master_key}')

    indices = [i for i in range(len(master_key)) if master_key[i] < 0]

    keys = []

    for i in range(2 ** 8):
        key_part = des.int_to_bits(i, 8)
        candidate = list(master_key)

        for i, index in enumerate(indices):
            candidate[index] = key_part[i]

        key = des.bits_to_block(candidate, 8)
        keys.append(key)

    return keys


def main():
    des1 = des.DES(b'12341234')

    plaintext = b'ABCDABCD'
    ciphertext = des1.encrypt(plaintext)

    print(plaintext.hex())
    print(ciphertext.hex())

    des2 = des.DES(b'12341234')
    des2.round_keys = [des2.round_keys[0]] * len(des2.round_keys)

    vuln_oracle = lambda blocks: [
        des2.encrypt(block) for block in blocks
    ]

    keys = recover_possible_keys(vuln_oracle, plaintext, ciphertext)
    print(keys)


if __name__ == '__main__':
    main()
