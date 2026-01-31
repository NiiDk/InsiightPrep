# Dockerfile for FinalPreps (Coolify compatible)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Install system deps (including libpq-dev for Postgres drivers)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Collect static files (requires env vars like SECRET_KEY and cloudinary config in production)
# Ensure you set env vars via Coolify (e.g., SECRET_KEY, DATABASE_URL, etc.) before build/run if necessary.
ENV DJANGO_SETTINGS_MODULE=FinalPreps.settings
RUN python manage.py collectstatic --noinput || true

# Expose port 8000 for Coolify
EXPOSE 8000

# Use gunicorn to run the app; bind to port 8000
CMD ["gunicorn", "FinalPreps.wsgi:application", "--bind", "0.0.0.0:8000"]
