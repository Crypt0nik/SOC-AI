FROM python:3.11-slim

LABEL org.opencontainers.image.title="soc-ai-api"
LABEL org.opencontainers.image.description="SOC-AI FastAPI backend"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY db/ ./db/
COPY api/ ./api/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
