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


def _set_nested_config(config_dict: dict, section: str, key: str, value: any) -> None:
    """Helper function to set nested configuration values.

    Args:
        config_dict: Configuration dictionary
        section: Section name (e.g., 'llm_judge', 'proxy')
        key: Configuration key
        value: Configuration value
    """
    if section not in config_dict:
        config_dict[section] = {}
    config_dict[section][key] = value


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file and environment variables.

    Environment variables take precedence over configuration file values.

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
    # LLM Judge configuration
    env_mappings = [
        ('LLM_JUDGE_PROVIDER', 'llm_judge', 'provider', str),
        ('LLM_JUDGE_MODEL', 'llm_judge', 'model', str),
        ('LLM_JUDGE_API_KEY', 'llm_judge', 'api_key', str),
        ('PROXY_HOST', 'proxy', 'host', str),
        ('PROXY_PORT', 'proxy', 'port', int),
    ]

    for env_var, section, key, type_converter in env_mappings:
        value = os.getenv(env_var)
        if value:
            _set_nested_config(config_dict, section, key, type_converter(value))

    # Top-level configuration
    if os.getenv('OPENAI_API_KEY'):
        config_dict['openai_api_key'] = os.getenv('OPENAI_API_KEY')

    return Config(**config_dict)
