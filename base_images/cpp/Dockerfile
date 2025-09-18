# Use the official GCC (GNU Compiler Collection) image
FROM gcc:latest

# --- NEW: Install dependencies during the build ---
# This runs only ONCE when you build the image.
RUN apt-get update && apt-get install -y wget && \
    wget -q https://github.com/nlohmann/json/releases/download/v3.11.2/json.hpp -O /usr/local/include/json.hpp && \
    apt-get purge -y wget && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy our standard C++ run script into the image's path
COPY scripts/cpp.sh /usr/local/bin/run_bot.sh

# Make the script executable
RUN chmod +x /usr/local/bin/run_bot.sh