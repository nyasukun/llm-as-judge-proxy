#!/bin/bash
# Start LLM as Judge Proxy

echo "Starting LLM as Judge Proxy..."
echo "================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Using environment variables."
    echo "Copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo ""
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if required variables are set
if [ -z "$LLM_JUDGE_API_KEY" ]; then
    echo "Error: LLM_JUDGE_API_KEY not set"
    exit 1
fi

# Start proxy
echo "Starting proxy on ${PROXY_HOST:-127.0.0.1}:${PROXY_PORT:-8080}..."
echo "LLM Judge: ${LLM_JUDGE_PROVIDER:-openai}/${LLM_JUDGE_MODEL:-gpt-4o-mini}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

mitmdump -s src/proxy_addon.py \
    --listen-host "${PROXY_HOST:-127.0.0.1}" \
    --listen-port "${PROXY_PORT:-8080}" \
    --set block_global=false
