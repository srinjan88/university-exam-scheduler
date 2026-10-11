# =============================================================================
# Dockerfile: University Examination Scheduler
# Target: Free Web Service on Render (Linux Container)
# =============================================================================

# 1. Base Image: Official lightweight Python slim image
FROM python:3.11-slim

# 2. Environment Variables:
# - PYTHONDONTWRITEBYTECODE: Disables creation of .pyc files
# - PYTHONUNBUFFERED: Flushes stdout/stderr immediately to container logs
# - PORT: Default port (Render injects $PORT at runtime, typically 10000)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

# 3. Install GCC and standard C build tools required for compiling the C engine
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Set application working directory
WORKDIR /app

# 5. Install Python dependencies (Flask, Gunicorn) first to leverage Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 6. Copy application code (c_engine, backend, frontend, tests)
COPY . /app

# 7. Compile the standalone C scheduling engine using GCC inside the container
#    Generates the native Linux ELF executable 'c_engine/scheduler' and grants execute permission
RUN gcc -std=c11 -Wall -Wextra -O2 c_engine/scheduler.c -o c_engine/scheduler \
    && chmod +x c_engine/scheduler

# 8. Create a non-root system user for security compliance
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 9. Expose port for documentation (Render routes external HTTP traffic to $PORT)
EXPOSE 10000

# 10. Start production WSGI server using Gunicorn
#     - Uses shell expansion so the runtime $PORT environment variable set by Render is respected
#     - Uses 2 workers with 4 threads per worker for responsive request handling
#     - Binds to 0.0.0.0
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 --timeout 60 backend.app:app"]

