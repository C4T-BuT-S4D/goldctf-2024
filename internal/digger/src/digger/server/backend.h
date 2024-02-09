#pragma once

#include <digger/server/models.h>

#include <digger/primitives/cache.h>

#include <digger/crypto/des.h>
#include <digger/crypto/context.h>

#include <string>

namespace Digger::Server {

    using UsersStorage = Primitives::Cache<std::string, User>;
    using ContextsStorage = Primitives::Cache<std::string, Crypto::Context>;

    class Backend {
    public:
        Backend(UsersStorage& Users, ContextsStorage& Contexts);
        ~Backend();

        void Register(const std::string& username, const std::string& password, const std::string& secret);
        std::string Login(const std::string& username, const std::string& password);

        std::string Encrypt(const std::string& username, const std::string& plaintext);
        std::string Decrypt(const std::string& username, const std::string& ciphertext);

    private:
        User LoadUser(const std::string& username);
        void StoreUser(const User& user);

    private:
        UsersStorage& Users;
        ContextsStorage& Contexts;
    };

}; /* namespace Digger::Server */
