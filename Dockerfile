# Builder stage
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Enable bytecode compilation and copy mode
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy only dependency files first to leverage caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . .

# Install application
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Clean up unnecessary files to reduce image size
RUN find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /app -type f -name "*.pyc" -delete \
    && find /app -type f -name "*.pyo" -delete \
    && find /app -type f -name ".DS_Store" -delete \
    && find /app -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Final stage
FROM python:3.13-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Create non-root user for security
RUN addgroup --system --gid 1001 appuser \
    && adduser --system --uid 1001 --gid 1001 --disabled-password appuser

# TODO: Hardcoding passwords can be a security risk. Use Docker secrets or environment variables.

# Set working directory
WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder --chown=appuser:appuser /app /app

# CREATE THE UPLOAD FOLDER HERE - after copying files but before switching user
RUN mkdir -p /app/memo_uploads && chown appuser:appuser /app/memo_uploads

# Switch to non-root user
USER appuser

# Run the FastAPI application by default
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]