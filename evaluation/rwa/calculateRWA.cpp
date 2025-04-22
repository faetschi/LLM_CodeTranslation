#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <filesystem>
#include <chrono>
#include <random>
#include <regex>
#include <set>

#include "inputloader.h"
#include "validation.h"
#include "riskweights.h"
#include "exposuremodel.h"
#include "capitalrequirement.h"
#include "reportwriter.h"

//----------------------------------------------------------------------------
// Verwendung
//----------------------------------------------------------------------------
void Verwendung() {
    std::cout << "Usage: calculateRWA <inputfile.csv>\n";
    std::cout << "Example: calculateRWA rwa_input.csv\n";
}

//----------------------------------------------------------------------------
// Eingabedatei laden
//----------------------------------------------------------------------------

bool loadExposuresFromCSV(const std::string& filename, std::vector<Exposure>& exposures) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Failed to open file.\n";
        return false;
    }

    std::string line;
    std::getline(file, line); // skip header

    int lineNumber = 1;
    while (std::getline(file, line)) {
        ++lineNumber;
        std::stringstream ss(line);
        std::string yearStr, assetClass, rating, exposureStr, country;

        if (!std::getline(ss, yearStr, ',')) goto fail;
        if (!std::getline(ss, assetClass, ',')) goto fail;
        if (!std::getline(ss, rating, ',')) goto fail;
        if (!std::getline(ss, exposureStr, ',')) goto fail;
        if (!std::getline(ss, country, ',')) goto fail;

        try {
            Exposure exp;
            exp.year = std::stoi(yearStr);
            exp.assetClass = assetClass;
            exp.rating = rating;
            exp.exposureAmount = std::stod(exposureStr);
            exp.country = country;
            exposures.push_back(exp);
        } catch (...) {
            std::cerr << "Invalid value format at line " << lineNumber << ": " << line << "\n";
            return false;
        }

        continue;

    fail:
        std::cerr << "Invalid row structure at line " << lineNumber << ": " << line << "\n";
        return false;
    }

    return !exposures.empty();
}

//----------------------------------------------------------------------------
// Risk Tabelle
//----------------------------------------------------------------------------

RiskWeightTable RiskWeightTable::defaultTable() {
    RiskWeightTable t;
    t.table["corporate"] = {
        {"AAA", 0.2}, {"AA", 0.25}, {"A", 0.3}, {"BBB", 0.5},
        {"BB", 0.75}, {"B", 1.0}, {"CCC", 1.5}, {"D", 1.5}
    };
    t.table["sovereign"] = {
        {"AAA", 0.0}, {"AA", 0.2}, {"A", 0.3}, {"BBB", 0.5},
        {"BB", 1.0}, {"B", 1.5}, {"D", 1.5}
    };
    t.table["mortgage"] = {
        {"AAA", 0.5}, {"AA", 0.5}, {"A", 0.5}, {"BBB", 0.75},
        {"BB", 1.0}, {"D", 1.5}
    };
    t.table["retail"] = {
        {"A", 0.75}, {"B", 0.75}, {"D", 1.5}
    };
    t.table["securitization"] = {
        {"AAA", 0.2}, {"AA", 0.5}, {"A", 1.0}, {"BBB", 1.0}, {"D", 1.5}
    };
    return t;
}

double RiskWeightTable::getRiskWeight(const std::string& assetClass, const std::string& rating) const {
    auto cls = table.find(assetClass);
    if (cls != table.end()) {
        auto r = cls->second.find(rating);
        if (r != cls->second.end()) return r->second;
    }
    return 1.0; // Default
}

//----------------------------------------------------------------------------
// Berechnungen
//----------------------------------------------------------------------------

double calculateRWA(double exposureAmount, double riskWeight) {
    return exposureAmount * riskWeight;
}

double calculateCapitalRequirement(double rwa, const std::string& /*country*/) {
    return rwa * 0.08; // Simplified: 8% flat requirement
}

//----------------------------------------------------------------------------
// Report erstellen
//----------------------------------------------------------------------------

