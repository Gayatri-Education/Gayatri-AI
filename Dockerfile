FROM node:22-bookworm-slim AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ backend/
COPY scripts/ scripts/
COPY data/ data/
COPY --from=frontend /frontend/dist/ frontend/dist/
RUN useradd --uid 10001 --create-home portal && mkdir var && chown portal:portal var && chmod -R a+rX data
USER portal
EXPOSE 8000
CMD ["sh", "-c", "python -m scripts.seed_db && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
