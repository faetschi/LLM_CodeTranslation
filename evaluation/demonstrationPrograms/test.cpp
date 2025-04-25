#include "SumCalculator.h"

SumCalculator::SumCalculator(const std::vector<int>& numbers)
    : data_(numbers) {}

int SumCalculator::sum() const {
    int total = 0;
    for (int val : data_) {
        total += val;
    }
    return total;
}
