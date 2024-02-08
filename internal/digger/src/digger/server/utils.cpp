#include <digger/server/utils.h>
#include <digger/crypto/types.h>

#include <sstream>
#include <fstream>
#include <iomanip>

using namespace Digger;
using namespace Digger::Server;

std::string CombinePath(const std::string& directory, const std::string& filename) {
    std::stringstream stream;

    stream << "./" << directory << "/" << filename;

    return stream.str();
}

bool Server::FileExists(const std::string& directory, const std::string& filename) {
    auto path = CombinePath(directory, filename);

    return std::filesystem::exists(path);
}

std::string Server::ReadFile(const std::string& directory, const std::string& filename) {
    auto path = CombinePath(directory, filename);

    std::ifstream file;
    file.open(path, std::ifstream::in);

    std::string content;
    file >> content;

    file.close();

    return content;
}

void Server::WriteFile(const std::string& directory, const std::string& filename, const std::string& content) {
    auto path = CombinePath(directory, filename);

    std::ofstream file;
    file.open(path, std::ofstream::out);

    file << content;

    file.close();
}

Crypto::Bytes Server::HexToBytes(const std::string& hex) {
    static const Crypto::Table<256> hexdigits = {
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 0, 0, 0, 0, 0,
        0, 10, 11, 12, 13, 14, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 10, 11, 12, 13, 14, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    };

    auto count = static_cast<size_t>(hex.size() / 2);

    if (count * 2 != hex.size()) {
        throw std::invalid_argument("invalid hex length");
    }

    Crypto::Bytes bytes(count);

    for (size_t i = 0; i < count; i += 1) {
        auto left = hex[2 * i];
        auto right = hex[2 * i + 1];

        if (!std::isxdigit(left) || !std::isxdigit(right)) {
            throw std::invalid_argument("invalid hex string");
        }

        left = hexdigits[static_cast<unsigned char>(left)];
        right = hexdigits[static_cast<unsigned char>(right)];

        bytes[i] = (left << 4) | right;
    }

    return bytes;
}

std::string Server::BytesToHex(const Crypto::Bytes& bytes) {
    std::stringstream stream;

    stream << std::hex << std::setfill('0');

    for (auto byte : bytes) {
        stream << std::setw(2) << static_cast<unsigned int>(byte);
    }

    return stream.str();
}

std::vector<Crypto::Bytes> Server::SplitBlocks(const Crypto::Bytes& bytes, size_t size) {
    auto count = static_cast<size_t>(bytes.size() / size);

    if (count * size != bytes.size()) {
        throw std::invalid_argument("invalid text length");
    }

    std::vector<Crypto::Bytes> result(count);

    auto it = bytes.begin();

    for (size_t i = 0; i < count; i += 1) {
        Crypto::Bytes block(size);

        std::copy(it, it + size, block.begin());
        it += size;

        result[i] = block;
    }

    return result;
}

Crypto::Bytes Server::JoinBlocks(const std::vector<Crypto::Bytes>& blocks, size_t size) {
    auto count = static_cast<size_t>(blocks.size() * size);
    Crypto::Bytes bytes(count);

    auto it = bytes.begin();

    for (auto block : blocks) {
        std::copy(block.begin(), block.end(), it);
        it += size;
    }

    return bytes;
}
