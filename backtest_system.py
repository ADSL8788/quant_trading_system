#!/usr/bin/env python3
"""专业回测系统"""
import sys
import os
sys.path.insert(0, '/home/fafa6/auto_trading_system')

import backtrader as bt
import pandas as pd
from datetime import datetime
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

from config.settings import config
from data_layer.tushare_client import TushareClient

class SimpleStrategy(bt.Strategy):
    """简单有效的均线策略"""
    
    params = (
        ('fast', 5),
        ('slow', 20),
    )
    
    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.slow)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
    def next(self):
        if not self.position:
            if self.crossover > 0:  # 金叉买入
                cash = self.broker.get_cash()
                size = int(cash * 0.3 / self.data.close[0])
                if size > 0:
                    self.buy(size=size)
                    print(f"买入 at {self.data.close[0]:.2f}")
        else:
            if self.crossover < 0:  # 死叉卖出
                self.close()
                print(f"卖出 at {self.data.close[0]:.2f}")

def run_backtest(ts_code, start_date='2023-01-01', end_date='2025-04-30'):
    """运行回测"""
    print(f"\n{'='*50}")
    print(f"回测: {ts_code}")
    print(f"期间: {start_date} 至 {end_date}")
    print(f"{'='*50}")
    
    # 获取数据
    client = TushareClient()
    df = client.get_kline(ts_code, days=800)
    
    if df.empty:
        print(f"❌ 无法获取 {ts_code} 数据")
        return None
    
    # 处理数据
    df['date'] = pd.to_datetime(df['timestamp'])
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    if df.empty:
        print(f"❌ {ts_code} 在指定日期范围无数据")
        return None
    
    df = df.rename(columns={'timestamp': 'datetime'})
    df = df.set_index('datetime')
    df = df.sort_index()
    
    print(f"数据量: {len(df)} 条K线")
    print(f"价格区间: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    # 运行回测
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(SimpleStrategy)
    cerebro.broker.setcash(1000000)  # 100万初始资金
    cerebro.broker.setcommission(commission=0.0003)  # 万三手续费
    
    initial_value = cerebro.broker.getvalue()
    print(f"初始资金: {initial_value:,.2f}")
    
    # 执行回测
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    
    # 计算收益
    total_return = (final_value - initial_value) / initial_value
    days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
    annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
    
    print(f"\n回测结果:")
    print(f"最终资金: {final_value:,.2f}")
    print(f"总收益率: {total_return:.2%}")
    print(f"年化收益率: {annual_return:.2%}")
    
    return {
        'ts_code': ts_code,
        'total_return': total_return,
        'annual_return': annual_return,
        'data_points': len(df)
    }

def main():
    print("="*60)
    print("🚀 自动交易系统回测")
    print("="*60)
    
    results = []
    for stock in config.WATCHLIST:
        result = run_backtest(stock['ts_code'])
        if result:
            results.append(result)
    
    # 汇总报告
    print("\n" + "="*60)
    print("📊 回测汇总报告")
    print("="*60)
    
    if results:
        for r in results:
            emoji = "🟢" if r['total_return'] > 0 else "🔴"
            print(f"{emoji} {r['ts_code']}: 收益率 {r['total_return']:.2%} | 年化 {r['annual_return']:.2%}")
        
        avg_return = sum(r['total_return'] for r in results) / len(results)
        print(f"\n平均收益率: {avg_return:.2%}")
        
        if avg_return > 0:
            print("✅ 策略在过去2年表现良好")
        else:
            print("⚠️ 策略亏损，需要优化参数")
    else:
        print("❌ 没有成功回测的数据")
    
    print("="*60)

if __name__ == "__main__":
    main()
