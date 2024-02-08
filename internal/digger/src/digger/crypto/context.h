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
        Table<56> PC1;
        Table<48> PC2;
        Table<16> KeyRotation;

        Table<64> InitialPermutation;
        Table<32> RoundPermutation;
        Table<64> FinalPermutation;

        Table<48> Expansion;
        Mapping<64> Sbox;
    };

}; /* namespace Digger::Crypto */
