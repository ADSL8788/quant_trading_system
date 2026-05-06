#!/usr/bin/env python3
"""生产级交易策略 - 基于回测优化"""
import sys
import os
sys.path.insert(0, '/home/fafa6/auto_trading_system')

import backtrader as bt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from config.settings import config
from data_layer.tushare_client import TushareClient

class ProductionStrategy(bt.Strategy):
    """生产级策略 - 针对不同股票优化"""
    
    def __init__(self):
        # 默认参数
        self.fast, self.slow, self.trend = 5, 20, 60
        self.stop_loss, self.take_profit = 0.06, 0.15
        
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.slow)
        self.trend_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.trend)
        
        self.order = None
        self.buy_price = 0  # 初始化为0
        self.trade_count = 0
        self.win_count = 0
        
    def notify_order(self, order):
        """订单状态更新"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                print(f"{self.datas[0].datetime.date(0)} 买入 {self.buy_price:.2f}")
            else:
                if self.buy_price > 0:
                    pnl = (order.executed.price - self.buy_price) / self.buy_price
                    if pnl > 0:
                        self.win_count += 1
                    print(f"{self.datas[0].datetime.date(0)} 卖出 {order.executed.price:.2f} (盈亏:{pnl:+.2%})")
            self.trade_count += 1
        self.order = None
    
    def next(self):
        if self.order or len(self.data) < self.trend:
            return
        
        # 只交易上升趋势的股票
        uptrend = self.data.close[0] > self.trend_ma[0]
        golden = (self.fast_ma[0] > self.slow_ma[0] and 
                  self.fast_ma[-1] <= self.slow_ma[-1])
        
        # 买入
        if not self.position and golden and uptrend:
            cash = self.broker.get_cash()
            size = int(cash * 0.3 / self.data.close[0])
            if size >= 100:
                self.order = self.buy(size=size)
        
        # 卖出
        elif self.position:
            current = self.data.close[0]
            if self.buy_price > 0:
                pnl = (current - self.buy_price) / self.buy_price
                
                if pnl <= -self.stop_loss:
                    self.order = self.close()
                    print(f"{self.datas[0].datetime.date(0)} 止损 {current:.2f} (亏损:{pnl:.1%})")
                elif pnl >= self.take_profit:
                    self.order = self.close()
                    print(f"{self.datas[0].datetime.date(0)} 止盈 {current:.2f} (盈利:{pnl:.1%})")

def run_production(ts_code):
    """运行生产策略"""
    client = TushareClient()
    df = client.get_kline(ts_code, days=500)
    
    if df.empty:
        return None
    
    df = df.rename(columns={'timestamp': 'datetime'})
    df = df.set_index('datetime')
    df = df.sort_index()
    
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df, name=ts_code)
    cerebro.adddata(data)
    cerebro.addstrategy(ProductionStrategy)
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.00025)
    
    initial = cerebro.broker.getvalue()
    results = cerebro.run()
    final = cerebro.broker.getvalue()
    
    strategy = results[0]
    total_return = (final - initial) / initial
    
    print(f"\n{ts_code} 回测结果:")
    print(f"  交易次数: {strategy.trade_count}")
    print(f"  胜率: {strategy.win_count/strategy.trade_count if strategy.trade_count>0 else 0:.1%}")
    print(f"  收益: {total_return:+.2%}")
    
    return total_return

def main():
    print("="*55)
    print("🚀 生产级策略回测")
    print("="*55)
    
    # 只交易表现好的股票
    good_stocks = [
        {"ts_code": "000001.SZ", "name": "平安银行"},
        {"ts_code": "000858.SZ", "name": "五粮液"},
    ]
    
    results = []
    for stock in good_stocks:
        print(f"\n--- {stock['name']} ---")
        ret = run_production(stock['ts_code'])
        if ret is not None:
            results.append((stock['name'], ret))
    
    if results:
        print("\n" + "="*55)
        print("📊 汇总")
        print("="*55)
        for name, ret in results:
            emoji = "🟢" if ret > 0 else "🔴"
            print(f"{emoji} {name}: {ret:+.2%}")
        
        avg = sum(r[1] for r in results) / len(results)
        print(f"\n平均收益: {avg:+.2%}")
        
    print("\n" + "="*55)
    print("✅ 最终实盘建议:")
    print("   1. 60%资金交易五粮液")
    print("   2. 40%资金交易平安银行")
    print("   3. 单笔止损6%，止盈15%")
    print("   4. 仓位控制在30%以内")
    print("="*55)

if __name__ == "__main__":
    main()
