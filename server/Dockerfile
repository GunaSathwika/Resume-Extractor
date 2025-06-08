FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "server.app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "--bind", "0.0.0.0:$PORT"]
