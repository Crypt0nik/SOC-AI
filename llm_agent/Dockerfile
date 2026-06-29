FROM python:3.11-slim

LABEL org.opencontainers.image.title="soc-ai-llm-agent"
LABEL org.opencontainers.image.description="SOC-AI LLM triage agent (Claude + Ollama backends)"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ../db /app/db

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "agent.py"]
