FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY assumption_zero/ assumption_zero/

# Create data directory
ENV AZERO_DATA_DIR=/app/azero_data
RUN mkdir -p /app/azero_data

EXPOSE 8000

CMD ["uvicorn", "assumption_zero.main:app", "--host", "0.0.0.0", "--port", "8000"]
