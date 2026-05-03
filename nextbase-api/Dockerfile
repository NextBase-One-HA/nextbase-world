# Build context must be the nextbase-api directory (files at context root).
#
# From repo root:
#   docker build -f nextbase-api/Dockerfile -t nextbase-api nextbase-api
#
# Cloud Run (from nextbase-api folder):
#   gcloud run deploy nextbase-api --source . --region asia-northeast1
#
# Canonical/inventory markdown: use NEXTBASE_CANONICAL_URL / NEXTBASE_INVENTORY_URL if docs/ not bundled.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY rooms_firestore.py .
COPY session_firestore.py .
COPY agent_tasks.py .
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
