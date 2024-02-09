#include <digger/server/backend.h>

#include <digger/server/utils.h>

#include <digger/crypto/des.h>
#include <digger/crypto/tables.h>
#include <digger/crypto/context.h>

#include <algorithm>

using namespace Digger;
using namespace Digger::Server;

const std::string PasswordsDirectory = "storage/passwords";
const std::string SecretsDirectory = "storage/secrets";

using Exception = std::runtime_error;

Backend::Backend(UsersStorage& users, ContextsStorage& contexts)
    : Users(users)
    , Contexts(contexts) { }

Backend::~Backend() { }

void ValidateUsername(const std::string& username) {
    if (username.size() < 8 || username.size() > 32) {
        throw Exception("invalid username size");
    }

    auto pos = std::find_if(username.begin(), username.end(), [](unsigned char c) {
        return !std::isalnum(c);
    });

    if (pos != username.end()) {
        throw Exception("invalid characters in username");
    }
}

void ValidatePassword(const std::string& password) {
    if (password.size() != 8) {
        throw Exception("invalid password size");
    }

    auto pos = std::find_if(password.begin(), password.end(), [](unsigned char c) {
        return !(std::isprint(c) && !std::isspace(c));
    });

    if (pos != password.end()) {
        throw Exception("invalid characters in password");
    }
}

User Backend::LoadUser(const std::string& username) {
    if (Users.Contains(username)) {
        return Users.Get(username);
    }

    auto password = ReadFile(PasswordsDirectory, username);
    auto secret = ReadFile(SecretsDirectory, username);

    auto user = User{
        .Username = username,
        .Password = password,
        .Secret = secret
    };

    return user;
}

void Backend::StoreUser(const User& user) {
    WriteFile(PasswordsDirectory, user.Username, user.Password);
    WriteFile(SecretsDirectory, user.Username, user.Secret);
}

void Backend::Register(const std::string& username, const std::string& password, const std::string& secret) {
    ValidateUsername(username);
    ValidatePassword(password);
    
    if (Users.Contains(username) || FileExists(PasswordsDirectory, username)) {
        throw Exception("user already exists");
    }

    auto user = User{
        .Username = username,
        .Password = password,
        .Secret = secret
    };

    StoreUser(user);
}

std::string Backend::Login(const std::string& username, const std::string& password) {
    ValidateUsername(username);
    ValidatePassword(password);

    if (!Users.Contains(username) && !FileExists(PasswordsDirectory, username)) {
        throw Exception("user does not exist");
    }

    auto user = LoadUser(username);

    if (user.Password != password) {
        throw Exception("invalid password");
    }

    return user.Secret;
}

std::string Backend::Encrypt(const std::string& username, const std::string& plaintext) {
    ValidateUsername(username);

    if (!Users.Contains(username) && !FileExists(PasswordsDirectory, username)) {
        throw Exception("user does not exist");
    }

    auto bytes = HexToBytes(plaintext);
    auto blocks = SplitBlocks(bytes, 8);

    if (!Users.Contains(username)) {
        auto user = LoadUser(username);
        auto context = Crypto::Context(
            Crypto::Tables::PC1,
            Crypto::Tables::PC2,
            Crypto::Tables::KEY_ROTATION,
            Crypto::Tables::INITIAL_PERMUTATION,
            Crypto::Tables::ROUND_PERMUTATION,
            Crypto::Tables::FINAL_PERMUTATION,
            Crypto::Tables::EXPANSION,
            Crypto::Tables::SBOX
        );

        Users.Add(user.Username, user);
        Contexts.Add(user.Username, context);
    }

    auto user = Users.Get(username);
    auto context = Contexts.Get(username);

    auto key = Crypto::Bytes(user.Password.begin(), user.Password.end());
    auto cipher = Crypto::DES(context, key);

    std::vector<Crypto::Bytes> result(blocks.size());

    for (size_t i = 0; i < blocks.size(); i += 1) {
        result[i] = cipher.Encrypt(blocks[i]);
    }

    auto ciphertext = JoinBlocks(result, 8);

    return BytesToHex(ciphertext);
}

std::string Backend::Decrypt(const std::string& username, const std::string& ciphertext) {
    ValidateUsername(username);

    if (!Users.Contains(username) && !FileExists(PasswordsDirectory, username)) {
        throw Exception("user does not exist");
    }

    auto bytes = HexToBytes(ciphertext);
    auto blocks = SplitBlocks(bytes, 8);

    if (!Users.Contains(username)) {
        auto user = LoadUser(username);
        auto context = Crypto::Context(
            Crypto::Tables::PC1,
            Crypto::Tables::PC2,
            Crypto::Tables::KEY_ROTATION,
            Crypto::Tables::INITIAL_PERMUTATION,
            Crypto::Tables::ROUND_PERMUTATION,
            Crypto::Tables::FINAL_PERMUTATION,
            Crypto::Tables::EXPANSION,
            Crypto::Tables::SBOX
        );

        Users.Add(user.Username, user);
        Contexts.Add(user.Username, context);
    }

    auto user = Users.Get(username);
    auto context = Contexts.Get(username);

    auto key = Crypto::Bytes(user.Password.begin(), user.Password.end());
    auto cipher = Crypto::DES(context, key);

    std::vector<Crypto::Bytes> result(blocks.size());

    for (size_t i = 0; i < blocks.size(); i += 1) {
        result[i] = cipher.Decrypt(blocks[i]);
    }

    auto plaintext = JoinBlocks(result, 8);

    return BytesToHex(plaintext);
}
