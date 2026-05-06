#!/usr/bin/env python3
"""一键添加技术面最强10只股票到预设池（直接调用 add_stock 模块）"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from auto_screener import AutoScreener
import add_stock

def main():
    screener = AutoScreener()
    stocks = screener.get_all_stocks()
    tech = screener.quick_technical_filter(stocks, top_n=300)
    top10 = tech.head(10)
    if top10.empty:
        print("⚠️ 未找到强势股票")
        return
    for _, row in top10.iterrows():
        ts_code = row['ts_code']
        name = row['name']
        print(f"添加: {ts_code} {name}")
        add_stock.add_stock(ts_code, name)
    print("✅ 添加完成")

if __name__ == "__main__":
    main()
