# Use Python 3.13 (more stable than 3.14 for dependencies)
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies for building numpy and timezone data
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to America/Chicago (can be overridden by environment variable)
ENV TZ=America/Chicago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database
RUN mkdir -p /app/data

# Run the bot
CMD ["python", "motd_bot.py"]
