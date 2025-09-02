FROM python:3.13-slim

# Install system dependencies required for lxml and other packages
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt1-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 9000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
# http://localhost:9000 or http://127.0.0.1:9000