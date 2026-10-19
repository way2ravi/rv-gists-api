# Use the official Python 3.13 slim image.
FROM python:3.13-slim

# Set the working directory.
WORKDIR /app

# Show logs immediately and prevent .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy app.py into /app.
COPY app.py .

# Run as a non-root user.
USER 10011:10011

# Document the application port.
EXPOSE 8080

# Start the API.
CMD ["python", "app.py"]