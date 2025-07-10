FROM python:3.12.9-slim

# Upgrade pip and install system dependencies
RUN pip install --upgrade pip \
 && apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    build-essential \
    libpq-dev \
    gcc \
    tesseract-ocr \
    poppler-utils \
    libc6-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install --prefer-binary blis \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir python-dotenv \
    && pip install --no-cache-dir spacy


# Copy application code
COPY . .

CMD ["python3", "main.py"]
