//----------------------------------------------------------------------------
// Includes
//----------------------------------------------------------------------------
#include <iostream>
#include <string>
#include <set>
#include <cstdlib>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <vector>
#include <algorithm>

using namespace std;

#include "datum.h"
#include "waehrung.h"

// Funktionsprototypen
void Verwendung();
int isValidTradingPair(const Datum& datum, const std::string& pair, bool verbose);

// Globale Variablen
int nAusgabe = 0;

// ============================================================================
// Datum Implementation
// ============================================================================
Datum::Datum() : tag(1), monat(1), jahr(2000), format(1), valid(false) {
    SetAktDatum();
}

void Datum::SetDatum(const std::string& strDatum) {
    if (strDatum.length() != 8 || !std::all_of(strDatum.begin(), strDatum.end(), ::isdigit)) {
        valid = false;
        return;
    }

    try {
        jahr = std::stoi(strDatum.substr(0, 4));
        monat = std::stoi(strDatum.substr(4, 2));
        tag   = std::stoi(strDatum.substr(6, 2));
    } catch (...) {
        valid = false;
        return;
    }

    valid = true;
}

void Datum::SetAktDatum() {
    std::time_t now = std::time(nullptr);
    std::tm* ltm = std::localtime(&now);
    tag = ltm->tm_mday;
    monat = ltm->tm_mon + 1;
    jahr = ltm->tm_year + 1900;
    valid = true;
}

void Datum::SetFormat(int fmt) {
    format = fmt;
}

int Datum::CheckDatum() const {
    if (!valid) return 1;

    if (jahr < 1900 || monat < 1 || monat > 12 || tag < 1 || tag > 31)
        return 1;

    std::tm tm = {};
    tm.tm_year = jahr - 1900;
    tm.tm_mon = monat - 1;
    tm.tm_mday = tag;

    std::time_t t = std::mktime(&tm);
    if (t == -1) return 1;

    // Normalize values
    return (tm.tm_mday == tag && tm.tm_mon + 1 == monat && tm.tm_year + 1900 == jahr) ? 0 : 1;
}

bool Datum::IsWeekend() const {
    std::tm tm = {};
    tm.tm_year = jahr - 1900;
    tm.tm_mon = monat - 1;
    tm.tm_mday = tag;
    std::mktime(&tm);
    return (tm.tm_wday == 0 || tm.tm_wday == 6);
}

bool Datum::IsBoersentag() const {
    if (!valid) return false;
    if (IsWeekend()) return false;

    std::string ddmm = (tag < 10 ? "0" : "") + std::to_string(tag) +
                       (monat < 10 ? "0" : "") + std::to_string(monat);
    static const std::vector<std::string> feiertage = { "0101", "2512" };
    return std::find(feiertage.begin(), feiertage.end(), ddmm) == feiertage.end();
}

std::string Datum::RawString() const {
    std::ostringstream oss;
    oss << std::setw(4) << std::setfill('0') << jahr
        << std::setw(2) << std::setfill('0') << monat
        << std::setw(2) << std::setfill('0') << tag;
    return oss.str();
}

std::ostream& operator<<(std::ostream& os, const Datum& d) {
    os << std::setw(2) << std::setfill('0') << d.tag << "."
       << std::setw(2) << std::setfill('0') << d.monat << "."
       << d.jahr;
    return os;
}
    
// ============================================================================
// Waehrung Implementation
// ============================================================================
Waehrung::Waehrung() {
    validPairs = { "EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCHF" };
}

bool Waehrung::IsValidPair(const std::string& pair) const {
    return validPairs.find(pair) != validPairs.end();
}

    
//----------------------------------------------------------------------------
// Hauptprogramm
//----------------------------------------------------------------------------
#ifndef UNIT_TESTING
int main(int argc, char* argv[]) {
    Datum datum;
    std::string pair;
    bool datumSet = false;
    bool pairSet = false;
    int verbose = 0;

    for (int i = 1; i < argc; ++i) {
        if (argv[i][0] == '-') {
            switch (argv[i][1]) {
            case 'd':
                if (i + 1 < argc) {
                    datum.SetDatum(argv[++i]);
                    datumSet = true;
                    if (datum.CheckDatum() != 0) {
                        std::cerr << "### Ungueltiges Datum (-d): " << argv[i] << " ###\n";
                        return 1;
                    }
                } else {
                    std::cerr << "### Kein Datum angegeben. Verwende -d <YYYYMMDD> ###\n";
                    return 1;
                }
                break;
            case 'p':
                if (i + 1 < argc) {
                    pair = argv[++i];
                    pairSet = true;
                } else {
                    std::cerr << "### Kein Waehrungspaar angegeben. Verwende -p <PAAR> ###\n";
                    return 1;
                }
                break;
            case 'v':
                verbose = 1;
                break;
            case 'h':
                Verwendung();
                return 0;
            default:
                std::cerr << "### Unbekannter Parameter: " << argv[i] << " ###\n";
                Verwendung();
                return 1;
            }
        }
    }

    if (!datumSet || !pairSet) {
        std::cerr << "### Fehlende Parameter. Datum und Waehrungspaar sind erforderlich. ###\n";
        Verwendung();
        return 1;
    }

    return isValidTradingPair(datum, pair, verbose);
}
#endif


//----------------------------------------------------------------------------
// Verwendung anzeigen
//----------------------------------------------------------------------------
void Verwendung() {
    std::cout << "Verwendung: isValidTradingPair -d <Datum> -p <CurrencyPair> [-v]\n";
    std::cout << "Beispiel:   isValidTradingPair -d 20250403 -p EURUSD -v\n";
}

//----------------------------------------------------------------------------
// Prüft, ob ein Währungspaar an einem gegebenen Datum gültig ist
//----------------------------------------------------------------------------
int isValidTradingPair(const Datum& datum, const std::string& pair, bool verbose) {
    Waehrung waehrung;

    if (!waehrung.IsValidPair(pair)) {
        if (verbose)
            std::cout << datum << " - Ungueltiges Waehrungspaar: " << pair << "\n";
        return 0;
    }

    if (!datum.IsBoersentag()) {
        if (verbose)
            std::cout << datum << " - Kein Handelstag\n";
        return 0;
    }

    if (verbose)
        std::cout << datum << " - Gueltiges Trading-Paar: " << pair << "\n";

    return 1;
}