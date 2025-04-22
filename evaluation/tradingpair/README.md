# isValidTradingPair

A C++ command-line tool that checks whether a given currency pair is tradable on a specific date.

- Validates currency pair (e.g. EURUSD, USDJPY)
- Checks if the date is a valid trading day (weekday, business day, not a holiday)
- Optional verbose output

## Param:
-d <YYYYMMDD> -p <CurrencyPair> [-v]

## Compile using MSYS

    open MSYS UCTR64 in admin

    cd "/c/Users/Admin/Desktop/FH/Bachelor Thesis/Bachelor Arbeit/Prototype/evaluation"

    make            # builds CLI
    make test       # builds testRunner
    make run        # runs CLI with default args
    ./testRunner    # runs tests
    ./isValidTradingPair -d 20250403 -p EURUSD -v

    make clean      # removes all .exe files

