"""mitmproxy addon for LLM as Judge proxy."""

import json
import logging
from mitmproxy import http
from typing import Optional

from src.llm_judge import LLMJudge
from src.config import Config, load_config

logger = logging.getLogger(__name__)


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
        return "api.openai.com" in flow.request.pretty_host

    def _create_error_response(self, flow: http.HTTPFlow, message: str, status_code: int = 403):
        """Create an error response.

        Args:
            flow: HTTP flow
            message: Error message
            status_code: HTTP status code
        """
        error_body = {
            "error": {
                "message": message,
                "type": "safety_violation",
                "code": "content_policy_violation"
            }
        }

        flow.response = http.Response.make(
            status_code,
            json.dumps(error_body),
            {"Content-Type": "application/json"}
        )

    def request(self, flow: http.HTTPFlow) -> None:
        """Handle incoming requests.

        Args:
            flow: HTTP flow
        """
        # Only process OpenAI API requests
        if not self._is_openai_api_request(flow):
            return

        try:
            # Parse request body
            request_body = flow.request.content.decode('utf-8')
            request_data = json.loads(request_body)

            logger.info(f"Intercepted OpenAI API request to {flow.request.path}")
            logger.debug(f"Request data: {request_data}")

            # Evaluate request with LLM judge
            is_safe = self.judge.evaluate_sync(request_data)

            if not is_safe:
                logger.warning("Request blocked by LLM judge")
                self._create_error_response(
                    flow,
                    "Request content violates safety policy and has been blocked.",
                    403
                )
                return

            logger.info("Request passed LLM judge evaluation")

        except json.JSONDecodeError:
            logger.warning("Could not decode request body as JSON")
        except Exception as e:
            logger.error(f"Error processing request: {e}")

    def response(self, flow: http.HTTPFlow) -> None:
        """Handle responses.

        Args:
            flow: HTTP flow
        """
        # Only process OpenAI API responses
        if not self._is_openai_api_request(flow):
            return

        # Skip if request was already blocked
        if flow.response is None:
            return

        # Skip if there was an error in the request
        if flow.response.status_code >= 400:
            return

        try:
            # Parse response body
            response_body = flow.response.content.decode('utf-8')
            response_data = json.loads(response_body)

            logger.info(f"Intercepted OpenAI API response from {flow.request.path}")
            logger.debug(f"Response data: {response_data}")

            # Parse request data for context
            request_body = flow.request.content.decode('utf-8')
            request_data = json.loads(request_body)

            # Evaluate response with LLM judge
            is_safe = self.judge.evaluate_sync(request_data, response_data)

            if not is_safe:
                logger.warning("Response blocked by LLM judge")
                self._create_error_response(
                    flow,
                    "Response content violates safety policy and has been blocked.",
                    403
                )
                return

            logger.info("Response passed LLM judge evaluation")

        except json.JSONDecodeError:
            logger.warning("Could not decode response body as JSON")
        except Exception as e:
            logger.error(f"Error processing response: {e}")


# Entry point for mitmproxy
addons = [OpenAIJudgeAddon()]
