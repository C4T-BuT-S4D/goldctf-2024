#include <digger/crypto/context.h>

#include <digger/crypto/tables.h>

using namespace Digger;
using namespace Digger::Crypto;

Context::Context()
    : PC1(Tables::PC1)
    , PC2(Tables::PC2)
    /* VULNERABILITY */ 
    /* , KeyRotation(Tables::KEY_ROTATION) */
    , InitialPermutation(Tables::INITIAL_PERMUTATION)
    , RoundPermutation(Tables::ROUND_PERMUTATION)
    , FinalPermutation(Tables::FINAL_PERMUTATION)
    , Expansion(Tables::EXPANSION)
    , Sbox(Tables::SBOX) { }

Context::~Context() { }

Context::Context(
    const Table<56>& pc1,
    const Table<48>& pc2,
    const Table<16>& keyRotation,
    const Table<64>& initialPermutation,
    const Table<32>& roundPermutation,
    const Table<64>& finalPermutation,
    const Table<48>& expansion,
    const Mapping<64>& sbox
)
    : PC1(pc1)
    , PC2(pc2)
    , KeyRotation(keyRotation)
    , InitialPermutation(initialPermutation)
    , RoundPermutation(roundPermutation)
    , FinalPermutation(finalPermutation)
    , Expansion(expansion)
    , Sbox(sbox) { }
