#ifndef INPUTPARSER_H
#define INPUTPARSER_H

#include <string>
#include <vector>
#include "clientprofile.h"

bool loadClientProfilesFromCSV(const std::string& filename, std::vector<ClientProfile>& out);

#endif // INPUTPARSER_H
