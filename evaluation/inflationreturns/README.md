# Inflation-Adjusted Return Calculator

A program that reads annual nominal return and inflation data from a CSV file, calculates real returns, and writes the result to a timestamped output file.

- Computes real return:  
  ```math
  \text{real} = \frac{1 + \text{nominal}}{1 + \text{inflation}} - 1
  ```
- Tracks accumulated real return over time
- Generates output in `output/adjReturns_*.csv`

## Compile using MSYS

    open MSYS UCTR64 in admin

    cd "/c/Users/Admin/Desktop/FH/Bachelor Thesis/Bachelor Arbeit/Prototype/evaluation/inflationreturns"

    make            # builds CLI
    make test       # builds testRunner
    make run        # runs CLI with default args
    ./calculateInflationAdjustedReturns data.csv # manual run
    
    make clean      # removes all .exe files

