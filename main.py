#!/usr/bin/env python3
"""Main entry point for LLM as Judge Proxy."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("LLM as Judge Proxy")
    print("==================")
    print()
    print("To start the proxy, run:")
    print("  mitmproxy -s src/proxy_addon.py --listen-host 127.0.0.1 --listen-port 8080")
    print()
    print("Or use mitmdump for headless mode:")
    print("  mitmdump -s src/proxy_addon.py --listen-host 127.0.0.1 --listen-port 8080")
    print()
    print("Configure your OpenAI client to use the proxy:")
    print("  HTTP_PROXY=http://127.0.0.1:8080 python your_script.py")
    print()
    print("See README.md for more details.")
