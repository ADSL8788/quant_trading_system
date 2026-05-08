#!/usr/bin/env python3
"""一键添加 auto_screener_results.csv 中的前 N 只股票到自选池"""
import sys
import pandas as pd
import add_stock

def main():
    try:
        df = pd.read_csv('auto_screener_results.csv')
    except FileNotFoundError:
        print("❌ 未找到 auto_screener_results.csv，请先运行 sc 或 scfull")
        return

    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    added = 0
    for _, row in df.head(top_n).iterrows():
        ts_code = row['ts_code']
        name = row['name']
        if add_stock.add_stock(ts_code, name):
            added += 1
    print(f"✅ 成功添加 {added}/{top_n} 只股票到自选池")

if __name__ == "__main__":
    main()
