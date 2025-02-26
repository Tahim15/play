FROM python:3.10-slim

# Install required dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libappindicator3-1 \
    libnss3 \
    libxss1 \
    libasound2 \
    libgbm-dev \
    ca-certificates \
    fonts-liberation \
    libvulkan1 \
    xdg-utils \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxcomposite1 \
    libxrandr2 \
    libasound2 \
    libxtst6 && \
    rm -rf /var/lib/apt/lists/*

# Install Playwright and its dependencies
RUN pip install playwright
RUN python -m playwright install

# Set working directory
WORKDIR /usr/src/app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the application port
EXPOSE 8087

# Run the application
CMD ["python", "bot.py"]
