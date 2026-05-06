#!/usr/bin/env python3
"""纯Dexter分析模式"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from config.settings import config
from dexter_wrapper import DexterWrapper

print("="*50)
print("🔬 Dexter 深度分析模式")
print("="*50)

d = DexterWrapper()

count = 0
for stock in config.WATCHLIST:
    if count >= 5:
        break
    print(f"\n📊 分析: {stock['name']} ({stock['ts_code']})")
    result = d.research_stock(stock['ts_code'], stock['name'])
    if result.get("success"):
        analysis = result.get("analysis", "")
        print(f"   {analysis[:200]}...")
    else:
        print("   分析失败")
    count += 1

print("="*50)
