FROM python:3.12-slim
WORKDIR /app
COPY requirements-billing.txt .
RUN pip install --no-cache-dir -r requirements-billing.txt
COPY main.py .
ENV PORT=8080
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
