#!/bin/bash
set -e # Exit immediately if a command fails

BOT_FILENAME="$1"
# Compile the C file, creating an executable named 'bot'
# The '-ljansson' flag links the Jansson library for JSON parsing.
gcc -std=c11 "$BOT_FILENAME" -o bot -ljansson

# Run the compiled bot and merge its error output
./bot 2>&1