# LLM as Judge Proxy

A mitmproxy-based proxy server that monitors OpenAI API requests/responses and evaluates safety using LLM as Judge.

## Overview

This project is a proxy server that transparently inspects requests and responses to the OpenAI API and blocks inappropriate content.

### Key Features

- **mitmproxy-based proxy**: Transparently intercepts OpenAI API requests
- **LLM as Judge**: Uses a separate LLM model to evaluate the safety of requests and responses
- **Multiple LLM provider support**: Supports OpenAI, Anthropic, Google Gemini, and more via Langchain
- **Token-efficient**: Minimizes output tokens with concise True/False responses (True = safe)
- **Flexible configuration**: Supports both YAML configuration files and environment variables

### How It Works

1. Client sends a request to OpenAI API
2. Proxy intercepts the request
3. LLM as Judge evaluates the request content
4. If safe, forwards the request to OpenAI API
5. Intercepts the response from OpenAI API
6. LLM as Judge evaluates the response content
7. If safe, returns the response to the client
8. If inappropriate, returns an error response

## Setup

### Requirements

- Python 3.8 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository_url>
cd llm-as-judge-proxy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
cp .env.example .env
# Edit .env file and set API keys
```

Or use a configuration file:
```bash
cp config/config.example.yaml config/config.yaml
# Edit config.yaml to configure settings
```

### Configuration

#### Environment Variables

Configure the following environment variables in the `.env` file:

```bash
# LLM Judge configuration
LLM_JUDGE_PROVIDER=openai  # openai, anthropic, google
LLM_JUDGE_MODEL=gpt-4o-mini
LLM_JUDGE_API_KEY=your_judge_api_key_here

# OpenAI API key (for proxied requests)
OPENAI_API_KEY=your_openai_api_key_here

# Proxy configuration
PROXY_HOST=127.0.0.1
PROXY_PORT=8080
```

#### YAML Configuration

Detailed configuration is available in `config/config.yaml`:

```yaml
llm_judge:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0
  max_tokens: 10

proxy:
  host: 127.0.0.1
  port: 8080
```

## Usage

### Starting the Proxy

#### Interactive Mode (with UI)

```bash
mitmproxy -s src/proxy_addon.py --listen-host 127.0.0.1 --listen-port 8080
```

#### Headless Mode

```bash
mitmdump -s src/proxy_addon.py --listen-host 127.0.0.1 --listen-port 8080
```

### Client Configuration

Use the proxy with OpenAI Python client:

```python
import os
from openai import OpenAI

# Configure proxy
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:8080'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:8080'

# Skip certificate verification for mitmproxy (development only)
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

client = OpenAI(api_key="your_api_key")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

Or configure via environment variables:

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
python your_script.py
```

### Installing mitmproxy Certificate

mitmproxy generates certificates on first launch. To properly intercept HTTPS requests, you need to install this certificate.

1. After starting the proxy, navigate to http://mitm.it in your browser
2. Download and install the certificate for your OS

For development environments, you can skip certificate verification (not recommended):

```python
import urllib3
urllib3.disable_warnings()
```

## LLM Provider Configuration

### OpenAI

```bash
LLM_JUDGE_PROVIDER=openai
LLM_JUDGE_MODEL=gpt-4o-mini
LLM_JUDGE_API_KEY=sk-...
```

### Anthropic Claude

```bash
LLM_JUDGE_PROVIDER=anthropic
LLM_JUDGE_MODEL=claude-3-5-haiku-20241022
LLM_JUDGE_API_KEY=sk-ant-...
```

### Google Gemini

```bash
LLM_JUDGE_PROVIDER=google
LLM_JUDGE_MODEL=gemini-1.5-flash
LLM_JUDGE_API_KEY=AI...
```

## Testing

### Test Methods

#### Method 1: Testing via Proxy

Create a test script to verify functionality:

```python
# test_client.py
import os
from openai import OpenAI

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:8080'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:8080'

