FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Fly.io uses 8080)
EXPOSE 8080

# Run the application on port 8080 (Fly.io default)
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
