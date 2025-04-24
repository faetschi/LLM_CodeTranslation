# Makefile for UserManager.cpp, BankingSystem.cpp, and SimpleTest.cpp (MSYS2 UCRT64)

CXX      := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -pedantic -O2

TARGETS  := user_manager.exe banking_system.exe simple_test.exe

all: $(TARGETS)

user_manager.exe: UserManager.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

banking_system.exe: BankingSystem.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

simple_test.exe: SimpleTest.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

clean:
	rm -f $(TARGETS)

.PHONY: all clean
