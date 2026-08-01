# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile for the CAR + DMA Super Breakout Scanner (Streamlit app)
#
# Build:
#   docker build -t stock-scanner:latest ./stock-screener
#
# Run (foreground):
#   docker run --rm -p 8501:8501 \
#     -v scanner-data:/app/data \
#     stock-scanner:latest
#
# Run (detached, custom admin password):
#   docker run -d --name scanner -p 8501:8501 \
#     -v scanner-data:/app/data \
#     -e ADMIN_USERNAME=admin \
#     -e ADMIN_PASSWORD=changeme \
#     stock-scanner:latest
#
# Open:  http://localhost:8501
# ─────────────────────────────────────────────────────────────────────────────

# Slim base image — Python 3.12 matches the dev environment.
FROM python:3.12-slim AS base

# Metadata
LABEL org.opencontainers.image.title="CAR + DMA Breakout Scanner" \
      org.opencontainers.image.description="Streamlit stock screener with mock trading" \
      org.opencontainers.image.source="https://github.com/heyaankitntf/stock-data-grid" \
      org.opencontainers.image.licenses="Apache-2.0"

# Prevent Python from writing .pyc files and buffering stdout/stderr.
# - PYTHONDONTWRITEBYTECODE: keeps the image small
# - PYTHONUNBUFFERED: ensures logs stream straight to docker logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# ── System deps ──────────────────────────────────────────────────────────────
# curl  → healthcheck
# ca-certificates → yfinance HTTPS calls to Yahoo Finance
# tini  → PID 1 init, properly forwards signals to streamlit (avoids
#         "Container didn't respond to SIGTERM" shutdown lag)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        tini \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user ────────────────────────────────────────────────────────────
# Run the app as an unprivileged user for defence-in-depth.
RUN groupadd --system --gid 1001 appuser \
 && useradd  --system --uid 1001 --gid appuser \
             --home-dir /app --shell /sbin/nologin appuser

WORKDIR /app

# ── Install Python deps first (better layer caching) ─────────────────────────
# Only requirements.txt changes when deps change — code edits don't bust this layer.
COPY --chown=appuser:appuser requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy app code ────────────────────────────────────────────────────────────
# Copy everything except what .dockerignore excludes.
COPY --chown=appuser:appuser . /app

# ── Persistent data directory ────────────────────────────────────────────────
# portfolio.json / session.json live here so user data survives container
# restarts when -v scanner-data:/app/data is used.
#
# IMPORTANT: chown /app itself (not just /app/data). WORKDIR /app above
# created the directory as root:root, and COPY --chown only chowns the
# files INSIDE /app, not /app itself. Without this, appuser can't create
# the /app/portfolio.json symlink at runtime → 'ln: Permission denied'.
RUN mkdir -p /app/data \
 && chown -R appuser:appuser /app /app/data

# Symlink the data files into /app/data on first run if they don't exist,
# so the app's hardcoded paths (APP_DIR/portfolio.json) still resolve.
# We do this in an ENTRYPOINT shim script.
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Streamlit default port
EXPOSE 8501

# Healthcheck — Streamlit exposes /_stcore/health on the same port.
# 5s startup, then every 30s; unhealthy after 3 consecutive failures.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${STREAMLIT_SERVER_PORT}/_stcore/health" || exit 1

# tini handles signal forwarding + zombie reaping.
ENTRYPOINT ["/usr/bin/tini", "--", "docker-entrypoint.sh"]

# Default command — run Streamlit.
# Flags mirror .streamlit/config.toml but are explicit so they apply even
# if the config file is missing or overridden.
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
