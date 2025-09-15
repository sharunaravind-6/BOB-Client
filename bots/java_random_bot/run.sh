#!/bin/bash

# This script will run inside the container, which has internet access to download this.
# Download a simple Java JSON library if it doesn't exist
if [ ! -f "json.jar" ]; then
    wget -q https://repo1.maven.org/maven2/org/json/json/20231013/json-20231013.jar -O json.jar
fi

# Compile the bot with the library in the classpath
javac -cp json.jar RandomBot.java

# Run the compiled bot
java -cp .:json.jar RandomBot