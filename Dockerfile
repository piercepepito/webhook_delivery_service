FROM python:3.13-slim

# PYTHONUNBUFFERED keeps logs flowing to `docker logs` immediately instead of
# sitting in a buffer. PYTHONDONTWRITEBYTECODE avoids .pyc clutter in the image.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencies first. This layer is cached and only rebuilds when
# requirements.txt changes -- not on every source edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create the runtime user before copying source so ownership can be set as we copy.
# Running as root is a standard security finding.
RUN useradd --create-home --uid 1000 appuser

# Source last: it changes on every edit, and this layer is cheap to rebuild.
COPY --chown=appuser:appuser . .

USER appuser

# Documentation only -- this does not publish the port. Compose's `ports:` does.
EXPOSE 8000

# Exec form (JSON array), so uvicorn is PID 1 and receives SIGTERM directly.
# --host 0.0.0.0 is required: bound to 127.0.0.1 the app would only listen
# inside the container and be unreachable from the host.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
