#pragma once
#include <vector>

struct AmortizationEntry {
    int month;
    double principal;
    double interest;
    double balance;
};

class LoanAmortizationCalculator {
public:
    LoanAmortizationCalculator(double principal, double annualRate, int termMonths);
    std::vector<AmortizationEntry> calculateSchedule() const;

private:
    double principal_;
    double annualRate_;
    int termMonths_;
};
