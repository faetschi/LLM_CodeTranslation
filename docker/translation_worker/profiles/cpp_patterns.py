# C++ Translation Hints

import re

def detect_cpp_patterns(cpp_code: str) -> list[str]:
    """
    Analyzes C++ code and provides hints for idiomatic Java 17+ translation.
    """
    hints = []
    detected_features = set() # To avoid redundant hints for the same feature type

    # --- Core Language Features ---

    # 1. Classes and Structs
    class_struct_matches = re.findall(r'\b(class|struct)\s+(\w+)', cpp_code)
    if class_struct_matches:
        detected_features.add("class/struct")
        types = [cs[0] for cs in class_struct_matches]
        names = [cs[1] for cs in class_struct_matches]
        has_class = 'class' in types
        has_struct = 'struct' in types
        hint = "Detected C++ "
        if has_class and has_struct: hint += f"classes/structs: {', '.join(names)}."
        elif has_class: hint += f"classes: {', '.join(names)}."
        else: hint += f"structs: {', '.join(names)}."
        hint += " Translate to Java classes. For simple data aggregates (esp. structs), consider using Java Records (Java 16+)."
        hints.append(hint)

    # 2. Namespaces
    namespace_matches = re.findall(r'\bnamespace\s+(\w+)', cpp_code)
    if namespace_matches:
        detected_features.add("namespace")
        hints.append(f"Uses namespaces: {', '.join(namespace_matches)}. Map to Java packages. Consider using static imports for functions/constants within namespaces if appropriate.")

    # 3. Templates
    if re.search(r'\btemplate\s*<', cpp_code):
        detected_features.add("template")
        hints.append("Uses C++ templates (e.g., template<typename T>). Translate using Java Generics (e.g., class MyClass<T>, <T> T myMethod(...)). Function templates might map to generic methods or overloaded methods.")

    # 4. Pointers (More specific detection)
    # Look for Type*, pointer variables, ->, or dereference *
    if re.search(r'\b\w+\s*\*\s*\w+|->|(?<!\s)\*(?!\s|=)', cpp_code):
         # Exclude multiplication *, assignment *= etc.
        if "pointer" not in detected_features:
            detected_features.add("pointer")
            hints.append("Uses C++ pointers (*, ->). Replace with Java object references. Java's garbage collector manages memory, eliminating the need for manual pointer arithmetic or explicit dereferencing in most cases.")

    # 5. Manual Memory Management (new/delete)
    if re.search(r'\b(new|delete)\b(?!\s*\[\])', cpp_code): # Exclude new[]/delete[] for now
        if "memory" not in detected_features:
            detected_features.add("memory")
            hints.append("Uses manual memory management (new/delete). Rely on Java's automatic garbage collection (GC). Object creation uses 'new ClassName()', but memory deallocation is handled by the JVM.")
    if re.search(r'\bdelete\s*\[\s*\]', cpp_code):
        if "memory" not in detected_features:
             detected_features.add("memory") # Add feature even if new/delete wasn't found
        hints.append("Uses 'delete[]'. Java GC handles array memory automatically as well.")

    # 6. Smart Pointers (unique_ptr, shared_ptr)
    if re.search(r'\b(std::unique_ptr|std::shared_ptr|std::weak_ptr)\s*<', cpp_code):
        if "pointer" not in detected_features: # Relates to pointer concept
             detected_features.add("pointer")
        hints.append("Uses C++ smart pointers (unique_ptr, shared_ptr). In Java, standard object references combined with GC typically suffice. No direct equivalent needed; focus on object lifecycle and references.")

    # 7. References (Type&, const Type&)
    if re.search(r'\b\w+\s*&(?!\&)\s*\w+', cpp_code): # Look for Type& var, avoid &&
        detected_features.add("reference")
        hints.append("Uses C++ references (&). Java passes object references by value. For 'const&' parameters, simply pass the object reference. For mutable references, ensure the passed object's state can be modified if intended.")

    # 8. Operator Overloading
    if re.search(r'\boperator\s*([+\-*/%^&|<>!=]=?|\[\]|\(\)|~|\+\+|--)\s*\(', cpp_code):
        detected_features.add("operator-overloading")
        hints.append("Uses operator overloading (e.g., operator+, operator==). Java does not support arbitrary operator overloading (except '+' for String). Implement corresponding methods (e.g., .add(), .equals(), .compareTo(), .get(), .set(), .invoke()).")

    # 9. Const Keyword
    if re.search(r'\bconst\b', cpp_code):
        detected_features.add("const")
        hints.append("Uses 'const'. Translate to Java's 'final'. 'final' variables cannot be reassigned. 'final' parameters cannot be reassigned within the method. 'final' methods cannot be overridden. 'final' classes cannot be subclassed. Map C++ 'const' correctness concepts appropriately.")

    # 10. Auto Keyword
    if re.search(r'\bauto\b', cpp_code):
        detected_features.add("auto")
        hints.append("Uses C++ 'auto' for type deduction. Use Java's 'var' for local variable type inference (Java 10+).")

    # 11. Range-based for loop
    if re.search(r'\bfor\s*\(\s*(auto|[\w:]+)\s+(&|&&)?\s*\w+\s*:\s*\w+', cpp_code):
        detected_features.add("range-for")
        hints.append("Uses C++ range-based for loop (for : ). Translate using Java's enhanced for loop (for (Type var : collection)).")

    # 12. Typedef / Using Alias
    if re.search(r'\b(typedef|using)\s+.*\s*=\s*.*;', cpp_code):
        detected_features.add("type-alias")
        hints.append("Uses 'typedef' or 'using' for type aliases. Java has no direct equivalent for complex type aliases. Replace simple aliases with the full type name. For function pointers aliased, use Java Functional Interfaces.")

    # 13. Preprocessor Directives (#define, #ifdef)
    if re.search(r'#\s*(define|ifdef|ifndef|endif)', cpp_code):
        detected_features.add("preprocessor")
        hints.append("Uses preprocessor directives (#define, #ifdef). For #define constants, use 'static final' fields in Java. For macros, use static methods or regular methods. For conditional compilation (#ifdef), use build system configurations (e.g., Maven profiles, Gradle flavors) or runtime flags/properties.")

    # --- Standard Library Features ---

    # 14. STL Containers
    stl_containers = set()
    if re.search(r'\b(std::)?vector\s*<', cpp_code): stl_containers.add("vector -> ArrayList/List")
    if re.search(r'\b(std::)?list\s*<', cpp_code): stl_containers.add("list -> LinkedList/List")
    if re.search(r'\b(std::)?map\s*<', cpp_code): stl_containers.add("map -> HashMap/TreeMap/Map")
    if re.search(r'\b(std::)?unordered_map\s*<', cpp_code): stl_containers.add("unordered_map -> HashMap/Map")
    if re.search(r'\b(std::)?set\s*<', cpp_code): stl_containers.add("set -> HashSet/TreeSet/Set")
    if re.search(r'\b(std::)?unordered_set\s*<', cpp_code): stl_containers.add("unordered_set -> HashSet/Set")
    if re.search(r'\b(std::)?deque\s*<', cpp_code): stl_containers.add("deque -> ArrayDeque/Deque")
    if re.search(r'\b(std::)?stack\s*<', cpp_code): stl_containers.add("stack -> Deque (use ArrayDeque)") # Stack class is discouraged
    if re.search(r'\b(std::)?queue\s*<', cpp_code): stl_containers.add("queue -> Queue (use LinkedList or ArrayDeque)")
    if re.search(r'\b(std::)?priority_queue\s*<', cpp_code): stl_containers.add("priority_queue -> PriorityQueue")
    if re.search(r'\b(std::)?pair\s*<', cpp_code): stl_containers.add("pair -> Custom class, Record, or Map.Entry")
    if stl_containers:
        detected_features.add("stl-container")
        hints.append(f"Uses STL containers: {', '.join(sorted(list(stl_containers)))}. Map to corresponding Java Collections Framework interfaces and classes. Use interfaces (List, Map, Set) in variable/parameter types.")

    # 15. STL Algorithms
    if re.search(r'#include\s*<algorithm>', cpp_code) or re.search(r'\bstd::(sort|find|count|transform|accumulate|for_each)\b', cpp_code):
        detected_features.add("stl-algorithm")
        hints.append("Uses STL algorithms (e.g., from <algorithm>). Translate using the Java Streams API (stream(), map(), filter(), reduce(), collect()) or appropriate methods from java.util.Collections/Arrays for equivalent functionality.")

    # 16. IOStream (cin, cout, cerr)
    if re.search(r'#include\s*<iostream>', cpp_code) or re.search(r'\b(std::)?(cout|cin|cerr)\b', cpp_code):
        detected_features.add("iostream")
        hints.append("Uses iostream (cout, cin, cerr). Map to System.out, System.in, System.err in Java. Use Scanner or BufferedReader for complex input parsing from System.in.")

    # 17. FStream (File I/O)
    if re.search(r'#include\s*<fstream>', cpp_code) or re.search(r'\b(std::)?(ifstream|ofstream|fstream)\b', cpp_code):
        detected_features.add("fstream")
        hints.append("Performs file I/O using fstream. Use modern Java NIO (java.nio.file.Files - e.g., Files.readString, Files.writeString, Files.newBufferedReader/Writer) or traditional IO (java.io.*) wrapped in try-with-resources statements.")

    # 18. String Manipulation (<string>, <sstream>)
    if re.search(r'#include\s*<(string|sstream)>', cpp_code) or re.search(r'\b(std::)?(string|stringstream)\b', cpp_code):
        detected_features.add("string")
        hints.append("Uses C++ std::string or stringstream. Use Java's String, StringBuilder (for mutable strings), String.format, or standard string methods for equivalent operations.")

    # 19. Chrono (Time utilities)
    if re.search(r'#include\s*<chrono>', cpp_code) or re.search(r'\b(std::)?chrono::', cpp_code):
        detected_features.add("chrono")
        hints.append("Uses C++ chrono library for time. Use the java.time API (Instant, Duration, LocalDateTime, ZonedDateTime, etc.) for modern, robust date/time handling in Java.")

    # 20. Threading (<thread>, <mutex>, <atomic>, <future>)
    uses_threading = False
    thread_libs = []
    if re.search(r'#include\s*<thread>', cpp_code) or re.search(r'\bstd::thread\b', cpp_code): thread_libs.append("thread")
    if re.search(r'#include\s*<mutex>', cpp_code) or re.search(r'\bstd::(mutex|lock_guard|unique_lock)\b', cpp_code): thread_libs.append("mutex")
    if re.search(r'#include\s*<atomic>', cpp_code) or re.search(r'\bstd::atomic\b', cpp_code): thread_libs.append("atomic")
    if re.search(r'#include\s*<future>', cpp_code) or re.search(r'\bstd::(future|async|promise)\b', cpp_code): thread_libs.append("future/async")
    if thread_libs:
        detected_features.add("threading")
        hints.append(f"Uses C++ concurrency features ({', '.join(thread_libs)}). Translate using java.util.concurrent package: "
                     "Use Executors/Thread/Runnable for tasks, "
                     "'synchronized' blocks or Locks (ReentrantLock) for mutex behavior, "
                     "java.util.concurrent.atomic classes for atomics, "
                     "and CompletableFuture/ExecutorService.submit for future/async operations. Consider Java 21+ virtual threads and structured concurrency.")

    # 21. Function Objects / Lambdas (<functional>)
    if re.search(r'#include\s*<functional>', cpp_code) or re.search(r'\bstd::function\b', cpp_code) or re.search(r'\[.*\]\s*\(.*\)\s*(->.*)?\s*{', cpp_code):
        detected_features.add("functional")
        hints.append("Uses C++ function objects, std::function, or lambdas. Translate using Java Functional Interfaces (like Runnable, Consumer, Supplier, Function, Predicate), lambda expressions (->), or method references (::).")

    # 22. Exception Handling (try/catch/throw)
    if re.search(r'\b(try\s*\{|catch\s*\(|throw)\b', cpp_code):
        detected_features.add("exception")
        hints.append("Uses C++ exception handling (try, catch, throw). Map directly to Java's try-catch-finally blocks. Ensure appropriate Java exception types (checked vs. unchecked) are used or defined.")

    # --- External Dependencies / Networking ---

    # 23. Common Networking/HTTP Libraries
    network_libs = []
    if re.search(r'#include\s*["<](curl/curl\.h|httplib\.h|boost/asio|cpprest/http_client\.h)', cpp_code, re.IGNORECASE): network_libs.append("includes")
    # Simple check for HTTP method usage as strings - might be less reliable
    if re.search(r'\b(GET|POST|PUT|DELETE|Http|Url|Request|Response)\b', cpp_code, re.IGNORECASE) and re.search(r'https?://', cpp_code): network_libs.append("keywords/url")
    if network_libs:
        if "networking" not in detected_features:
            detected_features.add("networking")
            hints.append("Appears to perform HTTP/networking operations (based on " + " & ".join(network_libs) + "). Use Java's built-in java.net.http.HttpClient (Java 11+) or libraries like OkHttp3 or Apache HttpClient for robust HTTP communication.")

    # 24. Boost Usage (General)
    if re.search(r'#include\s*<boost/', cpp_code):
        if "boost" not in detected_features:
            detected_features.add("boost")
            hints.append("Uses the Boost library. Identify the specific Boost components used and find Java equivalents (e.g., Boost.Filesystem -> java.nio.file, Boost.Asio -> Netty/java.nio/HttpClient, Boost.Test -> JUnit/TestNG). Common utilities might be found in Apache Commons or Guava.")

    # --- Final Generic Hints ---
    if not hints:
        hints.append("No specific C++ patterns detected by this script, but general translation principles apply.")
    else:
        hints.append("General: Ensure translated code is idiomatic Java 17+, leveraging features like Streams, Optionals, Records, try-with-resources, and the modern java.time and java.nio APIs where applicable.")

    return hints