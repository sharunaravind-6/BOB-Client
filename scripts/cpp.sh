#!/bin/bash
set -e # Exit immediately if a command fails

BOT_FILENAME="$1"
# Compile the C++ file using the C++17 standard, creating an executable named 'bot'
g++ -std=c++17 "$BOT_FILENAME" -o bot

# Run the compiled bot and merge its error output
./bot 2>&1