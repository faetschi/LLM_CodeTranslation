#ifndef WAEHRUNG_H
#define WAEHRUNG_H

#include <string>

class Waehrung {
public:
    Waehrung();
    bool IsValidPair(const std::string& pair) const;

private:
    std::set<std::string> validPairs;
};

#endif // WAEHRUNG_H
