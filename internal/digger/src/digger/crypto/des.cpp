#include <digger/crypto/des.h>

using namespace Digger;
using namespace Digger::Crypto;

template <size_t Size>
Bits ByteToBits(Byte byte) {
    Bits bits(Size);

    for (size_t i = 0; i < Size; i += 1) {
        bits[i] = (byte >> (Size - i - 1)) & 1;
    }

    return bits;
}

template <size_t Size>
Byte BitsToByte(const Bits& bits) {
    Byte byte = 0;

    for (size_t i = 0; i < Size; i += 1) {
        byte = byte | (bits[i] << (Size - i - 1));
    }

    return byte;
}

Bits BytesToBits(const Bytes& bytes) {
    Bits bits(8 * bytes.size());

    auto it = bits.begin();

    for (auto byte : bytes) {
        auto part = ByteToBits<8>(byte);

        it = std::copy(part.begin(), part.end(), it);
    }

    return bits;
}

Bytes BitsToBytes(const Bits& bits, size_t size) {
    Bytes bytes(size);

    auto it = bits.begin();
    auto part = Bits(8);

    for (size_t i = 0; i < size; i += 1) {
        std::copy(it, it + 8, part.begin());
        it += 8;

        bytes[i] = BitsToByte<8>(part);
    }

    return bytes;
}

std::pair<Bits, Bits> SplitBits(const Bits& bits, size_t size) {
    Bits first(size);
    Bits second(size);

    std::copy(bits.begin(), bits.begin() + size, first.begin());
    std::copy(bits.begin() + size, bits.end(), second.begin());

    return std::pair(first, second);
}

Bits JoinBits(const Bits& first, const Bits& second) {
    Bits bits(first.size() + second.size());

    auto it = bits.begin();

    it = std::copy(first.begin(), first.end(), it);
    it = std::copy(second.begin(), second.end(), it);

    return bits;
}

Bits Xor(const Bits& bits1, const Bits& bits2) {
    auto size = std::min(bits1.size(), bits2.size());

    Bits bits(size);

    for (size_t i = 0; i < size; i += 1) {
        bits[i] = bits1[i] ^ bits2[i];
    }

    return bits;
}

template <size_t Size>
Bits Permutate(const Bits& bits, const Table<Size>& table) {
    Bits result(Size);

    for (size_t i = 0; i < Size; i += 1) {
        result[i] = bits[table[i] - 1];
    }

    return result;
}

template <size_t Size>
Bits Expand(const Bits& bits, const Table<Size>& table) {
    Bits result(Size);

    for (size_t i = 0; i < Size; i += 1) {
        result[i] = bits[table[i] - 1];
    }

    return result;
}

template <size_t Size>
Bits Substitute(const Bits& bits, const Mapping<Size>& mapping) {
    Bytes pieces(8);

    auto it = bits.begin();
    Bits part(6);

    for (size_t i = 0; i < 8; i += 1) {
        std::copy(it, it + 6, part.begin());
        it += 6;

        pieces[i] = BitsToByte<6>(part);
    }

    Bits result(4 * 8);
    auto it2 = result.begin();

    for (size_t i = 0; i < 8; i += 1) {
        auto piece = pieces[i];

        auto row = (piece & 1) | ((piece >> 4) & 0b10);
        auto column = (piece & 0b011110) >> 1;

        auto value = static_cast<Byte>(mapping[i][row * 16 + column]);
        auto part = ByteToBits<4>(value);

        it2 = std::copy(part.begin(), part.end(), it2);
    }

    return result;
}

Bits DES::Function(const Bits& bits, const Bits& key) const {
    Bits result;

    result = Expand(bits, Ctx.Expansion);
    result = Xor(result, key);
    result = Substitute(result, Ctx.Sbox);
    result = Permutate(result, Ctx.RoundPermutation);

    return result;
}

KeySchedule DES::GenerateKeySchedule(const Bytes& key, size_t rounds) const {
    Bits bits = BytesToBits(key);

    bits = Permutate(bits, Ctx.PC1);
    auto pair = SplitBits(bits, 28);

    KeySchedule schedule;

    for (size_t round = 0; round < rounds; round += 1) {
        auto rotation = Ctx.KeyRotation[round];

        std::rotate(pair.first.begin(), pair.first.begin() + rotation, pair.first.end());
        std::rotate(pair.second.begin(), pair.second.begin() + rotation, pair.second.end());

        auto key = JoinBits(pair.first, pair.second);
        key = Permutate(key, Ctx.PC2);

        schedule.push_back(key);
    }

    return schedule;
}

Bytes DES::ProcessBlock(const Bytes& text, const KeySchedule& schedule) const {
    auto bits = BytesToBits(text);

    bits = Permutate(bits, Ctx.InitialPermutation);
    auto pair = SplitBits(bits, 32);

    for (auto key : schedule) {
        auto result = Function(pair.second, key);
        auto tmp = Xor(result, pair.first);

        pair.first = pair.second;
        pair.second = tmp;
    }

    bits = JoinBits(pair.second, pair.first);
    bits = Permutate(bits, Ctx.FinalPermutation);

    return BitsToBytes(bits, 8);
}

DES::DES(const Context& ctx, const Bytes& key, size_t rounds)
    : Ctx(ctx) {
    RoundKeys = GenerateKeySchedule(key, rounds);
    ReversedRoundKeys = KeySchedule(RoundKeys.rbegin(), RoundKeys.rend());
}

DES::~DES() { }

Bytes DES::Encrypt(const Bytes& plaintext) const {
    return ProcessBlock(plaintext, RoundKeys);
}

Bytes DES::Decrypt(const Bytes& ciphertext) const {
    return ProcessBlock(ciphertext, ReversedRoundKeys);
}
