#ifndef SCOREWEIGHTS_H
#define SCOREWEIGHTS_H

#include <string>
#include <unordered_map>

class ScoreWeights {
public:
    void setWeight(const std::string& factorName, double weight);
    double getWeight(const std::string& factorName) const;

    static ScoreWeights defaultWeights(); // <-- Add this

private:
    std::unordered_map<std::string, double> weights;
};

#endif // SCOREWEIGHTS_H
