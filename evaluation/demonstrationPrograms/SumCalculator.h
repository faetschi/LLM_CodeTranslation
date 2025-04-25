#include <vector>

class SumCalculator {
public:
    SumCalculator(const std::vector<int>& numbers);
    int sum() const;
private:
    std::vector<int> data_;
};
