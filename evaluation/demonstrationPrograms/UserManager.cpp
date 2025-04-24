// This file manages user accounts, allowing adding, removing, listing, and retrieving users.

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <stdexcept>
#include <optional>

/// Represents a simple user object
class User {
private:
    std::string username;
    std::string email;
    int accessLevel;

public:
    // Default constructor added to fix STL map usage!
    User() : username(""), email(""), accessLevel(1) {}

    User(const std::string& uname, const std::string& mail, int level)
        : username(uname), email(mail), accessLevel(level) {}

    std::string getUsername() const {
        return username;
    }

    std::string getEmail() const {
        return email;
    }

    int getAccessLevel() const {
        return accessLevel;
    }

    void printInfo() const {
        std::cout << "User: " << username << " | Email: " << email 
                  << " | Access Level: " << accessLevel << std::endl;
    }
};

/// Manages user accounts in the system
class UserManager {
private:
    std::map<std::string, User> userMap;

public:
    /// Adds a new user if username does not already exist
    void addUser(const std::string& username, const std::string& email, int accessLevel) {
        if (userMap.find(username) != userMap.end()) {
            throw std::runtime_error("User already exists: " + username);
        }

        if (accessLevel < 1 || accessLevel > 5) {
            throw std::invalid_argument("Access level must be between 1 and 5.");
        }

        User newUser(username, email, accessLevel);
        userMap[username] = newUser;
    }

    /// Removes a user by username
    void removeUser(const std::string& username) {
        if (userMap.erase(username) == 0) {
            std::cout << "No such user to remove: " << username << std::endl;
        }
    }

    /// Retrieves a user by username
    std::optional<User> getUser(const std::string& username) const {
        auto it = userMap.find(username);
        if (it != userMap.end()) {
            return it->second;
        }
        return std::nullopt;
    }

    /// Prints all registered users
    void listUsers() const {
        if (userMap.empty()) {
            std::cout << "No users found." << std::endl;
            return;
        }

        for (const auto& pair : userMap) {
            pair.second.printInfo();
        }
    }
};

int main() {
    UserManager manager;

    try {
        manager.addUser("alice", "alice@example.com", 3);
        manager.addUser("bob", "bob@example.com", 2);
        manager.addUser("charlie", "charlie@example.com", 5);
    } catch (const std::exception& e) {
        std::cerr << "Error adding user: " << e.what() << std::endl;
    }

    manager.listUsers();

    std::cout << "\nRemoving user 'bob'...\n";
    manager.removeUser("bob");

    std::cout << "\nUser list after removal:\n";
    manager.listUsers();

    std::cout << "\nTrying to fetch user 'alice':\n";
    auto user = manager.getUser("alice");
    if (user.has_value()) {
        user->printInfo();
    } else {
        std::cout << "User not found." << std::endl;
    }

    return 0;
}
