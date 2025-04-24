#ifndef UTILITIES_H
#define UTILITIES_H

#include <string>
#include <algorithm>
#include <cctype>

namespace util {

    inline std::string trim(const std::string& str) {
        auto begin = str.find_first_not_of(" \t\r\n");
        auto end = str.find_last_not_of(" \t\r\n");
        return (begin == std::string::npos) ? "" : str.substr(begin, end - begin + 1);
    }

    inline std::string toLower(const std::string& str) {
        std::string out = str;
        std::transform(out.begin(), out.end(), out.begin(), [](unsigned char c){ return std::tolower(c); });
        return out;
    }

    inline bool isNumeric(const std::string& s) {
        return !s.empty() && std::all_of(s.begin(), s.end(), ::isdigit);
    }

}

#endif // UTILITIES_H
