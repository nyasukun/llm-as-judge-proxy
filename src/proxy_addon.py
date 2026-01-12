"""mitmproxy addon for LLM as Judge proxy."""

import json
import logging
from mitmproxy import http
from typing import Optional, Dict, Any

from src.llm_judge import LLMJudge
from src.config import Config, load_config

logger = logging.getLogger(__name__)

# Constants
OPENAI_API_HOST = "api.openai.com"
ERROR_TYPE_SAFETY = "safety_violation"
ERROR_CODE_POLICY = "content_policy_violation"


class OpenAIJudgeAddon:
    """mitmproxy addon that judges OpenAI API requests and responses."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the addon.

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.judge = LLMJudge(self.config.llm_judge)
        logger.info(f"Initialized OpenAI Judge Addon with {self.config.llm_judge.provider} provider")

    def _is_openai_api_request(self, flow: http.HTTPFlow) -> bool:
        """Check if the request is to OpenAI API.

        Args:
            flow: HTTP flow

        Returns:
            True if request is to OpenAI API
        """
        return OPENAI_API_HOST in flow.request.pretty_host

    def _parse_json_content(self, content: bytes, label: str) -> Optional[Dict[str, Any]]:
        """Parse JSON content from bytes.

        Args:
            content: Raw bytes content
            label: Label for logging (e.g., "request", "response")

        Returns:
            Parsed JSON dict or None if parsing fails
        """
        try:
            content_str = content.decode('utf-8')
            return json.loads(content_str)
        except json.JSONDecodeError:
            logger.warning(f"Could not decode {label} body as JSON")
            return None
        except Exception as e:
            logger.error(f"Error parsing {label} JSON: {e}")
            return None

    def _create_error_response(self, flow: http.HTTPFlow, message: str, status_code: int = 403) -> None:
        """Create an error response for blocked content.

        Args:
            flow: HTTP flow
            message: Error message
            status_code: HTTP status code (default: 403)
        """
        error_body = {
            "error": {
                "message": message,
                "type": ERROR_TYPE_SAFETY,
                "code": ERROR_CODE_POLICY
            }
        }

        flow.response = http.Response.make(
            status_code,
            json.dumps(error_body),
            {"Content-Type": "application/json"}
        )

    def request(self, flow: http.HTTPFlow) -> None:
        """Handle incoming requests and evaluate safety.

        Args:
            flow: HTTP flow
        """
        if not self._is_openai_api_request(flow):
            return

        request_data = self._parse_json_content(flow.request.content, "request")
        if not request_data:
            return

        try:
            logger.info(f"Intercepted OpenAI API request to {flow.request.path}")
            logger.debug(f"Request data: {request_data}")

            is_safe = self.judge.evaluate_sync(request_data)

            if not is_safe:
                logger.warning("Request blocked by LLM judge")
                self._create_error_response(
                    flow,
                    "Request content violates safety policy and has been blocked."
                )
            else:
                logger.info("Request passed LLM judge evaluation")

        except Exception as e:
            logger.error(f"Error evaluating request: {e}")

    def response(self, flow: http.HTTPFlow) -> None:
        """Handle responses and evaluate safety.

        Args:
            flow: HTTP flow
        """
        if not self._is_openai_api_request(flow):
            return

        # Skip if request was already blocked or resulted in error
        if flow.response is None or flow.response.status_code >= 400:
            return

        response_data = self._parse_json_content(flow.response.content, "response")
        request_data = self._parse_json_content(flow.request.content, "request")

        if not response_data or not request_data:
            return

        try:
            logger.info(f"Intercepted OpenAI API response from {flow.request.path}")
            logger.debug(f"Response data: {response_data}")

            is_safe = self.judge.evaluate_sync(request_data, response_data)

            if not is_safe:
                logger.warning("Response blocked by LLM judge")
                self._create_error_response(
                    flow,
                    "Response content violates safety policy and has been blocked."
                )
            else:
                logger.info("Response passed LLM judge evaluation")

        except Exception as e:
            logger.error(f"Error evaluating response: {e}")


# Entry point for mitmproxy
addons = [OpenAIJudgeAddon()]
