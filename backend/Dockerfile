FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AZERO_DATA_DIR=/app/azero_data

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the package before installation so the built wheel contains the source.
COPY pyproject.toml README.md ./
COPY assumption_zero/ assumption_zero/
RUN pip install --no-cache-dir .

# Run the API without root privileges.
RUN useradd --create-home --uid 10001 azero \
    && mkdir -p /app/azero_data \
    && chown -R azero:azero /app

USER azero

EXPOSE 8000

CMD ["uvicorn", "assumption_zero.main:app", "--host", "0.0.0.0", "--port", "8000"]
