#!/usr/bin/env python3
"""实用版回测系统 - 平衡风险和收益"""
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

class PracticalStrategy(bt.Strategy):
    """实用交易策略 - 适合A股市场"""
    
    params = (
        ('fast', 5),       # 快线
        ('slow', 20),      # 慢线  
        ('trend', 60),     # 趋势线
        ('stop_loss', 0.05),   # 止损5%
        ('take_profit', 0.10), # 止盈10%
    )
    
    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.slow)
        self.trend_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.trend)
        
        self.order = None
        self.buy_price = 0
        self.trade_count = 0
        
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f"{dt} {txt}")
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.trade_count += 1
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'✅ 买入: {order.executed.price:.2f}')
            else:
                profit = (order.executed.price - self.buy_price) / self.buy_price
                self.log(f'❌ 卖出: {order.executed.price:.2f} (盈亏:{profit:+.2%})')
        self.order = None
    
    def next(self):
        if self.order or len(self.data) < self.p.trend:
            return
        
        # 趋势判断
        uptrend = self.data.close[0] > self.trend_ma[0]
        
        # 金叉死叉
        golden = self.fast_ma[0] > self.slow_ma[0] and self.fast_ma[-1] <= self.slow_ma[-1]
        death = self.fast_ma[0] < self.slow_ma[0] and self.fast_ma[-1] >= self.slow_ma[-1]
        
        # 持仓管理
        if not self.position:
            # 买入：金叉 + 上升趋势
            if golden and uptrend:
                cash = self.broker.get_cash()
                size = int(cash * 0.3 / self.data.close[0])
                if size > 0:
                    self.order = self.buy(size=size)
        else:
            # 卖出条件
            if death:
                self.order = self.close()
            else:
                # 止损止盈
                current_price = self.data.close[0]
                pnl = (current_price - self.buy_price) / self.buy_price
                
                if pnl <= -self.p.stop_loss:
                    self.log(f'⚠️ 止损触发 (亏损:{pnl:.2%})')
                    self.order = self.close()
                elif pnl >= self.p.take_profit:
                    self.log(f'🎯 止盈触发 (盈利:{pnl:.2%})')
                    self.order = self.close()

def run_backtest(ts_code, start_date='2023-01-01', end_date='2025-04-30'):
    print(f"\n{'='*55}")
    print(f"回测: {ts_code}")
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
    
    print(f"数据量: {len(df)} 条K线")
    
    # 运行回测
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(PracticalStrategy)
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.0003)
    
    initial_value = cerebro.broker.getvalue()
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    
    # 获取策略实例
    strategy = results[0]
    
    total_return = (final_value - initial_value) / initial_value
    days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
    annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
    
    print(f"\n📊 回测结果:")
    print(f"   初始资金: {initial_value:,.0f}")
    print(f"   最终资金: {final_value:,.0f}")
    print(f"   总收益率: {total_return:+.2%}")
    print(f"   年化收益: {annual_return:+.2%}")
    print(f"   交易次数: {strategy.trade_count}")
    
    return {
        'ts_code': ts_code,
        'total_return': total_return,
        'annual_return': annual_return,
        'trades': strategy.trade_count
    }

def main():
    print("="*55)
    print("🚀 实用策略回测系统")
    print("="*55)
    
    results = []
    for stock in config.WATCHLIST:
        result = run_backtest(stock['ts_code'])
        if result:
            results.append(result)
    
    print("\n" + "="*55)
    print("📊 回测汇总")
    print("="*55)
    
    for r in results:
        emoji = "🟢" if r['total_return'] > 0 else "🔴"
        print(f"{emoji} {r['ts_code']}: 收益 {r['total_return']:+.2%} | 年化 {r['annual_return']:+.2%} | 交易 {r['trades']}次")
    
    if results:
        avg_return = sum(r['total_return'] for r in results) / len(results)
        print(f"\n平均收益率: {avg_return:+.2%}")
        
        if avg_return > 0.10:
            print("✅ 优秀！策略表现良好")
        elif avg_return > 0:
            print("✅ 正收益，可以接受")
        else:
            print("⚠️ 亏损，需要优化参数")
    
    # 参数优化建议
    print("\n" + "="*55)
    print("💡 参数优化建议:")
    print("   fast=5, slow=20, stop=5%, profit=10%")
    print("   (可尝试调整周期以适应不同股票)")
    print("="*55)

if __name__ == "__main__":
    main()
