FROM python:3.11-slim

# ------------------------
# Env config
# ------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ------------------------
# System dependencies
# ------------------------
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ------------------------
# Install Python dependencies (layer caching)
# ------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ------------------------
# Copy application code
# ------------------------
COPY app ./app
COPY alembic.ini .
COPY migrations ./migrations
COPY scripts ./scripts

# ------------------------
# Expose port
# ------------------------
EXPOSE 8000

# ------------------------
# Start application
# ------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
