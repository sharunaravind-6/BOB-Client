# Use the official GCC (GNU Compiler Collection) image
FROM gcc:latest

# Set the working directory
WORKDIR /app

# Copy the pre-downloaded json library from our local folder into a standard include path
COPY base_images/cpp/json.hpp /usr/local/include/json.hpp

# Copy our standard C++ run script into the image's path
COPY scripts/cpp.sh /usr/local/bin/run_bot.sh

# Make the script executable
RUN chmod +x /usr/local/bin/run_bot.sh

# Add this line to "warm up" the g++ compiler and build its cache
RUN g++ --version