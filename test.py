"""测试环境配置"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 40)
print("环境测试")
print("=" * 40)

# 测试1：检查环境变量
tushare_token = os.getenv("TUSHARE_TOKEN")
deepseek_key = os.getenv("DEEPSEEK_API_KEY")

print(f"Tushare Token: {'已配置' if tushare_token else '❌ 未配置'}")
print(f"DeepSeek Key: {'已配置' if deepseek_key else '❌ 未配置'}")

# 测试2：导入模块
try:
    import tushare as ts
    print("✅ tushare 导入成功")
except Exception as e:
    print(f"❌ tushare 导入失败: {e}")

try:
    import openai
    print("✅ openai 导入成功")
except Exception as e:
    print(f"❌ openai 导入失败: {e}")

try:
    import redis
    print("✅ redis 导入成功")
except Exception as e:
    print(f"❌ redis 导入失败: {e}")

print("=" * 40)
