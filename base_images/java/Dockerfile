# Use the standard, non-interactive JDK image.
FROM openjdk:17-jdk-bullseye

# Set the working directory
WORKDIR /app

# --- NEW ---
# Copy the pre-downloaded json library into a standard location in the image
COPY json-20231013.jar /usr/share/java/json.jar