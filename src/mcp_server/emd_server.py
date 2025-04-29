#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from typing import Optional, Dict, Any, List, Union

import httpx
from mcp.server.fastmcp import FastMCP

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
print(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
from emd.sdk.status import get_model_status as emd_get_model_status
from emd.sdk.invoke.conversation_invoker import ConversationInvoker as EMDConversationInvoker
from emd.sdk.deploy import deploy as emd_deploy
from emd.models import Model as EMDModel

# Initialize FastMCP server
mcp = FastMCP("emd")

# Constants
USER_AGENT = "emd-app/1.0"

@mcp.tool()
async def invoke_model(model_id: str, model_tag: str, user_message: str) -> str:
    """Invokes a model with the given user message.
    Args:
        model_id: Model ID (e.g. Qwen2.5-0.5B-Instruct)
        model_tag: Model tag (e.g. dev)
        user_message: User message to send to the model
    """
    invoker = EMDConversationInvoker(model_id, model_tag)
    invoker.add_user_message(user_message)
    ret = invoker.invoke(stream=False)
    return ret

@mcp.tool()
async def list_models() -> List[str]:
    """Lists all available models."""
    return EMDModel.get_supported_models()

@mcp.tool()
async def deploy_model(model_id: str, model_tag: str, instance_type="g5.4xlarge",
                      engine_type="vllm", service_type="sagemaker_realtime") -> str:
    """Deploys a model with the given model ID and tag.
    Args:
        model_id: Model ID (e.g. Qwen2.5-0.5B-Instruct)
        model_tag: Model tag (e.g. dev)
        instance_type: Instance type (e.g. g5.4xlarge)
        engine_type: Engine type (e.g. vllm)
        service_type: Service type (e.g. sagemaker_realtime)
    """
    return emd_deploy(model_id=model_id, model_tag=model_tag,
                      instance_type=instance_type, engine_type=engine_type,
                      service_type=service_type)

@mcp.tool()
async def get_model_status(model_id: Optional[str] = "", model_tag: str = "dev") -> List[str]:
    """Gets the status of a model. If model_id is empty, it returns the status of all models.
    Args:
        model_id: Model ID (e.g. Qwen2.5-0.5B-Instruct) or empty for all models
        model_tag: Model tag (e.g. dev)
    """
    # When model_id is empty string, pass None to the underlying function
    actual_model_id = None if not model_id else model_id
    return emd_get_model_status(model_id=actual_model_id, model_tag=model_tag)

def test_tools():
    import asyncio
    """Test the invoke_model function."""
    model_id = "Qwen2.5-0.5B-Instruct"
    model_tag = "dev2"
    user_message = "What is the weather like in New York?"
    # Get supported models
    models = asyncio.run(list_models())
    print(f"Available models: {models}")

    # Deploy a model
    deploy_result = asyncio.run(deploy_model(model_id=model_id, model_tag=model_tag))
    print(f"Deploy result: {deploy_result}")

    # Get the model status
    status = asyncio.run(get_model_status(model_id=model_id, model_tag=model_tag))
    print(f"Model status: {status}")
    
    # Call the invoke_model function
    result = asyncio.run(invoke_model(model_id=model_id, model_tag=model_tag, user_message=user_message))
    print(f"Model response: {result}")

if __name__ == "__main__":
    # test_tools()
    # Initialize and run the server
    mcp.run(transport='stdio')