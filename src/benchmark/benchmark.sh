export BASE_URL=127.0.0.1:8081
export SYSTEM_PROMPT=1
python benchmark.py --max_users 10 --session_time 300 --ping_correction
