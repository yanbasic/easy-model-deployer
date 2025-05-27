import json

import sys
sys.path.append("src/pipeline")
from emd.sdk.clients.sagemaker_client import SageMakerClient

request = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {
            "role": "assistant",
            "content": "The Los Angeles Dodgers won the World Series in 2020.",
        },
        {
            "role": "user",
            "content": "Where was it played? The answer should be as long as possible.",
        },
    ],
    "model": "Qwen/Qwen2-beta-7B-Chat",
    # "model": "Qwen/Qwen2.5-72B-Instruct-AWQ",
    # "model": "deepseek-ai/deepseek-llm-7b-chat",
    # "stream": False,
}

with open('/home/ubuntu/Project/easy-model-deployer/src/pipeline/backend/comfyui/ComfyUI_inpaint_bus_4_api.json') as f:
    workflow = json.load(f)
comfy_ui_request = {
    "workflow": workflow
}

if __name__ == "__main__":
    # Initialize clients
    invoke_vllm_sagemaker_client = SageMakerClient(
        region="us-east-1",
        # region="cn-north-1",
        # endpoint_name="Qwen-Qwen2-5-72B-Instruct-AWQ-vllm-2024-11-11-08-04-56",
        # endpoint_name="Qwen-Qwen2-5-72B-Instruct-AWQ-vllm-2024-11-15-06-11-08",
        endpoint_name="Qwen-Qwen2-beta-7B-Chat-vllm-2024-11-24-02-23-10",
        # endpoint_name="Qwen-Qwen2-beta-7B-Chat-vllm-2024-11-15-03-45-30",
        stream=True,
    )
    invoke_comfy_ui_sagemaker_client = SageMakerClient(
        name="comfyui",
        region="us-west-2",
        endpoint_name="txt2video-LTX-comfyui-2025-05-23-02-29-57",
    )

    # Test invoke
    # invoke_vllm_sagemaker_client.invoke(request)
    # invoke_vllm_ec2_client.invoke(request)
    invoke_comfy_ui_sagemaker_client.invoke_async(comfy_ui_request)

    # invoke_vllm_sagemaker_stream_client.invoke(request)
    # with open("src/invoke/workflow_api_animatediff.json") as f:
    #     prompt = json.load(f)
    #     invoke_comfy_ui_ec2_client.invoke(prompt)
