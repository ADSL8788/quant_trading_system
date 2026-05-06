#!/usr/bin/env python3
"""显示预设股票池清单"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from config.settings import config

def main():
    stocks = config.WATCHLIST
    if not stocks:
        print("⚠️ 预设股票池为空")
        return

    print("\n" + "=" * 60)
    print(f"📋 预设股票池清单 (共 {len(stocks)} 只)")
    print("=" * 60)
    print(f"{'序号':<4} {'代码':<12} {'名称':<10} {'板块':<12}")
    print("-" * 60)

    for idx, stock in enumerate(stocks, 1):
        print(f"{idx:<4} {stock['ts_code']:<12} {stock['name']:<10} {stock.get('sector', '未分类'):<12}")

    print("=" * 60)

if __name__ == "__main__":
    main()
