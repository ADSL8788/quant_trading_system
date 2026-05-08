#!/usr/bin/env python3
"""全市场扫描 - 热度排序取前500只 + 技术筛选（修正版）"""
import sys
import os
sys.path.insert(0, '/home/fafa6/auto_trading_system')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm

from config.settings import config
from data_layer.tushare_client import TushareClient

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colorize(text, color):
    return f"{color}{text}{Color.END}"

class AutoScreener:
    def __init__(self):
        self.client = TushareClient()
        self.pro = self.client.pro

    def get_recent_limit_up_codes(self, days=20):
        """获取近期涨停股票集合（需积分>2000）"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days+10)
        try:
            df = self.pro.limit_list(start_date=start_date.strftime('%Y%m%d'),
                                     end_date=end_date.strftime('%Y%m%d'),
                                     limit_type='U')
            if df is not None and not df.empty:
                return set(df['ts_code'].unique())
        except:
            pass
        return set()

    def get_all_stocks_with_heat(self):
        """获取全市场股票并计算综合热度分，返回按热度降序的DataFrame"""
        stocks = self.pro.stock_basic(exchange='', list_status='L')
        stocks = stocks[
            (stocks['list_date'] < (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')) &
            (~stocks['name'].str.contains('ST|退', case=False, na=False)) &
            (stocks['market'].isin(['主板', '创业板', '科创板']))
        ]
        print(f"✅ 初始股票池: {len(stocks)} 只")

        latest_trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        daily_basic = self.pro.daily_basic(trade_date=latest_trade_date,
                                           fields='ts_code,turnover_rate,total_mv')
        if daily_basic.empty:
            print("⚠️ 无法获取 daily_basic，跳过热度排序")
            stocks['heat'] = 0
            return stocks

        #limit_codes = self.get_recent_limit_up_codes()
        #print(f"✅ 近期涨停股票数: {len(limit_codes)}")

        stocks = stocks.merge(daily_basic, on='ts_code', how='left')
        stocks['turnover_rate'] = stocks['turnover_rate'].fillna(0)
        stocks['total_mv'] = stocks['total_mv'].fillna(0)

        # 换手率归一化
        max_turn = stocks['turnover_rate'].max()
        min_turn = stocks['turnover_rate'].min()
        if max_turn > min_turn:
            stocks['turn_score'] = (stocks['turnover_rate'] - min_turn) / (max_turn - min_turn)
        else:
            stocks['turn_score'] = 0

        # 小市值归一化（越小分越高）
        max_mv = stocks['total_mv'].max()
        min_mv = stocks['total_mv'].min()
        if max_mv > min_mv:
            stocks['mv_score'] = 1 - (stocks['total_mv'] - min_mv) / (max_mv - min_mv)
        else:
            stocks['mv_score'] = 0

        #stocks['limit_bonus'] = stocks['ts_code'].apply(lambda x: 1 if x in limit_codes else 0)
        stocks['heat'] = stocks['turn_score'] * 0.7 + stocks['mv_score'] * 0.3
        stocks = stocks.sort_values('heat', ascending=False)

        print("\n🔥 热度排序前10只股票（用于技术筛选）:")
        print(stocks[['ts_code','name','turnover_rate','total_mv','heat']].head(10).to_string(index=False))
        return stocks

    def quick_technical_filter(self, stocks_df, top_n=500):
        print(f"\n📈 技术指标快速筛选（分析热度前 {top_n} 只）")
        print("传入 quick_technical_filter 的前5只股票代码:", stocks_df['ts_code'].head(5).tolist())
        results = []
        total = min(len(stocks_df), top_n)
        today = datetime.now().strftime('%Y-%m-%d')
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
                last_date = df['timestamp'].iloc[-1].strftime('%Y-%m-%d')
                momentum = (close[-1] - close[-20]) / close[-20] if len(close)>=20 else 0
                ma20 = np.mean(close[-20:])
                ma60 = np.mean(close[-60:]) if len(close)>=60 else close[-1]
                price_above_ma = close[-1] > ma20 and ma20 > ma60
                vol_ratio = (volume[-5:].mean() / volume[-20:].mean()) if len(volume)>=20 else 1
                if len(close) >= 15:
                    delta = np.diff(close[-15:])
                    gain = np.mean([d for d in delta if d > 0]) if any(d>0 for d in delta) else 0
                    loss = -np.mean([d for d in delta if d < 0]) if any(d<0 for d in delta) else 0.001
                    rs = gain / loss
                    rsi = 100 - 100/(1+rs)
                else:
                    rsi = 50
                score = 0
                if momentum > 0.05: score += 30
                elif momentum > 0.02: score += 15
                if price_above_ma: score += 25
                if vol_ratio > 1.3: score += 15
                if score >= 25:
                    results.append({
                        'scan_date': today,
                        'last_date': last_date,
                        'ts_code': ts_code,
                        'name': name,
                        'close': round(close[-1], 2),
                        'momentum': round(momentum, 4),
                        'ma20': round(ma20, 2),
                        'ma60': round(ma60, 2),
                        'volume_ratio': round(vol_ratio, 2),
                        'rsi': round(rsi, 1),
                        'score': score,
                        'exp_change': round(momentum * 100, 1)
                    })
                pbar.update(1)
        result_df = pd.DataFrame(results)
        if not result_df.empty:
            result_df = result_df.sort_values('score', ascending=False)
        print(f"✅ 技术筛选通过: {len(result_df)} 只")
        return result_df

    def scan_and_select(self, top_n=20):
        stocks_with_heat = self.get_all_stocks_with_heat()
        tech_ok = self.quick_technical_filter(stocks_with_heat, top_n=500)
        if tech_ok.empty:
            print("⚠️ 未筛选出股票")
            return tech_ok
        latest_date = tech_ok['last_date'].max()
        print(f"\n📅 扫描数据截止日期: {latest_date}")
        print(f"📊 本次扫描共分析 {len(stocks_with_heat)} 只股票，筛选出 {len(tech_ok)} 只符合技术条件")
        return tech_ok.head(top_n)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='全量扫描所有股票（忽略财务筛选）')
    args = parser.parse_args()

    screener = AutoScreener()
    if args.full:
        all_stocks = screener.get_all_stocks_with_heat()
        tech_ok = screener.quick_technical_filter(all_stocks, top_n=len(all_stocks))
        results = tech_ok.head(20)
    else:
        results = screener.scan_and_select(top_n=20)

    if results.empty:
        return
    print("\n🏆 Top 20 推荐股票")
    print("="*100)
    for i, row in results.reset_index(drop=True).iterrows():
        if row['score'] >= 60:
            action = colorize("强烈关注", Color.RED)
        elif row['score'] >= 40:
            action = colorize("适当关注", Color.YELLOW)
        else:
            action = colorize("一般关注", Color.WHITE)
        momentum_str = colorize(f"{row['momentum']:+.1%}", Color.RED if row['momentum']>0 else Color.GREEN)
        print(f"{i+1}. {row['name']} ({row['ts_code']}) 日期:{row['last_date']} "
              f"收盘:{row['close']:.2f} 动量:{momentum_str} RSI:{row['rsi']:.0f} 评分:{row['score']} {action}")
    results.to_csv('auto_screener_results.csv', index=False, encoding='utf-8-sig')
    print(f"\n✅ 详细结果已保存到 auto_screener_results.csv")

if __name__ == "__main__":
    main()
