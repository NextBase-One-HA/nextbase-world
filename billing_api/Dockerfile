# Deploy from THIS directory (billing_api):
#   cd billing_api && gcloud run deploy nextbase-billing --source . --region asia-northeast1
#
# canonical/ is committed under billing_api/ — do not manual-cp before deploy (use git pull).
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache dependency layer when only app code changes
COPY requirements-billing.txt .
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir --retries 5 -r requirements-billing.txt

COPY . .

RUN test -d canonical \
  && test -f canonical/ORE_LAYER_SYNC.json \
  && test -f canonical/ORE_LAYER_LOCK.json

ENV CANONICAL_PATH=/app/canonical
ENV PYTHONPATH=/app
ENV PORT=8080
EXPOSE 8080

CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
