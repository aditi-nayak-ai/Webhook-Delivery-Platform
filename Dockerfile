FROM python:3.11-slim

WORKDIR /app

# System deps (for psycopg2)
RUN apt-get update && apt-get install -y gcc libpq-dev

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1

# Default command (Web service)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
