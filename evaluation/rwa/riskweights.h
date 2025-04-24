#ifndef RISKWEIGHTS_H
#define RISKWEIGHTS_H

#include <string>
#include <map>

class RiskWeightTable {
public:
    static RiskWeightTable defaultTable();
    double getRiskWeight(const std::string& assetClass, const std::string& rating) const;

private:
    std::map<std::string, std::map<std::string, double>> table;
};

#endif // RISKWEIGHTS_H
