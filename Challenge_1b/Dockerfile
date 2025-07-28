# # ----------- builder -----------
FROM --platform=linux/amd64 python:3.10-slim AS builder

# Avoid interactive install prompts and speed up builds
ENV DEBIAN_FRONTEND=noninteractive

# Upgrade pip/wheel/setuptools first for modern projects
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc g++ libc6-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install Python dependencies into a virtualenv
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --default-timeout=120 --retries=20 -r requirements.txt

# ----------- runtime -----------
FROM --platform=linux/amd64 python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Copy preinstalled virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copy your app source code
COPY src/ ./src

# (Optional) Ensure src is a package for "python -m src.pipeline"
RUN [ -f src/_init.py ] || touch src/init_.py

ENTRYPOINT ["python", "-m", "src.pipeline"]