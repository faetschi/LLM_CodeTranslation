// BankingSystem.cpp
// Minimal C++ example C++, to demonstrate operations such as account creation, deposits, withdrawals,
// funds transfer, interest application, and generating account statements.

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <stdexcept>
#include <ctime>
#include <iomanip>

using namespace std;

// Utility function: returns the current date and time as a formatted string.
string getCurrentTime() {
    time_t now = time(0);
    tm *ltm = localtime(&now);
    char buf[32];
    sprintf(buf, "%04d-%02d-%02d %02d:%02d:%02d",
            1900 + ltm->tm_year,
            1 + ltm->tm_mon,
            ltm->tm_mday,
            ltm->tm_hour,
            ltm->tm_min,
            ltm->tm_sec);
    return string(buf);
}

// Structure representing a transaction record.
struct Transaction {
    int transactionID;
    string type;         // e.g., Deposit, Withdrawal, Interest
    double amount;
    string timestamp;
    string description;
    
    Transaction(int id, const string &t, double amt, const string &desc)
    : transactionID(id), type(t), amount(amt), description(desc) {
        timestamp = getCurrentTime();
    }
};

// Class representing a bank account with various business operations.
class BankAccount {
private:
    int accountNumber;
    string accountHolder;
    double balance;
    double interestRate; // Annual interest rate (in percentage).
    vector<Transaction> transactionHistory;
    int nextTransactionID;

    // Helper method to log a transaction.
    void logTransaction(const string &type, double amount, const string &description) {
        transactionHistory.push_back(Transaction(nextTransactionID++, type, amount, description));
    }

public:
    // Constructor: initializes an account and logs an initial deposit if applicable.
    BankAccount(int accNum, const string &holder, double initialDeposit, double rate = 0.0)
    : accountNumber(accNum), accountHolder(holder), balance(0.0), interestRate(rate), nextTransactionID(1) {
        if (initialDeposit < 0) {
            throw invalid_argument("Initial deposit cannot be negative.");
        }
        if (initialDeposit > 0) {
            deposit(initialDeposit, "Initial deposit");
        }
    }

    int getAccountNumber() const {
        return accountNumber;
    }

    const string& getAccountHolder() const {
        return accountHolder;
    }

    double getBalance() const {
        return balance;
    }

    double getInterestRate() const {
        return interestRate;
    }

    // Deposit funds into the account.
    // The optional description parameter allows custom logging (e.g., for transfers).
    void deposit(double amount, const string &description = "Deposit") {
        if (amount <= 0) {
            throw invalid_argument("Deposit amount must be positive.");
        }
        balance += amount;
        logTransaction("Deposit", amount, description);
        cout << "Deposited " << amount << " to account " << accountNumber 
             << ". New balance: " << balance << endl;
    }

    // Withdraw funds from the account.
    void withdraw(double amount, const string &description = "Withdrawal") {
        if (amount <= 0) {
            throw invalid_argument("Withdrawal amount must be positive.");
        }
        if (balance < amount) {
            throw runtime_error("Insufficient funds for withdrawal.");
        }
        balance -= amount;
        logTransaction("Withdrawal", amount, description);
        cout << "Withdrew " << amount << " from account " << accountNumber 
             << ". New balance: " << balance << endl;
    }

    // Transfer funds from this account to another account.
    // It performs a withdrawal on the sender and a deposit on the receiver.
    void transfer(BankAccount &toAccount, double amount) {
        if (amount <= 0) {
            throw invalid_argument("Transfer amount must be positive.");
        }
        if (balance < amount) {
            throw runtime_error("Insufficient funds for transfer.");
        }
        // Withdraw from the sender account with a transfer description.
        withdraw(amount, "Transfer to account " + to_string(toAccount.getAccountNumber()));
        // Deposit into the receiver account with a transfer description.
        toAccount.deposit(amount, "Transfer from account " + to_string(accountNumber));
        cout << "Transferred " << amount << " from account " << accountNumber 
             << " to account " << toAccount.getAccountNumber() << endl;
    }

    // Apply monthly interest to the account balance.
    // For demonstration, monthly interest is calculated as (annual rate/12).
    void applyMonthlyInterest() {
        double interest = balance * (interestRate / 100.0) / 12.0;
        balance += interest;
        logTransaction("Interest", interest, "Monthly interest applied");
        cout << "Applied interest " << interest << " to account " << accountNumber 
             << ". New balance: " << balance << endl;
    }

    // Print a detailed account statement including all transactions.
    void printStatement() const {
        cout << "\nAccount Statement for " << accountHolder 
             << " (Account Number: " << accountNumber << ")" << endl;
        cout << "------------------------------------------------------------------" << endl;
        cout << left << setw(15) << "TransactionID" 
             << setw(15) << "Type" 
             << setw(15) << "Amount" 
             << setw(25) << "Timestamp" 
             << "Description" << endl;
        cout << "------------------------------------------------------------------" << endl;
        for (const auto &tx : transactionHistory) {
            cout << left << setw(15) << tx.transactionID 
                 << setw(15) << tx.type 
                 << setw(15) << tx.amount 
                 << setw(25) << tx.timestamp 
                 << tx.description << endl;
        }
        cout << "------------------------------------------------------------------" << endl;
        cout << "Current Balance: " << balance << endl;
    }
};

// Class representing the overall banking system.
// It manages multiple accounts and can perform system-wide operations.
class BankingSystem {
private:
    map<int, BankAccount> accounts;
    int nextAccountNumber;

public:
    BankingSystem() : nextAccountNumber(1000) {} // Assume account numbers start from 1000.

    // Create a new bank account and add it to the system.
    int createAccount(const string &holder, double initialDeposit, double interestRate) {
        int accNum = nextAccountNumber++;
        BankAccount newAccount(accNum, holder, initialDeposit, interestRate);
        accounts.insert({accNum, newAccount});
        cout << "Created account " << accNum << " for " << holder 
             << " with initial deposit " << initialDeposit << endl;
        return accNum;
    }

    // Retrieve an account by account number.
    BankAccount& getAccount(int accountNumber) {
        auto it = accounts.find(accountNumber);
        if (it == accounts.end()) {
            throw runtime_error("Account not found.");
        }
        return it->second;
    }

    // Apply monthly updates (e.g., interest application) to all accounts.
    void performMonthlyUpdates() {
        cout << "\nPerforming monthly updates for all accounts...\n" << endl;
        for (auto &pair : accounts) {
            pair.second.applyMonthlyInterest();
        }
    }

    // Print account statements for all accounts in the system.
    void printAllStatements() const {
        for (const auto &pair : accounts) {
            pair.second.printStatement();
            cout << endl;
        }
    }
};

int main() {
    try {
        BankingSystem bank;
        
        // Create bank accounts for customers.
        int aliceAcc = bank.createAccount("Alice Johnson", 5000.0, 1.2); // 1.2% annual interest
        int bobAcc = bank.createAccount("Bob Smith", 3000.0, 1.0);         // 1.0% annual interest

        // Retrieve accounts to perform transactions.
        BankAccount &aliceAccount = bank.getAccount(aliceAcc);
        BankAccount &bobAccount = bank.getAccount(bobAcc);

        // Perform various transactions.
        aliceAccount.deposit(1500.0);
        bobAccount.withdraw(500.0);
        aliceAccount.transfer(bobAccount, 2000.0);

        // Apply monthly interest to all accounts.
        bank.performMonthlyUpdates();

        // Generate and print account statements.
        bank.printAllStatements();
    }
    catch (const exception &ex) {
        cerr << "Error: " << ex.what() << endl;
    }
    return 0;
}
