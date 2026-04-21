# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Create media and static directories
RUN mkdir -p /app/media /app/static

# Expose port 8000
EXPOSE 8000

# Start the application using Gunicorn or just runserver for now
# We will use gunicorn in the docker-compose for production-like setups
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
