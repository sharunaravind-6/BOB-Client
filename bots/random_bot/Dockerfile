# Use a slim, official Python image as a base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the bot's code into the container
COPY . .

# Make the run script executable
RUN chmod +x run.sh

# The command that will be executed when the container starts
CMD ["./run.sh"]