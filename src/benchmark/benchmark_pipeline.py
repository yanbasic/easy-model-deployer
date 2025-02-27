from benchmark import (OpenAIUserDef, OpenAIStreamUserDef)
from benchmark.benchmark_pipeline import start_benchmark_session

import asyncio
from common import start_benchmark_session
import argparse

session_time = 300
ping_correction = True
max_users_list = [1, 5, 10]

for max_users in max_users_list:
    args = argparse.Namespace(max_users=max_users, session_time=session_time, ping_correction=ping_correction)
    asyncio.run(start_benchmark_session(args, OpenAIStreamUserDef))
    print(f"Stream Benchmarking with {max_users} users completed.")
    asyncio.run(start_benchmark_session(args, OpenAIUserDef))
    print(f"Benchmarking with {max_users} users completed.")