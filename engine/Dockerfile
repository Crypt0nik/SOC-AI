FROM python:3.11-slim

LABEL org.opencontainers.image.title="soc-ai-engine"
LABEL org.opencontainers.image.description="SOC-AI Sigma detection engine"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ../db /app/db

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "engine.py"]
