import httpx
import sys
import os
from emd.models.utils.constants import ModelType
import inspect
from backend.backend import OpenAICompitableProxyBackendBase
from emd.utils.logger_utils import get_logger

logger = get_logger(__name__)

class HiggsAudioBackend(OpenAICompitableProxyBackendBase):
    """
    Higgs Audio Backend that uses the Docker image's native entrypoint
    instead of the standard vLLM serve command.

    This backend is specifically designed for the Higgs Audio v2 Generation 3B Base model
    which provides its own API server via the pre-built Docker image with entrypoint:
    ["python3", "-m", "vllm.entrypoints.bosonai.api_server"]
    """

    def before_start(self,model_dir=None):
        logger.info(f"before_startbefore_startbefore_startbefore_startbefore_start")

    def create_proxy_server_start_command(self, model_path):
        return f'python3 -m vllm.entrypoints.bosonai.api_server --served-model-name higgs-audio-v2-generation-3B-base --model bosonai/higgs-audio-v2-generation-3B-base --audio-tokenizer-type bosonai/higgs-audio-v2-tokenizer --limit-mm-per-prompt audio=50 --max-model-len 8192 --tensor-parallel-size 8 --pipeline-parallel-size 1 --port 8000 --gpu-memory-utilization 0.65 --disable-mm-preprocessor-cache'

    def openai_create_helper(self, fn: callable, request: dict):
        """
        Helper method to handle OpenAI-compatible API calls with extra parameters.
        """
        sig = inspect.signature(fn)
        extra_body = request.get("extra_body", {})
        extra_params = {k: request.pop(k) for k in list(request.keys()) if k not in sig.parameters}
        extra_body.update(extra_params)
        request['extra_body'] = extra_body
        return fn(**request)

    def invoke(self, request):
        """
        Invoke the Higgs Audio model with OpenAI-compatible API.
        Supports audio modalities for voice cloning, smart voice generation, and multi-speaker synthesis.
        """
        # Transform input to Higgs Audio format
        request = self._transform_request(request)

        logger.info(f"Higgs Audio request: {request}")

        # Handle different model types - Higgs Audio is primarily for audio generation
        if self.model_type == ModelType.AUDIO:
            # Use chat completions endpoint for audio generation
            response = self.openai_create_helper(self.client.chat.completions.create, request)
        else:
            # Fallback to standard chat completions
            response = self.openai_create_helper(self.client.chat.completions.create, request)

        logger.info(f"Higgs Audio response: {response}, request: {request}")

        if request.get("stream", False):
            return self._transform_streaming_response(response)
        else:
            return self._transform_response(response)

    async def ainvoke(self, request):
        """
        Async invoke the Higgs Audio model with OpenAI-compatible API.
        """
        # Transform input to Higgs Audio format
        request = self._transform_request(request)

        logger.info(f"Higgs Audio async request: {request}")

        # Handle different model types - Higgs Audio is primarily for audio generation
        if self.model_type == ModelType.AUDIO:
            # Use chat completions endpoint for audio generation
            response = await self.openai_create_helper(self.async_client.chat.completions.create, request)
        else:
            # Fallback to standard chat completions
            response = await self.openai_create_helper(self.async_client.chat.completions.create, request)

        logger.info(f"Higgs Audio async response: {response}, request: {request}")

        if request.get("stream", False):
            logger.info(f"Higgs Audio streaming response: {response}")
            return await self._atransform_streaming_response(response)
        else:
            return await self._atransform_response(response)
