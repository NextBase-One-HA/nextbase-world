# Build from repository root (nextbase-world):
#   docker build -f cloud_run/smile-friend-engine/Dockerfile .
#
# Cloud Run (project nb-official-base, region us-central1) example:
#   gcloud run deploy smile-friend-engine \
#     --project nb-official-base --region us-central1 --source . \
#     ...
# Or build this image and deploy with a persisted volume for GLB_FREE_QUOTA_DB_PATH.

FROM python:3.12-slim-bookworm

WORKDIR /app
COPY smile_friend_engine /app/smile_friend_engine
RUN pip install --no-cache-dir -r /app/smile_friend_engine/requirements.txt

ENV PORT=8080
EXPOSE 8080
CMD sh -c "exec uvicorn smile_friend_engine.main:app --host 0.0.0.0 --port ${PORT}"
