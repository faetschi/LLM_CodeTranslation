#include <gtest/gtest.h>
#include "../amortization.h"

// Test that the correct number of amortization entries is generated
TEST(LoanAmortizationCalculatorTest, CorrectNumberOfEntries) {
    LoanAmortizationCalculator calc(100000, 5.0, 12);
    auto schedule = calc.calculateSchedule();
    EXPECT_EQ(schedule.size(), 12);
}

// Final balance after all payments should be zero (or very close)
TEST(LoanAmortizationCalculatorTest, FinalBalanceIsZero) {
    LoanAmortizationCalculator calc(120000, 3.0, 24);
    auto schedule = calc.calculateSchedule();
    double finalBalance = schedule.back().balance;
    EXPECT_NEAR(finalBalance, 0.0, 1e-2); // small rounding error allowed
}

// Monthly payment should remain stable (principal + interest)
TEST(LoanAmortizationCalculatorTest, MonthlyPaymentIsStable) {
    LoanAmortizationCalculator calc(200000, 4.5, 36);
    auto schedule = calc.calculateSchedule();

    double firstPayment = schedule[0].principal + schedule[0].interest;

    for (const auto& entry : schedule) {
        double payment = entry.principal + entry.interest;
        EXPECT_NEAR(payment, firstPayment, 0.01); // allow 1 cent tolerance
    }
}

// First entry should have highest interest, last entry should have lowest
TEST(LoanAmortizationCalculatorTest, InterestDecreasesOverTime) {
    LoanAmortizationCalculator calc(150000, 6.0, 24);
    auto schedule = calc.calculateSchedule();

    EXPECT_GT(schedule[0].interest, schedule.back().interest);
}

// Principal part of payment should increase over time
TEST(LoanAmortizationCalculatorTest, PrincipalIncreasesOverTime) {
    LoanAmortizationCalculator calc(150000, 6.0, 24);
    auto schedule = calc.calculateSchedule();

    EXPECT_LT(schedule[0].principal, schedule.back().principal);
}
