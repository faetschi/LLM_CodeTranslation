#ifndef RETURNDATA_H
#define RETURNDATA_H

#include <string>
#include <vector>

struct ReturnData {
    int year;
    double nominalRate;   // e.g. 0.07 for 7%
    double inflationRate; // e.g. 0.015 for 1.5%
};

bool loadReturnDataFromCSV(const std::string& filename, std::vector<ReturnData>& out);

#endif // RETURNDATA_H
