#!/usr/bin/env python3
"""Dexter 指定股票分析"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from dexter_wrapper import DexterWrapper

if len(sys.argv) < 2:
    print("用法: python dex_stock.py <股票代码> [股票名称]")
    print("示例: python dex_stock.py 300750 宁德时代")
    sys.exit(0)

code = sys.argv[1]
name = sys.argv[2] if len(sys.argv) > 2 else code

if '.' not in code:
    if code.startswith(('60', '68')):
        ts_code = f"{code}.SH"
    else:
        ts_code = f"{code}.SZ"
else:
    ts_code = code

print("=" * 50)
print(f"🔬 Dexter 深度分析: {name} ({ts_code})")
print("=" * 50)

d = DexterWrapper()
result = d.research_stock(ts_code, name)

if result.get("success"):
    print(result.get("analysis", ""))
else:
    print("❌ 分析失败")

print("=" * 50)
