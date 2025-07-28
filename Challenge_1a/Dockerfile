# Adobe India Hackathon 2025 - Challenge 1a
# High-Performance PDF Processing Container
# Multi-stage build for optimal performance and size

# Build stage - Install dependencies and compile
FROM --platform=linux/amd64 python:3.10-slim as builder

# Set build arguments
ARG BUILDPLATFORM
ARG TARGETPLATFORM

# Install build dependencies for PyMuPDF compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Runtime stage - Minimal image for execution
FROM --platform=linux/amd64 python:3.10-slim

# Set metadata
LABEL maintainer="Adobe Hackathon Challenge 1a"
LABEL description="High-performance PDF to JSON converter"
LABEL version="1.0.0"

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Set working directory
WORKDIR /app

# Create app user for security (non-root)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create directories and set permissions
RUN mkdir -p /app/input /app/output && \
    chown -R appuser:appuser /app

# Copy application files
COPY process_pdfs.py /app/
COPY output_schema.json /app/

# Set file permissions
RUN chmod +x /app/process_pdfs.py && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables for optimization
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pymupdf; print('PyMuPDF OK')" || exit 1

# Default command
CMD ["python", "process_pdfs.py"]
