# Evaluation of C++ Programs

This repository contains C++ programs intended for the evaluation, comparison, and translation. In order to compile and run the programs, please follow the setup instructions below.

## Prerequisites

- **MSYS2**: Install the [MSYS2](https://www.msys2.org/) environment for Windows, which provides a full UNIX-like build environment.
- **UCRT64 Toolchain**: Use the UCRT64 environment within MSYS2 for compatibility and modern C++ support.
- **GNU Make**: Included in MSYS2 by default.

## Setup Instructions

1. **Install MSYS2**

   Download and install MSYS2 from https://www.msys2.org/

2. **Update MSYS2 and Install Build Tools**

   Open the MSYS2 terminal and run:

    ```sh
    pacman -Syu
    ```

   If prompted, close and reopen the terminal, then update again:

3. **Install the UCRT64 Toolchain**

   In your MSYS2 terminal, install the required packages:

    ```sh
    pacman -S --needed base-devel mingw-w64-ucrt-x86_64-toolchain
    ```

4. **Switch to UCRT64 Environment**

   Open the **MSYS2 MinGW UCRT64** terminal (ucrt64.exe) as ``Admin`` from the Start Menu.

5. **Clone the Repository**

    ```sh
    git clone https://github.com/faetschi/LLM_CodeTranslation
    cd LLM_CodeTranslation
    ```

6. **Build the Program**

   Run make in the project directory:

    ```sh
    make
    ```

7. **Run the Program**

   After building, you can execute the compiled program as follows (replace `<program>` with the actual executable name):

    ```sh
    ./<program>
    ```

## Notes

- All necessary dependencies for building standard C++ programs are included with the MSYS2 UCRT64 toolchain.
- If your program has additional dependencies, refer to its individual README or the Makefile for further instructions.
- If you encounter any issues, check your environment variables and ensure you are using the **UCRT64** terminal.
