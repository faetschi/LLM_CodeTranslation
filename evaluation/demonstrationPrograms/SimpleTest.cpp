// SimpleTest.cpp
// VERY simple C++ program demonstrating various utility functions and a Rectangle class.

#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <map>
#include <cmath>

// Function to add two integers
int add(int a, int b) {
    return a + b;
}

// Function to calculate factorial of a number
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

// Function to check if a string is a palindrome
bool isPalindrome(const std::string& s) {
    int left = 0;
    int right = s.length() - 1;
    while (left < right) {
        if (s[left] != s[right]) {
            return false;
        }
        left++;
        right--;
    }
    return true;
}

// Function to reverse an array of integers
std::vector<int> reverseArray(const std::vector<int>& arr) {
    std::vector<int> result = arr;
    std::reverse(result.begin(), result.end());
    return result;
}

// Function to calculate average of a list of numbers
double calculateAverage(const std::vector<int>& numbers) {
    if (numbers.empty()) return 0.0;
    int sum = 0;
    for (int num : numbers) {
        sum += num;
    }
    return static_cast<double>(sum) / numbers.size();
}

// Function to count occurrences of each character in a string
std::map<char, int> countCharacters(const std::string& str) {
    std::map<char, int> charCount;
    for (char c : str) {
        charCount[c]++;
    }
    return charCount;
}

// Class with a simple method
class Rectangle {
public:
    int width;
    int height;

    Rectangle(int w, int h) : width(w), height(h) {}

    int area() const {
        return width * height;
    }

    int perimeter() const {
        return 2 * (width + height);
    }

    bool isSquare() const {
        return width == height;
    }
};

int main() {
    // Test add function
    std::cout << "add(5, 7) = " << add(5, 7) << std::endl;

    // Test factorial function
    std::cout << "factorial(5) = " << factorial(5) << std::endl;

    // Test isPalindrome function
    std::string testStr = "level";
    std::cout << "isPalindrome('" << testStr << "') = " << (isPalindrome(testStr) ? "true" : "false") << std::endl;

    // Test reverseArray function
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    std::vector<int> reversed = reverseArray(numbers);
    std::cout << "reverseArray({1,2,3,4,5}) = ";
    for (int num : reversed) {
        std::cout << num << " ";
    }
    std::cout << std::endl;

    // Test calculateAverage function
    std::cout << "Average = " << calculateAverage(numbers) << std::endl;

    // Test countCharacters function
    std::string sentence = "hello world";
    std::map<char, int> charMap = countCharacters(sentence);
    std::cout << "Character counts in '" << sentence << "':\n";
    for (const auto& pair : charMap) {
        std::cout << pair.first << ": " << pair.second << std::endl;
    }

    // Test Rectangle class
    Rectangle rect(4, 5);
    std::cout << "Rectangle area (4x5) = " << rect.area() << std::endl;
    std::cout << "Rectangle perimeter (4x5) = " << rect.perimeter() << std::endl;
    std::cout << "Is rectangle a square? " << (rect.isSquare() ? "Yes" : "No") << std::endl;

    return 0;
}