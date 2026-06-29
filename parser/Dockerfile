FROM python:3.11-slim

LABEL org.opencontainers.image.title="soc-ai-parser"
LABEL org.opencontainers.image.description="SOC-AI log ingestion module"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy module source
COPY . .
# Copy shared db package
COPY ../db /app/db

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "parser.py"]
