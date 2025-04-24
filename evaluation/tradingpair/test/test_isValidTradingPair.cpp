#include "gtest/gtest.h"
#include "../datum.h"
#include "../waehrung.h"

class TestTradingPair {
public:
    static bool isBoersetag(const std::string& dateStr) {
        Datum date;
        date.SetDatum(dateStr);
        return date.IsBoersentag();
    }

    static bool isValidPair(const std::string& pair) {
        Waehrung w;
        return w.IsValidPair(pair);
    }

    static int checkDatum(const std::string& dateStr) {
        Datum d;
        d.SetDatum(dateStr);
        return d.CheckDatum();
    }
};

TEST(BoersetagTest, WeekdayIsValid) {
    EXPECT_TRUE(TestTradingPair::isBoersetag("20250403")); // Thursday
}

TEST(BoersetagTest, WeekendIsInvalid) {
    EXPECT_FALSE(TestTradingPair::isBoersetag("20250406")); // Sunday
}

TEST(CurrencyPairTest, ValidPair) {
    EXPECT_TRUE(TestTradingPair::isValidPair("EURUSD"));
}

TEST(CurrencyPairTest, InvalidPair) {
    EXPECT_FALSE(TestTradingPair::isValidPair("XYZ123"));
}

TEST(DatumTest, ValidDateFormat) {
    EXPECT_EQ(TestTradingPair::checkDatum("20250403"), 0);  // ✅ valid
}

TEST(DatumTest, InvalidCalendarDay) {
    EXPECT_NE(TestTradingPair::checkDatum("20250230"), 0);  // Feb 30 → ❌
}

TEST(DatumTest, TooShortDate) {
    EXPECT_NE(TestTradingPair::checkDatum("202504"), 0);  // too short → ❌
}

TEST(DatumTest, NonDigitDate) {
    EXPECT_NE(TestTradingPair::checkDatum("BADDATE"), 0);  // not numeric → ❌
}
