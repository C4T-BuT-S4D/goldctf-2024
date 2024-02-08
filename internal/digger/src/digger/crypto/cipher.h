#pragma once

#include <digger/crypto/types.h>

namespace Digger::Crypto {

    class Cipher {
    public:
        virtual Bytes Encrypt(const Bytes& plaintext) const = 0;
        virtual Bytes Decrypt(const Bytes& ciphertext) const = 0;
    };

}; /* namespace Digger::Crypto */
