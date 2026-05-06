#!/usr/bin/env python3
"""最终实战策略 - 基于回测结果优化"""
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

class FinalStrategy(bt.Strategy):
    """最终优化策略 - 结合实战经验"""
    
    params = (
        # 均线参数（根据不同股票微调）
        ('fast', 5),
        ('slow', 20),
        ('trend', 60),
        
        # 风控参数
        ('stop_loss', 0.06),      # 6%止损
        ('take_profit', 0.12),    # 12%止盈
        ('trailing_stop', 0.05),  # 5%移动止损
        
        # 仓位管理
        ('position_size', 0.3),   # 30%仓位
    )
    
    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.slow)
        self.trend_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.trend)
        
        self.order = None
        self.buy_price = 0
        self.buy_date = None
        self.highest_price = 0  # 移动止损用
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
                self.highest_price = order.executed.price
                self.log(f'📈 买入 {order.executed.price:.2f}')
            else:
                profit = (order.executed.price - self.buy_price) / self.buy_price
                if profit > 0:
                    self.win_count += 1
                    
                # 计算持仓天数
                hold_days = (self.datas[0].datetime.date(0) - self.buy_date).days
                
                self.log(f'📉 卖出 {order.executed.price:.2f} '
                        f'(盈亏:{profit:+.2%} 持仓:{hold_days}天)')
        self.order = None
    
    def next(self):
        if self.order or len(self.data) < self.p.trend:
            return
        
        # 趋势判断
        uptrend = self.data.close[0] > self.trend_ma[0]
        
        # 金叉死叉
        golden = (self.fast_ma[0] > self.slow_ma[0] and 
                  self.fast_ma[-1] <= self.slow_ma[-1])
        death = (self.fast_ma[0] < self.slow_ma[0] and 
                 self.fast_ma[-1] >= self.slow_ma[-1])
        
        # 买入条件
        if not self.position and golden and uptrend:
            cash = self.broker.get_cash()
            size = int(cash * self.p.position_size / self.data.close[0])
            if size >= 100:
                self.order = self.buy(size=size)
                
        # 卖出条件
        elif self.position:
            current_price = self.data.close[0]
            pnl = (current_price - self.buy_price) / self.buy_price
            
            # 更新最高价
            if current_price > self.highest_price:
                self.highest_price = current_price
            
            # 移动止损
            trailing_stop_price = self.highest_price * (1 - self.p.trailing_stop)
            
            # 卖出信号
            sell_signal = False
            sell_reason = ""
            
            # 1. 死叉卖出
            if death:
                sell_signal = True
                sell_reason = "死叉信号"
            
            # 2. 止损
            elif pnl <= -self.p.stop_loss:
                sell_signal = True
                sell_reason = f"止损 ({pnl:.2%})"
            
            # 3. 止盈
            elif pnl >= self.p.take_profit:
                sell_signal = True
                sell_reason = f"止盈 ({pnl:.2%})"
            
            # 4. 移动止损
            elif current_price <= trailing_stop_price and self.highest_price > self.buy_price * 1.02:
                sell_signal = True
                sell_reason = f"移动止损 (回撤{(self.highest_price-current_price)/self.highest_price:.2%})"
            
            # 5. 跌破趋势线
            elif current_price < self.trend_ma[0]:
                sell_signal = True
                sell_reason = "跌破趋势线"
            
            if sell_signal:
                self.log(f'💡 {sell_reason}')
                self.order = self.close()

def run_final_backtest(ts_code, start_date='2023-01-01', end_date='2025-04-30'):
    print(f"\n{'='*55}")
    print(f"最终策略回测: {ts_code}")
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
    
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(FinalStrategy)
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.00025)
    
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
    print("🎯 最终实战策略回测")
    print("="*55)
    
    results = []
    for stock in config.WATCHLIST:
        result = run_final_backtest(stock['ts_code'])
        if result:
            results.append(result)
    
    print("\n" + "="*55)
    print("📊 策略评估")
    print("="*55)
    
    total_return_sum = 0
    for r in results:
        emoji = "🟢" if r['total_return'] > 0 else "🔴"
        print(f"{emoji} {r['ts_code']}: 收益 {r['total_return']:+.2%} | "
              f"年化 {r['annual_return']:+.2%} | "
              f"交易 {r['trades']}次 | 胜率 {r['win_rate']:.1%}")
        total_return_sum += r['total_return']
    
    if results:
        avg_return = total_return_sum / len(results)
        print(f"\n{'='*55}")
        print(f"平均收益率: {avg_return:+.2%}")
        
        # 综合建议
        if avg_return > 0.10:
            print("🎉 策略优秀！建议实盘测试")
        elif avg_return > 0.05:
            print("👍 策略良好，可小仓位测试")
        elif avg_return > 0:
            print("📈 策略盈利，继续优化")
        else:
            print("⚠️ 策略亏损，建议使用第一版实用策略")
    
    print("\n" + "="*55)
    print("💡 实盘建议:")
    print("1. 优先交易五粮液和平安银行（历史表现好）")
    print("2. 贵州茅台波动大，建议降低仓位")
    print("3. 使用移动止盈止损，让利润奔跑")
    print("4. 关注大盘趋势，熊市减少交易")
    print("="*55)

if __name__ == "__main__":
    main()
