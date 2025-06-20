# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy your application code
COPY main.py .

# Install dependencies
RUN pip install --no-cache-dir kopf kubernetes pyyaml

# Command to run the operator
CMD ["kopf", "run", "--standalone", "main.py"]
