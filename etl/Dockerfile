FROM python:3.12-slim

# Avoid stdio buffering & pyc files inside the container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_HOST=db \
    DB_PORT=5432 \
    DB_NAME=fifth_referee \
    DB_USER=fr_user \
    DB_PASSWORD=fr_password

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy only the ETL sources (add more paths here when needed)
COPY etl ./etl

# Default command can be overridden via docker-compose
CMD ["python", "-m", "etl.main"]
