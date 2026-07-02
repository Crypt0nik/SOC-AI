FROM python:3.11-slim
WORKDIR /app
COPY notifications/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY db/ ./db/
COPY notifications/ ./notifications/
CMD ["python", "-m", "notifications.dispatcher"]
