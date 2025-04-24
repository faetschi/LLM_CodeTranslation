# Makefile for Loan Amortization Calculator (MSYS2)

CXX := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -O2
TARGET := loan_calculator
SRC := loanAmortizationCalculator.cpp
OBJ := $(SRC:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET) $(TEST_TARGET) *.o

# Test-related settings
TEST_DIR := test
TEST_SRC := $(TEST_DIR)/test_amortization.cpp
TEST_TARGET := test_runner

# Detect GoogleTest includes/libs if installed globally (adjust if local)
GTEST_FLAGS := -lgtest -lgtest_main -pthread

test: $(TEST_TARGET)
	./$(TEST_TARGET)

$(TEST_TARGET): $(SRC) $(TEST_SRC)
	$(CXX) $(CXXFLAGS) -DUNIT_TEST -o $@ $^ $(GTEST_FLAGS)

