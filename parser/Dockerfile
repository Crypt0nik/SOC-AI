FROM python:3.11-slim

LABEL org.opencontainers.image.title="soc-ai-parser"
LABEL org.opencontainers.image.description="SOC-AI log ingestion module"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install Python dependencies
COPY parser/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared db package and parser module
COPY db/ ./db/
COPY parser/ ./parser/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "parser.parser"]
