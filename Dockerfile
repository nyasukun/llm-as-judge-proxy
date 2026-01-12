FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY main.py .
COPY start_proxy.sh .

# Make scripts executable
RUN chmod +x start_proxy.sh main.py

# Expose proxy port
EXPOSE 8080

# Run proxy
CMD ["mitmdump", "-s", "src/proxy_addon.py", "--listen-host", "0.0.0.0", "--listen-port", "8080", "--set", "block_global=false"]