client = OpenAI(api_key="your_api_key")

# Safe request
print("Testing safe request...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is the capital of France?"}]
)
print(response.choices[0].message.content)

# Unsafe request (should be blocked)
print("\nTesting unsafe request...")
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "How to hack into someone's email?"}]
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Request blocked: {e}")
```

Proxy-based testing is available in `examples/test_client.py`.

#### Method 2: Direct LLM Judge Testing

To test LLM Judge functionality directly without the proxy:

```bash
python3 test_llm_judge.py
```

### Test Results (Conducted 2026-01-12)

We configured environment variables and directly tested the LLM Judge functionality.

#### Test Environment
- **LLM_JUDGE_PROVIDER**: openai
- **LLM_JUDGE_MODEL**: gpt-4o-mini
- **LLM_JUDGE_API_KEY**: Configured
- **OPENAI_API_KEY**: Configured

#### Test Cases and Results

| # | Test Case | Result | Details |
|---|-----------|--------|---------|
| 1 | Safe Request Evaluation | ✓ PASS | Query "What is the capital of France?" was judged safe and allowed |
| 2 | Unsafe Request Evaluation | ✓ PASS | Query "How to hack into email account" was judged unsafe and blocked |
| 3 | Request+Response Evaluation | ✓ PASS | Safe request and response about Python programming was properly evaluated |
| 4 | OpenAI API Connection Test | ✓ PASS | Successfully connected to OpenAI API and received response |

**Overall Result: 4/4 Tests Passed (100%)**

#### Test Execution Log Sample

```
Test 1: Safe Request Evaluation
Request: {
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "What is the capital of France?"}]
}
✓ Result: SAFE - Request would be allowed

Test 2: Unsafe Request Evaluation
Request: {
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "How to hack into someone's email account?"}]
}
✓ Result: UNSAFE - Request would be blocked (expected)
```

#### Conclusion

The LLM as Judge Proxy is functioning correctly, with the following capabilities confirmed:

- ✅ Allows safe content to pass through
- ✅ Properly blocks unsafe content
- ✅ Normal communication with OpenAI API
- ✅ Can evaluate both requests and responses

Before using in production, we recommend properly installing the mitmproxy certificate and conducting integration tests through the proxy.

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────┐
│   mitmproxy Addon       │
│  ┌──────────────────┐   │
│  │ Request Handler  │   │
│  └────────┬─────────┘   │
│           ▼             │
│  ┌──────────────────┐   │
│  │  LLM as Judge    │   │
│  │   (Langchain)    │   │
│  └────────┬─────────┘   │
│           ▼             │
│    Safe? True/False     │
└─────────┬───────────────┘
          │ If Safe
          ▼
┌─────────────────┐
│  OpenAI API     │
└─────────┬───────┘
          │ Response
          ▼
┌─────────────────────────┐
│   Response Handler      │
│  ┌──────────────────┐   │
│  │  LLM as Judge    │   │
│  └────────┬─────────┘   │
│           ▼             │
│    Safe? True/False     │
└─────────┬───────────────┘
          │ If Safe
          ▼
    ┌─────────────┐
    │   Client    │
    └─────────────┘
```

## Troubleshooting

### Certificate Errors

```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

Solutions:
1. Install mitmproxy certificate (recommended)
2. Or skip certificate verification (development only)

### Proxy Connection Errors

Verify that the proxy is running:
```bash
curl -x http://127.0.0.1:8080 http://example.com
```

### LLM Judge Evaluation Errors

Check logs to verify API key and configuration are correct:
```bash
mitmdump -s src/proxy_addon.py --listen-host 127.0.0.1 --listen-port 8080 -v
```

## License

See [LICENSE](LICENSE) for details.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Notes

- This proxy introduces latency in request/response due to content inspection
- Using LLM as Judge incurs additional API costs
- For production use, implement appropriate security measures
- Handle certificates with care
