# Use official Python slim image
FROM python:3.10-slim

# Install system dependencies required for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl xvfb libxi6 libgconf-2-4 libappindicator3-1 libnss3 \
    libxss1 libasound2 libgbm-dev ca-certificates fonts-liberation \
    libvulkan1 xdg-utils libatk-bridge2.0-0 libgtk-3-0 libxcomposite1 \
    libxrandr2 libasound2 libxtst6 libu2f-udev libdrm2 && \
    rm -rf /var/lib/apt/lists/*

# Install Playwright and browsers
RUN pip install --no-cache-dir playwright && \
    python -m playwright install --with-deps

# Set working directory
WORKDIR /usr/src/app

# Copy dependencies file first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the application port (if needed)
EXPOSE 8087

# Run the application
CMD ["python", "bot.py"]
