# ---- Configuration ----
CXX := g++
CXXFLAGS := -std=c++17 -Wall

# Paths to MSYS2 UCRT64 (adjust if installed elsewhere)
INCLUDE := -I"C:/Program Files/MSYS2/ucrt64/include"
LIBS    := -L"C:/Program Files/MSYS2/ucrt64/lib" -lgtest -lgtest_main -pthread

# Files
SRC := isValidTradingPair.cpp
HEADERS := datum.h waehrung.h
TEST := test/test_isValidTradingPair.cpp
OUT := isValidTradingPair.exe
TEST_OUT := testRunner.exe

# ---- Targets ----

all: $(OUT)

run: $(OUT)
	./$(OUT) -d 20250403 -p EURUSD -v

$(OUT): $(SRC) $(HEADERS)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(OUT)

test: $(SRC) $(TEST) $(HEADERS)
	$(CXX) $(CXXFLAGS) $(SRC) $(TEST) -o $(TEST_OUT) $(INCLUDE) $(LIBS) -DUNIT_TESTING

clean:
	rm -f *.exe test/*.exe

.PHONY: all test clean run
