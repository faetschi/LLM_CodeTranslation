# Loan Amortization Calculator

The program calculates a **fixed-rate loan amortization schedule**, which breaks down each monthly payment over the full loan term.

## CSV Output Columns

| Column       | Meaning                                                                 |
|--------------|-------------------------------------------------------------------------|
| `Month`      | Payment number (1 to N, e.g., 360 for a 30-year mortgage)              |
| `Principal`  | Portion of the monthly payment that reduces the loan balance           |
| `Interest`   | Portion of the monthly payment that goes toward interest               |
| `Balance`    | Remaining loan balance **after** this payment                          |

    1. Reads loan amount, interest rate, and term from input.csv
    2. Calculates monthly payments and interest breakdown
    3. Saves result to semicolon-separated CSV
    4. Includes unit tests with make test


The amortization schedule is calculated using the **standard annuity formula** for fixed-rate loans:

```math
M = P \cdot \frac{r(1 + r)^n}{(1 + r)^n - 1}
```

## Compile using MSYS

    open MSYS UCTR64 in admin

    cd "/c/Users/Admin/Desktop/FH/Bachelor Thesis/Bachelor Arbeit/Prototype/evaluation/amortization"

    make            # builds CLI
    make test       # builds testRunner
    make run        # runs CLI with default args
    ./testRunner    # runs tests
    ./loan_calculator

    make clean      # removes all .exe files

