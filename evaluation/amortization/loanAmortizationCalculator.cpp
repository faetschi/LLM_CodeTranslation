#include "amortization.h"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <filesystem>

LoanAmortizationCalculator::LoanAmortizationCalculator(double principal, double annualRate, int termMonths)
    : principal_(principal), annualRate_(annualRate), termMonths_(termMonths) {}

std::vector<AmortizationEntry> LoanAmortizationCalculator::calculateSchedule() const {
    std::vector<AmortizationEntry> schedule;
    double monthlyRate = annualRate_ / 12.0 / 100.0;
    double balance = principal_;

    double monthlyPayment = (principal_ * monthlyRate) / (1 - std::pow(1 + monthlyRate, -termMonths_));

    for (int i = 1; i <= termMonths_; ++i) {
        double interest = balance * monthlyRate;
        double principalPaid = monthlyPayment - interest;
        balance -= principalPaid;

        if (i == termMonths_) balance = 0.0; // Ensure last balance is zero

        schedule.push_back({i, principalPaid, interest, balance});
    }

    return schedule;
}

bool readInputFromCSV(const std::string& filePath, double& principal, double& rate, int& term) {
    std::ifstream file(filePath);
    if (!file.is_open()) {
        std::cerr << "Could not open input file: " << filePath << "\n";
        return false;
    }

    std::string line;

    // Skip the header line
    if (!std::getline(file, line)) {
        std::cerr << "Input file is empty.\n";
        return false;
    }

    // Read the actual data line
    if (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string value;

        try {
            if (std::getline(ss, value, ';')) principal = std::stod(value);
            if (std::getline(ss, value, ';')) rate = std::stod(value);
            if (std::getline(ss, value, ';')) term = std::stoi(value);
        } catch (...) {
            std::cerr << "Failed to parse input values (invalid format).\n";
            return false;
        }

        if (principal <= 0 || rate <= 0 || term <= 0) {
            std::cerr << "Invalid input values: Principal, rate, and term must be positive.\n";
            return false;
        }

        return true;
    }

    std::cerr << "No data line found in input file.\n";
    return false;
}


bool writeScheduleToCSV(const std::string& filePath, const std::vector<AmortizationEntry>& schedule) {
    std::filesystem::create_directories("output");

    std::ofstream file(filePath);
    if (!file.is_open()) {
        std::cerr << "Could not write to file: " << filePath << "\n";
        return false;
    }

    file << "Month;Principal;Interest;Balance\n";
    for (const auto& entry : schedule) {
        file << entry.month << ";"
             << std::fixed << std::setprecision(2)
             << entry.principal << ";"
             << entry.interest << ";"
             << entry.balance << "\n";
    }

    return true;
}

#ifndef UNIT_TEST
int main() {
    double principal;
    double rate;
    int term;

    if (!readInputFromCSV("input.csv", principal, rate, term)) {
        std::cerr << "Failed to read input.csv\n";
        return 1;
    }

    LoanAmortizationCalculator calculator(principal, rate, term);
    auto schedule = calculator.calculateSchedule();

    if (!writeScheduleToCSV("output/schedule_output.csv", schedule)) {
        std::cerr << "Failed to write output file\n";
        return 1;
    }

    std::cout << "Amortization schedule saved to output/schedule_output.csv\n";
    return 0;
}
#endif
