#ifndef REPORTWRITER_H
#define REPORTWRITER_H

#include <string>
#include <vector>
#include "exposuremodel.h"

bool writeRWAReport(const std::vector<ExposureResult>& results, const std::string& filename);
std::string generateReportFilename();

#endif // REPORTWRITER_H
