FROM python:3.12-slim

RUN pip install --upgrade pip
# Install system dependencies needed for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    tesseract-ocr \
    poppler-utils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir python-dotenv

# Copy application code
COPY . .

# start
CMD ["python", "main.py"]