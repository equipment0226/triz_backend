FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HF_HOME=/data/models HF_HUB_DISABLE_TELEMETRY=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
COPY app.py inference.py ./
ENV DRAWING_DEVICE=cpu DRAWING_CPU_THREADS=2 DRAWING_DATA_DIR=/data PORT=8000
EXPOSE 8000
CMD ["python", "app.py"]
