import sys
import os
import json

# 确保使用本地修改过的 requests 库，而非系统 pip 版本
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "requests", "src"))

import requests

# 验证 User-Agent 默认值已经修改
print(f"默认 User-Agent: {requests.utils.default_user_agent()}")

# 发起 GET 请求
resp = requests.get("https://httpbin.org/user-agent")
resp.raise_for_status()

data = resp.json()
print(f"响应 JSON: {json.dumps(data, indent=2)}")

# 保存到 agent_identity.json
output_path = os.path.join(os.path.dirname(__file__), "agent_identity.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"\n响应已保存到: {output_path}")
