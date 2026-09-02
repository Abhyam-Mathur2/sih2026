FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system utilities if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements-cpu.txt pyproject.toml ./

# Install CPU-only torch first to keep image size small
RUN pip install --no-cache-dir -r requirements-cpu.txt

# Install application dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Expose default port
EXPOSE 8000

# Start FastAPI application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
