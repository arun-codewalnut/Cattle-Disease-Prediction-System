FROM python:3.13-slim

WORKDIR /app

# build-essential is needed here (unlike a bare Windows venv) to compile shap/chroma-hnswlib
# native extensions — this container path works even where local Windows setup needs
# Microsoft C++ Build Tools installed separately. See AGENTS.md.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
