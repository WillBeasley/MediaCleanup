FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script and entrypoint
COPY script.py .
COPY docker-entrypoint.sh .

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

# Set environment variables to ensure proper output handling
ENV PYTHONUNBUFFERED=1
ENV DOCKER_CONTAINER=1

# Use the entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