bool writeRWAReport(const std::vector<ExposureResult>& results, const std::string& filename) {
    std::filesystem::create_directories("output");
    std::ofstream outFile("output/" + filename);
    if (!outFile.is_open()) return false;

    outFile << "Year,AssetClass,Rating,Exposure,RiskWeight,RWA,CapitalRequirement\n";

    for (const auto& r : results) {
        outFile << r.exposure.year << ","
                << r.exposure.assetClass << ","
                << r.exposure.rating << ","
                << std::fixed << std::setprecision(0) << r.exposure.exposureAmount << ","  // <- No decimal
                << std::fixed << std::setprecision(2) << r.riskWeight << ","
                << std::fixed << std::setprecision(2) << r.rwa << ","
                << std::fixed << std::setprecision(2) << r.capitalRequirement << "\n";
    }

    outFile.close();
    return true;
}


//----------------------------------------------------------------------------
// Hauptprogramm
//----------------------------------------------------------------------------
#ifndef UNIT_TESTING
int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Invalid number of arguments.\n\n";
        Verwendung();
        return 1;
    }

    std::string filename = argv[1];

    if (!std::filesystem::exists(filename)) {
        std::cerr << "Input file does not exist: " << filename << "\n";
        return 1;
    }

    if (!std::regex_match(filename, std::regex(".*\\.csv"))) {
        std::cerr << "Invalid file type. Please provide a CSV file.\n";
        return 1;
    }

    std::vector<Exposure> exposures;
    if (!loadExposuresFromCSV(filename, exposures)) {
        std::cerr << "Failed to read input file or file is empty.\n";
        return 1;
    }

    bool hasInvalid = false;
    for (auto& exp : exposures) {
        exp.assetClass = trim(exp.assetClass);
        exp.rating = trim(exp.rating);

        if (exp.exposureAmount <= 0.0) {
            std::cerr << "Exposure amount <= 0 at year " << exp.year << "\n";
            hasInvalid = true;
        }

        if (!isValidRating(exp.rating)) {
            std::cerr << "Unknown credit rating: '" << exp.rating << "' at year " << exp.year << "\n";
            hasInvalid = true;
        }

        if (!isValidAssetClass(exp.assetClass)) {
            std::cerr << "Unknown asset class: '" << exp.assetClass << "' at year " << exp.year << "\n";
            hasInvalid = true;
        }
    }

    if (hasInvalid) {
        std::cerr << "Validation failed due to invalid exposure entries.\n";
        return 1;
    }

    RiskWeightTable weights = RiskWeightTable::defaultTable();
    std::vector<ExposureResult> rwaResults;

    for (const auto& exp : exposures) {
        double riskWeight = weights.getRiskWeight(exp.assetClass, exp.rating);

        if (riskWeight == 1.0) {
            std::cerr << "Default risk weight applied (100%) for asset class '"
                      << exp.assetClass << "', rating '" << exp.rating << "'\n";
        }

        double rwa = calculateRWA(exp.exposureAmount, riskWeight);
        double capital = calculateCapitalRequirement(rwa, exp.country);

        rwaResults.push_back({exp, riskWeight, rwa, capital});
    }

    std::string reportFile = generateReportFilename();
    if (!writeRWAReport(rwaResults, reportFile)) {
        std::cerr << "Failed to write report.\n";
        return 1;
    }    

    std::cout << "Calculation complete.\n";
    std::cout << "Report generated: output/" << reportFile << "\n";

    return 0;
}
#endif

//----------------------------------------------------------------------------
// Hilfsfunktionen
//----------------------------------------------------------------------------
std::string trim(const std::string& str) {
    size_t first = str.find_first_not_of(" \t\r\n");
    size_t last = str.find_last_not_of(" \t\r\n");
    return (first == std::string::npos) ? "" : str.substr(first, last - first + 1);
}

bool isValidRating(const std::string& rating) {
    static const std::set<std::string> validRatings = {
        "AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"
    };
    return validRatings.count(rating);
}

bool isValidAssetClass(const std::string& assetClass) {
    static const std::set<std::string> validClasses = {
        "corporate", "mortgage", "sovereign", "retail", "securitization"
    };
    return validClasses.count(assetClass);
}

std::string generateReportFilename() {
    auto now = std::chrono::system_clock::now();
    auto in_time = std::chrono::system_clock::to_time_t(now);
    std::tm tm = *std::localtime(&in_time);

    std::ostringstream oss;
    oss << "rwa_report_"
        << std::put_time(&tm, "%Y%m%d_%H%M");

    // Zufällige 6-digit number
    std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<int> dist(100000, 999999);
    oss << "_" << dist(rng) << ".csv";

    return oss.str();
}

