# from openai import OpenAI
# import json

# # client = OpenAI(base_url="http://localhost:80/v1", api_key="dummy")
# client = OpenAI(
#     # base_url="http://ec2-18-237-85-14.us-west-2.compute.amazonaws.com/v1", 
#     # base_url="http://localhost:8080/v1", 
#     base_url="http://ec2-18-236-129-53.us-west-2.compute.amazonaws.com:80/v1", 
#     api_key="dummy"
# )

# def get_weather(location: str, unit: str):
#     return f"Getting the weather for {location} in {unit}..."
# tool_functions = {"get_weather": get_weather}

# tools = [{
#     "type": "function",
#     "function": {
#         "name": "get_weather",
#         "description": "Get the current weather in a given location",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "location": {"type": "string", "description": "City and state, e.g., 'San Francisco, CA'"},
#                 "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
#             },
#             "required": ["location", "unit"]
#         }
#     }
# }]

# response = client.chat.completions.create(
#     # model="GLM-Z1-9B-0414",
#     # model="GLM-4-9B-0414",
#     # model="UI-TARS-1.5-7B",
#     # model="gemma-3-27b-it",
#     # model="Qwen2.5-VL-72B-Instruct-AWQ",
#     # model="Qwen2.5-VL-72B-Instruct-AWQ",
#     # model="Qwen3-8B",
#     model="gpt-oss-20b",
#     # model="Qwen3-30B-A3B",
#     messages=[
#     {
#         "role": "system", 
#         "content": "You are a helpful assistant."
#     },
#     {
#         "role": "user", 
#         "content": "What's the weather like in San Francisco?"
#     },
#     # {
#     #     "role": "user", 
#     #     "content": "What's the weather like in San Francisco? unit is fahrenheit"
#     # }
#     ],
#     tools=tools,
#     # tool_choice="auto",
#     # tool_choice="get_weather",
#     # tool_choice="required",
#     max_completion_tokens=512,
#     extra_body = {"chat_template_kwargs": {"enable_thinking": False}},
#     stream=True
# )
# # print(response.choices[0].message)
# # tool_call = response.choices[0].message.tool_calls[0].function
# # print(f"Function called: {tool_call.name}")
# # print(f"Arguments: {tool_call.arguments}")
# # print(f"Result: {get_weather(**json.loads(tool_call.arguments))}")

# think_start = False
# for i in response:
#     # print(i)
#     reasoning_content = getattr(i.choices[0].delta,"reasoning_content",None)
#     content = i.choices[0].delta.content
#     if reasoning_content:
#         if not think_start:
#             print("Thinking...")
#             think_start = True
#         print(reasoning_content,end="")
#     if content is not None:
#         if think_start:
#             print("\nOutput: ")
#             think_start = False
#         print(content, end="")



# gptoss test

from openai import OpenAI
import json

# client = OpenAI(base_url="http://localhost:80/v1", api_key="dummy")
client = OpenAI(
    # base_url="http://ec2-18-237-85-14.us-west-2.compute.amazonaws.com/v1", 
    # base_url="http://localhost:8000/v1", 
    base_url="http://ec2-18-236-253-251.us-west-2.compute.amazonaws.com/v1", 
    # base_url="http://ec2-18-236-129-53.us-west-2.compute.amazonaws.com:80/v1", 
    api_key="dummy"
)

def get_weather(location: str, unit: str):
    return f"Getting the weather for {location} in {unit}..."
tool_functions = {"get_weather": get_weather}

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City and state, e.g., 'San Francisco, CA'"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location", "unit"]
        }
    }
}]

response = client.chat.completions.create(
    # model="GLM-Z1-9B-0414",
    # model="GLM-4-9B-0414",
    # model="UI-TARS-1.5-7B",
    # model="gemma-3-27b-it",
    # model="Qwen2.5-VL-72B-Instruct-AWQ",
    # model="Qwen2.5-VL-72B-Instruct-AWQ",
    # model="Qwen3-8B",
    # model="gpt-oss-20b",
    # model="openai/gpt-oss-20b",
    # model="qwen3-next",
    model="Qwen3-Coder-30B-A3B-Instruct",
    # model="Qwen3-30B-A3B",
    messages=[
    # {
    #     "role": "system", 
    #     "content": "You are a helpful assistant."
    # },
    {
        "role": "user", 
        "content": "What's the weather like in San Francisco?"
    },
    # {
    #     "role": "user", 
    #     "content": "What's the weather like in San Francisco? unit is fahrenheit"
    # }
    ],
    tools=tools,
    # tool_choice="auto",
    # tool_choice="get_weather",
    # tool_choice="required",
    max_completion_tokens=512,
    # reasoning_effort="high",
    stream=False
)
print(response.choices[0].message)
# tool_call = response.choices[0].message.tool_calls[0].function
# print(f"Function called: {tool_call.name}")
# print(f"Arguments: {tool_call.arguments}")
# print(f"Result: {get_weather(**json.loads(tool_call.arguments))}")

# think_start = False
# for i in response:
#     print(i)
#     reasoning_content = getattr(i.choices[0].delta,"reasoning_content",None)
#     content = i.choices[0].delta.content
#     if reasoning_content:
#         if not think_start:
#             print("Thinking...")
#             think_start = True
#         print(reasoning_content,end="")
#     if content is not None:
#         if think_start:
#             print("\nOutput: ")
#             think_start = False
#         print(content, end="")


# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "get_weather",
#             "description": "Get current weather in a given city",
#             "parameters": {
#                 "type": "object",
#                 "properties": {"city": {"type": "string"}},
#                 "required": ["city"]
#             },
#         },
#     }
# ]
 
# response = client.chat.completions.create(
#     # model="gpt-oss-20b",
#     model="openai/gpt-oss-20b",
#     messages=[{"role": "user", "content": "What's the weather in Berlin right now?"}],
#     tools=tools
# )
 
# print(response.choices[0].message)