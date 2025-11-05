import openai

# 替换为你的 OpenAI API 密钥
api_key = "your_openai_api_key"

def chat_with_openai_stream(prompt):
    client = openai.OpenAI(
        api_key=api_key,
        # base_url="http://127.0.0.1:8080/v1"
        # base_url="http://127.0.0.1:8080/v1"
        base_url="http://ec2-18-236-253-251.us-west-2.compute.amazonaws.com/v1"
    )

    response = client.chat.completions.create(
        # model="DeepSeek-R1-Distill-Qwen-1.5B",
        # model="Qwen2.5-72B-Instruct-AWQ",
        # model="QwQ-32B",
        model="Qwen3-Coder-30B-A3B-Instruct",
        # model="Qwen2.5-1.5B-Instruct",
        messages=[
            # {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
        # {"role": "assistant", "content": "<think>\n"}
        ],
        stream=True,
        temperature=0.7
    )

    print("AI: ", end="", flush=True)
    # print(response)
    for chunk in response:
        # print(chunk)
        # print(sfbdfb)
        # print(type(chunk))
        content = chunk.choices[0].delta.content
        think = getattr(chunk.choices[0].delta,"reasoning_content",None)
        if think is not None:
            print(think,end="",flush=True)
        else:
            print(content, end="", flush=True)
        # if chunk.choices[0].delta.content, end="", flush=True
        # print(chunk)
        # if "choices" in chunk and len(chunk["choices"]) > 0:
        #     delta = chunk["choices"][0]["delta"]
        #     if "content" in delta:
        #         print(delta["content"], end="", flush=True)

    print("\n")  # 打印换行


def chat_with_openai_stream_with_tool_call(prompt):
    client = openai.OpenAI(
        api_key=api_key,
        # base_url="http://127.0.0.1:8080/v1"
        # base_url="http://127.0.0.1:8080/v1"
        base_url="http://ec2-18-236-253-251.us-west-2.compute.amazonaws.com/v1"
    )
    tools=[
    {
        "type":"function",
        "function":{
            "name": "square_the_number",
            "description": "output the square of the number.",
            "parameters": {
                "type": "object",
                "required": ["input_num"],
                "properties": {
                    'input_num': {
                        'type': 'number', 
                        'description': 'input_num is a number that will be squared'
                        }
                },
            }
        }
    }
]

    response = client.chat.completions.create(
        # model="DeepSeek-R1-Distill-Qwen-1.5B",
        # model="Qwen2.5-72B-Instruct-AWQ",
        # model="QwQ-32B",
        model="Qwen3-Coder-30B-A3B-Instruct",
        tools=tools,
        # model="Qwen2.5-1.5B-Instruct",
        messages=[
            # {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
        # {"role": "assistant", "content": "<think>\n"}
        ],
        stream=True,
        temperature=0.7
    )

    print("AI: ", end="", flush=True)
    # print(response)
    for chunk in response:
        # print(chunk)
        # print(sfbdfb)
        # print(type(chunk))
        content = chunk.choices[0].delta.content
        think = getattr(chunk.choices[0].delta,"reasoning_content",None)
        if think is not None:
            print(think,end="",flush=True)
        else:
            print(content, end="", flush=True)
        # if chunk.choices[0].delta.content, end="", flush=True
        # print(chunk)
        # if "choices" in chunk and len(chunk["choices"]) > 0:
        #     delta = chunk["choices"][0]["delta"]
        #     if "content" in delta:
        #         print(delta["content"], end="", flush=True)

    print("\n")  # 打印换行


def chat_with_openai(prompt):
    client = openai.OpenAI(
        api_key=api_key,
        base_url="http://127.0.0.1:9000/v1"
    )

    response = client.chat.completions.create(
        model="DeepSeek-R1-Distill-Qwen-1.5B",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
        stream=False
    )

    print(response)
# 测试调用
# chat_with_openai_stream("9.11和9.9哪个更大？")
# chat_with_openai_stream("你好")
# chat_with_openai_stream("Write a quick sort algorithm.")
chat_with_openai_stream_with_tool_call("请计算16的平方。")
# chat_with_openai("你好")
