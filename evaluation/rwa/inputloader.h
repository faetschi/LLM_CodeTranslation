#ifndef INPUTLOADER_H
#define INPUTLOADER_H

#include <string>
#include <vector>
#include "exposuremodel.h"

bool loadExposuresFromCSV(const std::string& filename, std::vector<Exposure>& exposures);

#endif // INPUTLOADER_H
