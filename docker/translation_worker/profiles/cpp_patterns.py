# cpp_behavior_profiler.py

import re

def detect_cpp_patterns(cpp_code: str) -> list[str]:
    hints = []

    # 1. Class declarations
    classes = re.findall(r'\bclass\s+(\w+)', cpp_code)
    if classes:
        hints.append(f"Detected C++ class declarations: {', '.join(classes)}.")

    # 2. Namespace usage
    namespaces = re.findall(r'\bnamespace\s+(\w+)', cpp_code)
    if namespaces:
        hints.append(f"Uses namespaces: {', '.join(namespaces)}. Consider using Java packages or nested classes.")

    # 3. Templates
    if re.search(r'\btemplate\s*<', cpp_code):
        hints.append("Uses C++ templates. Translate to Java generics or method overloading.")

    # 4. Raw pointers
    if re.search(r'\b\w+\s*\*', cpp_code):
        hints.append("Uses pointer declarations. Use Java object references instead.")

    # 5. Manual memory management
    if re.search(r'\b(new|delete)\b', cpp_code):
        hints.append("Uses manual memory management (new/delete). Java handles memory via garbage collection.")

    # 6. STL containers
    stl_containers = []
    if re.search(r'\bvector<', cpp_code):
        stl_containers.append("vector")
    if re.search(r'\bmap<', cpp_code):
        stl_containers.append("map")
    if stl_containers:
        hints.append(f"Uses STL containers: {', '.join(stl_containers)}. Map to Java Collections (e.g., List, Map).")

    # 7. HTTP clients via include
    if re.search(r'#include\s*["<](httplib|curl|cpprest|boost/asio).*?[">]', cpp_code, re.IGNORECASE):
        hints.append(
            "Performs HTTP networking operations (e.g., GET, POST with headers and JSON payloads). "
            "Translate to idiomatic Java using java.net.http.HttpClient or okhttp3.OkHttpClient."
        )

    # 8. HTTP actions manually invoked
    if re.search(r'\b(GET|POST|PUT|DELETE)\s*\(', cpp_code) and re.search(r'http[s]?://', cpp_code):
        hints.append(
            "Sends HTTP requests to remote servers. Use modern Java HTTP clients like java.net.http.HttpClient."
        )

    # 9. Multithreading
    if re.search(r'#include\s*<thread>', cpp_code):
        hints.append("Uses multithreading. Translate to Java using java.util.concurrent.Executors or Thread classes.")

    # 10. File I/O
    if re.search(r'#include\s*<fstream>', cpp_code):
        hints.append("Performs file input/output. Use java.io.FileReader, BufferedReader, or FileWriter in Java.")

    # 11. Mutex/Synchronization
    if re.search(r'#include\s*<mutex>', cpp_code):
        hints.append("Uses std::mutex for synchronization. Use synchronized blocks or java.util.concurrent.locks.ReentrantLock in Java.")

    # 12. Time utilities
    if re.search(r'#include\s*<chrono>', cpp_code):
        hints.append("Uses time measurement or delays. Use java.time.* API or System.currentTimeMillis().")

    # 13. Exception handling
    if re.search(r'\btry\s*\{.*?\}\s*catch\s*\(', cpp_code, re.DOTALL):
        hints.append("Uses exception handling. Map try-catch blocks to Java's try-catch syntax with appropriate exception types.")

    return hints