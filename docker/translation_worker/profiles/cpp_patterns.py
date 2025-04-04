import re

def detect_cpp_patterns(cpp_code: str) -> list[str]:
    """
    Provides C++ hints for idiomatic Java 17+ translation.
    """
    hints = []
    
    # # Detect use of classic CLI signature
    # if re.search(r'main\s*\(\s*int\s+argc\s*,\s*char\s*\*\s*argv\s*\[\s*\]\s*\)', cpp_code):
    #     hints.append(
    #         "- The program uses 'main(int argc, char* argv[])'. Make it possible to use CLI arguments similiarly in Java."
    #     )
    #     hints.append(
    #         "- Preserve the original CLI flag parsing logic, including default values and usage fallback behavior."
    #     )
        
    return hints
