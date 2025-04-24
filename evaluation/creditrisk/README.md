# Credit Risk Scoring Tool

A program that reads client profiles from a CSV file, calculates a credit score based on configurable weightings, maps it to a credit rating, and exports the results to a CSV report.

- Validates and scores client profiles
- Calculates risk scores based on age, income, employment, industry, and debt
- Maps scores to risk ratings (AAA - D)
- Outputs results to `output/credit_ratings_*.csv`

## Compile using MSYS

    open MSYS UCTR64 in admin

    cd "/c/Users/Admin/Desktop/FH/Bachelor Thesis/Bachelor Arbeit/Prototype/evaluation/creditrisk"

    make            # builds CLI
    make test       # builds testRunner
    make run        # runs CLI with default args
    ./creditRiskScoring clients.csv      # manual run
    
    make clean      # removes all .exe files

