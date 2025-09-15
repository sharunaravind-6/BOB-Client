#!/bin/bash
set -x

# No more wget! The library is already in the image.

# Compile the GreedyBot.java file, referencing the library's new location.
javac -cp /usr/share/java/json.jar GreedyBot.java

# Run the compiled bot with the hang-fix and the correct classpath.
java -Djava.util.prefs.userRoot=/dev/null -cp .:/usr/share/java/json.jar GreedyBot