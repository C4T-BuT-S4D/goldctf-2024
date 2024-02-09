#pragma once

#include <digger/crypto/types.h>

namespace Digger::Crypto {

    class Context {
    public:
        Context();
        ~Context();

        Context(
            const Table<56>& pc1,
            const Table<48>& pc2,
            const Table<16>& keyRotation,
            const Table<64>& initialPermutation,
            const Table<32>& roundPermutation,
            const Table<64>& finalPermutation,
            const Table<48>& expansion,
            const Mapping<64>& sbox
        );

    public:
        Table<56> PC1  = Table<56>();
        Table<48> PC2  = Table<48>();
        Table<16> KeyRotation = Table<16>();

        Table<64> InitialPermutation = Table<64>();
        Table<32> RoundPermutation = Table<32>();
        Table<64> FinalPermutation = Table<64>();

        Table<48> Expansion = Table<48>();
        Mapping<64> Sbox = Mapping<64>();
    };

}; /* namespace Digger::Crypto */
