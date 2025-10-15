# ======================
# Base image
# ======================
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ======================
# Set work directory
# ======================
WORKDIR /app

# ======================
# Install system deps
# ======================
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ======================
# Install dependencies
# ======================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ======================
# Copy project files
# ======================
COPY . .

# ======================
# Collect static files
# ======================
RUN python manage.py collectstatic --noinput

# ======================
# Expose port and run server
# ======================
EXPOSE 8000
CMD ["uvicorn", "core.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]
