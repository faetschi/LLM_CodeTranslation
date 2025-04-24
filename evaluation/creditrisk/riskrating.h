#ifndef RISKRATING_H
#define RISKRATING_H

#include <string>

class RiskRatingMapper {
public:
    std::string getRating(double score) const {
        if (score >= 0.85) return "AAA";
        if (score >= 0.70) return "AA";
        if (score >= 0.60) return "A";
        if (score >= 0.50) return "BBB";
        if (score >= 0.40) return "BB";
        if (score >= 0.30) return "B";
        return "D";
    }
};

#endif // RISKRATING_H
