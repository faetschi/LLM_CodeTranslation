#ifndef CALCULATIONS_H
#define CALCULATIONS_H

#include <vector>
#include "returndata.h"

struct AdjustedReturn {
    int year;
    double nominalRate;
    double inflationRate;
    double realRate;
    double accumulated;
};

std::vector<AdjustedReturn> computeInflationAdjustedReturns(const std::vector<ReturnData>& data);

#endif // CALCULATIONS_H
