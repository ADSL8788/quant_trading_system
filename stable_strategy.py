#!/usr/bin/env python3
"""稳定版策略 - 基于真实历史数据"""
import sys
import os
sys.path.insert(0, '/home/fafa6/auto_trading_system')

import backtrader as bt
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from config.settings import config
from data_layer.tushare_client import TushareClient

class StableStrategy(bt.Strategy):
    """稳定策略 - 减少交易频率，提高胜率"""
    
    params = (
        ('fast', 10),       # 更长的均线周期
        ('slow', 30),
        ('trend', 120),
        ('stop_loss', 0.10),    # 放宽到10%止损
        ('take_profit', 0.20),  # 20%止盈
    )
    
    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.slow)
        self.trend_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.trend)
        
        # 增加RSI过滤
        self.rsi = bt.indicators.RelativeStrengthIndex(self.data.close, period=14)
        
        self.order = None
        self.buy_price = 0
        self.trade_count = 0
        self.win_count = 0
        
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.trade_count += 1
                print(f"{self.datas[0].datetime.date(0)} 买入 {self.buy_price:.2f}")
            else:
                if self.buy_price > 0:
                    pnl = (order.executed.price - self.buy_price) / self.buy_price
                    if pnl > 0:
                        self.win_count += 1
                    print(f"{self.datas[0].datetime.date(0)} 卖出 {order.executed.price:.2f} (盈亏:{pnl:+.2%})")
        self.order = None
    
    def next(self):
        if self.order or len(self.data) < self.p.trend:
            return
        
        # 趋势过滤
        uptrend = self.data.close[0] > self.trend_ma[0] and self.fast_ma[0] > self.slow_ma[0]
        
        # 金叉信号（更严格）
        golden = (self.fast_ma[0] > self.slow_ma[0] and 
                  self.fast_ma[-1] <= self.slow_ma[-1] and
                  self.rsi[0] > 40 and self.rsi[0] < 70)  # RSI过滤
        
        if not self.position and golden and uptrend:
            cash = self.broker.get_cash()
            size = int(cash * 0.25 / self.data.close[0])  # 25%仓位
            if size >= 100:
                self.order = self.buy(size=size)
        
        elif self.position:
            current = self.data.close[0]
            pnl = (current - self.buy_price) / self.buy_price
            
            # 卖出条件
            sell = False
            
            # 1. 止盈
            if pnl >= self.p.take_profit:
                sell = True
                print(f"🎯 止盈触发")
            # 2. 止损
            elif pnl <= -self.p.stop_loss:
                sell = True
                print(f"⚠️ 止损触发")
            # 3. 趋势反转
            elif current < self.trend_ma[0] and pnl > 0:
                sell = True
                print(f"📉 趋势反转")
            
            if sell:
                self.order = self.close()

def run_stable_backtest(ts_code, start_date='2022-01-01', end_date='2025-04-30'):
    """运行稳定版回测"""
    print(f"\n{'='*55}")
    print(f"稳定策略回测: {ts_code}")
    print(f"期间: {start_date} 至 {end_date}")
    print(f"{'='*55}")
    
    client = TushareClient()
    df = client.get_kline(ts_code, days=1200)
    
    if df.empty:
        return None
    
    df['date'] = pd.to_datetime(df['timestamp'])
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    df = df.rename(columns={'timestamp': 'datetime'})
    df = df.set_index('datetime')
    df = df.sort_index()
    
    print(f"数据量: {len(df)} 条 ({df.index[0].date()} 至 {df.index[-1].date()})")
    
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(StableStrategy)
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.00025)
    
    initial = cerebro.broker.getvalue()
    results = cerebro.run()
    final = cerebro.broker.getvalue()
    
    strategy = results[0]
    total_return = (final - initial) / initial
    
    print(f"\n📊 结果:")
    print(f"   交易次数: {strategy.trade_count}")
    print(f"   胜率: {strategy.win_count/strategy.trade_count if strategy.trade_count>0 else 0:.1%}")
    print(f"   收益: {total_return:+.2%}")
    
    return total_return

def main():
    print("="*55)
    print("🚀 稳定版策略回测 (2022-2025)")
    print("="*55)
    
    stocks = [
        {"ts_code": "000001.SZ", "name": "平安银行"},
        {"ts_code": "600519.SH", "name": "贵州茅台"},
        {"ts_code": "000858.SZ", "name": "五粮液"},
    ]
    
    results = []
    for stock in stocks:
        ret = run_stable_backtest(stock['ts_code'])
        if ret is not None:
            results.append((stock['name'], ret))
    
    print("\n" + "="*55)
    print("📊 三年回测汇总 (2022-2025)")
    print("="*55)
    
    total = 0
    for name, ret in results:
        emoji = "🟢" if ret > 0 else "🔴"
        print(f"{emoji} {name}: {ret:+.2%}")
        total += ret
    
    if results:
        avg = total / len(results)
        print(f"\n平均年化收益: {avg:+.2%}")
        
        if avg > 0.10:
            print("🎉 策略优秀！")
        elif avg > 0.05:
            print("👍 策略良好")
        elif avg > 0:
            print("📈 策略盈利")
        else:
            print("⚠️ 策略亏损，需要调整参数")
    
    # 对比基准
    print(f"\n📈 基准对比:")
    print(f"   银行定期存款: +2.00%/年")
    print(f"   沪深300指数: -5% ~ +10%")

if __name__ == "__main__":
    main()
