FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY examples/definitions ./examples/definitions

RUN pip install --no-cache-dir ".[cli]"
RUN pip install --no-cache-dir ".[mcp]"

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    PALM_STORAGE_BACKEND=filesystem \
    PALM_DATA_DIR=/data \
    PALM_SERVER_HOST=0.0.0.0 \
    PALM_SERVER_PORT=8080 \
    PALM_LOG_FILE=/var/log/palm/palm.log

VOLUME ["/data", "/var/log/palm"]

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"

ENTRYPOINT ["/entrypoint.sh"]