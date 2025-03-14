from batch_deploy_test import (
    Task,
    test_one_task
)


tasks = [
        {
            "deploy_config":{
                "model_id": "Qwen2.5-0.5B-Instruct",
                "instance_type":"g5.2xlarge",
                "engine_type":"vllm",
                "service_type":"sagemaker",
                "framework_type":"fastapi",
                "model_tag":"batch_test"
            },
            "invoke_config":{
                "pyloads":[{
                    "messages": [
                        {
                            "role": "user",
                            "content": "Explain async programming in Python"
                        }
                    ]
                }],
            }
        },
        {
            "deploy_config":{
                "model_id": "Qwen2.5-1.5B-Instruct",
                "instance_type":"g5.2xlarge",
                "engine_type":"vllm",
                "service_type":"sagemaker",
                "framework_type":"fastapi",
                "model_tag":"batch_test"
            },
            "invoke_config":{
                "pyloads":[{
                    "messages": [
                        {
                            "role": "user",
                            "content": "Explain async programming in Python"
                        }
                    ]
                }],
            }
        },
        {
            "deploy_config":{
                "model_id": "Qwen2.5-7B-Instruct",
                "instance_type":"g5.12xlarge",
                "engine_type":"vllm",
                "service_type":"sagemaker",
                "framework_type":"fastapi",
                "model_tag":"batch_test"
            },
            "invoke_config":{
                "pyloads":[{
                    "messages": [
                        {
                            "role": "user",
                            "content": "Explain async programming in Python"
                        }
                    ]
                }],
            }
        },
        {
            "deploy_config":{
                "model_id": "Qwen2.5-32B-Instruct",
                "instance_type":"g5.12xlarge",
                "engine_type":"vllm",
                "service_type":"sagemaker",
                "framework_type":"fastapi",
                "model_tag":"batch_test"
            },
            "invoke_config":{
                "pyloads":[{
                    "messages": [
                        {
                            "role": "user",
                            "content": "Explain async programming in Python"
                        }
                    ]
                }],
            }
        },
        {
            "deploy_config":{
                "model_id": "Qwen2.5-32B-Instruct",
                "instance_type":"g5.12xlarge",
                "engine_type":"vllm",
                "service_type":"sagemaker",
                "framework_type":"fastapi",
                "model_tag":"batch_test"
            },
            "invoke_config":{
                "pyloads":[{
                    "messages": [
                        {
                            "role": "user",
                            "content": "Explain async programming in Python"
                        }
                    ]
                }],
            }
        },
        {
            "deploy_config":{
                "model_id": "Qwen2.5-72B-Instruct",
                "instance_type":"g5.48xlarge",
                "engine_type":"vllm",
                "service_type":"sagemaker",
                "framework_type":"fastapi",
                "model_tag":"batch_test"
            },
            "invoke_config":{
                "pyloads":[{
                    "messages": [
                        {
                            "role": "user",
                            "content": "Explain async programming in Python"
                        }
                    ]
                }],
            }
        },
        {
            "deploy_config":{
                "model_id": "Qwen2.5-72B-Instruct-AWQ",
                "instance_type":"g5.12xlarge",
                "engine_type":"vllm",
                "service_type":"sagemaker",
                "framework_type":"fastapi",
                "model_tag":"batch_test"
            },
            "invoke_config":{
                "pyloads":[{
                    "messages": [
                        {
                            "role": "user",
                            "content": "Explain async programming in Python"
                        }
                    ]
                }],
            }
        },
        {
            "deploy_config":{
                "model_id": "bge-base-en-v1.5",
                "instance_type":"g5.xlarge",
                "engine_type":"vllm",
                "service_type":"sagemaker",
                "framework_type":"fastapi",
                "model_tag":"batch_test"
            },
            "invoke_config":{
                "pyloads":[{
                    "input": ['Who you are?']
                }],
            }
        },
        {
            "deploy_config":{
                "model_id": "bge-reranker-v2-m3",
                "instance_type":"g5.xlarge",
                "engine_type":"vllm",
                "service_type":"sagemaker",
                "framework_type":"fastapi",
                "model_tag":"batch_test"
            },
            "invoke_config":{
                "pyloads":[{
                    "encoding_format": "float",
                    "text_1": "What's the capital of China?",
                    "text_2": "Beijing"
                }],
            }
        }
    ]
tasks = [Task(**task) for task in tasks]
test_ret = []
for task in tasks:
    test_ret.append(test_one_task(task))


# print test ret
print("=="*50 + "test ret" + "=="*50)
for ret in test_ret:
    task = ret['task']
    model_id = task.deploy_config.model_id
    print(f"model_id: {model_id}\ntest code:{ret['code']}\nerror:{ret['error']}")
    print("=="*50)

if all([ret['code'] == 0 for ret in test_ret]):
    print("=="*50 + "all success" + "=="*50)
