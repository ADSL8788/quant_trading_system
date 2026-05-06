#!/usr/bin/env python3
"""优化后的回测系统"""
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

class OptimizedStrategy(bt.Strategy):
    """优化后的交易策略"""
    
    params = (
        ('fast', 10),      # 快线周期
        ('slow', 30),      # 慢线周期
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('atr_period', 14),
        ('risk_percent', 0.02),
    )
    
    def __init__(self):
        # 均线系统
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.slow)
        
        # RSI（避免追涨杀跌）
        self.rsi = bt.indicators.RelativeStrengthIndex(self.data.close, period=self.p.rsi_period)
        
        # ATR（动态止损）
        self.atr = bt.indicators.AverageTrueRange(self.data, period=self.p.atr_period)
        
        # 成交量均线
        self.volume_ma = bt.indicators.SimpleMovingAverage(self.data.volume, period=20)
        
        self.order = None
        self.trade_count = 0
        
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f"{dt} {txt}")
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.trade_count += 1
            if order.isbuy():
                self.log(f'买入: {order.executed.price:.2f}')
            else:
                self.log(f'卖出: {order.executed.price:.2f}')
        self.order = None
    
    def next(self):
        if self.order:
            return
        
        # 等待足够数据
        if len(self.data) < self.p.slow:
            return
        
        # 获取信号
        fast = self.fast_ma[0]
        slow = self.slow_ma[0]
        prev_fast = self.fast_ma[-1]
        prev_slow = self.slow_ma[-1]
        
        # 金叉和死叉
        golden_cross = prev_fast <= prev_slow and fast > slow
        death_cross = prev_fast >= prev_slow and fast < slow
        
        # RSI条件
        rsi_ok = self.rsi[0] < self.p.rsi_oversold
        rsi_bad = self.rsi[0] > self.p.rsi_overbought
        
        # 成交量确认
        volume_ok = self.data.volume[0] > self.volume_ma[0]
        
        # 持仓管理
        if not self.position:
            # 买入条件
            if golden_cross and rsi_ok and volume_ok:
                cash = self.broker.get_cash()
                risk_amount = cash * self.p.risk_percent
                atr_value = self.atr[0]
                
                if atr_value > 0:
                    size = int(risk_amount / atr_value)
                    size = min(size, int(cash * 0.3 / self.data.close[0]))
                    
                    if size > 0:
                        self.order = self.buy(size=size)
                        self.log(f'🔴 BUY (RSI:{self.rsi[0]:.1f})')
        else:
            # 卖出条件
            if death_cross or rsi_bad:
                self.order = self.close()
                self.log(f'🟢 SELL (RSI:{self.rsi[0]:.1f})')
            elif self.data.close[0] < self.position.price - 2 * self.atr[0]:
                self.order = self.close()
                self.log(f'⚠️ STOP LOSS')

def run_optimized_backtest(ts_code, start_date='2023-01-01', end_date='2025-04-30'):
    """运行优化后的回测"""
    print(f"\n{'='*60}")
    print(f"优化策略回测: {ts_code}")
    print(f"{'='*60}")
    
    client = TushareClient()
    df = client.get_kline(ts_code, days=800)
    
    if df.empty:
        print(f"❌ 无法获取 {ts_code} 数据")
        return None
    
    df['date'] = pd.to_datetime(df['timestamp'])
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    df = df.rename(columns={'timestamp': 'datetime'})
    df = df.set_index('datetime')
    df = df.sort_index()
    
    print(f"数据量: {len(df)} 条")
    
    # 运行回测
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(OptimizedStrategy)
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.0003)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    initial_value = cerebro.broker.getvalue()
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    
    # 获取分析结果（修复None问题）
    strategy = results[0]
    sharpe_analyzer = strategy.analyzers.sharpe.get_analysis()
    drawdown_analyzer = strategy.analyzers.drawdown.get_analysis()
    
    sharpe_ratio = sharpe_analyzer.get('sharperatio', None)
    if sharpe_ratio is None:
        sharpe_ratio = sharpe_analyzer.get('sharperatio', 0)
        if sharpe_ratio is None:
            sharpe_ratio = 0
    
    max_drawdown = drawdown_analyzer.get('max', {})
    if isinstance(max_drawdown, dict):
        drawdown_pct = max_drawdown.get('drawdown', 0)
    else:
        drawdown_pct = 0
    
    total_return = (final_value - initial_value) / initial_value
    days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
    annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
    
    print(f"\n📈 回测结果:")
    print(f"   初始资金: {initial_value:,.0f}")
    print(f"   最终资金: {final_value:,.0f}")
    print(f"   总收益率: {total_return:+.2%}")
    print(f"   年化收益: {annual_return:+.2%}")
    print(f"   夏普比率: {sharpe_ratio:.2f}")
    print(f"   最大回撤: {drawdown_pct:.2f}%")
    print(f"   交易次数: {strategy.trade_count}")
    
    return {
        'ts_code': ts_code,
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe': sharpe_ratio,
        'max_drawdown': drawdown_pct,
        'trades': strategy.trade_count
    }

def main():
    print("="*60)
    print("🚀 优化策略回测系统")
    print("="*60)
    
    results = []
    for stock in config.WATCHLIST:
        result = run_optimized_backtest(stock['ts_code'])
        if result:
            results.append(result)
    
    print("\n" + "="*60)
    print("📊 优化策略汇总")
    print("="*60)
    
    if results:
        for r in results:
            emoji = "🟢" if r['total_return'] > 0 else "🔴"
            print(f"{emoji} {r['ts_code']}: 收益 {r['total_return']:+.2%} | "
                  f"夏普 {r['sharpe']:.2f} | 回撤 {r['max_drawdown']:.1f}% | "
                  f"交易 {r['trades']}次")
        
        avg_return = sum(r['total_return'] for r in results) / len(results)
        print(f"\n平均收益率: {avg_return:+.2%}")
        
        if avg_return > 0:
            print("✅ 优化策略表现良好！")
        else:
            print("⚠️ 仍需进一步优化")
    
    print("\n" + "="*60)
    print("💡 下一步优化建议:")
    print("1. 调整均线周期参数")
    print("2. 加入大盘趋势过滤")
    print("3. 使用周线级别信号")
    print("4. 集成DeepSeek市场情绪")
    print("="*60)

if __name__ == "__main__":
    main()
