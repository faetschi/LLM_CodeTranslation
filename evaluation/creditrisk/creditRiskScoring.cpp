#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <iomanip>
#include <map>
#include <set>
#include <chrono>
#include <random>
#include <filesystem>
#include "clientprofile.h"
#include "riskfactor.h"
#include "scoreweights.h"
#include "scoreengine.h"
#include "riskrating.h"
#include "inputparser.h"
#include "utilities.h"

using namespace std;

//----------------------------------------------------------------------------
// Output file
//----------------------------------------------------------------------------
string generateOutputFilename() {
    auto now = chrono::system_clock::now();
    time_t time = chrono::system_clock::to_time_t(now);
    tm tm = *localtime(&time);

    ostringstream oss;
    oss << "credit_ratings_"
        << put_time(&tm, "%Y%m%d_%H%M_");

    mt19937 rng(random_device{}());
    uniform_int_distribution<> dist(0, 9);
    for (int i = 0; i < 6; ++i)
        oss << dist(rng);

    oss << ".csv";
    return oss.str();
}

//----------------------------------------------------------------------------
// Validierung
//----------------------------------------------------------------------------
bool validateClientProfile(const ClientProfile& profile, int row) {
    bool valid = true;

    if (profile.age <= 0 || profile.age > 120) {
        cerr << "Row " << row << ": Invalid age: " << profile.age << "\n";
        valid = false;
    }

    if (profile.income < 0) {
        cerr << "Row " << row << ": Negative income\n";
        valid = false;
    }

    if (profile.employment.empty() || profile.industry.empty()) {
        cerr << "Row " << row << ": Missing employment or industry info\n";
        valid = false;
    }

    if (profile.debt < 0) {
        cerr << "Row " << row << ": Negative debt\n";
        valid = false;
    }

    return valid;
}

ScoreWeights ScoreWeights::defaultWeights() {
    ScoreWeights sw;
    sw.setWeight("age", 0.1);
    sw.setWeight("income", 0.3);
    sw.setWeight("employment", 0.2);
    sw.setWeight("industry", 0.2);
    sw.setWeight("debt", 0.2);
    return sw;
}

double ScoreEngine::calculateScore(const ClientProfile& client, const ScoreWeights& weights) {
    double score = 0.0;

    // --- Age: scaled between 18–75, ideal around 45
    if (client.age >= 18 && client.age <= 75) {
        double ageScore = 1.0 - std::abs(45.0 - client.age) / 45.0; // peak at age 45
        score += weights.getWeight("age") * ageScore;
    }

    // --- Income: full weight above threshold
    if (client.income >= 30000)
        score += weights.getWeight("income");

    // --- Employment type: stable jobs
    static const std::set<std::string> stableEmployment = { "permanent", "self-employed" };
    if (stableEmployment.count(client.employment))
        score += weights.getWeight("employment");

    // --- Industry type: safe industries
    static const std::set<std::string> safeIndustries = { "finance", "it", "pharma" };
    if (safeIndustries.count(client.industry))
        score += weights.getWeight("industry");

    // --- Debt-to-income ratio
    double dti = client.debt / (client.income + 1.0); // avoid div/0
    if (dti <= 0.25)
        score += weights.getWeight("debt");
    else if (dti <= 0.5)
        score += weights.getWeight("debt") * 0.5;

    // --- Penalties
    if (client.debt > 50000)
        score -= 0.1;
    if (client.age < 21 || client.age > 75)
        score -= 0.05;

    // --- Country-specific adjustment
    static const std::map<std::string, double> countryRisk = {
        {"AT", 1.0}, {"DE", 0.95}, {"GR", 0.7}, {"US", 1.0}, {"BR", 0.6}
    };
    auto it = countryRisk.find(client.country);
    if (it != countryRisk.end())
        score *= it->second;

    return std::clamp(score, 0.0, 1.0); // Ensure 0 <= score <= 1
}

void ScoreWeights::setWeight(const std::string& factorName, double weight) {
    weights[factorName] = weight;
}

double ScoreWeights::getWeight(const std::string& factorName) const {
    auto it = weights.find(factorName);
    return (it != weights.end()) ? it->second : 0.0;
}


//----------------------------------------------------------------------------
// Ausgabedatei schreiben
//----------------------------------------------------------------------------
void writeResultsToCSV(const vector<pair<ClientProfile, string>>& results, const string& filename) {
    filesystem::create_directories("output");
    ofstream outFile("output/" + filename);

    if (!outFile.is_open()) {
        cerr << "Could not write to file: output/" << filename << "\n";
        return;
    }

    outFile << "ClientID,Score,Rating\n";
    for (const auto& [client, rating] : results) {
        outFile << client.clientId << ","
                << fixed << setprecision(2)
                << client.calculatedScore << ","
                << rating << "\n";
    }

    outFile.close();
}

//----------------------------------------------------------------------------
// Daten laden
//----------------------------------------------------------------------------

bool loadClientProfilesFromCSV(const std::string& filename, std::vector<ClientProfile>& out) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Could not open input file: " << filename << "\n";
        return false;
    }

    std::string line;
    std::getline(file, line); // Skip header

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string id, name, country, type, ageStr, incomeStr, employment, industry, debtStr;

        if (!std::getline(ss, id, ',') ||
            !std::getline(ss, name, ',') ||
            !std::getline(ss, country, ',') ||
            !std::getline(ss, type, ',') ||
            !std::getline(ss, ageStr, ',') ||
            !std::getline(ss, incomeStr, ',') ||
            !std::getline(ss, employment, ',') ||
            !std::getline(ss, industry, ',') ||
            !std::getline(ss, debtStr, ',')) {
            std::cerr << "Invalid row: " << line << "\n";
            return false;
        }

        try {
            ClientProfile client;
            client.clientId = id;
            client.name = name;
            client.country = country;
            client.clientType = type;
            client.age = std::stoi(ageStr);
            client.income = std::stod(incomeStr);
            client.employment = employment;
            client.industry = industry;
            client.debt = std::stod(debtStr);
            out.push_back(client);
        } catch (...) {
            std::cerr << "Parsing failed for row: " << line << "\n";
            return false;
        }
    }

    return !out.empty();
}


//----------------------------------------------------------------------------
// Hauptfunktion
//----------------------------------------------------------------------------
#ifndef UNIT_TESTING
int main(int argc, char* argv[]) {
    if (argc != 2) {
        cerr << "Usage: creditRiskScoring <inputfile.csv>\n";
        return 1;
    }

    string filename = argv[1];
    if (!filesystem::exists(filename)) {
        cerr << "File not found: " << filename << "\n";
        return 1;
    }

    vector<ClientProfile> clients;
    if (!loadClientProfilesFromCSV(filename, clients)) {
        cerr << "Failed to load client data\n";
        return 1;
    }

    ScoreWeights weights = ScoreWeights::defaultWeights();
    RiskRatingMapper ratingMapper;

    vector<pair<ClientProfile, string>> results;
    int row = 1;

    for (auto& client : clients) {
        if (!validateClientProfile(client, row++)) {
            cerr << "Skipping invalid client entry.\n";
            continue;
        }

        client.calculatedScore = ScoreEngine::calculateScore(client, weights);
        string rating = ratingMapper.getRating(client.calculatedScore);
        results.emplace_back(client, rating);
    }

    if (results.empty()) {
        cerr << "No valid entries to score.\n";
        return 1;
    }

    string outFile = generateOutputFilename();
    writeResultsToCSV(results, outFile);

    cout << "Credit scoring complete. Output written to output/" << outFile << "\n";
    return 0;
}
#endif
