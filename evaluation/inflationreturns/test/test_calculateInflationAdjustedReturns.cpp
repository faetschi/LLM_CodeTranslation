#include "gtest/gtest.h"
#include "../returndata.h"
#include "../calculations.h"
#include "../outputwriter.h"
#include <fstream>
#include <filesystem>

namespace fs = std::filesystem;

// Test helper: create a CSV file with given content
void writeTestCSV(const std::string& path, const std::string& content) {
    std::ofstream file(path);
    file << content;
    file.close();
}

// Test helper: build ReturnData vector
std::vector<ReturnData> makeData(std::vector<int> years, std::vector<double> nominal, std::vector<double> inflation) {
    std::vector<ReturnData> data;
    for (size_t i = 0; i < years.size(); ++i) {
        data.push_back({ years[i], nominal[i], inflation[i] });
    }
    return data;
}

// Clean test files after all tests
class ReturnDataTestSuite : public ::testing::Test {
protected:
    std::string testDir = "test_temp";

    void SetUp() override {
        fs::create_directory(testDir);
    }

    void TearDown() override {
        fs::remove_all(testDir);
    }

    std::string testPath(const std::string& name) {
        return testDir + "/" + name;
    }
};

TEST_F(ReturnDataTestSuite, ValidCSVLoadsSuccessfully) {
    std::string path = testPath("valid.csv");
    writeTestCSV(path, "Year,Nominal,Inflation\n1994,0.04,0.03\n1995,0.05,0.02");

    std::vector<ReturnData> data;
    bool success = loadReturnDataFromCSV(path, data);

    ASSERT_TRUE(success);
    ASSERT_EQ(data.size(), 2);
    EXPECT_EQ(data[0].year, 1994);
    EXPECT_DOUBLE_EQ(data[0].nominalRate, 0.04);
    EXPECT_DOUBLE_EQ(data[0].inflationRate, 0.03);
}

TEST_F(ReturnDataTestSuite, MalformedRowThrowsAndStops) {
    std::string path = testPath("malformed.csv");
    writeTestCSV(path, "Year,Nominal,Inflation\nASDF,0.04,0.03");

    std::vector<ReturnData> data;
    EXPECT_DEATH({
        loadReturnDataFromCSV(path, data);
    }, "Ungültige Zeile");
}

TEST_F(ReturnDataTestSuite, SemanticallyInvalidRowCausesExit) {
    std::string path = testPath("invalid.csv");
    writeTestCSV(path, "Year,Nominal,Inflation\n1994,999999,0.03");

    std::vector<ReturnData> data;
    EXPECT_DEATH({
        loadReturnDataFromCSV(path, data);
    }, "Ungültige Werte");
}

TEST_F(ReturnDataTestSuite, EmptyFileReturnsFalse) {
    std::string path = testPath("empty.csv");
    writeTestCSV(path, "");

    std::vector<ReturnData> data;
    bool success = loadReturnDataFromCSV(path, data);

    EXPECT_FALSE(success);
    EXPECT_TRUE(data.empty());
}

// ------------------ computeInflationAdjustedReturns Tests ------------------

TEST(CalculationTest, HandlesSimpleScenario) {
    auto data = makeData({2020, 2021}, {0.05, 0.03}, {0.02, 0.01});
    auto results = computeInflationAdjustedReturns(data);

    ASSERT_EQ(results.size(), 2);
    EXPECT_NEAR(results[0].realRate, (1.05 / 1.02 - 1), 0.0001);
    EXPECT_NEAR(results[1].realRate, (1.03 / 1.01 - 1), 0.0001);
}

TEST(CalculationTest, HandlesNegativeReturns) {
    auto data = makeData({2022}, {-0.02}, {0.01});
    auto results = computeInflationAdjustedReturns(data);

    ASSERT_EQ(results.size(), 1);
    EXPECT_NEAR(results[0].realRate, ((1 - 0.02) / (1 + 0.01) - 1), 0.0001);
}

TEST(CalculationTest, HandlesZeroInflation) {
    auto data = makeData({2023}, {0.04}, {0.0});
    auto results = computeInflationAdjustedReturns(data);

    ASSERT_EQ(results.size(), 1);
    EXPECT_NEAR(results[0].realRate, 0.04, 0.0001);
}

TEST(CalculationTest, HandlesHighInflation) {
    auto data = makeData({2024}, {0.08}, {0.15});
    auto results = computeInflationAdjustedReturns(data);

    ASSERT_EQ(results.size(), 1);
    double expected = (1.08 / 1.15 - 1);
    EXPECT_NEAR(results[0].realRate, expected, 0.0001);
}

TEST(CalculationTest, HandlesZeroNominalAndZeroInflation) {
    auto data = makeData({2025}, {0.0}, {0.0});
    auto results = computeInflationAdjustedReturns(data);

    ASSERT_EQ(results.size(), 1);
    EXPECT_NEAR(results[0].realRate, 0.0, 0.0001);
    EXPECT_NEAR(results[0].accumulated, 0.0, 0.0001);
}

TEST(CalculationTest, HandlesZeroNominalPositiveInflation) {
    auto data = makeData({2026}, {0.0}, {0.05});
    auto results = computeInflationAdjustedReturns(data);

    ASSERT_EQ(results.size(), 1);
    double expected = (1.0 / 1.05 - 1.0);
    EXPECT_NEAR(results[0].realRate, expected, 0.0001);
}

TEST(CalculationTest, HandlesHyperInflation) {
    auto data = makeData({2027}, {0.10}, {2.0}); // 200% inflation
    auto results = computeInflationAdjustedReturns(data);

    ASSERT_EQ(results.size(), 1);
    double expected = (1.10 / 3.0 - 1.0);
    EXPECT_NEAR(results[0].realRate, expected, 0.0001);
}

TEST(CalculationTest, HandlesMultipleYearsAccumulation) {
    auto data = makeData({2020, 2021, 2022}, {0.05, 0.03, 0.04}, {0.02, 0.01, 0.025});
    auto results = computeInflationAdjustedReturns(data);

    ASSERT_EQ(results.size(), 3);

    double r1 = 1 + (1.05 / 1.02 - 1);
    double r2 = r1 * (1 + (1.03 / 1.01 - 1));
    double r3 = r2 * (1 + (1.04 / 1.025 - 1));

    EXPECT_NEAR(results[2].accumulated + 1, r3, 0.0001);
}

TEST(CalculationTest, HandlesInvalidYears) {
    auto data = makeData({-100, 0, 9999}, {0.02, 0.03, 0.04}, {0.01, 0.01, 0.01});
    auto results = computeInflationAdjustedReturns(data);

    ASSERT_EQ(results.size(), 3); // System should still process the year as-is
    EXPECT_NEAR(results[0].realRate, (1.02 / 1.01 - 1), 0.0001);
    EXPECT_EQ(results[0].year, -100);
    EXPECT_EQ(results[1].year, 0);
    EXPECT_EQ(results[2].year, 9999);
}
