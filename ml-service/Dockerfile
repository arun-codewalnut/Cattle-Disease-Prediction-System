FROM python:3.13-slim

WORKDIR /app

# No apt/build-essential step: every dependency ships a prebuilt manylinux wheel for cp313 now
# that shap (never imported — M1 uses XGBoost's own pred_contribs) and chroma-hnswlib are gone.
# Dropping the compiler keeps the image small enough for hosted builders like Railway.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hosted platforms (Railway etc.) inject PORT; default to 8000 locally. --host "" listens on
# every interface over both IPv4 and IPv6 (Railway's private network resolves to IPv6), where
# 0.0.0.0 alone is IPv4-only and "::" alone is IPv6-only. docker-compose.yml
# overrides this with --reload for local dev.
CMD ["sh", "-c", "exec uvicorn app.main:app --host '' --port ${PORT:-8000}"]
