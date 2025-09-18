# Use the official GCC (GNU Compiler Collection) image
FROM gcc:latest

# Install the Jansson library for JSON parsing in C
RUN apt-get update && apt-get install -y libjansson-dev

# Set the working directory
WORKDIR /app

# Copy our standard C run script into the image's path
COPY scripts/c.sh /usr/local/bin/run_bot.sh