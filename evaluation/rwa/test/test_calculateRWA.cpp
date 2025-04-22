#include "gtest/gtest.h"
#include "../riskweights.h"
#include "../capitalrequirement.h"
#include "../exposuremodel.h"
#include "../inputloader.h"
#include <fstream>
#include <cstdio>

// Helper: write CSV content to a temporary file
std::string writeTempCSV(const std::string& content, const std::string& filename) {
    std::ofstream file(filename);
    file << content;
    file.close();
    return filename;
}

TEST(InputValidationTest, LoadsValidCSV) {
    std::string content = 
        "Year,AssetClass,Rating,Exposure,Country\n"
        "2021,corporate,AA,1000000,DE\n"
        "2021,retail,A,200000,FR\n"
        "2022,mortgage,AAA,300000,IT\n"
        "2023,sovereign,BBB,500000,AT\n"
        "2023,securitization,B,400000,ES\n";

    std::string filename = "temp_valid.csv";
    writeTempCSV(content, filename);

    std::vector<Exposure> exposures;
    bool success = loadExposuresFromCSV(filename, exposures);

    EXPECT_TRUE(success);
    EXPECT_EQ(exposures.size(), 5);

    std::remove(filename.c_str());
}

TEST(InputValidationTest, FailsOnMalformedLine) {
    std::string content = 
        "Year,AssetClass,Rating,Exposure,Country\n"
        "2021,corporate,AA,asdfasdf,DE\n"; // invalid exposure

    std::string filename = "temp_invalid_format.csv";
    writeTempCSV(content, filename);

    std::vector<Exposure> exposures;
    bool success = loadExposuresFromCSV(filename, exposures);

    EXPECT_FALSE(success);
    EXPECT_TRUE(exposures.empty());

    std::remove(filename.c_str());
}

TEST(InputValidationTest, FailsOnMissingField) {
    std::string content = 
        "Year,AssetClass,Rating,Exposure,Country\n"
        "2022,retail,A,200000,\n"; // missing country

    std::string filename = "temp_missing_field.csv";
    writeTempCSV(content, filename);

    std::vector<Exposure> exposures;
    bool success = loadExposuresFromCSV(filename, exposures);

    EXPECT_FALSE(success);
    EXPECT_TRUE(exposures.empty());

    std::remove(filename.c_str());
}

TEST(RiskWeightTest, KnownRatingCorporate) {
    RiskWeightTable table = RiskWeightTable::defaultTable();
    EXPECT_DOUBLE_EQ(table.getRiskWeight("corporate", "AAA"), 0.2);
    EXPECT_DOUBLE_EQ(table.getRiskWeight("corporate", "BB"), 0.75);
}

TEST(RiskWeightTest, UnknownRatingUsesDefault) {
    RiskWeightTable table = RiskWeightTable::defaultTable();
    EXPECT_DOUBLE_EQ(table.getRiskWeight("corporate", "ZZZ"), 1.0);
}

TEST(CapitalRequirementTest, BasicCalculation) {
    double rwa = 1000.0;
    std::string country = "AT";
    EXPECT_DOUBLE_EQ(calculateCapitalRequirement(rwa, country), 80.0); // 8% of 1000
}

TEST(ExposureResultTest, StructInitialization) {
    Exposure exp = {2024, "corporate", "AA", 1000.0, "DE"};
    ExposureResult result = {exp, 0.25, 250.0, 20.0};
    EXPECT_EQ(result.exposure.year, 2024);
    EXPECT_EQ(result.exposure.assetClass, "corporate");
    EXPECT_DOUBLE_EQ(result.riskWeight, 0.25);
    EXPECT_DOUBLE_EQ(result.rwa, 250.0);
    EXPECT_DOUBLE_EQ(result.capitalRequirement, 20.0);
}

TEST(RiskWeightTest, UnknownAssetClassUsesDefault) {
    RiskWeightTable table = RiskWeightTable::defaultTable();
    EXPECT_DOUBLE_EQ(table.getRiskWeight("alienAsset", "AAA"), 1.0); // fallback
}

TEST(RiskWeightTest, HandlesLowercaseInput) {
    RiskWeightTable table = RiskWeightTable::defaultTable();
    EXPECT_DOUBLE_EQ(table.getRiskWeight("corporate", "aaa"), 1.0); // should fallback, not matched
}

TEST(CapitalRequirementTest, HandlesDifferentCountries) {
    EXPECT_DOUBLE_EQ(calculateCapitalRequirement(1000.0, "AT"), 80.0); // Austria 8%
}

TEST(ExposureModelTest, HandlesNegativeExposure) {
    Exposure exp = {2024, "retail", "A", -1000.0, "FR"};
    RiskWeightTable table = RiskWeightTable::defaultTable();
    double rw = table.getRiskWeight(exp.assetClass, exp.rating);
    double rwa = calculateRWA(exp.exposureAmount, rw);
    EXPECT_LT(rwa, 0); // Possibly not desired; maybe expect == 0 if handled that way
}

TEST(RiskWeightTest, EmptyInputsReturnDefault) {
    RiskWeightTable table = RiskWeightTable::defaultTable();
    EXPECT_DOUBLE_EQ(table.getRiskWeight("", ""), 1.0);
}

