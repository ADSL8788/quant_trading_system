#!/usr/bin/env python3
"""极简选股：输出技术面最强10只股票的代码（一行一个）"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from auto_screener import AutoScreener

screener = AutoScreener()
stocks = screener.get_all_stocks_with_heat()
tech = screener.quick_technical_filter(stocks, top_n=300)
for _, row in tech.head(10).iterrows():
    print(row['ts_code'])
