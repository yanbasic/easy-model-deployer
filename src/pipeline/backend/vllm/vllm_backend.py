import httpx
import sys
import os
from emd.models.utils.constants import ModelType
import inspect
from backend.backend import OpenAICompitableProxyBackendBase
from emd.utils.logger_utils import get_logger

logger = get_logger(__name__)

class VLLMBackend(OpenAICompitableProxyBackendBase):

    def create_proxy_server_start_command(self,model_path):
        # os.system(f"{sys.executable} -m pip list")
        serve_command = f'vllm serve {model_path} --port {self.server_port} --trust-remote-code --served-model-name={self.model_id} --tensor_parallel_size={self.gpu_num} {self.default_cli_args} {self.cli_args}'
        if self.environment_variables:
            serve_command = f'{self.environment_variables} && {serve_command}'

        if self.model_type == ModelType.RERANK:
            serve_command += " --task score"
        if self.api_key:
            serve_command += f" --api-key {self.api_key}"
        return serve_command

    def openai_create_helper(self,fn:callable,request:dict):
        sig = inspect.signature(fn)
        extra_body = request.get("extra_body",{})
        extra_params = {k:request.pop(k) for k in list(request.keys()) if k not in sig.parameters}
        extra_body.update(extra_params)
        request['extra_body'] = extra_body
        return fn(**request)

    def invoke(self, request):
        # Transform input to vllm format
        request = self._transform_request(request)
        # Invoke vllm
        logger.info(f"Chat request:{request}")
        if self.model_type == ModelType.EMBEDDING:
            # print('cal embedding....')
            response =self.openai_create_helper(self.client.embeddings.create,request)
            # print('end cal embedding....')
        elif self.model_type == ModelType.RERANK:
            headers = {
                "accept": "application/json",
                "Accept-Type": "application/json",
            }
            response = httpx.post(
                f'{self.base_url}/rerank',
                json=request,
                headers=headers
            ).json()
        else:
            # response = self.client.chat.completions.create(**request)
            response = self.openai_create_helper(self.client.chat.completions.create,request)
        logger.info(f"response:{response},{request}")

        if request.get("stream", False):
            return self._transform_streaming_response(response)
        else:
            return self._transform_response(response)

    async def ainvoke(self, request):
        # Transform input to vllm format
        request = self._transform_request(request)
        # Invoke vllm
        logger.info(f"Chat request:{request}")
        if self.model_type == ModelType.EMBEDDING:
            # print('cal embedding....')
            response = await self.openai_create_helper(self.async_client.embeddings.create,request)
            # print('end cal embedding....')
        elif self.model_type == ModelType.RERANK:
            headers = {
                "accept": "application/json",
                "Accept-Type": "application/json",
            }
            response = httpx.post(
                f'{self.base_url}/rerank',
                json=request,
                headers=headers
            ).json()
        else:
            response = await self.openai_create_helper(
                self.async_client.chat.completions.create,
                request
            )
        logger.info(f"response:{response},{request}")

        if request.get("stream", False):
            logger.info(f"engine streaming response {response}")
            return await self._atransform_streaming_response(response)
        else:
            return await self._atransform_response(response)
