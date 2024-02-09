#pragma once

#include <digger/server/backend.h>

#include <string>

namespace Digger::Server {

    class Frontend {
    public:
        Frontend();
        ~Frontend();

        void Run();

    private:
        void HandleRequest(Backend& backend);

        void HandleHelp(Backend& backend);
        void HandleRegister(Backend& backend);
        void HandleLogin(Backend& backend);
        void HandleLogout(Backend& backend);
        void HandleEncrypt(Backend& backend);
        void HandleDecrypt(Backend& backend);

    private:
        UsersStorage Users;
        ContextsStorage Contexts;

        std::string Username;
        bool Authorized;

        bool Exited;
    };

}; /* namespace Digger::Server */
