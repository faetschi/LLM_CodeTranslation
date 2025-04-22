# ---- Configuration ----
CXX := g++
CXXFLAGS := -std=c++17 -Wall

INCLUDE := -I"C:/Program Files/MSYS2/ucrt64/include"
LIBS    := -L"C:/Program Files/MSYS2/ucrt64/lib" -lgtest -lgtest_main -pthread

SRC := creditRiskScoring.cpp
TEST := test/test_creditRiskScoring.cpp
OUT := creditRiskScoring.exe
TEST_OUT := testRunner.exe

# ---- Targets ----

all: $(OUT)

run: $(OUT)
	./$(OUT) clients.csv

$(OUT): $(SRC)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(OUT)

test: $(SRC) $(TEST)
	$(CXX) $(CXXFLAGS) $(SRC) $(TEST) -o $(TEST_OUT) $(INCLUDE) $(LIBS) -DUNIT_TESTING
	./$(TEST_OUT)

clean:
	rm -f *.exe output/*.csv

.PHONY: all run test clean
