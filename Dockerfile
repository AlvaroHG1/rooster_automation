FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Create non-root user with home directory
RUN useradd -m -u 1000 -d /home/automation automation && \
    mkdir -p /app /app/shared /app/logs /app/config && \
    chown -R automation:automation /app /home/automation

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=automation:automation app/ app/
COPY --chown=automation:automation config/ config/
COPY --chown=automation:automation main.py .

# Switch to non-root user
USER automation

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/automation

# Run the application
CMD ["python", "main.py"]
