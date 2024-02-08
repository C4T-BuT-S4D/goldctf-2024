#pragma once

#include <digger/crypto/types.h>

#include <string>
#include <vector>

namespace Digger::Server {

    bool FileExists(const std::string& directory, const std::string& filename);
    std::string ReadFile(const std::string& directory, const std::string& filename);
    void WriteFile(const std::string& directory, const std::string& filename, const std::string& content);

    Crypto::Bytes HexToBytes(const std::string& hex);
    std::string BytesToHex(const Crypto::Bytes& bytes);

    std::vector<Crypto::Bytes> SplitBlocks(const Crypto::Bytes& bytes, size_t size);
    Crypto::Bytes JoinBlocks(const std::vector<Crypto::Bytes>& bytes, size_t size);

}; /* namespace Digger::Server */
