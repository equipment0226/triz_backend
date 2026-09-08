FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-kor && rm -rf /var/lib/apt/lists/*
WORKDIR /app/pilot
COPY pilot/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY pilot/ ./
ENV APP_HOST=:: APP_PORT=8000 TRIZ_EMBED_MCP=true STORAGE_DIR=/data/storage DB_PATH=/data/triz.db
ENV TRIZ_MCP_URL=http://127.0.0.1:8000/agent/mcp
EXPOSE 8000
CMD ["python", "run.py"]
