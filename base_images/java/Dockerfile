# Use the standard, non-interactive JDK image.
# FROM openjdk:17-jdk-bullseye

# # Set the working directory
# WORKDIR /app

# # --- NEW ---
# # Copy the pre-downloaded json library into a standard location in the image
# COPY json-20231013.jar /usr/share/java/json.jar


FROM openjdk:17-jdk-bullseye
WORKDIR /app
COPY json-20231013.jar /usr/share/java/json.jar
# Add this line to copy the script
COPY scripts/java.sh /app/run.sh