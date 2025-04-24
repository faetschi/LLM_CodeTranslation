#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <random>
#include <filesystem>

#include "returndata.h"
#include "calculations.h"
#include "outputwriter.h"

//---------------------------------------------------
// Datenladung Implementation
//---------------------------------------------------

bool loadReturnDataFromCSV(const std::string& filename, std::vector<ReturnData>& out) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Datei konnte nicht geöffnet werden: " << filename << "\n";
        return false;
    }

    std::string line;
    std::getline(file, line); // Skip header

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string yearStr, nominalStr, inflationStr;

        if (!std::getline(ss, yearStr, ',') ||
            !std::getline(ss, nominalStr, ',') ||
            !std::getline(ss, inflationStr, ',')) {
            std::cerr << "Strukturfehler in Zeile: " << line << std::endl;
            std::exit(EXIT_FAILURE);
        }

        try {
            int year = std::stoi(yearStr);
            double nominal = std::stod(nominalStr);
            double inflation = std::stod(inflationStr);

            // Semantic checks
            if (year < 1900 || year > 2100 ||
                nominal < -1.0 || nominal > 1.0 ||
                inflation < -1.0 || inflation > 1.0) {
                std::cerr << "Ungültige Werte in Zeile: " << line << std::endl;
                std::exit(EXIT_FAILURE);
            }

            out.push_back({year, nominal, inflation});
        } catch (...) {
            std::cerr << "Ungültige Zeile in CSV (Parsing-Fehler): " << line << std::endl;
            std::exit(EXIT_FAILURE);
        }
    }

    return !out.empty();
}


//---------------------------------------------------
// Kalkulationen Implementation
//---------------------------------------------------

std::vector<AdjustedReturn> computeInflationAdjustedReturns(const std::vector<ReturnData>& data) {
    std::vector<AdjustedReturn> result;
    double accumulated = 1;   

    for (const auto& entry : data) {
        double real = (1 + entry.nominalRate) / (1 + entry.inflationRate) - 1;
        accumulated *= (1 + real);

        result.push_back({
            entry.year,
            entry.nominalRate,
            entry.inflationRate,
            real,
            accumulated - 1
        });
    }

    return result;
}

//---------------------------------------------------
// OutputWriter Implementation
//---------------------------------------------------

void writeAdjustedReturnsToFile(const std::vector<AdjustedReturn>& data, const std::string& filename) {
    std::filesystem::create_directories("output");
    std::ofstream outFile("output/" + filename);

    if (!outFile.is_open()) {
        std::cerr << "Fehler beim Schreiben der Datei: output/" << filename << std::endl;
        return;
    }

    outFile << "Year,Nominal %,Inflation %,Real %,Accumulated %\n";

    for (const auto& r : data) {
        outFile << r.year << ","
                << std::fixed << std::setprecision(2)
                << r.nominalRate * 100 << ","
                << r.inflationRate * 100 << ","
                << r.realRate * 100 << ","
                << r.accumulated * 100 << "\n";
    }

    outFile.close();
}

//---------------------------------------------------
// Ergebnis Generierung
//---------------------------------------------------

std::string generateOutputFilename() {
    auto now = std::chrono::system_clock::now();
    auto in_time = std::chrono::system_clock::to_time_t(now);
    std::tm tm = *std::localtime(&in_time);

    // Format: YYYYMMDD_HHMM
    std::ostringstream oss;
    oss << "adjReturns_"
        << std::put_time(&tm, "%Y%m%d_%H%M_");

    // Append 6 random digits
    std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<> dist(0, 9);
    for (int i = 0; i < 6; ++i) {
        oss << dist(rng);
    }

    oss << ".csv";
    return oss.str();
}


//----------------------------------------------------------------------------
// Verwendung anzeigen
//----------------------------------------------------------------------------
void Verwendung() {
    std::cout << "Verwendung: calculateInflationAdjustedReturns <inputfile.csv>\n";
    std::cout << "Beispiel:   calculateInflationAdjustedReturns data.csv\n";
}

//---------------------------------------------------
// Hauptprogramm
//---------------------------------------------------
#ifndef UNIT_TESTING
int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Ungültige Anzahl an Argumenten!\n\n";
        Verwendung();
        return 1;
    }

    std::string inputFile = argv[1];
    std::vector<ReturnData> inputData;

    if (!loadReturnDataFromCSV(inputFile, inputData)) {
        std::cerr << "Konnte Eingabedaten nicht laden.\n";
        return 1;
    }

    auto adjusted = computeInflationAdjustedReturns(inputData);
    std::string filename = generateOutputFilename();
    writeAdjustedReturnsToFile(adjusted, filename);

    std::cout << "Ergebnisse gespeichert in: output/" << filename << "\n";
    return 0;
}
#endif
