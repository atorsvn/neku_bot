FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    sox \
    libsox-fmt-mp3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader punkt

COPY . .

CMD ["python", "neku.py"]
