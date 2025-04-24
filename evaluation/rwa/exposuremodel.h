#ifndef EXPOSUREMODEL_H
#define EXPOSUREMODEL_H

#include <string>

struct Exposure {
    int year;
    std::string assetClass;
    std::string rating;
    double exposureAmount;
    std::string country;
};

struct ExposureResult {
    Exposure exposure;
    double riskWeight;
    double rwa;
    double capitalRequirement;
};

double calculateRWA(double exposureAmount, double riskWeight);

#endif // EXPOSUREMODEL_H
