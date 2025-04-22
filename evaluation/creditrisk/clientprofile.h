#ifndef CLIENTPROFILE_H
#define CLIENTPROFILE_H

#include <string>

struct ClientProfile {
    std::string clientId;
    std::string name;
    std::string country;
    std::string clientType; // "corporate", "retail", "sovereign"

    int age;
    double income;
    std::string employment;
    std::string industry;
    double debt;

    double calculatedScore = 0.0;
};

#endif // CLIENTPROFILE_H
