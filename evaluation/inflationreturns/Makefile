# ---- Configuration ----
CXX := g++
CXXFLAGS := -std=c++17 -Wall

INCLUDE := -I"C:/Program Files/MSYS2/ucrt64/include"
LIBS    := -L"C:/Program Files/MSYS2/ucrt64/lib" -lgtest -lgtest_main -pthread

SRC := calculateInflationAdjustedReturns.cpp
TEST := test/test_calculateInflationAdjustedReturns.cpp
OUT := calculateInflationAdjustedReturns.exe
TEST_OUT := testRunner.exe

# ---- Targets ----

all: $(OUT)

run: $(OUT)
	./$(OUT) data.csv

$(OUT): $(SRC)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(OUT)

test: $(SRC) $(TEST)
	$(CXX) $(CXXFLAGS) $(SRC) $(TEST) -o $(TEST_OUT) $(INCLUDE) $(LIBS) -DUNIT_TESTING
	./$(TEST_OUT)

clean:
	rm -f *.exe output/*.csv

.PHONY: all test clean run
