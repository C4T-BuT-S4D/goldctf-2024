#pragma once

#include <string>

namespace Digger::Server {

    struct User {
        std::string Username;
        std::string Password;
        std::string Secret;
    };

}; /* namespace Digger::Server */
