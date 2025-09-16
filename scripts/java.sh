#!/bin/bash
# This script compiles and runs a Java file.
# It uses the filename passed in as the first argument ("$1").
cd /app
BOT_FILENAME="$1"
# This line strips the ".java" extension to get the class name
BOT_CLASSNAME=$(basename "$BOT_FILENAME" .java)

# Compile the specific Java file provided.
javac -cp /usr/share/java/json.jar "$BOT_FILENAME"

# Run the compiled class.
java -Djava.util.prefs.userRoot=/dev/null -cp .:/usr/share/java/json.jar "$BOT_CLASSNAME" 2>&1