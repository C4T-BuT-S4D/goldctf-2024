#pragma once

#include <digger/crypto/types.h>
#include <digger/crypto/cipher.h>
#include <digger/crypto/context.h>

#include <vector>

namespace Digger::Crypto {

    using KeySchedule = std::vector<Bits>;

    class DES : public Cipher {
    public:
        DES(const Context& ctx, const Bytes& key, size_t rounds = 16);
        ~DES();

        Bytes Encrypt(const Bytes& plaintext) const;
        Bytes Decrypt(const Bytes& ciphertext) const;

    private:
        KeySchedule GenerateKeySchedule(const Bytes& key, size_t rounds) const;
        Bytes ProcessBlock(const Bytes& text, const KeySchedule& schedule) const;
        Bits Function(const Bits& bits, const Bits& key) const;

    private:
        const Context& Ctx;

        KeySchedule RoundKeys;
        KeySchedule ReversedRoundKeys;
    };

}; /* namespace Digger::Crypto */
