# Risk-Weighted Assets (RWA) Calculator

The program calculates Risk-Weighted Assets and capital requirements based on Basel-like rules. It processes a CSV file of credit exposures, applies asset class and rating-specific risk weights, and generates a detailed report.

- Reads exposures from rwa_input.csv
- Validates asset class, rating, and input format
- Applies default risk weight table

Calculates:

- Risk-Weighted Assets (RWA)
- Capital requirement (8% of RWA)
- Outputs a timestamped CSV report to /output/

## Compile using MSYS

    open MSYS UCTR64 in admin

    cd "/c/Users/Admin/Desktop/FH/Bachelor Thesis/Bachelor Arbeit/Prototype/evaluation/rwa"

    make            # builds CLI
    make test       # builds testRunner
    make run        # runs CLI with default args
    ./testRunner    # runs tests
    ./calculateRWA 

    make clean      # removes all .exe files

