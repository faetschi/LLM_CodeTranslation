#ifndef VALIDATION_H
#define VALIDATION_H

#include <string>
#include <vector>
#include "exposuremodel.h"

bool isValidRating(const std::string& rating);
bool isValidAssetClass(const std::string& assetClass);
std::string trim(const std::string& str);

#endif // VALIDATION_H
