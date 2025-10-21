FROM python:3.11-slim

LABEL maintainer="HMSE Project"
LABEL description="HMSE Energy Break-Even Calculator - Reproducible Environment"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy calculator script
COPY energy_calculator.py .

# Set entrypoint
ENTRYPOINT ["python", "energy_calculator.py"]


