from strands import Agent
from strands.models.openai import OpenAIModel
from strands_tools import calculator, current_time
import logging

model = OpenAIModel(
    client_args={
        "api_key": "xxx",
        "base_url": "http://localhost:8080/v1/",
    },
    # **model_config
    model_id="Qwen3-8B",
    params={
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
    }
)


agent = Agent(model=model, tools=[calculator, current_time])
response = agent("现在几点")
print(response)
