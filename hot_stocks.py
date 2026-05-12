#!/usr/bin/env python3
"""极简选股：输出技术面最强10只股票（代码+名称+涨幅）"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from auto_screener import AutoScreener

screener = AutoScreener()
stocks = screener.get_all_stocks_with_heat()
# 只分析前300只加速
tech = screener.quick_technical_filter(stocks, top_n=300)
tech = tech.head(10)

print("\n🔥 技术面最强10只股票")
print("=" * 50)
for _, row in tech.iterrows():
    print(f"{row['ts_code']:<12} {row['name']:<8} 涨幅 {row['momentum']:>+6.1%}")
print("=" * 50)
print("使用 'add <代码> 名称' 快速加入预设池")
