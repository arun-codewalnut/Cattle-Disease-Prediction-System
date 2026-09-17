FROM python:3.13-slim

WORKDIR /app

# build-essential is needed here (unlike a bare Windows venv) to compile shap/chroma-hnswlib
# native extensions — this container path works even where local Windows setup needs
# Microsoft C++ Build Tools installed separately. See AGENTS.md.
#
# Force https for the Debian archive: something in this network path was consistently
# corrupting plain-HTTP .deb downloads (same expected hash, different received content, on
# every retry — a transparent proxy/inspection tool, not random flakiness). HTTPS routes
# around it since that content can't be rewritten in transit the same way.
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/*.sources 2>/dev/null; \
    sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list 2>/dev/null; \
    apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
