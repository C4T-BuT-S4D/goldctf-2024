#include <digger/server/frontend.h>

#include <digger/server/backend.h>

#include <iostream>

using namespace Digger;
using namespace Digger::Server;

Frontend::Frontend()
    : Users(UsersStorage())
    , Contexts(ContextsStorage())
    , Authorized(false)
    , Exited(false) { }

Frontend::~Frontend() { }

std::string ToLower(const std::string& text) {
    std::string result(text.size(), '\0');

    for (size_t i = 0; i < text.size(); i += 1) {
        result[i] = std::tolower(text[i]);
    }

    return result;
}

void Frontend::Run() {
    std::cout << "=====================" << std::endl;
    std::cout << "=   Digger v0.0.1   =" << std::endl;
    std::cout << "=====================" << std::endl;
    std::cout << std::endl;

    while (!Exited) {
        /* VULNERABILITY */
        auto ctx = std::move(Contexts);
        auto backend = Backend(Users, ctx);

        try {
            while (!Exited) {
                HandleRequest(backend);
            }
        } catch (const std::exception& ex) {
            std::cout << "error: " << ex.what() << std::endl;
        }
    }
}

void Frontend::HandleRequest(Backend& backend) {
    std::cout << "> ";

    std::string op;
    std::cin >> op;

    if (ToLower(op) == "help") {
        HandleHelp(backend);
        return;
    }
            
    if (ToLower(op) == "register") {
        HandleRegister(backend);
        return;
    }
            
    if (ToLower(op) == "login") {
        HandleLogin(backend);
        return;
    }

    if (ToLower(op) == "logout") {
        HandleLogout(backend);
        return;
    }
    
    if (ToLower(op) == "encrypt") {
        HandleEncrypt(backend);
        return;
    }
    
    if (ToLower(op) == "decrypt") {
        HandleDecrypt(backend);
        return;
    }
    
    if (ToLower(op) == "exit" || op.size() == 0) {
        std::cout << "bye" << std::endl;
        Exited = true;
        return;
    }

    std::cout << "unknown command, use HELP" << std::endl;
}

void Frontend::HandleHelp(Backend& backend) {
    std::cout << "use REGISTER, LOGIN, LOGOUT, ENCRYPT, DECRYPT or EXIT" << std::endl;
}

void Frontend::HandleRegister(Backend& backend) {
    if (Authorized) {
        std::cout << "you are logged in, please logout first" << std::endl;
        return;
    }

    std::string username, password, secret;

    std::cout << "username: ";
    std::cin >> username;

    std::cout << "password: ";
    std::cin >> password;

    std::cout << "secret: ";
    std::cin >> secret;

    backend.Register(username, password, secret);

    std::cout << "successfully registered" << std::endl;
}

void Frontend::HandleLogin(Backend& backend) {
    if (Authorized) {
        std::cout << "you are logged in, please logout first" << std::endl;
        return;
    }

    std::string username, password;

    std::cout << "username: ";
    std::cin >> username;

    std::cout << "password: ";
    std::cin >> password;

    auto secret = backend.Login(username, password);

    Authorized = true;
    Username = username;

    std::cout << "successfully logged in, your secret: " << secret << std::endl;
}

void Frontend::HandleLogout(Backend& backend) {
    if (!Authorized) {
        std::cout << "you are not logged in, please login first" << std::endl;
        return;
    }

    Authorized = false;
    Username = "";

    std::cout << "successfully logged out" << std::endl;
}

void Frontend::HandleEncrypt(Backend& backend) {
    std::string username, plaintext;

    if (Authorized) {
        username = Username;
    } else {
        std::cout << "username: ";
        std::cin >> username;
    }

    std::cout << "plaintext (hex): ";
    std::cin >> plaintext;

    auto ciphertext = backend.Encrypt(username, plaintext);

    std::cout << "ciphertext (hex):" << std::endl;
    std::cout << ciphertext << std::endl;
}

void Frontend::HandleDecrypt(Backend& backend) {
    if (!Authorized) {
        std::cout << "you need to login first" << std::endl;
        return;
    }

    std::string ciphertext;

    std::cout << "ciphertext (hex): ";
    std::cin >> ciphertext;

    auto plaintext = backend.Decrypt(Username, ciphertext);

    std::cout << "plaintext (hex):" << std::endl;
    std::cout << plaintext << std::endl;
}
