#ifndef OUTPUTWRITER_H
#define OUTPUTWRITER_H

#include <vector>
#include <string>
#include "returndata.h"

void writeAdjustedReturnsToFile(const std::vector<AdjustedReturn>& data, const std::string& filename);

#endif
