#include "gtest/gtest.h"
#include "../clientprofile.h"
#include "../scoreweights.h"
#include "../scoreengine.h"
#include "../riskrating.h"

// Helper to create client profiles
ClientProfile makeClient(const std::string& id, int age, double income, const std::string& emp, const std::string& industry, double debt, const std::string& country = "AT") {
    ClientProfile client;
    client.clientId = id;
    client.name = "Test Client";
    client.country = country;
    client.clientType = "retail";
    client.age = age;
    client.income = income;
    client.employment = emp;
    client.industry = industry;
    client.debt = debt;
    return client;
}

// --- Tests ---

TEST(ScoreEngineTest, CalculatesHighScoreCorrectly) {
    ClientProfile client = makeClient("C001", 45, 100000, "permanent", "finance", 2000);
    ScoreWeights weights = ScoreWeights::defaultWeights();
    double score = ScoreEngine::calculateScore(client, weights);

    EXPECT_GE(score, 0.85);
    EXPECT_LE(score, 1.0);
}

TEST(ScoreEngineTest, CalculatesMediumScoreCorrectly) {
    ClientProfile client = makeClient("C002", 35, 40000, "permanent", "retail", 10000);
    ScoreWeights weights = ScoreWeights::defaultWeights();
    double score = ScoreEngine::calculateScore(client, weights);

    EXPECT_GT(score, 0.5);
    EXPECT_LT(score, 0.85);
}

TEST(ScoreEngineTest, CalculatesLowScoreCorrectly) {
    ClientProfile client = makeClient("C003", 20, 5000, "unemployed", "unknown", 30000);
    ScoreWeights weights = ScoreWeights::defaultWeights();
    double score = ScoreEngine::calculateScore(client, weights);

    EXPECT_GE(score, 0.0);
    EXPECT_LT(score, 0.4);
}

TEST(ScoreEngineTest, AppliesCountryAdjustment) {
    ClientProfile client = makeClient("C004", 45, 100000, "permanent", "finance", 2000, "GR"); // Greece = 0.7
    ScoreWeights weights = ScoreWeights::defaultWeights();
    double score = ScoreEngine::calculateScore(client, weights);

    EXPECT_LT(score, 0.85); // Should be lowered by country factor
}

TEST(RiskRatingTest, MapsScoreToCorrectRating) {
    RiskRatingMapper mapper;
    EXPECT_EQ(mapper.getRating(0.85), "AAA");
    EXPECT_EQ(mapper.getRating(0.75), "AA");
    EXPECT_EQ(mapper.getRating(0.65), "A");
    EXPECT_EQ(mapper.getRating(0.55), "BBB");
    EXPECT_EQ(mapper.getRating(0.45), "BB");
    EXPECT_EQ(mapper.getRating(0.35), "B");
    EXPECT_EQ(mapper.getRating(0.25), "D"); // previously said "CCC"
}

TEST(RiskRatingTest, HandlesOutOfRangeScores) {
    RiskRatingMapper mapper;
    EXPECT_EQ(mapper.getRating(-0.1), "D");     // fallback to D
    EXPECT_EQ(mapper.getRating(1.5), "AAA");    // upper bound fallback
}
