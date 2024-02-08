#!/usr/bin/env python3

from typing import List, Tuple

import tables


Bits = List[int]
Bytes = bytes

Table = Tuple[int]
Mapping = List[Tuple[int]]

KeySchedule = List[Bits]

 
def int_to_bits(value: int, size: int) -> Bits:
    bits = []

    for i in reversed(range(size)):
        bits.append((value >> i) & 1)

    return bits


def bits_to_int(bits: Bits) -> int:
    value = 0

    for bit in bits:
        value <<= 1
        value |= bit

    return value


def block_to_bits(block: Bytes) -> Bits:
    bits = []

    for byte in block:
        bits.extend(int_to_bits(byte, 8))

    return bits


def bits_to_block(bits: Bits, size: int) -> Bytes:
    block_bytes = []

    for i in range(size):
        byte = bits_to_int(bits[i * 8 : (i + 1) * 8])
        block_bytes.append(byte)

    return Bytes(block_bytes)


def xor(bits1: Bits, bits2: Bits) -> Bits:
    return [x ^ y for x, y in zip(bits1, bits2)]


def permutate(bits: Bits, table: Table) -> Bits:
    return [
        bits[table[i] - 1]
        for i in range(len(table))
    ]


def expand(bits: Bits, table: Table) -> Bits:
    return [
        bits[table[i] - 1]
        for i in range(len(table))
    ]


def substitute(bits: Bits, mapping: Mapping) -> Bits:
    pieces = []

    for i in range(8):
        piece_bits = bits[i * 6 : (i + 1) * 6]

        piece = bits_to_int(piece_bits)
        pieces.append(piece)

    values = []

    for i, piece in enumerate(pieces):
        row = (piece & 1) | ((piece >> 4) & 0b10)
        column = (piece & 0b011110) >> 1

        values.append(mapping[i][row * 16 + column])

    result_bits = []

    for value in values:
        result_bits.extend(int_to_bits(value, 4))

    return result_bits


class DES:
    def __init__(self, key: Bytes, rounds: int = 16):
        self.rounds = rounds
        self.round_keys = self._key_schedule(key)
        self.reversed_round_keys = self.round_keys[::-1]

    def encrypt(self, block: Bytes) -> Bytes:
        return self._process_block(block, self.round_keys)

    def decrypt(self, block: Bytes) -> Bytes:
        return self._process_block(block, self.reversed_round_keys)

    def _key_schedule(self, key: Bytes) -> KeySchedule:
        key = block_to_bits(key)

        key = permutate(key, tables.PC1)
        left, right = key[:28], key[28:]

        round_keys = []

        for i in range(self.rounds):
            rotation = tables.KEY_ROTATION[i]

            left = left[rotation:] + left[:rotation]
            right = right[rotation:] + right[:rotation]

            round_key = permutate(left + right, tables.PC2)
            round_keys.append(round_key)

        return round_keys

    def _process_block(self, block: Bytes, schedule: KeySchedule) -> Bytes:
        bits = block_to_bits(block)

        bits = permutate(bits, tables.INITIAL_PERMUTATION)
        left, right = bits[:32], bits[32:]

        for i in range(self.rounds):
            new_right = self._function(right, schedule[i])
            left, right = right, xor(new_right, left)

        result_bits = right + left
        result_bits = permutate(result_bits, tables.FINAL_PERMUTATION)

        return bits_to_block(result_bits, 8)

    def _function(self, bits: Bits, key_bits: Bits) -> Bits:
        bits = expand(bits, tables.EXPANSION)
        bits = xor(bits, key_bits)
        bits = substitute(bits, tables.SBOX)
        bits = permutate(bits, tables.ROUND_PERMUTATION)

        return bits


def main():
    des = DES(b'12345678')
    assert des.encrypt(b'0A1B2C3D') == b'X\xa1K\xcek\x0c\xc4\x90'
    assert des.decrypt(b'X\xa1K\xcek\x0c\xc4\x90') == b'0A1B2C3D'


if __name__ == '__main__':
    main()
