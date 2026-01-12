"""Configuration handler for LLM as Judge Proxy."""

import os
from typing import Optional
from pydantic import BaseModel, Field
import yaml
from dotenv import load_dotenv


class LLMJudgeConfig(BaseModel):
    """Configuration for LLM as Judge."""

    provider: str = Field(default="openai", description="LLM provider (openai, anthropic, google)")
    model: str = Field(default="gpt-4o-mini", description="Model name")
    api_key: Optional[str] = Field(default=None, description="API key for the LLM provider")
    temperature: float = Field(default=0.0, description="Temperature for LLM generation")
    max_tokens: int = Field(default=10, description="Maximum tokens for response")


class ProxyConfig(BaseModel):
    """Configuration for the proxy server."""

    host: str = Field(default="127.0.0.1", description="Proxy host")
    port: int = Field(default=8080, description="Proxy port")


class Config(BaseModel):
    """Main configuration."""

    llm_judge: LLMJudgeConfig = Field(default_factory=LLMJudgeConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key for proxied requests")


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file and environment variables.

    Args:
        config_path: Path to configuration file (YAML)

    Returns:
        Config object
    """
    load_dotenv()

    config_dict = {}

    # Load from YAML file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f) or {}

    # Override with environment variables
    if os.getenv('LLM_JUDGE_PROVIDER'):
        if 'llm_judge' not in config_dict:
            config_dict['llm_judge'] = {}
        config_dict['llm_judge']['provider'] = os.getenv('LLM_JUDGE_PROVIDER')

    if os.getenv('LLM_JUDGE_MODEL'):
        if 'llm_judge' not in config_dict:
            config_dict['llm_judge'] = {}
        config_dict['llm_judge']['model'] = os.getenv('LLM_JUDGE_MODEL')

    if os.getenv('LLM_JUDGE_API_KEY'):
        if 'llm_judge' not in config_dict:
            config_dict['llm_judge'] = {}
        config_dict['llm_judge']['api_key'] = os.getenv('LLM_JUDGE_API_KEY')

    if os.getenv('OPENAI_API_KEY'):
        config_dict['openai_api_key'] = os.getenv('OPENAI_API_KEY')

    if os.getenv('PROXY_HOST'):
        if 'proxy' not in config_dict:
            config_dict['proxy'] = {}
        config_dict['proxy']['host'] = os.getenv('PROXY_HOST')

    if os.getenv('PROXY_PORT'):
        if 'proxy' not in config_dict:
            config_dict['proxy'] = {}
        config_dict['proxy']['port'] = int(os.getenv('PROXY_PORT'))

    return Config(**config_dict)
