#!/usr/bin/env python3
"""高级优化版回测 - 增加多个过滤条件"""
import sys
import os
sys.path.insert(0, '/home/fafa6/auto_trading_system')

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from config.settings import config
from data_layer.tushare_client import TushareClient

class AdvancedStrategy(bt.Strategy):
    """高级策略：多重过滤 + 动态仓位"""
    
    params = (
        ('fast', 10),       # 快线
        ('slow', 30),       # 慢线  
        ('trend', 120),     # 长期趋势线
        ('volume_period', 20),
        ('stop_loss', 0.08),    # 止损放宽到8%
        ('take_profit', 0.15),  # 止盈15%
        ('max_position', 0.4),  # 最大仓位40%
    )
    
    def __init__(self):
        # 均线系统
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.slow)
        self.trend_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.trend)
        
        # 成交量
        self.volume_ma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.p.volume_period)
        
        # MACD
        self.macd = bt.indicators.MACD(self.data.close)
        
        # RSI
        self.rsi = bt.indicators.RSI(self.data.close, period=14)
        
        self.order = None
        self.buy_price = 0
        self.buy_date = None
        self.trade_count = 0
        self.win_count = 0
        
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f"{dt} {txt}")
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.trade_count += 1
            if order.isbuy():
                self.buy_price = order.executed.price
                self.buy_date = self.datas[0].datetime.date(0)
                self.log(f'📈 买入: {order.executed.price:.2f}')
            else:
                profit = (order.executed.price - self.buy_price) / self.buy_price
                if profit > 0:
                    self.win_count += 1
                self.log(f'📉 卖出: {order.executed.price:.2f} (盈亏:{profit:+.2%})')
        self.order = None
    
    def next(self):
        if self.order or len(self.data) < self.p.trend:
            return
        
        # 多重过滤条件
        uptrend = self.data.close[0] > self.trend_ma[0]  # 长期趋势向上
        volume_ok = self.data.volume[0] > self.volume_ma[0]  # 放量
        macd_bullish = self.macd.macd[0] > self.macd.signal[0]  # MACD金叉
        rsi_ok = 30 < self.rsi[0] < 70  # 非超买超卖
        
        # 金叉信号
        golden = (self.fast_ma[0] > self.slow_ma[0] and 
                  self.fast_ma[-1] <= self.slow_ma[-1])
        
        # 死叉信号  
        death = (self.fast_ma[0] < self.slow_ma[0] and 
                 self.fast_ma[-1] >= self.slow_ma[-1])
        
        # 买入：金叉 + 趋势向上 + 放量 + MACD向好
        if not self.position and golden and uptrend and volume_ok and macd_bullish and rsi_ok:
            cash = self.broker.get_cash()
            size = int(cash * self.p.max_position / self.data.close[0])
            if size >= 100:  # A股最少100股
                self.order = self.buy(size=size)
                
        elif self.position:
            # 卖出条件
            should_sell = False
            
            # 死叉卖出
            if death:
                should_sell = True
                self.log(f'🔴 死叉卖出信号')
            
            # 止损止盈
            current_price = self.data.close[0]
            pnl = (current_price - self.buy_price) / self.buy_price
            
            if pnl <= -self.p.stop_loss:
                should_sell = True
                self.log(f'⚠️ 止损触发 ({pnl:.2%})')
            elif pnl >= self.p.take_profit:
                should_sell = True
                self.log(f'🎯 止盈触发 ({pnl:.2%})')
            
            # 跌破趋势线
            elif current_price < self.trend_ma[0]:
                should_sell = True
                self.log(f'📉 跌破趋势线')
            
            if should_sell:
                self.order = self.close()

def run_advanced_backtest(ts_code, start_date='2023-01-01', end_date='2025-04-30'):
    print(f"\n{'='*55}")
    print(f"高级策略回测: {ts_code}")
    print(f"{'='*55}")
    
    client = TushareClient()
    df = client.get_kline(ts_code, days=800)
    
    if df.empty:
        return None
    
    df['date'] = pd.to_datetime(df['timestamp'])
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    df = df.rename(columns={'timestamp': 'datetime'})
    df = df.set_index('datetime')
    df = df.sort_index()
    
    print(f"数据量: {len(df)} 条")
    
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(AdvancedStrategy)
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.00025)  # 降低手续费
    
    initial_value = cerebro.broker.getvalue()
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    
    strategy = results[0]
    
    total_return = (final_value - initial_value) / initial_value
    days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
    annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
    
    win_rate = strategy.win_count / strategy.trade_count if strategy.trade_count > 0 else 0
    
    print(f"\n📊 回测结果:")
    print(f"   初始资金: {initial_value:,.0f}")
    print(f"   最终资金: {final_value:,.0f}")
    print(f"   总收益率: {total_return:+.2%}")
    print(f"   年化收益: {annual_return:+.2%}")
    print(f"   交易次数: {strategy.trade_count}")
    print(f"   胜率: {win_rate:.1%}")
    
    return {
        'ts_code': ts_code,
        'total_return': total_return,
        'annual_return': annual_return,
        'trades': strategy.trade_count,
        'win_rate': win_rate
    }

def main():
    print("="*55)
    print("🚀 高级优化策略回测 (多重过滤)")
    print("="*55)
    
    results = []
    for stock in config.WATCHLIST:
        result = run_advanced_backtest(stock['ts_code'])
        if result:
            results.append(result)
    
    print("\n" + "="*55)
    print("📊 优化策略汇总")
    print("="*55)
    
    for r in results:
        emoji = "🟢" if r['total_return'] > 0 else "🔴"
        print(f"{emoji} {r['ts_code']}: 收益 {r['total_return']:+.2%} | "
              f"年化 {r['annual_return']:+.2%} | 交易 {r['trades']}次 | 胜率 {r['win_rate']:.1%}")
    
    if results:
        avg_return = sum(r['total_return'] for r in results) / len(results)
        print(f"\n平均收益率: {avg_return:+.2%}")
        
        # 给出综合评分
        if avg_return > 0.15:
            print("🎉 优秀！策略表现出色")
        elif avg_return > 0.05:
            print("👍 良好，可以实盘测试")
        elif avg_return > 0:
            print("📈 正收益，可继续优化")
        else:
            print("⚠️ 仍亏损，需要重新设计")
    
    print("\n" + "="*55)
    print("💡 最终优化策略:")
    print("1. 放宽止损到8%，让利润奔跑")
    print("2. 增加成交量确认信号")
    print("3. 使用MACD过滤假信号")
    print("4. 仓位控制在40%以内")
    print("="*55)

if __name__ == "__main__":
    main()
