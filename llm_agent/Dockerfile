FROM python:3.11-slim

LABEL org.opencontainers.image.title="soc-ai-llm-agent"
LABEL org.opencontainers.image.description="SOC-AI LLM triage agent (Claude + Codex + Ollama backends)"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY llm_agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY db/ ./db/
COPY llm_agent/ ./llm_agent/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "llm_agent.agent"]
