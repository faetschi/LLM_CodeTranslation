#ifndef RISKFACTOR_H
#define RISKFACTOR_H

#include "clientprofile.h"

class RiskFactor {
public:
    virtual ~RiskFactor() = default;
    virtual double compute(const ClientProfile& client) const = 0;
    virtual std::string name() const = 0;
};

class LeverageRatioFactor : public RiskFactor {
public:
    double compute(const ClientProfile& client) const override;
    std::string name() const override { return "LeverageRatio"; }
};

class ExternalRatingFactor : public RiskFactor {
public:
    double compute(const ClientProfile& client) const override;
    std::string name() const override { return "ExternalRating"; }
};

class CountryRiskFactor : public RiskFactor {
public:
    double compute(const ClientProfile& client) const override;
    std::string name() const override { return "CountryRisk"; }
};

#endif // RISKFACTOR_H
