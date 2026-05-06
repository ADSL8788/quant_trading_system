#!/usr/bin/env python3
"""全市场扫描 - 技术筛选版（无财务）"""
import sys
import os
sys.path.insert(0, '/home/fafa6/auto_trading_system')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm

from config.settings import config
from data_layer.tushare_client import TushareClient

class AutoScreener:
    def __init__(self):
        self.client = TushareClient()
        self.pro = self.client.pro

    def get_all_stocks(self):
        stocks = self.pro.stock_basic(exchange='', list_status='L')
        stocks = stocks[
            (stocks['list_date'] < (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')) &
            (~stocks['name'].str.contains('ST|退', case=False, na=False)) &
            (stocks['market'].isin(['主板', '创业板', '科创板']))
        ]
        print(f"✅ 初始池: {len(stocks)} 只")
        return stocks

    def quick_technical_filter(self, stocks_df, top_n=500):
        print("\n📈 技术指标快速筛选（无财务过滤）")
        results = []
        total = min(len(stocks_df), top_n)
        with tqdm(total=total, desc="技术筛选", ncols=80) as pbar:
            for _, stock in stocks_df.head(total).iterrows():
                ts_code = stock['ts_code']
                name = stock['name']
                df = self.client.get_kline(ts_code, days=120)
                if len(df) < 50:
                    pbar.update(1)
                    continue
                close = df['close'].values
                volume = df['volume'].values
                momentum = (close[-1] - close[-20]) / close[-20] if len(close)>=20 else 0
                ma20 = np.mean(close[-20:])
                ma60 = np.mean(close[-60:]) if len(close)>=60 else close[-1]
                price_above_ma = close[-1] > ma20 and ma20 > ma60
                vol_ratio = (volume[-5:].mean() / volume[-20:].mean()) if len(volume)>=20 else 1
                score = 0
                if momentum > 0.05: score += 30
                elif momentum > 0.02: score += 15
                if price_above_ma: score += 25
                if vol_ratio > 1.3: score += 15
                if score >= 25:
                    results.append({
                        'ts_code': ts_code,
                        'name': name,
                        'score': score,          # 确保有 score 列
                        'momentum': round(momentum, 3),
                        'price': round(close[-1], 2)
                    })
                pbar.update(1)
        result_df = pd.DataFrame(results)
        if not result_df.empty:
            result_df = result_df.sort_values('score', ascending=False)
        print(f"✅ 技术筛选通过: {len(result_df)} 只")
        return result_df.head(100)

    def scan_and_select(self, top_n=20):
        all_stocks = self.get_all_stocks()
        tech_ok = self.quick_technical_filter(all_stocks)
        return tech_ok.head(top_n)

def main():
    screener = AutoScreener()
    results = screener.scan_and_select(top_n=20)
    if results.empty:
        print("⚠️ 未筛选出股票")
        return
    print("\n🏆 Top 20 推荐股票")
    print("="*50)
    for i, (_, row) in enumerate(results.iterrows(), 1):
        action = "🟢 强烈关注" if row['score'] >= 60 else "🟡 适当关注"
        print(f"{i}. {row['name']} ({row['ts_code']}) 评分 {row['score']:.1f} | 涨幅 {row['momentum']:+.1%} | {action}")
    results.to_csv('auto_screener_results.csv', index=False)
    print(f"\n✅ 结果已保存到 auto_screener_results.csv")

if __name__ == "__main__":
    main()
