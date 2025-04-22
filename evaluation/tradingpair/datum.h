#ifndef DATUM_H
#define DATUM_H

#include <string>
#include <iostream>

class Datum {
public:
    Datum();
    void SetDatum(const std::string& strDatum);
    void SetAktDatum();
    void SetFormat(int fmt);
    int CheckDatum() const;
    bool IsWeekend() const;
    bool IsBoersentag() const;
    std::string RawString() const;
    friend std::ostream& operator<<(std::ostream& os, const Datum& d);

private:
    int tag, monat, jahr, format;
    bool valid;
};

#endif // DATUM_H
