FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY web/ ./web/
ENV PYTHONPATH=/app/src PORT=8080
# DOPPEL_ALLOW_SPEND is deliberately NOT set: the deployed console can sweep, score and
# report, but cannot register a domain. A public URL must not be able to spend money.
CMD ["sh","-c","uvicorn doppel.app:app --host 0.0.0.0 --port ${PORT}"]
