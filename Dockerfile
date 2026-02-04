FROM python:3.12-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

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

# Install Playwright system dependencies (requires root)
# Update apt cache first to ensure package availability
RUN apt-get update && \
    playwright install-deps chromium && \
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY --chown=automation:automation app/ app/
COPY --chown=automation:automation config/ config/
COPY --chown=automation:automation main.py .

# Switch to non-root user
USER automation

# Install Playwright browsers as non-root user (stores in user's home)
RUN playwright install chromium

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/automation

# Run the application
CMD ["python", "main.py"]
