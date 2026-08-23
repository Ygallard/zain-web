# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create the application user and grant it access to all project files.
RUN groupadd --gid 10001 appuser \
	&& useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin appuser \
	&& chown -R 10001:10001 /app

# Expose port
EXPOSE 5000

# Run the application without root privileges.
USER 10001:10001

# Command to run the app
CMD ["python", "app.py"]
